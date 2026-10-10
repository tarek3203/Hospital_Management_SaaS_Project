"""Multi-branch overview: the same key numbers side by side for every branch."""

import frappe
from frappe.utils import flt, get_first_day, nowdate

from hospital_saas.billing import default_company


@frappe.whitelist()
def get_overview():
	if not {"Super Admin", "Hospital Admin", "System Manager"} & set(frappe.get_roles()):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	company = default_company()
	month_start = get_first_day(nowdate())
	rows = []
	for branch in frappe.get_all("Branch", pluck="name", order_by="name"):
		doctors = frappe.get_all("Healthcare Practitioner", filters={"hospital": ["like", f"%{branch}%"], "status": "Active"}, pluck="name")
		root = frappe.db.get_value("Healthcare Service Unit", {"healthcare_service_unit_name": f"{branch} Branch", "company": company}, ["lft", "rgt"], as_dict=True)
		beds = occupied = 0
		if root:
			beds, occupied = frappe.db.sql(
				"""select count(*), coalesce(sum(occupancy_status = 'Occupied'), 0) from `tabHealthcare Service Unit`
				where inpatient_occupancy = 1 and is_group = 0 and lft > %s and rgt < %s""",
				(root.lft, root.rgt),
			)[0]
		appts_today = frappe.db.count("Patient Appointment", {"practitioner": ["in", doctors or [""]], "appointment_date": nowdate(), "status": ["!=", "Cancelled"]})
		appts_month = frappe.db.count("Patient Appointment", {"practitioner": ["in", doctors or [""]], "appointment_date": [">=", month_start], "status": ["!=", "Cancelled"]})
		opd_income = flt(
			frappe.db.sql(
				"""select coalesce(sum(si.grand_total), 0) from `tabSales Invoice` si
				join `tabPatient Appointment` a on a.ref_sales_invoice = si.name
				where si.docstatus = 1 and si.posting_date >= %s and a.practitioner in %s""",
				(month_start, doctors or [""]),
			)[0][0]
		)
		rows.append(
			{
				"branch": branch,
				"doctors": len(doctors),
				"staff": frappe.db.count("Employee", {"branch": branch, "status": "Active"}),
				"beds": int(beds),
				"occupied": int(occupied),
				"appointments_today": appts_today,
				"appointments_month": appts_month,
				"opd_income_month": opd_income,
			}
		)
	return rows
