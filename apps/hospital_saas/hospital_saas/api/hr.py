"""Attendance (with QR kiosk check-in), duty roster and annual calendar for /hms."""

import frappe
from frappe import _
from frappe.utils import add_days, get_datetime, getdate, now_datetime, nowdate

from hospital_saas.billing import default_company
from hospital_saas.api.session import require_staff

HR_ROLES = ("HR Manager", "HR User", "System Manager")


def require_hr():
	if not set(HR_ROLES) & set(frappe.get_roles()):
		frappe.throw(_("Only HR staff can do this."), frappe.PermissionError)


@frappe.whitelist()
def get_attendance(date: str | None = None):
	require_staff()
	frappe.has_permission("Attendance", "read", throw=True)
	day = getdate(date or nowdate())
	employees = frappe.get_list(
		"Employee",
		filters={"status": "Active", "company": default_company()},
		fields=["name", "employee_name", "designation", "department", "branch"],
		order_by="employee_name",
		limit=0,
	)
	marked = {
		a.employee: a.status
		for a in frappe.get_list("Attendance", filters={"attendance_date": day, "docstatus": 1}, fields=["employee", "status"], limit=0)
	}
	checkins = {}
	for c in frappe.get_list(
		"Employee Checkin",
		filters={"time": ["between", [f"{day} 00:00:00", f"{day} 23:59:59"]]},
		fields=["employee", "time", "log_type"],
		order_by="time asc",
		limit=0,
	):
		entry = checkins.setdefault(c.employee, {})
		if c.log_type == "IN" and "in" not in entry:
			entry["in"] = get_datetime(c.time).strftime("%H:%M")
		if c.log_type == "OUT":
			entry["out"] = get_datetime(c.time).strftime("%H:%M")
	rows = []
	for e in employees:
		status = marked.get(e.name) or ("Present" if e.name in checkins else ("Not marked" if day >= getdate() else "Absent"))
		rows.append({**e, "department": (e.department or "").rsplit(" - ", 1)[0], "status": status, **checkins.get(e.name, {})})
	counts = {}
	for r in rows:
		counts[r["status"]] = counts.get(r["status"], 0) + 1
	return {"date": day, "rows": rows, "counts": counts, "can_mark": bool(set(HR_ROLES) & set(frappe.get_roles()))}


@frappe.whitelist(methods=["POST"])
def qr_checkin(code: str):
	"""Kiosk: the scanner types the employee ID from the staff card and presses Enter."""
	require_staff()
	require_hr()
	code = (code or "").strip()
	employee = frappe.db.get_value("Employee", {"name": code, "status": "Active"}, ["name", "employee_name"], as_dict=True)
	if not employee:
		frappe.throw(_("No active staff member with ID {0}").format(code))
	today = nowdate()
	last = frappe.get_all(
		"Employee Checkin",
		filters={"employee": employee.name, "time": [">=", f"{today} 00:00:00"]},
		fields=["log_type"],
		order_by="time desc",
		limit=1,
	)
	log_type = "OUT" if last and last[0].log_type == "IN" else "IN"
	frappe.get_doc({"doctype": "Employee Checkin", "employee": employee.name, "log_type": log_type, "time": now_datetime(), "device_id": "QR kiosk"}).insert()
	if log_type == "IN" and not frappe.db.exists("Attendance", {"employee": employee.name, "attendance_date": today, "docstatus": ["!=", 2]}):
		att = frappe.get_doc({"doctype": "Attendance", "employee": employee.name, "attendance_date": today, "status": "Present", "company": default_company()})
		att.insert()
		att.submit()
	return {"employee": employee.name, "employee_name": employee.employee_name, "log_type": log_type, "time": now_datetime().strftime("%H:%M")}


@frappe.whitelist(methods=["POST"])
def mark_attendance(employee: str, status: str, date: str | None = None):
	require_staff()
	require_hr()
	if status not in ("Present", "Absent", "On Leave", "Half Day"):
		frappe.throw(_("Invalid status"))
	day = date or nowdate()
	existing = frappe.db.get_value("Attendance", {"employee": employee, "attendance_date": day, "docstatus": 1})
	if existing:
		frappe.get_doc("Attendance", existing).cancel()
	att = frappe.get_doc({"doctype": "Attendance", "employee": employee, "attendance_date": day, "status": status, "company": default_company()})
	att.insert()
	att.submit()
	return status


@frappe.whitelist()
def get_roster(start: str | None = None):
	require_staff()
	frappe.has_permission("Shift Assignment", "read", throw=True)
	start = getdate(start or nowdate())
	start = add_days(start, -((start.weekday() + 2) % 7))  # weeks start on Saturday
	days = [getdate(add_days(start, i)) for i in range(7)]
	shifts = {s.name: s for s in frappe.get_all("Shift Type", fields=["name", "start_time", "end_time", "color"])}
	assignments = frappe.get_list(
		"Shift Assignment",
		filters={"docstatus": 1, "status": "Active", "start_date": ["<=", days[-1]], "end_date": [">=", days[0]]},
		fields=["employee", "employee_name", "department", "shift_type", "start_date", "end_date"],
		limit=0,
	)
	grid = {}
	for a in assignments:
		row = grid.setdefault(a.employee, {"employee": a.employee, "employee_name": a.employee_name, "department": (a.department or "").rsplit(" - ", 1)[0], "days": {}})
		for d in days:
			if getdate(a.start_date) <= d <= getdate(a.end_date or a.start_date):
				row["days"][str(d)] = a.shift_type
	return {
		"days": [str(d) for d in days],
		"rows": sorted(grid.values(), key=lambda r: (r["department"], r["employee_name"])),
		"shifts": [
			{"name": s.name, "time": f"{str(s.start_time)[:5]}-{str(s.end_time)[:5]}", "color": s.color} for s in shifts.values()
		],
	}


@frappe.whitelist()
def get_calendar():
	require_staff()
	company_list = frappe.db.get_value("Company", default_company(), "default_holiday_list")
	if not company_list:
		return {"name": None, "holidays": []}
	holidays = frappe.get_all(
		"Holiday", filters={"parent": company_list, "weekly_off": 0}, fields=["holiday_date", "description"], order_by="holiday_date"
	)
	return {"name": company_list, "holidays": holidays, "weekly_off": "Friday"}
