"""OPD: out-patient list, patient profile and visit pages for /hms.

A "visit" is a Patient Appointment (its name is the OPD number). The doctor's
consultation for it is the Patient Encounter linked to the appointment, and its
charges are the Sales Invoice the appointment was billed on.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, nowdate, nowtime

from hospital_saas.api.patients import age_from_dob
from hospital_saas.billing import default_company
from hospital_saas.utils import hhmm


def check_patient(patient):
	if not frappe.has_permission("Patient", "read", patient):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


# ---------------------------------------------------------------- OPD list


@frappe.whitelist()
def get_opd_patients(search: str | None = None, start: int = 0, page_length: int = 20):
	"""Patients with at least one OPD visit, latest visit first."""
	frappe.has_permission("Patient", "read", throw=True)
	# The site's date, not the database server's (MariaDB runs in UTC).
	conditions, values = "", {"start": cint(start), "page_length": cint(page_length), "today": nowdate()}
	if search:
		conditions = "and (p.patient_name like %(like)s or p.name like %(like)s or p.mobile like %(like)s)"
		values["like"] = f"%{search}%"
	rows = frappe.db.sql(
		f"""
		select p.name, p.patient_name, p.sex, p.dob, p.mobile, p.inpatient_status,
			count(a.name) as visits, max(timestamp(a.appointment_date, a.appointment_time)) as last_visit,
			substring_index(group_concat(a.practitioner_name order by a.appointment_date desc, a.appointment_time desc), ',', 1) as consultant
		from `tabPatient` p
		join `tabPatient Appointment` a on a.patient = p.name and a.status != 'Cancelled'
		where a.appointment_date <= %(today)s {conditions}
		group by p.name
		order by last_visit desc
		limit %(page_length)s offset %(start)s
		""",
		values,
		as_dict=True,
	)
	total = frappe.db.sql(
		f"""select count(distinct p.name) from `tabPatient` p
		join `tabPatient Appointment` a on a.patient = p.name and a.status != 'Cancelled'
		where a.appointment_date <= %(today)s {conditions}""",
		values,
	)[0][0]
	for row in rows:
		row.age = age_from_dob(row.dob)
	return {"rows": rows, "total": total}


# ---------------------------------------------------------------- patient profile


def patient_header(patient):
	p = frappe.db.get_value(
		"Patient",
		patient,
		[
			"name", "patient_name", "sex", "dob", "mobile", "email", "blood_group", "image",
			"allergies", "medical_history", "surgical_history", "patient_details", "inpatient_status",
			"marital_status", "occupation", "creation",
		],
		as_dict=True,
	)
	if not p:
		frappe.throw(_("Patient {0} not found").format(patient), frappe.DoesNotExistError)
	p.age = age_from_dob(p.dob)
	p.address = (p.patient_details or "").removeprefix("Address: ")
	p.visits = frappe.db.count("Patient Appointment", {"patient": patient, "status": ["!=", "Cancelled"], "appointment_date": ["<=", nowdate()]})
	return p


@frappe.whitelist()
def get_patient_profile(patient: str):
	check_patient(patient)
	header = patient_header(patient)
	encounters = frappe.get_list(
		"Patient Encounter", filters={"patient": patient, "docstatus": 1}, pluck="name", limit=0
	)
	symptoms = distinct_children("Patient Encounter Symptom", "complaint", encounters)
	diagnoses = distinct_children("Patient Encounter Diagnosis", "diagnosis", encounters)
	consultants = frappe.db.sql(
		"""select practitioner, practitioner_name, count(*) as visits from `tabPatient Appointment`
		where patient = %s and status != 'Cancelled' group by practitioner order by visits desc""",
		patient,
		as_dict=True,
	)
	return {
		"patient": header,
		"history": {
			"Visits": header.visits,
			"IPD": frappe.db.count("Inpatient Record", {"patient": patient}),
			"Pharmacy": pharmacy_bill_count(patient),
			"Pathology": frappe.db.count("Lab Test", {"patient": patient, "lab_test_group": ["!=", "Radiology"]}),
			"Radiology": frappe.db.count("Lab Test", {"patient": patient, "lab_test_group": "Radiology"}),
			"Ambulance": frappe.db.count("Ambulance Call", {"patient": patient}),
		},
		"symptoms": symptoms,
		"diagnoses": diagnoses,
		"consultants": consultants,
		"recent_visits": get_patient_visits(patient)[:5],
	}


def distinct_children(doctype, field, parents):
	if not parents:
		return []
	return frappe.db.sql(
		f"select distinct `{field}` from `tab{doctype}` where parent in %s order by `{field}`",
		[parents],
		pluck=True,
	)


def pharmacy_bill_count(patient):
	return frappe.db.sql(
		"""select count(distinct si.name) from `tabSales Invoice` si
		join `tabSales Invoice Item` sii on sii.parent = si.name
		where si.patient = %s and si.docstatus = 1 and sii.item_group = 'Pharmacy'""",
		patient,
	)[0][0]


@frappe.whitelist()
def get_patient_visits(patient: str):
	check_patient(patient)
	visits = frappe.get_list(
		"Patient Appointment",
		filters={"patient": patient, "status": ["!=", "Cancelled"]},
		fields=[
			"name", "appointment_date", "appointment_time", "practitioner", "practitioner_name",
			"department", "appointment_type", "status", "invoiced", "ref_sales_invoice",
		],
		order_by="appointment_date desc, appointment_time desc",
		limit=0,
	)
	encounters = {
		e.appointment: e
		for e in frappe.get_list(
			"Patient Encounter",
			filters={"patient": patient, "docstatus": ["!=", 2]},
			fields=["name", "appointment", "docstatus"],
			limit=0,
		)
	}
	for visit in visits:
		visit.appointment_time = hhmm(visit.appointment_time)
		enc = encounters.get(visit.name)
		visit.encounter = enc.name if enc else None
		visit.consulted = bool(enc and enc.docstatus == 1)
		visit.symptoms = distinct_children("Patient Encounter Symptom", "complaint", [enc.name]) if enc else []
		visit.diagnoses = distinct_children("Patient Encounter Diagnosis", "diagnosis", [enc.name]) if enc else []
	return visits


@frappe.whitelist()
def get_patient_labs(patient: str):
	check_patient(patient)
	return frappe.get_list(
		"Lab Test",
		filters={"patient": patient, "docstatus": ["!=", 2]},
		fields=["name", "lab_test_name", "date", "result_date", "status", "practitioner_name", "docstatus", "department"],
		order_by="date desc",
		limit=0,
	)


@frappe.whitelist()
def get_patient_vitals(patient: str, appointment: str | None = None):
	check_patient(patient)
	filters = {"patient": patient, "docstatus": ["!=", 2]}
	if appointment:
		filters["appointment"] = appointment
	rows = frappe.get_list(
		"Vital Signs",
		filters=filters,
		fields=[
			"name", "signs_date", "signs_time", "temperature", "pulse", "respiratory_rate",
			"bp_systolic", "bp_diastolic", "height", "weight", "bmi", "vital_signs_note", "appointment",
		],
		order_by="signs_date desc, signs_time desc",
		limit=0,
	)
	for row in rows:
		row.signs_time = hhmm(row.signs_time)
		if not row.bmi and row.height and row.weight:
			row.bmi = round(flt(row.weight) / flt(row.height) ** 2, 1)
	return rows


@frappe.whitelist()
def get_patient_timeline(patient: str):
	"""Medical record entries, described in one line each (newest first)."""
	check_patient(patient)
	rows = frappe.db.sql(
		"""select name, communication_date as date, subject, reference_doctype, reference_name, owner
		from `tabPatient Medical Record` where patient = %s
		order by communication_date desc, creation desc limit 100""",
		patient,
		as_dict=True,
	)
	return [describe_record(row) for row in rows]


def describe_record(row):
	ref, name = row.reference_doctype, row.reference_name
	entry = {"name": row.name, "date": row.date, "kind": "Note", "title": "Note", "detail": None, "reference": name}
	if ref == "Patient Encounter":
		enc = frappe.db.get_value("Patient Encounter", name, ["practitioner_name", "encounter_comment"], as_dict=True) or {}
		diagnoses = distinct_children("Patient Encounter Diagnosis", "diagnosis", [name])
		entry.update(
			kind="Consultation",
			title=f"Consultation with {enc.get('practitioner_name') or 'doctor'}",
			detail="; ".join(filter(None, [", ".join(diagnoses), enc.get("encounter_comment")])),
		)
	elif ref == "Lab Test":
		test = frappe.db.get_value("Lab Test", name, ["lab_test_name", "status"], as_dict=True) or {}
		entry.update(kind="Lab", title=f"{test.get('lab_test_name') or 'Lab test'}", detail=test.get("status"))
	elif ref == "Vital Signs":
		v = frappe.db.get_value("Vital Signs", name, ["bp_systolic", "bp_diastolic", "pulse", "temperature", "weight"], as_dict=True) or {}
		parts = [
			f"BP {v.get('bp_systolic')}/{v.get('bp_diastolic')}" if v.get("bp_systolic") else None,
			f"Pulse {v.get('pulse')}" if v.get("pulse") else None,
			f"Temp {v.get('temperature')} F" if v.get("temperature") else None,
			f"Weight {v.get('weight')} kg" if v.get("weight") else None,
		]
		entry.update(kind="Vitals", title="Vitals recorded", detail=", ".join(filter(None, parts)))
	elif ref:
		entry.update(kind=ref, title=ref, detail=frappe.utils.strip_html(row.subject or "")[:200])
	else:
		entry.update(detail=frappe.utils.strip_html(row.subject or ""))
	return entry


@frappe.whitelist(methods=["POST"])
def add_timeline_note(patient: str, note: str, date: str | None = None):
	check_patient(patient)
	doc = frappe.get_doc(
		{
			"doctype": "Patient Medical Record",
			"patient": patient,
			"subject": note,
			"communication_date": date or nowdate(),
			"status": "Open",
		}
	)
	doc.insert()
	return doc.name


# ---------------------------------------------------------------- visit


@frappe.whitelist()
def get_visit(appointment: str):
	appt = frappe.get_doc("Patient Appointment", appointment)
	appt.check_permission("read")
	check_patient(appt.patient)

	encounter = frappe.db.get_value(
		"Patient Encounter", {"appointment": appointment, "docstatus": ["!=", 2]}, "name", order_by="docstatus desc"
	)
	consultation = consultation_data(encounter) if encounter else None

	invoice = appt.ref_sales_invoice
	charges, payments, billing = [], [], {"total": 0, "paid": 0, "outstanding": 0}
	if invoice and frappe.has_permission("Sales Invoice", "read", invoice):
		si = frappe.db.get_value("Sales Invoice", invoice, ["grand_total", "outstanding_amount", "docstatus"], as_dict=True)
		charges = frappe.get_all(
			"Sales Invoice Item",
			filters={"parent": invoice},
			fields=["item_code", "item_name", "item_group", "qty", "rate", "amount", "discount_amount"],
			order_by="idx",
		)
		payments = frappe.db.sql(
			"""select pe.name, pe.posting_date, pe.mode_of_payment, pe.reference_no, per.allocated_amount as amount
			from `tabPayment Entry Reference` per join `tabPayment Entry` pe on pe.name = per.parent
			where per.reference_name = %s and pe.docstatus = 1 order by pe.posting_date""",
			invoice,
			as_dict=True,
		)
		billing = {
			"total": flt(si.grand_total),
			"paid": flt(si.grand_total) - flt(si.outstanding_amount),
			"outstanding": flt(si.outstanding_amount),
		}

	labs = frappe.get_list(
		"Lab Test",
		filters={"patient": appt.patient, "date": appt.appointment_date, "docstatus": ["!=", 2]},
		fields=["name", "lab_test_name", "date", "status", "docstatus", "practitioner_name"],
		limit=0,
	)
	return {
		"patient": patient_header(appt.patient),
		"visit": {
			"name": appt.name,
			"date": appt.appointment_date,
			"time": hhmm(appt.appointment_time),
			"status": appt.status,
			"practitioner": appt.practitioner,
			"practitioner_name": appt.practitioner_name,
			"practitioner_designation": frappe.db.get_value("Healthcare Practitioner", appt.practitioner, "designation"),
			"department": appt.department,
			"appointment_type": appt.appointment_type,
			"notes": appt.notes,
			"invoice": invoice,
		},
		"consultation": consultation,
		"charges": charges,
		"payments": payments,
		"billing": billing,
		"labs": labs,
		"vitals": get_patient_vitals(appt.patient, appointment),
		"can": {
			"consult": bool(frappe.has_permission("Patient Encounter", "create")),
			"vitals": bool(frappe.has_permission("Vital Signs", "create")),
			"pay": bool(frappe.has_permission("Payment Entry", "create")),
		},
	}


def consultation_data(encounter):
	enc = frappe.get_doc("Patient Encounter", encounter)
	if not enc.has_permission("read"):
		return None
	return {
		"name": enc.name,
		"docstatus": enc.docstatus,
		"date": enc.encounter_date,
		"practitioner_name": enc.practitioner_name,
		"symptoms": [r.complaint for r in enc.symptoms],
		"diagnoses": [r.diagnosis for r in enc.diagnosis],
		"notes": enc.encounter_comment,
		"medicines": [
			{
				"drug_code": r.drug_code,
				"drug_name": r.drug_name,
				"dosage": r.dosage,
				"period": r.period,
				"dosage_form": r.dosage_form,
				"comment": r.comment,
			}
			for r in enc.drug_prescription
		],
		"lab_tests": [
			{"lab_test_code": r.lab_test_code, "lab_test_name": r.lab_test_name, "comment": r.lab_test_comment}
			for r in enc.lab_test_prescription
		],
	}


@frappe.whitelist()
def get_consultation_options():
	return {
		"complaints": frappe.get_all("Complaint", pluck="name", order_by="name"),
		"diagnoses": frappe.get_all("Diagnosis", pluck="name", order_by="name"),
		"medicines": frappe.get_all(
			"Item",
			filters={"item_group": "Pharmacy", "disabled": 0},
			fields=["name as value", "item_name as label"],
			order_by="item_name",
		),
		"dosages": frappe.get_all("Prescription Dosage", pluck="name", order_by="name"),
		"periods": frappe.get_all("Prescription Duration", pluck="name", order_by="number asc, period asc"),
		"dosage_forms": frappe.get_all("Dosage Form", pluck="name", order_by="name"),
		"lab_tests": frappe.get_all(
			"Lab Test Template", filters={"disabled": 0}, fields=["name as value", "lab_test_name as label"], order_by="name"
		),
	}


@frappe.whitelist(methods=["POST"])
def save_consultation(appointment: str, data: dict | str, submit: int = 0):
	"""Create or update the visit's Patient Encounter; submit to finalise it."""
	from hospital_saas.api.lab import create_ordered_tests

	data = frappe.parse_json(data)
	appt = frappe.get_doc("Patient Appointment", appointment)
	appt.check_permission("read")
	name = frappe.db.get_value("Patient Encounter", {"appointment": appointment, "docstatus": 0})
	if frappe.db.exists("Patient Encounter", {"appointment": appointment, "docstatus": 1}):
		frappe.throw(_("This visit's consultation is already completed."))

	enc = frappe.get_doc("Patient Encounter", name) if name else frappe.new_doc("Patient Encounter")
	if enc.is_new():
		enc.update(
			{
				"patient": appt.patient,
				"appointment": appt.name,
				"appointment_type": appt.appointment_type,
				"practitioner": appt.practitioner,
				"medical_department": appt.department,
				"company": appt.company or default_company(),
				"encounter_date": nowdate(),
				"encounter_time": nowtime(),
			}
		)
	enc.encounter_comment = data.get("notes")
	enc.set("symptoms", [{"complaint": c} for c in ensure_masters("Complaint", "complaints", data.get("symptoms"))])
	enc.set("diagnosis", [{"diagnosis": d} for d in ensure_masters("Diagnosis", "diagnosis", data.get("diagnoses"))])
	enc.set(
		"drug_prescription",
		[
			{
				"drug_code": m.get("drug_code"),
				"dosage": m.get("dosage"),
				"period": m.get("period"),
				"dosage_form": m.get("dosage_form") or "Tablet",
				"comment": m.get("comment"),
			}
			for m in data.get("medicines") or []
			if m.get("drug_code")
		],
	)
	enc.set(
		"lab_test_prescription",
		[{"lab_test_code": t.get("lab_test_code"), "lab_test_comment": t.get("comment")} for t in data.get("lab_tests") or [] if t.get("lab_test_code")],
	)
	enc.save()
	if cint(submit):
		enc.submit()
		create_ordered_tests(enc)
		if appt.status in ("Open", "Scheduled", "Checked In", "Confirmed"):
			frappe.db.set_value("Patient Appointment", appt.name, "status", "Checked Out")
	return enc.name


