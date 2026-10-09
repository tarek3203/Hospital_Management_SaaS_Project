"""Role dashboards for /hms.

Every job gets the same response shape so one Vue page renders them all:
    {"cards": [...], "charts": [...], "lists": [...]}
"""

import frappe
from frappe.utils import add_days, flt, get_first_day, getdate, nowdate

from hospital_saas.api.session import get_job
from hospital_saas.utils import hhmm

# Income module per invoice line: item_group decides, OPD/IPD split by item.
IPD_ITEMS = ("IPD-VISIT", "GENERAL-WARD-BED", "PRIVATE-CABIN", "ICU-BED")
MODULE_SQL = f"""
	case
		when sii.item_group = 'Laboratory' then 'Pathology'
		when sii.item_group = 'Radiology' then 'Radiology'
		when sii.item_group = 'Pharmacy' then 'Pharmacy'
		when sii.item_code in {IPD_ITEMS} then 'IPD'
		when sii.item_group = 'Healthcare Services' then 'OPD'
		else 'Other'
	end
"""
MODULES = ["OPD", "IPD", "Pharmacy", "Pathology", "Radiology", "Other"]


@frappe.whitelist()
def get_dashboard():
	job = get_job()
	builder = {
		"Super Admin": admin_dashboard,
		"Admin": admin_dashboard,
		"Accountant": accountant_dashboard,
		"Doctor": doctor_dashboard,
		"Receptionist": reception_dashboard,
		"Nurse": nurse_dashboard,
		"Pharmacist": pharmacy_dashboard,
		"Pathologist": lab_dashboard,
		"Radiologist": lab_dashboard,
	}.get(job)
	if not builder:
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	return builder()


# ---------------------------------------------------------------- building blocks


def card(label, value, icon, fmt="number", hint=None):
	return {"label": label, "value": value, "icon": icon, "format": fmt, "hint": hint}


def income_by_module(from_date, to_date):
	rows = frappe.db.sql(
		f"""
		select {MODULE_SQL} as module, sum(sii.base_net_amount) as amount
		from `tabSales Invoice Item` sii
		join `tabSales Invoice` si on si.name = sii.parent
		where si.docstatus = 1 and si.posting_date between %s and %s
		group by module
		""",
		(from_date, to_date),
		as_dict=True,
	)
	totals = {r.module: flt(r.amount) for r in rows}
	return {m: totals.get(m, 0) for m in MODULES}


def daily_income_and_expense(days=30):
	start = add_days(nowdate(), -(days - 1))
	income = dict(
		frappe.db.sql(
			"""select posting_date, sum(paid_amount) from `tabPayment Entry`
			where docstatus = 1 and payment_type = 'Receive' and posting_date >= %s
			group by posting_date""",
			start,
		)
	)
	expense = dict(
		frappe.db.sql(
			"""select posting_date, sum(paid_amount) from `tabPayment Entry`
			where docstatus = 1 and payment_type = 'Pay' and posting_date >= %s
			group by posting_date""",
			start,
		)
	)
	data = []
	for i in range(days):
		day = getdate(add_days(start, i))
		data.append({"date": str(day), "Income": flt(income.get(day)), "Expense": flt(expense.get(day))})
	return {
		"type": "line",
		"title": "Income and expense, last 30 days",
		"data": data,
		"x": "date",
		"y": ["Income", "Expense"],
		"format": "currency",
	}


def payments_by_mode(from_date):
	rows = frappe.db.sql(
		"""select mode_of_payment as label, sum(paid_amount) as value from `tabPayment Entry`
		where docstatus = 1 and payment_type = 'Receive' and posting_date >= %s
		group by mode_of_payment order by value desc""",
		from_date,
		as_dict=True,
	)
	return {"type": "donut", "title": "Collections by payment mode, this month", "data": rows, "format": "currency"}


def appointments_by_department(from_date):
	rows = frappe.db.sql(
		"""select department as label, count(*) as value from `tabPatient Appointment`
		where appointment_date >= %s and status != 'Cancelled'
		group by department order by value desc limit 8""",
		from_date,
		as_dict=True,
	)
	return {"type": "donut", "title": "Appointments by department, this month", "data": rows}


def bed_counts():
	rows = dict(
		frappe.db.sql(
			"""select occupancy_status, count(*) from `tabHealthcare Service Unit`
			where inpatient_occupancy = 1 and is_group = 0 group by occupancy_status"""
		)
	)
	return rows.get("Occupied", 0), sum(rows.values())


