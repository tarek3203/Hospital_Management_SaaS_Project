"""Operation theatre bookings (Patient Operation) for OPD visits and IPD stays."""

import frappe
from frappe import _
from frappe.utils import flt

from hospital_saas.utils import hhmm

FIELDS = [
	"name", "patient", "patient_name", "inpatient_record", "appointment", "operation_name", "category",
	"status", "operation_date", "operation_time", "ot_room", "surgeon", "surgeon_name", "assistant",
	"anaesthetist", "anaesthesia_type", "pre_op_notes", "operation_notes", "result", "charge",
]
EDITABLE = [f for f in FIELDS if f not in ("name", "patient_name", "surgeon_name")]


@frappe.whitelist()
def get_operations(patient: str | None = None, record: str | None = None, appointment: str | None = None):
	filters = {}
	if record:
		filters["inpatient_record"] = record
	elif appointment:
		filters["appointment"] = appointment
	elif patient:
		filters["patient"] = patient
	else:
		frappe.throw(_("Patient, IPD or OPD number is required"))
	rows = frappe.get_list("Patient Operation", filters=filters, fields=FIELDS, order_by="operation_date desc", limit=0)
	for r in rows:
		r.operation_time = hhmm(r.operation_time)
	return {
		"rows": rows,
		"can": {"write": bool(frappe.has_permission("Patient Operation", "create"))},
		"categories": frappe.get_meta("Patient Operation").get_field("category").options.split("\n"),
		"anaesthesia": [a for a in frappe.get_meta("Patient Operation").get_field("anaesthesia_type").options.split("\n") if a],
	}


@frappe.whitelist(methods=["POST"])
def save_operation(data: dict | str):
	data = frappe.parse_json(data)
	values = {k: data.get(k) for k in EDITABLE if k in data}
	values["charge"] = flt(values.get("charge"))
	if data.get("name"):
		doc = frappe.get_doc("Patient Operation", data["name"])
		doc.update(values)
		doc.save()
	else:
		doc = frappe.get_doc({"doctype": "Patient Operation", **values})
		doc.insert()
	return doc.name