def ensure_masters(doctype, fieldname, values):
	"""Free-typed symptoms and diagnoses become new masters, like Smart Hospital allows."""
	result = []
	for value in values or []:
		value = (value or "").strip()
		if not value:
			continue
		if not frappe.db.exists(doctype, value):
			frappe.get_doc({"doctype": doctype, fieldname: value}).insert(ignore_permissions=True)
		result.append(value)
	return result


@frappe.whitelist(methods=["POST"])
def add_vitals(appointment: str, temperature=None, pulse=None, respiratory_rate=None, bp_systolic=None, bp_diastolic=None, height=None, weight=None, note=None):
	appt = frappe.get_doc("Patient Appointment", appointment)
	appt.check_permission("read")
	vitals = frappe.get_doc(
		{
			"doctype": "Vital Signs",
			"patient": appt.patient,
			"appointment": appt.name,
			"company": appt.company or default_company(),
			"signs_date": nowdate(),
			"signs_time": nowtime(),
			"temperature": temperature,
			"pulse": pulse,
			"respiratory_rate": respiratory_rate,
			"bp_systolic": bp_systolic,
			"bp_diastolic": bp_diastolic,
			"height": flt(height) or None,
			"weight": flt(weight) or None,
			"vital_signs_note": note,
		}
	)
	vitals.insert()
	vitals.submit()
	return vitals.name


