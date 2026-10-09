"""Pathology and Radiology worklists for /hms.

Both are Frappe Health Lab Tests. Radiology tests are the ones whose template
sits in the "Radiology" item group (descriptive reports such as X-ray or USG
findings); everything else is pathology.
"""

import frappe
from frappe import _
from frappe.utils import cint, now_datetime, nowdate, nowtime

from hospital_saas.api.opd import check_patient, patient_header
from hospital_saas.billing import default_company
from hospital_saas.utils import hhmm

RADIOLOGY_GROUP = "Radiology"


def section_filter(section):
	return ["=", RADIOLOGY_GROUP] if section == "Radiology" else ["!=", RADIOLOGY_GROUP]


def display_status(test):
	if test.docstatus == 2:
		return "Cancelled"
	if test.status == "Approved":
		return "Approved"
	if test.docstatus == 1:
		return "Report ready"
	return "Pending"


@frappe.whitelist()
def get_worklist(section: str = "Pathology", status: str | None = None, search: str | None = None, start: int = 0, page_length: int = 50):
	filters = {"lab_test_group": section_filter(section), "docstatus": ["!=", 2]}
	if status == "Pending":
		filters["docstatus"] = 0
	elif status == "Report ready":
		filters.update({"docstatus": 1, "status": ["!=", "Approved"]})
	elif status == "Approved":
		filters["status"] = "Approved"
	or_filters = None
	if search:
		like = f"%{search}%"
		or_filters = {"patient_name": ["like", like], "patient": ["like", like], "name": ["like", like], "lab_test_name": ["like", like]}
	rows = frappe.get_list(
		"Lab Test",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "patient", "patient_name", "lab_test_name", "practitioner_name", "date", "time", "result_date", "status", "docstatus", "invoiced", "inpatient_record"],
		order_by="date desc, creation desc",
		start=cint(start),
		page_length=cint(page_length),
	)
	for r in rows:
		r.time = hhmm(r.time)
		r.display_status = display_status(r)
	counts = {
		"Pending": frappe.db.count("Lab Test", {"lab_test_group": section_filter(section), "docstatus": 0}),
		"Report ready": frappe.db.count("Lab Test", {"lab_test_group": section_filter(section), "docstatus": 1, "status": ["!=", "Approved"]}),
		"Approved": frappe.db.count("Lab Test", {"lab_test_group": section_filter(section), "status": "Approved"}),
		"Today": frappe.db.count("Lab Test", {"lab_test_group": section_filter(section), "date": nowdate(), "docstatus": ["!=", 2]}),
	}
	return {"rows": rows, "counts": counts}


@frappe.whitelist()
def get_templates(section: str = "Pathology"):
	return frappe.get_all(
		"Lab Test Template",
		filters={"disabled": 0, "lab_test_group": section_filter(section)},
		fields=["name as value", "lab_test_name as label", "lab_test_rate as rate", "lab_test_template_type as type"],
		order_by="lab_test_name",
	)


@frappe.whitelist()
def get_test(name: str):
	test = frappe.get_doc("Lab Test", name)
	test.check_permission("read")
	check_patient(test.patient)
	descriptive = bool(test.descriptive_test_items)
	return {
		"patient": patient_header(test.patient),
		"test": {
			"name": test.name,
			"lab_test_name": test.lab_test_name,
			"template": test.template,
			"group": test.lab_test_group,
			"date": test.date,
			"time": hhmm(test.time),
			"practitioner_name": test.practitioner_name,
			"result_date": test.result_date,
			"status": display_status(test),
			"docstatus": test.docstatus,
			"comment": test.lab_test_comment,
			"approved_date": test.approved_date,
			"approved_by": frappe.db.get_value("User", test.modified_by, "full_name") if test.status == "Approved" else None,
			"submitted_by": frappe.db.get_value("User", test.owner, "full_name"),
			"descriptive": descriptive,
		},
		"results": [
			{"name": r.name, "label": r.lab_test_particulars, "value": r.result_value}
			for r in test.descriptive_test_items
		]
		if descriptive
		else [
			{
				"name": r.name,
				"label": r.lab_test_event or r.lab_test_name,
				"value": r.result_value,
				"uom": r.lab_test_uom,
				"normal_range": r.normal_range,
			}
			for r in test.normal_test_items
		],
		"can": {
			"edit": test.docstatus == 0 and bool(frappe.has_permission("Lab Test", "write")),
			"approve": test.docstatus == 1 and test.status != "Approved" and "LabTest Approver" in frappe.get_roles(),
		},
	}


@frappe.whitelist(methods=["POST"])
def save_results(name: str, results: list | str, comment: str | None = None, submit: int = 0):
	results = {r["name"]: r.get("value") for r in frappe.parse_json(results)}
	test = frappe.get_doc("Lab Test", name)
	if test.docstatus != 0:
		frappe.throw(_("The report is already final."))
	for row in [*test.normal_test_items, *test.descriptive_test_items]:
		if row.name in results:
			row.result_value = results[row.name]
	test.lab_test_comment = comment
	test.result_date = nowdate()
	test.save()
	if cint(submit):
		test.submit()
	return test.name


@frappe.whitelist(methods=["POST"])
def approve(name: str):
	from healthcare.healthcare.doctype.lab_test.lab_test import update_status

	if "LabTest Approver" not in frappe.get_roles():
		frappe.throw(_("Only approvers can approve reports."), frappe.PermissionError)
	test = frappe.get_doc("Lab Test", name)
	test.check_permission("write")
	if test.docstatus != 1:
		frappe.throw(_("Complete the report before approving it."))
	update_status("Approved", name)
	return "Approved"


@frappe.whitelist(methods=["POST"])
def create_test(patient: str, template: str, practitioner: str | None = None):
	frappe.has_permission("Lab Test", "create", throw=True)
	test = frappe.get_doc(
		{
			"doctype": "Lab Test",
			"patient": patient,
			"patient_sex": frappe.db.get_value("Patient", patient, "sex"),
			"template": template,
			"practitioner": practitioner,
			"company": default_company(),
			"date": nowdate(),
			"time": nowtime(),
			"inpatient_record": frappe.db.get_value("Patient", patient, "inpatient_record") or None,
		}
	)
	test.insert()
	return test.name


def create_ordered_tests(encounter):
	"""Draft lab tests for what the doctor ordered, so they reach the worklist."""
	for row in encounter.lab_test_prescription:
		if row.lab_test_code and not frappe.db.exists("Lab Test", {"patient": encounter.patient, "template": row.lab_test_code, "date": encounter.encounter_date}):
			frappe.get_doc(
				{
					"doctype": "Lab Test",
					"patient": encounter.patient,
					"patient_sex": frappe.db.get_value("Patient", encounter.patient, "sex"),
					"template": row.lab_test_code,
					"practitioner": encounter.practitioner,
					"company": encounter.company,
					"date": encounter.encounter_date,
					"time": now_datetime().time(),
					"inpatient_record": encounter.inpatient_record,
				}
			).insert(ignore_permissions=True)
