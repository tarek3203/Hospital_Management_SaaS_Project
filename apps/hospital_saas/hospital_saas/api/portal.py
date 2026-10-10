"""Patient portal endpoints. Every function works only on the logged-in
patient's own records, found through Patient.user_id, and reads with
ignore_permissions because portal users hold no list permissions."""

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate

from hospital_saas.api.patients import age_from_dob
from hospital_saas.api.session import get_job
from hospital_saas.billing import default_company
from hospital_saas.utils import hhmm


def my_patient():
	if get_job() != "Patient":
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return frappe.db.get_value("Patient", {"user_id": frappe.session.user}, "name")


def rows(doctype, filters, fields, order_by):
	return frappe.get_all(doctype, filters=filters, fields=fields, order_by=order_by, limit=100)


@frappe.whitelist()
def get_dashboard():
	patient = my_patient()
	p = frappe.db.get_value("Patient", patient, ["name", "patient_name", "sex", "dob", "blood_group", "mobile", "allergies", "inpatient_status"], as_dict=True)
	p.age = age_from_dob(p.dob)
	upcoming = rows(
		"Patient Appointment",
		{"patient": patient, "appointment_date": [">=", nowdate()], "status": ["in", ["Scheduled", "Open", "Confirmed", "Checked In"]]},
		["name", "appointment_date", "appointment_time", "practitioner_name", "department", "status"],
		"appointment_date asc, appointment_time asc",
	)
	for a in upcoming:
		a.appointment_time = hhmm(a.appointment_time)
	due = flt(frappe.db.sql("select coalesce(sum(outstanding_amount), 0) from `tabSales Invoice` where docstatus = 1 and patient = %s", patient)[0][0])
	return {
		"patient": p,
		"counts": {
			"Appointments": frappe.db.count("Patient Appointment", {"patient": patient}),
			"Lab reports": frappe.db.count("Lab Test", {"patient": patient, "docstatus": 1}),
			"Admissions": frappe.db.count("Inpatient Record", {"patient": patient}),
			"Bills": frappe.db.count("Sales Invoice", {"patient": patient, "docstatus": 1}),
		},
		"due": due,
		"upcoming": upcoming[:5],
	}


@frappe.whitelist()
def get_records(kind: str):
	patient = my_patient()
	if kind in ("appointments", "opd"):
		data = rows(
			"Patient Appointment",
			{"patient": patient, **({"appointment_date": ["<=", nowdate()]} if kind == "opd" else {})},
			["name", "appointment_date", "appointment_time", "practitioner_name", "department", "appointment_type", "status", "paid_amount"],
			"appointment_date desc",
		)
		for r in data:
			r.appointment_time = hhmm(r.appointment_time)
		if kind == "opd":
			for r in data:
				enc = frappe.db.get_value("Patient Encounter", {"appointment": r.name, "docstatus": 1})
				r.diagnosis = ", ".join(frappe.get_all("Patient Encounter Diagnosis", filters={"parent": enc}, pluck="diagnosis")) if enc else None
				r.prescription = bool(enc)
		return data
	if kind == "ipd":
		data = rows("Inpatient Record", {"patient": patient}, ["name", "admitted_datetime", "discharge_datetime", "status", "primary_practitioner", "medical_department"], "admitted_datetime desc")
		for r in data:
			r.consultant = frappe.db.get_value("Healthcare Practitioner", r.primary_practitioner, "practitioner_name")
		return data
	if kind in ("pathology", "radiology"):
		group = ["=", "Radiology"] if kind == "radiology" else ["!=", "Radiology"]
		return rows(
			"Lab Test",
			{"patient": patient, "lab_test_group": group, "docstatus": ["!=", 2]},
			["name", "lab_test_name", "date", "status", "docstatus", "practitioner_name"],
			"date desc",
		)
	if kind == "pharmacy":
		return frappe.db.sql(
			"""select distinct si.name, si.posting_date, si.grand_total, si.outstanding_amount
			from `tabSales Invoice` si join `tabSales Invoice Item` sii on sii.parent = si.name
			where si.docstatus = 1 and si.patient = %s and sii.item_group = 'Pharmacy'
			order by si.posting_date desc""",
			patient,
			as_dict=True,
		)
	if kind == "bills":
		return rows("Sales Invoice", {"patient": patient, "docstatus": 1}, ["name", "posting_date", "grand_total", "outstanding_amount"], "posting_date desc")
	if kind == "blood-bank":
		return rows("Blood Issue", {"patient": patient}, ["name", "issue_date", "blood_group", "component", "bag", "charge"], "issue_date desc")
	if kind == "ambulance":
		return rows("Ambulance Call", {"patient": patient}, ["name", "call_date", "vehicle", "pickup", "destination", "charge", "status"], "call_date desc")
	if kind == "live":
		return rows(
			"Live Meeting",
			{"patient": patient, "meeting_type": "Consultation"},
			["name", "title", "doctor_name", "meeting_date", "meeting_time", "status", "join_url"],
			"meeting_date desc",
		)
	if kind == "downloads":
		return rows("Shared Content", {"audience": "Patients"}, ["name", "title", "content_type", "file", "url", "upload_date"], "upload_date desc")
	if kind == "surveys":
		return rows("Survey Form", {"audience": "Patients", "is_active": 1}, ["name", "title", "description"], "creation desc")
	frappe.throw(_("Unknown section"))


