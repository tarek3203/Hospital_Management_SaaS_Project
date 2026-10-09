"""IPD: admitted patients, bed board, admission, transfer, rounds, nurse notes,
running bill and discharge for /hms.

An IPD stay is an Inpatient Record. Doctor rounds are Patient Encounters linked
to it, nurse notes are Patient Medical Records pointing at it, and advance
payments are Payment Entries whose reference number is the record's name.
"""

import math

import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime, getdate, now_datetime, nowdate, nowtime

from hospital_saas.api.opd import check_patient, distinct_children, ensure_masters, patient_header
from hospital_saas.billing import default_company
from hospital_saas.utils import hhmm

ACTIVE = ("Admitted", "Discharge Scheduled")


# ---------------------------------------------------------------- list and beds


@frappe.whitelist()
def get_ipd_patients(status: str = "Admitted", search: str | None = None):
	filters = {"status": ["in", ACTIVE]} if status == "Admitted" else {"status": "Discharged"}
	or_filters = None
	if search:
		like = f"%{search}%"
		or_filters = {"patient_name": ["like", like], "patient": ["like", like], "name": ["like", like]}
	rows = frappe.get_list(
		"Inpatient Record",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"name", "patient", "patient_name", "gender", "mobile", "primary_practitioner",
			"medical_department", "admitted_datetime", "discharge_datetime", "status",
			"expected_length_of_stay",
		],
		order_by="admitted_datetime desc",
		limit=200,
	)
	names = {r.primary_practitioner for r in rows if r.primary_practitioner}
	doctors = dict(frappe.get_all("Healthcare Practitioner", filters={"name": ["in", list(names)]}, fields=["name", "practitioner_name"], as_list=True)) if names else {}
	beds = current_beds([r.name for r in rows])
	for r in rows:
		r.consultant = doctors.get(r.primary_practitioner)
		r.bed = beds.get(r.name)
		r.los = length_of_stay(r.admitted_datetime, r.discharge_datetime)
	return rows


def current_beds(records):
	if not records:
		return {}
	rows = frappe.db.sql(
		"""select parent, service_unit from `tabInpatient Occupancy`
		where parent in %s order by check_in""",
		[records],
	)
	# Last occupancy wins: that is the current (or final) bed.
	return {parent: bed_label(unit) for parent, unit in rows}


def bed_label(unit):
	return (unit or "").removesuffix(f" - {frappe.db.get_value('Company', default_company(), 'abbr')}")


def length_of_stay(admitted, discharged=None):
	if not admitted:
		return 0
	end = get_datetime(discharged) if discharged else now_datetime()
	return max(1, math.ceil((end - get_datetime(admitted)).total_seconds() / 86400))


@frappe.whitelist()
def get_bed_board():
	"""Branch > floor > ward > beds, with who is in each occupied bed."""
	frappe.has_permission("Healthcare Service Unit", "read", throw=True)
	units = frappe.get_all(
		"Healthcare Service Unit",
		fields=["name", "healthcare_service_unit_name", "parent_healthcare_service_unit", "is_group", "inpatient_occupancy", "service_unit_type", "occupancy_status"],
		order_by="lft",
	)
	occupants = {
		row.service_unit: row
		for row in frappe.db.sql(
			"""select io.service_unit, ir.name as record, ir.patient, ir.patient_name, ir.admitted_datetime
			from `tabInpatient Occupancy` io join `tabInpatient Record` ir on ir.name = io.parent
			where io.left = 0 and ir.status in %s""",
			[ACTIVE],
			as_dict=True,
		)
	}
	by_name = {u.name: u for u in units}
	wards = {}
	for u in units:
		if u.is_group or not u.inpatient_occupancy:
			continue
		ward = by_name.get(u.parent_healthcare_service_unit)
		floor = by_name.get(ward.parent_healthcare_service_unit) if ward else None
		branch = by_name.get(floor.parent_healthcare_service_unit) if floor else None
		key = ward.name if ward else "Other"
		entry = wards.setdefault(
			key,
			{
				"ward": strip_branch(ward.healthcare_service_unit_name) if ward else "Other",
				"floor": strip_branch(floor.healthcare_service_unit_name) if floor else "",
				"branch": (branch.healthcare_service_unit_name if branch else "").removesuffix(" Branch"),
				"beds": [],
			},
		)
		occupant = occupants.get(u.name)
		entry["beds"].append(
			{
				"name": u.name,
				"label": strip_branch(u.healthcare_service_unit_name).replace(entry["ward"], "").strip() or u.healthcare_service_unit_name,
				"type": u.service_unit_type,
				"status": "Occupied" if occupant or u.occupancy_status == "Occupied" else "Vacant",
				"patient_name": occupant.patient_name if occupant else None,
				"record": occupant.record if occupant else None,
				"los": length_of_stay(occupant.admitted_datetime) if occupant else None,
			}
		)
	return list(wards.values())