@frappe.whitelist(methods=["POST"])
def add_payment(invoice: str, amount: float, mode_of_payment: str, reference_no: str | None = None):
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	frappe.get_doc("Sales Invoice", invoice).check_permission("read")
	outstanding = flt(frappe.db.get_value("Sales Invoice", invoice, "outstanding_amount"))
	amount = flt(amount)
	if amount <= 0 or amount > outstanding:
		frappe.throw(_("Amount must be between 1 and the due amount {0}").format(outstanding))
	company = frappe.db.get_value("Sales Invoice", invoice, "company")
	pe = get_payment_entry("Sales Invoice", invoice)
	pe.mode_of_payment = mode_of_payment
	pe.paid_to = frappe.db.get_value(
		"Mode of Payment Account", {"parent": mode_of_payment, "company": company}, "default_account"
	)
	pe.paid_amount = pe.received_amount = amount
	pe.references[0].allocated_amount = amount
	pe.reference_no = reference_no or invoice
	pe.reference_date = getdate()
	pe.insert()
	pe.submit()
	return pe.name


@frappe.whitelist(methods=["POST"])
def update_allergies(patient: str, allergies: str | None = None):
	doc = frappe.get_doc("Patient", patient)
	doc.allergies = allergies
	doc.save()
	return doc.allergies