def todays_appointments(filters=None, limit=10):
	filters = {"appointment_date": nowdate(), **(filters or {})}
	rows = frappe.get_list(
		"Patient Appointment",
		filters=filters,
		fields=["name", "patient_name", "practitioner_name", "appointment_time", "status"],
		order_by="appointment_time asc",
		limit=limit,
	)
	for r in rows:
		r.appointment_time = hhmm(r.appointment_time)
	return {
		"title": "Today's appointments",
		"columns": [
			{"key": "appointment_time", "label": "Time"},
			{"key": "patient_name", "label": "Patient"},
			{"key": "practitioner_name", "label": "Doctor"},
			{"key": "status", "label": "Status", "badge": True},
		],
		"rows": rows,
		"link": "/appointments",
	}


def count(doctype, filters):
	return frappe.db.count(doctype, filters)


# ---------------------------------------------------------------- per job


def admin_dashboard():
	month_start = get_first_day(nowdate())
	today_income = income_by_module(nowdate(), nowdate())
	month_income = income_by_module(month_start, nowdate())
	occupied, beds = bed_counts()
	cards = [
		card(f"{m} income", month_income[m], icon, "currency", f"Today {today_income[m]:,.0f}")
		for m, icon in [("OPD", "activity"), ("IPD", "layers"), ("Pharmacy", "package"), ("Pathology", "droplet")]
	]
	cards += [
		card("Patients", count("Patient", {}), "users"),
		card("Appointments today", count("Patient Appointment", {"appointment_date": nowdate()}), "calendar"),
		card("Admitted", count("Inpatient Record", {"status": "Admitted"}), "layers"),
		card("Bed occupancy", f"{occupied}/{beds}", "grid", "text"),
	]
	return {
		"cards": cards,
		"charts": [daily_income_and_expense(), appointments_by_department(month_start)],
		"lists": [todays_appointments()],
	}


def accountant_dashboard():
	month_start = get_first_day(nowdate())
	month_income = income_by_module(month_start, nowdate())
	outstanding = frappe.db.sql(
		"select coalesce(sum(outstanding_amount), 0) from `tabSales Invoice` where docstatus = 1"
	)[0][0]
	collected_today = frappe.db.sql(
		"""select coalesce(sum(paid_amount), 0) from `tabPayment Entry`
		where docstatus = 1 and payment_type = 'Receive' and posting_date = %s""",
		nowdate(),
	)[0][0]
	unpaid = frappe.get_list(
		"Sales Invoice",
		filters={"docstatus": 1, "outstanding_amount": [">", 0]},
		fields=["name", "patient_name", "posting_date", "grand_total", "outstanding_amount"],
		order_by="posting_date desc",
		limit=10,
	)
	return {
		"cards": [
			card("Income this month", sum(month_income.values()), "trending-up", "currency"),
			card("Collected today", collected_today, "dollar-sign", "currency"),
			card("Outstanding dues", outstanding, "alert-circle", "currency"),
			card("Unpaid invoices", count("Sales Invoice", {"docstatus": 1, "outstanding_amount": [">", 0]}), "file-text"),
		],
		"charts": [daily_income_and_expense(), payments_by_mode(month_start)],
		"lists": [
			{
				"title": "Unpaid invoices",
				"columns": [
					{"key": "name", "label": "Invoice"},
					{"key": "patient_name", "label": "Patient"},
					{"key": "posting_date", "label": "Date"},
					{"key": "outstanding_amount", "label": "Due", "format": "currency"},
				],
				"rows": unpaid,
			}
		],
	}


def doctor_dashboard():
	practitioner = frappe.db.get_value("Healthcare Practitioner", {"user_id": frappe.session.user})
	mine = {"practitioner": practitioner}
	month_start = get_first_day(nowdate())
	return {
		"cards": [
			card("My appointments today", count("Patient Appointment", {**mine, "appointment_date": nowdate()}), "calendar"),
			card("Waiting (checked in)", count("Patient Appointment", {**mine, "appointment_date": nowdate(), "status": "Checked In"}), "clock"),
			card("My inpatients", count("Inpatient Record", {"primary_practitioner": practitioner, "status": "Admitted"}), "layers"),
			card("Consultations this month", count("Patient Encounter", {**mine, "encounter_date": [">=", month_start], "docstatus": 1}), "activity"),
		],
		"charts": [visits_per_day(mine)],
		"lists": [todays_appointments(mine)],
	}


def visits_per_day(filters, days=14):
	start = add_days(nowdate(), -(days - 1))
	rows = dict(
		frappe.db.sql(
			"""select appointment_date, count(*) from `tabPatient Appointment`
			where practitioner = %s and appointment_date >= %s and status != 'Cancelled'
			group by appointment_date""",
			(filters["practitioner"], start),
		)
	)
	data = [
		{"date": str(getdate(add_days(start, i))), "Visits": rows.get(getdate(add_days(start, i)), 0)}
		for i in range(days)
	]
	return {"type": "bar", "title": "My visits, last 14 days", "data": data, "x": "date", "y": ["Visits"]}