def strip_branch(name):
	return (name or "").rsplit(" ", 1)[0] if (name or "").endswith((" DHN", " UTR")) else name


@frappe.whitelist()
def get_admission_options():
	beds = frappe.get_all(
		"Healthcare Service Unit",
		filters={"inpatient_occupancy": 1, "is_group": 0, "occupancy_status": "Vacant"},
		fields=["name", "healthcare_service_unit_name", "service_unit_type"],
		order_by="healthcare_service_unit_name",
	)
	rates = dict(frappe.get_all("Healthcare Service Unit Type", filters={"inpatient_occupancy": 1}, fields=["name", "rate"], as_list=True))
	return {
		"beds": [
			{"value": b.name, "label": strip_branch(b.healthcare_service_unit_name), "type": b.service_unit_type, "rate": flt(rates.get(b.service_unit_type))}
			for b in beds
		],
		"bed_types": [{"name": k, "rate": flt(v)} for k, v in rates.items()],
		"practitioners": frappe.get_all(
			"Healthcare Practitioner", filters={"status": "Active"}, fields=["name as value", "practitioner_name as label", "department"], order_by="practitioner_name"
		),
	}


# ---------------------------------------------------------------- admit, transfer, discharge


@frappe.whitelist(methods=["POST"])
def admit(patient: str, bed: str, practitioner: str, expected_length_of_stay: int = 3, note: str | None = None, appointment: str | None = None, advance: float = 0, mode_of_payment: str | None = None):
	from healthcare.healthcare.doctype.inpatient_record.inpatient_record import admit_patient

	frappe.has_permission("Inpatient Record", "create", throw=True)
	if frappe.db.get_value("Patient", patient, "inpatient_status") in ACTIVE:
		frappe.throw(_("Patient is already admitted."))
	doctor = frappe.db.get_value("Healthcare Practitioner", practitioner, ["department"], as_dict=True)
	record = frappe.get_doc(
		{
			"doctype": "Inpatient Record",
			"patient": patient,
			"company": default_company(),
			"primary_practitioner": practitioner,
			"admission_practitioner": practitioner,
			"medical_department": doctor.department,
			"admission_service_unit_type": frappe.db.get_value("Healthcare Service Unit", bed, "service_unit_type"),
			"scheduled_date": nowdate(),
			"admission_instruction": note,
			"expected_length_of_stay": cint(expected_length_of_stay),
			"admission_encounter": frappe.db.get_value("Patient Encounter", {"appointment": appointment, "docstatus": 1}) if appointment else None,
		}
	)
	record.insert()
	admit_patient(record, bed, now_datetime(), None)
	if flt(advance) > 0 and mode_of_payment:
		add_advance(record.name, advance, mode_of_payment)
	return record.name


@frappe.whitelist(methods=["POST"])
def transfer(record: str, bed: str):
	from healthcare.healthcare.doctype.inpatient_record.inpatient_record import transfer_patient

	doc = frappe.get_doc("Inpatient Record", record)
	doc.check_permission("write")
	for occ in doc.inpatient_occupancies:
		if not occ.left:
			occ.check_out = now_datetime()
			frappe.db.set_value("Healthcare Service Unit", occ.service_unit, "occupancy_status", "Vacant")
	transfer_patient(doc, bed, now_datetime())
	return bed_label(bed)


@frappe.whitelist(methods=["POST"])
def discharge(record: str, summary: str | None = None, followup_date: str | None = None, mode_of_payment: str | None = None):
	"""Final bill (advances applied automatically), free the bed, mark discharged."""
	from healthcare.healthcare.doctype.inpatient_record.inpatient_record import discharge_patient

	doc = frappe.get_doc("Inpatient Record", record)
	doc.check_permission("write")
	if doc.status == "Discharged":
		frappe.throw(_("Already discharged."))
	invoice = make_final_bill(doc, mode_of_payment)
	doc.discharge_note = summary
	doc.discharge_instructions = summary
	doc.followup_date = followup_date or None
	doc.discharge_practitioner = doc.primary_practitioner
	discharge_patient(doc)
	frappe.db.set_value("Patient", doc.patient, {"inpatient_status": "", "inpatient_record": None})
	return {"invoice": invoice}