@frappe.whitelist()
def get_booking_options():
	my_patient()
	return {
		"practitioners": frappe.get_all(
			"Healthcare Practitioner",
			filters={"status": "Active"},
			fields=["name", "practitioner_name", "department", "op_consulting_charge"],
			order_by="practitioner_name",
		)
	}


@frappe.whitelist()
def get_slots(practitioner: str, date: str):
	my_patient()
	if getdate(date) < getdate():
		return []
	return _slots(practitioner, date)


def _slots(practitioner, date):
	from frappe.utils import cint, now_datetime
	from healthcare.healthcare.doctype.patient_appointment.patient_appointment import get_available_slots

	doctor = frappe.get_doc("Healthcare Practitioner", practitioner)
	day = getdate(date)
	now = now_datetime()
	out = []
	for schedule in get_available_slots(doctor, day):
		booked = {}
		for appt in schedule["appointments"]:
			if appt.get("appointment_time") is not None:
				key = hhmm(appt["appointment_time"])
				booked[key] = booked.get(key, 0) + 1
		capacity = cint(schedule["service_unit_capacity"]) if schedule["allow_overlap"] else 1
		for slot in schedule["avail_slot"]:
			t = hhmm(slot.from_time)
			if day == now.date() and t <= now.strftime("%H:%M"):
				continue
			if booked.get(t, 0) < max(capacity, 1):
				out.append({"time": t, "service_unit": schedule["service_unit"]})
	return sorted(out, key=lambda s: s["time"])


@frappe.whitelist(methods=["POST"])
def book(practitioner: str, date: str, time: str):
	patient = my_patient()
	slot = next((s for s in _slots(practitioner, date) if s["time"] == time), None)
	if not slot:
		frappe.throw(_("That time is no longer available. Please pick another slot."))
	doctor = frappe.db.get_value("Healthcare Practitioner", practitioner, ["department"], as_dict=True)
	appt = frappe.get_doc(
		{
			"doctype": "Patient Appointment",
			"patient": patient,
			"practitioner": practitioner,
			"department": doctor.department,
			"appointment_type": frappe.db.get_single_value("Healthcare Settings", "default_appointment_type"),
			"appointment_for": "Practitioner",
			"appointment_date": date,
			"appointment_time": time,
			"duration": 15,
			"service_unit": slot["service_unit"],
			"company": default_company(),
			"notes": "Booked from the patient portal. Fee payable at the counter.",
		}
	)
	appt.insert(ignore_permissions=True)
	return appt.name


@frappe.whitelist(methods=["POST"])
def cancel(appointment: str):
	patient = my_patient()
	appt = frappe.get_doc("Patient Appointment", appointment)
	if appt.patient != patient:
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	if appt.status not in ("Scheduled", "Open", "Confirmed") or appt.invoiced:
		frappe.throw(_("This appointment can no longer be cancelled online. Please call the hospital."))
	frappe.db.set_value("Patient Appointment", appointment, "status", "Cancelled")
	return "Cancelled"


@frappe.whitelist()
def get_lab_report(name: str):
	"""A completed report of the patient's own, in the shape the staff report page uses."""
	patient = my_patient()
	test = frappe.get_doc("Lab Test", name)
	if test.patient != patient or test.docstatus != 1:
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	from hospital_saas.api.lab import display_status
	from hospital_saas.api.opd import patient_header

	descriptive = bool(test.descriptive_test_items)
	return {
		"patient": patient_header(patient),
		"test": {
			"name": test.name,
			"lab_test_name": test.lab_test_name,
			"group": test.lab_test_group,
			"date": test.date,
			"practitioner_name": test.practitioner_name,
			"result_date": test.result_date,
			"status": display_status(test),
			"comment": test.lab_test_comment,
			"approved_by": frappe.db.get_value("User", test.modified_by, "full_name") if test.status == "Approved" else None,
			"submitted_by": frappe.db.get_value("User", test.owner, "full_name"),
			"descriptive": descriptive,
		},
		"results": [{"name": r.name, "label": r.lab_test_particulars, "value": r.result_value} for r in test.descriptive_test_items]
		if descriptive
		else [{"name": r.name, "label": r.lab_test_event or r.lab_test_name, "value": r.result_value, "uom": r.lab_test_uom, "normal_range": r.normal_range} for r in test.normal_test_items],
	}


@frappe.whitelist()
def get_receipt(invoice: str):
	from hospital_saas.api.billing import receipt_data

	patient = my_patient()
	si = frappe.get_doc("Sales Invoice", invoice)
	if si.patient != patient or si.docstatus != 1:
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return receipt_data(si)


def patient_survey(name):
	my_patient()
	survey = frappe.get_doc("Survey Form", name)
	if survey.audience != "Patients" or not survey.is_active:
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return survey


@frappe.whitelist()
def get_survey(name: str):
	from hospital_saas.api.registers import survey_data

	data = survey_data(patient_survey(name))
	data["comments"] = []  # other patients' comments are not shown in the portal
	return data


@frappe.whitelist(methods=["POST"])
def submit_survey(name: str, answers: list | str, comment: str | None = None):
	from hospital_saas.api.registers import save_response

	survey = patient_survey(name)
	respondent = frappe.db.get_value("Patient", my_patient(), "patient_name")
	return save_response(survey, answers, respondent, comment, ignore_permissions=True)