def reception_dashboard():
	occupied, beds = bed_counts()
	today = {"appointment_date": nowdate()}
	return {
		"cards": [
			card("Appointments today", count("Patient Appointment", today), "calendar"),
			card("Checked in", count("Patient Appointment", {**today, "status": "Checked In"}), "user-check"),
			card("New patients today", count("Patient", {"creation": [">=", nowdate()]}), "user-plus"),
			card("Vacant beds", beds - occupied, "grid", hint=f"{occupied} of {beds} occupied"),
		],
		"charts": [appointments_by_department(get_first_day(nowdate()))],
		"lists": [todays_appointments(limit=15)],
	}


def nurse_dashboard():
	occupied, beds = bed_counts()
	inpatients = frappe.get_list(
		"Inpatient Record",
		filters={"status": "Admitted"},
		fields=["patient_name", "primary_practitioner_name", "admitted_datetime", "expected_length_of_stay"],
		order_by="admitted_datetime desc",
		limit=15,
	)
	return {
		"cards": [
			card("Admitted patients", count("Inpatient Record", {"status": "Admitted"}), "layers"),
			card("Vacant beds", beds - occupied, "grid", hint=f"{occupied} of {beds} occupied"),
			card("Vitals recorded today", count("Vital Signs", {"signs_date": nowdate()}), "heart"),
			card("Appointments today", count("Patient Appointment", {"appointment_date": nowdate()}), "calendar"),
		],
		"charts": [],
		"lists": [
			{
				"title": "Admitted patients",
				"columns": [
					{"key": "patient_name", "label": "Patient"},
					{"key": "primary_practitioner_name", "label": "Doctor"},
					{"key": "admitted_datetime", "label": "Admitted", "format": "datetime"},
				],
				"rows": inpatients,
			}
		],
	}


def pharmacy_dashboard():
	month_start = get_first_day(nowdate())
	month_income = income_by_module(month_start, nowdate())
	low_stock = frappe.db.sql(
		"""select b.item_code, i.item_name, b.warehouse, b.actual_qty, r.warehouse_reorder_level as reorder_level
		from `tabBin` b
		join `tabItem` i on i.name = b.item_code
		join `tabItem Reorder` r on r.parent = b.item_code and r.warehouse = b.warehouse
		where i.item_group = 'Pharmacy' and b.actual_qty <= r.warehouse_reorder_level
		order by b.actual_qty asc""",
		as_dict=True,
	)
	stock_value = frappe.db.sql(
		"""select coalesce(sum(b.stock_value), 0) from `tabBin` b
		join `tabItem` i on i.name = b.item_code where i.item_group = 'Pharmacy'"""
	)[0][0]
	return {
		"cards": [
			card("Pharmacy sales this month", month_income["Pharmacy"], "package", "currency"),
			card("Medicines", count("Item", {"item_group": "Pharmacy", "disabled": 0}), "box"),
			card("Below reorder level", len(low_stock), "alert-triangle"),
			card("Stock value", stock_value, "archive", "currency"),
		],
		"charts": [],
		"lists": [
			{
				"title": "Below reorder level",
				"columns": [
					{"key": "item_name", "label": "Medicine"},
					{"key": "warehouse", "label": "Store"},
					{"key": "actual_qty", "label": "In stock"},
					{"key": "reorder_level", "label": "Reorder at"},
				],
				"rows": low_stock,
			}
		],
	}


def lab_dashboard():
	month_start = get_first_day(nowdate())
	pending = frappe.get_list(
		"Lab Test",
		filters={"docstatus": 0},
		fields=["name", "patient_name", "lab_test_name", "date", "status"],
		order_by="date desc",
		limit=15,
	)
	return {
		"cards": [
			card("Tests today", count("Lab Test", {"date": nowdate()}), "droplet"),
			card("Pending results", count("Lab Test", {"docstatus": 0}), "clock"),
			card("Completed this month", count("Lab Test", {"docstatus": 1, "date": [">=", month_start]}), "check-circle"),
			card("Lab income this month", income_by_module(month_start, nowdate())["Pathology"], "dollar-sign", "currency"),
		],
		"charts": [tests_by_template(month_start)],
		"lists": [
			{
				"title": "Pending results",
				"columns": [
					{"key": "patient_name", "label": "Patient"},
					{"key": "lab_test_name", "label": "Test"},
					{"key": "date", "label": "Date"},
					{"key": "status", "label": "Status", "badge": True},
				],
				"rows": pending,
			}
		],
	}


def tests_by_template(from_date):
	rows = frappe.db.sql(
		"""select lab_test_name as label, count(*) as value from `tabLab Test`
		where date >= %s group by lab_test_name order by value desc limit 8""",
		from_date,
		as_dict=True,
	)
	return {"type": "donut", "title": "Tests by type, this month", "data": rows}