def make_final_bill(doc, mode_of_payment=None):
	lines = [c for c in compute_charges(doc) if not c.get("billed")]
	if not lines:
		return None
	customer = frappe.db.get_value("Patient", doc.patient, "customer")
	invoice = frappe.get_doc(
		{
			"doctype": "Sales Invoice",
			"customer": customer,
			"patient": doc.patient,
			"company": doc.company or default_company(),
			"posting_date": nowdate(),
			"due_date": nowdate(),
			"inpatient_record": doc.name if frappe.get_meta("Sales Invoice").has_field("inpatient_record") else None,
			"allocate_advances_automatically": 1,
			"remarks": f"IPD final bill for {doc.name}",
			"items": [{"item_code": c["item_code"], "qty": c["qty"], "rate": c["rate"], "description": c["description"]} for c in lines],
		}
	)
	invoice.insert()
	invoice.submit()
	for occ in doc.inpatient_occupancies:
		frappe.db.set_value("Inpatient Occupancy", occ.name, "invoiced", 1)
	outstanding = flt(frappe.db.get_value("Sales Invoice", invoice.name, "outstanding_amount"))
	if outstanding > 0 and mode_of_payment:
		from hospital_saas.api.opd import add_payment

		add_payment(invoice.name, outstanding, mode_of_payment)
	return invoice.name


# ---------------------------------------------------------------- one stay


@frappe.whitelist()
def get_stay(record: str):
	doc = frappe.get_doc("Inpatient Record", record)
	doc.check_permission("read")
	check_patient(doc.patient)

	rounds = frappe.get_list(
		"Patient Encounter",
		filters={"inpatient_record": record, "docstatus": ["!=", 2]},
		fields=["name", "encounter_date", "encounter_time", "practitioner_name", "docstatus", "encounter_comment"],
		order_by="encounter_date desc, encounter_time desc",
		limit=0,
	)
	for r in rounds:
		r.encounter_time = hhmm(r.encounter_time)
		r.symptoms = distinct_children("Patient Encounter Symptom", "complaint", [r.name])
		r.diagnoses = distinct_children("Patient Encounter Diagnosis", "diagnosis", [r.name])
		r.medicines = frappe.get_all(
			"Drug Prescription",
			filters={"parent": r.name},
			fields=["drug_name", "dosage", "period", "dosage_form", "comment"],
			order_by="idx",
		)

	charges = compute_charges(doc)
	total = sum(flt(c["amount"]) for c in charges)
	payments = advances(doc)
	paid = sum(flt(p.amount) for p in payments)
	final_bill = frappe.db.get_value(
		"Sales Invoice", {"remarks": f"IPD final bill for {record}", "docstatus": 1}, ["name", "grand_total", "outstanding_amount"], as_dict=True
	)
	if final_bill:
		# After discharge the final invoice is the source of truth.
		payments += frappe.db.sql(
			"""select pe.name, pe.posting_date, pe.mode_of_payment, pe.reference_no, per.allocated_amount as amount
			from `tabPayment Entry Reference` per join `tabPayment Entry` pe on pe.name = per.parent
			where per.reference_name = %s and pe.docstatus = 1 and pe.reference_no != %s""",
			(final_bill.name, record),
			as_dict=True,
		)
		total = flt(final_bill.grand_total)
		paid = total - flt(final_bill.outstanding_amount)

	start = getdate(doc.admitted_datetime or doc.scheduled_date)
	end = getdate(doc.discharge_datetime) if doc.discharge_datetime else getdate()
	labs = frappe.get_list(
		"Lab Test",
		filters={"patient": doc.patient, "date": ["between", [start, end]], "docstatus": ["!=", 2]},
		fields=["name", "lab_test_name", "date", "status", "docstatus", "practitioner_name"],
		limit=0,
	)
	vitals = frappe.get_list(
		"Vital Signs",
		filters={"patient": doc.patient, "signs_date": ["between", [start, end]], "docstatus": ["!=", 2]},
		fields=["name", "signs_date", "signs_time", "temperature", "pulse", "respiratory_rate", "bp_systolic", "bp_diastolic", "height", "weight", "bmi"],
		order_by="signs_date desc, signs_time desc",
		limit=0,
	)
	for v in vitals:
		v.signs_time = hhmm(v.signs_time)

	practitioner_names = dict(
		frappe.get_all(
			"Healthcare Practitioner",
			filters={"name": ["in", [p for p in (doc.primary_practitioner, doc.secondary_practitioner) if p]]},
			fields=["name", "practitioner_name"],
			as_list=True,
		)
	)
	beds = [
		{
			"bed": bed_label(o.service_unit),
			"type": frappe.db.get_value("Healthcare Service Unit", o.service_unit, "service_unit_type"),
			"check_in": o.check_in,
			"check_out": o.check_out,
			"current": not o.left,
		}
		for o in doc.inpatient_occupancies
	]
	return {
		"patient": patient_header(doc.patient),
		"stay": {
			"name": doc.name,
			"status": doc.status,
			"admitted": doc.admitted_datetime,
			"discharged": doc.discharge_datetime,
			"los": length_of_stay(doc.admitted_datetime, doc.discharge_datetime),
			"expected_length_of_stay": doc.expected_length_of_stay,
			"consultant": practitioner_names.get(doc.primary_practitioner),
			"practitioner": doc.primary_practitioner,
			"department": doc.medical_department,
			"bed": next((b["bed"] for b in reversed(beds) if b["current"]), beds[-1]["bed"] if beds else None),
			"bed_type": next((b["type"] for b in reversed(beds) if b["current"]), None),
			"admission_note": doc.admission_instruction,
			"discharge_note": frappe.utils.strip_html(doc.discharge_note or ""),
			"followup_date": doc.followup_date,
		},
		"rounds": rounds,
		"nurse_notes": nurse_notes(record),
		"beds": beds,
		"charges": charges,
		"payments": payments,
		"billing": {"total": total, "paid": paid, "outstanding": max(total - paid, 0), "invoice": final_bill.name if final_bill else None},
		"labs": labs,
		"vitals": vitals,
		"can": {
			"round": bool(frappe.has_permission("Patient Encounter", "create")),
			"vitals": bool(frappe.has_permission("Vital Signs", "create")),
			"note": bool(frappe.has_permission("Patient Medical Record", "create")),
			"pay": bool(frappe.has_permission("Payment Entry", "create")),
			"manage": bool(frappe.has_permission("Inpatient Record", "write")) and doc.status in ACTIVE,
		},
	}


