"""Appointment list, slot lookup and booking for /hms."""

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, nowdate

from hospital_saas.billing import create_invoice, default_company
from hospital_saas.utils import hhmm
from hospital_saas.api.session import require_staff

LIST_FIELDS = [
	"name",
	"patient",
	"patient_name",
	"practitioner",
	"practitioner_name",
	"department",
	"appointment_date",
	"appointment_time",
	"appointment_type",
	"status",
	"invoiced",
	"paid_amount",
]


@frappe.whitelist()
def get_appointments(
	date: str | None = None,
	status: str | None = None,
	practitioner: str | None = None,
	search: str | None = None,
	start: int = 0,
	page_length: int = 50,
):
	require_staff()
	filters = {"appointment_date": date or nowdate()}
	if status:
		filters["status"] = status
	if practitioner:
		filters["practitioner"] = practitioner
	or_filters = None
	if search:
		like = f"%{search}%"
		or_filters = {"patient_name": ["like", like], "patient": ["like", like], "name": ["like", like]}
	rows = frappe.get_list(
		"Patient Appointment",
		fields=LIST_FIELDS,
		filters=filters,
		or_filters=or_filters,
		order_by="appointment_time asc",
		start=cint(start),
		page_length=cint(page_length),
	)
	for row in rows:
		row.appointment_time = hhmm(row.appointment_time)
	counts = dict(
		frappe.get_list(
			"Patient Appointment",
			fields=["status", {"COUNT": "*", "as": "count"}],
			filters={k: v for k, v in filters.items() if k != "status"},
			group_by="status",
			as_list=True,
		)
	)
	return {"rows": rows, "counts": counts}


@frappe.whitelist()
def get_booking_options():
	require_staff()
	practitioners = frappe.get_list(
		"Healthcare Practitioner",
		fields=["name", "practitioner_name", "department", "op_consulting_charge", "designation"],
		filters={"status": "Active"},
		order_by="practitioner_name asc",
	)
	return {
		"departments": sorted({p.department for p in practitioners if p.department}),
		"practitioners": practitioners,
		"appointment_types": frappe.get_all("Appointment Type", pluck="name"),
		"modes_of_payment": frappe.get_all("Mode of Payment", filters={"enabled": 1}, pluck="name"),
	}


@frappe.whitelist()
def get_slots(practitioner: str, date: str):
	"""Bookable times for a doctor on a date, with how many are already booked."""
	require_staff()
	from healthcare.healthcare.doctype.patient_appointment.patient_appointment import get_available_slots

	doctor = frappe.get_doc("Healthcare Practitioner", practitioner)
	day = getdate(date)
	now = frappe.utils.now_datetime()
	slots = []
	for schedule in get_available_slots(doctor, day):
		booked = {}
		for appt in schedule["appointments"]:
			if appt.get("appointment_time") is not None:
				key = hhmm(appt["appointment_time"])
				booked[key] = booked.get(key, 0) + 1
		capacity = cint(schedule["service_unit_capacity"]) if schedule["allow_overlap"] else 1
		for slot in schedule["avail_slot"]:
			time = hhmm(slot.from_time)
			if day == now.date() and time <= now.strftime("%H:%M"):
				continue
			slots.append(
				{
					"time": time,
					"service_unit": schedule["service_unit"],
					"booked": booked.get(time, 0),
					"full": booked.get(time, 0) >= max(capacity, 1),
				}
			)
	return sorted(slots, key=lambda s: s["time"])


@frappe.whitelist(methods=["POST"])
def book_appointment(
	patient: str,
	practitioner: str,
	date: str,
	time: str,
	service_unit: str | None = None,
	appointment_type: str | None = None,
	notes: str | None = None,
	fee: float | None = None,
	mode_of_payment: str | None = None,
	paid_amount: float | None = None,
):
	require_staff()
	doctor = frappe.db.get_value(
		"Healthcare Practitioner", practitioner, ["department", "op_consulting_charge"], as_dict=True
	)
	appointment = frappe.get_doc(
		{
			"doctype": "Patient Appointment",
			"patient": patient,
			"practitioner": practitioner,
			"department": doctor.department,
			"appointment_type": appointment_type
			or frappe.db.get_single_value("Healthcare Settings", "default_appointment_type"),
			"appointment_for": "Practitioner",
			"appointment_date": date,
			"appointment_time": time,
			"duration": 15,
			"service_unit": service_unit,
			"notes": notes,
			"company": default_company(),
		}
	)
	appointment.insert()

	fee = flt(doctor.op_consulting_charge) if fee is None else flt(fee)
	paid = 0
	if mode_of_payment:
		paid = fee if paid_amount is None else min(flt(paid_amount), fee)
	invoice = None
	if fee > 0:
		invoice = create_invoice(
			patient,
			[{"item_code": consultation_item(), "qty": 1, "rate": fee}],
			mode_of_payment=mode_of_payment,
			paid_amount=paid,
		)
		appointment.db_set({"invoiced": 1, "ref_sales_invoice": invoice, "paid_amount": paid})
	return {"name": appointment.name, "invoice": invoice}


@frappe.whitelist(methods=["POST"])
def set_status(appointment: str, status: str):
	require_staff()
	from healthcare.healthcare.doctype.patient_appointment.patient_appointment import (
		check_in_appointment,
		update_status,
	)

	doc = frappe.get_doc("Patient Appointment", appointment)
	doc.check_permission("write")
	if status == "Checked In":
		check_in_appointment(appointment)
	elif status in ("Cancelled", "No Show", "Checked Out"):
		update_status(appointment, status)
	else:
		frappe.throw(_("Unsupported status {0}").format(status))
	return frappe.db.get_value("Patient Appointment", appointment, "status")


def consultation_item():
	return frappe.db.get_single_value("Healthcare Settings", "op_consulting_charge_item") or "OPD-CONSULT"
