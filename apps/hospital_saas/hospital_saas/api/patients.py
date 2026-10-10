"""Patient search, list and registration for /hms."""

import frappe
from frappe.utils import add_months, cint, getdate, nowdate
from hospital_saas.api.session import require_staff

PATIENT_FIELDS = [
	"name",
	"patient_name",
	"sex",
	"dob",
	"blood_group",
	"mobile",
	"email",
	"status",
	"inpatient_status",
	"creation",
]


@frappe.whitelist()
def get_patients(search: str | None = None, start: int = 0, page_length: int = 20):
	require_staff()
	or_filters = None
	if search:
		like = f"%{search}%"
		or_filters = {"patient_name": ["like", like], "name": ["like", like], "mobile": ["like", like]}
	rows = frappe.get_list(
		"Patient",
		fields=PATIENT_FIELDS,
		or_filters=or_filters,
		order_by="creation desc",
		start=cint(start),
		page_length=cint(page_length),
	)
	for row in rows:
		row.age = age_from_dob(row.dob)
	total = len(frappe.get_list("Patient", or_filters=or_filters, pluck="name")) if search else frappe.db.count("Patient")
	return {"rows": rows, "total": total}


@frappe.whitelist()
def search_patients(txt: str = ""):
	"""Lightweight lookup for pickers."""
	require_staff()
	like = f"%{txt}%"
	return frappe.get_list(
		"Patient",
		fields=["name", "patient_name", "mobile", "sex"],
		or_filters={"patient_name": ["like", like], "name": ["like", like], "mobile": ["like", like]},
		filters={"status": "Active"},
		order_by="modified desc",
		page_length=10,
	)


@frappe.whitelist(methods=["POST"])
def register_patient(
	first_name: str,
	sex: str,
	mobile: str,
	last_name: str | None = None,
	dob: str | None = None,
	age: int | None = None,
	blood_group: str | None = None,
	email: str | None = None,
	address: str | None = None,
	marital_status: str | None = None,
):
	require_staff()
	if not dob and age:
		dob = add_months(nowdate(), -12 * cint(age))
	patient = frappe.get_doc(
		{
			"doctype": "Patient",
			"first_name": first_name.strip(),
			"last_name": (last_name or "").strip(),
			"sex": sex,
			"dob": dob,
			"blood_group": blood_group,
			"mobile": mobile.strip(),
			"email": email,
			"marital_status": marital_status,
			"patient_details": f"Address: {address}" if address else None,
		}
	)
	patient.insert()
	return {"name": patient.name, "patient_name": patient.patient_name}


@frappe.whitelist()
def get_form_options():
	require_staff()
	return {
		"genders": frappe.get_all("Gender", pluck="name", order_by="name"),
		"blood_groups": ["A Positive", "A Negative", "B Positive", "B Negative", "O Positive", "O Negative", "AB Positive", "AB Negative"],
		"marital_statuses": ["Single", "Married", "Divorced", "Widow"],
	}


def age_from_dob(dob):
	if not dob:
		return None
	dob, today = getdate(dob), getdate()
	return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