def compute_charges(doc):
	"""Running bill: bed days, doctor rounds and lab tests during the stay."""
	lines = []
	for occ in doc.inpatient_occupancies:
		unit_type = frappe.db.get_value("Healthcare Service Unit", occ.service_unit, "service_unit_type")
		rate, item = frappe.db.get_value("Healthcare Service Unit Type", unit_type, ["rate", "item_code"]) or (0, None)
		days = length_of_stay(occ.check_in, occ.check_out)
		if item:
			lines.append(
				{
					"item_code": item,
					"description": f"{unit_type}: {bed_label(occ.service_unit)}",
					"category": "Bed",
					"date": getdate(occ.check_in),
					"qty": days,
					"rate": flt(rate),
					"amount": days * flt(rate),
					"billed": occ.invoiced,
				}
			)
	visit_item = frappe.db.get_single_value("Healthcare Settings", "inpatient_visit_charge_item") or "IPD-VISIT"
	for enc in frappe.get_all(
		"Patient Encounter",
		filters={"inpatient_record": doc.name, "docstatus": 1},
		fields=["encounter_date", "practitioner", "practitioner_name"],
	):
		fee = flt(frappe.db.get_value("Healthcare Practitioner", enc.practitioner, "inpatient_visit_charge"))
		lines.append(
			{
				"item_code": visit_item,
				"description": f"Doctor visit: {enc.practitioner_name}",
				"category": "Consultant",
				"date": enc.encounter_date,
				"qty": 1,
				"rate": fee,
				"amount": fee,
				"billed": doc.status == "Discharged",
			}
		)
	return sorted(lines, key=lambda line: (line["category"] != "Bed", str(line["date"])))


def advances(doc):
	return frappe.db.sql(
		"""select name, posting_date, mode_of_payment, reference_no, paid_amount as amount
		from `tabPayment Entry` where docstatus = 1 and payment_type = 'Receive'
		and party_type = 'Customer' and party = %s and (reference_no = %s or remarks like %s)
		order by posting_date""",
		(frappe.db.get_value("Patient", doc.patient, "customer"), doc.name, f"%{doc.name}%"),
		as_dict=True,
	)


def nurse_notes(record):
	return frappe.db.sql(
		"""select name, communication_date as date, subject, owner, creation
		from `tabPatient Medical Record` where reference_doctype = 'Inpatient Record' and reference_name = %s
		order by creation desc""",
		record,
		as_dict=True,
	)


# ---------------------------------------------------------------- actions during the stay


@frappe.whitelist(methods=["POST"])
def add_nurse_note(record: str, note: str):
	doc = frappe.get_doc("Inpatient Record", record)
	doc.check_permission("read")
	check_patient(doc.patient)
	pmr = frappe.get_doc(
		{
			"doctype": "Patient Medical Record",
			"patient": doc.patient,
			"subject": note,
			"communication_date": nowdate(),
			"status": "Open",
			"reference_doctype": "Inpatient Record",
			"reference_name": record,
		}
	)
	pmr.insert()
	return pmr.name


@frappe.whitelist(methods=["POST"])
def add_advance(record: str, amount: float, mode_of_payment: str, reference_no: str | None = None):
	"""Deposit against the stay; applied to the final bill at discharge."""
	frappe.has_permission("Payment Entry", "create", throw=True)
	frappe.get_doc("Inpatient Record", record).check_permission("read")
	return make_advance(record, amount, mode_of_payment, reference_no)


def make_advance(record, amount, mode_of_payment, reference_no=None, posting_date=None):
	doc = frappe.get_doc("Inpatient Record", record)
	posting_date = posting_date or nowdate()
	company = doc.company or default_company()
	account = frappe.db.get_value("Mode of Payment Account", {"parent": mode_of_payment, "company": company}, "default_account")
	pe = frappe.get_doc(
		{
			"doctype": "Payment Entry",
			"payment_type": "Receive",
			"company": company,
			"posting_date": posting_date,
			"mode_of_payment": mode_of_payment,
			"party_type": "Customer",
			"party": frappe.db.get_value("Patient", doc.patient, "customer"),
			"paid_amount": flt(amount),
			"received_amount": flt(amount),
			"paid_to": account,
			"reference_no": record,
			"reference_date": posting_date,
			"remarks": f"IPD advance for {record}" + (f" ({reference_no})" if reference_no else ""),
		}
	)
	pe.setup_party_account_field()
	pe.set_missing_values()
	pe.insert()
	pe.submit()
	return pe.name


@frappe.whitelist(methods=["POST"])
def save_round(record: str, data: dict | str):
	"""Doctor's ward round: a submitted encounter linked to the stay."""
	from hospital_saas.api.lab import create_ordered_tests

	data = frappe.parse_json(data)
	doc = frappe.get_doc("Inpatient Record", record)
	doc.check_permission("read")
	if doc.status not in ACTIVE:
		frappe.throw(_("Patient is not admitted."))
	enc = frappe.get_doc(
		{
			"doctype": "Patient Encounter",
			"patient": doc.patient,
			"inpatient_record": record,
			"appointment_type": "Ward Round"
			if frappe.db.exists("Appointment Type", "Ward Round")
			else frappe.db.get_single_value("Healthcare Settings", "default_appointment_type"),
			"practitioner": frappe.db.get_value("Healthcare Practitioner", {"user_id": frappe.session.user}) or doc.primary_practitioner,
			"medical_department": doc.medical_department,
			"company": doc.company or default_company(),
			"encounter_date": nowdate(),
			"encounter_time": nowtime(),
			"encounter_comment": data.get("notes"),
			"symptoms": [{"complaint": c} for c in ensure_masters("Complaint", "complaints", data.get("symptoms"))],
			"diagnosis": [{"diagnosis": d} for d in ensure_masters("Diagnosis", "diagnosis", data.get("diagnoses"))],
			"drug_prescription": [
				{"drug_code": m.get("drug_code"), "dosage": m.get("dosage"), "period": m.get("period"), "dosage_form": m.get("dosage_form") or "Tablet", "comment": m.get("comment")}
				for m in data.get("medicines") or []
				if m.get("drug_code")
			],
			"lab_test_prescription": [{"lab_test_code": t.get("lab_test_code")} for t in data.get("lab_tests") or [] if t.get("lab_test_code")],
		}
	)
	enc.insert()
	enc.submit()
	create_ordered_tests(enc)
	return enc.name


@frappe.whitelist(methods=["POST"])
def add_ipd_vitals(record: str, **values):
	doc = frappe.get_doc("Inpatient Record", record)
	doc.check_permission("read")
	vitals = frappe.get_doc(
		{
			"doctype": "Vital Signs",
			"patient": doc.patient,
			"inpatient_record": record,
			"company": doc.company or default_company(),
			"signs_date": nowdate(),
			"signs_time": nowtime(),
			**{k: values.get(k) for k in ("temperature", "pulse", "respiratory_rate", "bp_systolic", "bp_diastolic") if values.get(k)},
			"height": flt(values.get("height")) or None,
			"weight": flt(values.get("weight")) or None,
			"vital_signs_note": values.get("note"),
		}
	)
	vitals.insert()
	vitals.submit()
	return vitals.name
