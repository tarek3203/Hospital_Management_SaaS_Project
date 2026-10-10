"""Report catalogue for /hms: one report per Smart Hospital report group, each a
date-range query returning columns and rows (exported as CSV in the browser)."""

import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate

from hospital_saas.api.dashboard import MODULE_SQL
from hospital_saas.api.session import get_job, require_staff

MONEY = "currency"


def col(key, label, fmt=None):
	return {"key": key, "label": label, "format": fmt}


def q(sql, values):
	return frappe.db.sql(sql, values, as_dict=True)


def finance(f, t):
	return [col("day", "Date"), col("module", "Module"), col("bills", "Bills"), col("amount", "Billed", MONEY)], q(
		f"""select si.posting_date as day, {MODULE_SQL} as module, count(distinct si.name) as bills, sum(sii.base_net_amount) as amount
		from `tabSales Invoice` si join `tabSales Invoice Item` sii on sii.parent = si.name
		where si.docstatus = 1 and si.posting_date between %(f)s and %(t)s
		group by day, module order by day desc, module""",
		{"f": f, "t": t},
	)


def appointment(f, t):
	return [col("appointment_date", "Date"), col("name", "No"), col("patient_name", "Patient"), col("practitioner_name", "Doctor"), col("department", "Department"), col("status", "Status"), col("paid_amount", "Paid", MONEY)], q(
		"""select appointment_date, name, patient_name, practitioner_name, department, status, paid_amount
		from `tabPatient Appointment` where appointment_date between %(f)s and %(t)s order by appointment_date desc, appointment_time""",
		{"f": f, "t": t},
	)


def opd(f, t):
	return [col("encounter_date", "Date"), col("name", "Consultation"), col("patient_name", "Patient"), col("practitioner_name", "Doctor"), col("medical_department", "Department"), col("diagnosis", "Diagnosis")], q(
		"""select e.encounter_date, e.name, e.patient_name, e.practitioner_name, e.medical_department,
			(select group_concat(d.diagnosis separator ', ') from `tabPatient Encounter Diagnosis` d where d.parent = e.name) as diagnosis
		from `tabPatient Encounter` e where e.docstatus = 1 and e.inpatient_record is null and e.encounter_date between %(f)s and %(t)s
		order by e.encounter_date desc""",
		{"f": f, "t": t},
	)


def ipd(f, t):
	return [col("name", "IPD No"), col("patient_name", "Patient"), col("medical_department", "Department"), col("admitted", "Admitted"), col("discharged", "Discharged"), col("status", "Status")], q(
		"""select name, patient_name, medical_department, date(admitted_datetime) as admitted, date(discharge_datetime) as discharged, status
		from `tabInpatient Record` where date(admitted_datetime) between %(f)s and %(t)s or (status != 'Discharged' and date(admitted_datetime) <= %(t)s)
		order by admitted_datetime desc""",
		{"f": f, "t": t},
	)


def pharmacy(f, t):
	return [col("item_name", "Medicine"), col("qty", "Quantity sold"), col("amount", "Sales", MONEY)], q(
		"""select sii.item_name, sum(sii.qty) as qty, sum(sii.base_net_amount) as amount
		from `tabSales Invoice Item` sii join `tabSales Invoice` si on si.name = sii.parent
		where si.docstatus = 1 and sii.item_group = 'Pharmacy' and si.posting_date between %(f)s and %(t)s
		group by sii.item_name order by amount desc""",
		{"f": f, "t": t},
	)


def lab(group):
	def report(f, t):
		condition = "=" if group == "Radiology" else "!="
		return [col("lab_test_name", "Test"), col("total", "Tests"), col("completed", "Completed"), col("approved", "Approved")], q(
			f"""select lab_test_name, count(*) as total, sum(docstatus = 1) as completed, sum(status = 'Approved') as approved
			from `tabLab Test` where docstatus != 2 and lab_test_group {condition} 'Radiology' and date between %(f)s and %(t)s
			group by lab_test_name order by total desc""",
			{"f": f, "t": t},
		)

	return report


def blood_bank(f, t):
	return [col("issue_date", "Date"), col("name", "Issue"), col("patient_name", "Patient"), col("blood_group", "Group"), col("component", "Component"), col("charge", "Charge", MONEY)], q(
		"""select issue_date, name, patient_name, blood_group, component, charge from `tabBlood Issue`
		where issue_date between %(f)s and %(t)s order by issue_date desc""",
		{"f": f, "t": t},
	)


def ambulance(f, t):
	return [col("call_date", "Date"), col("name", "Call"), col("patient_name", "Patient"), col("vehicle", "Vehicle"), col("destination", "To"), col("status", "Status"), col("charge", "Charge", MONEY)], q(
		"""select call_date, name, patient_name, vehicle, destination, status, charge from `tabAmbulance Call`
		where call_date between %(f)s and %(t)s order by call_date desc""",
		{"f": f, "t": t},
	)


def birth_death(f, t):
	return [col("date", "Date"), col("kind", "Record"), col("name", "No"), col("person", "Name"), col("detail", "Detail")], q(
		"""select birth_date as date, 'Birth' as kind, name, child_name as person, concat(gender, ', mother ', mother_name) as detail
		from `tabBirth Record` where birth_date between %(f)s and %(t)s
		union all
		select death_date, 'Death', name, patient_name, cause from `tabDeath Record` where death_date between %(f)s and %(t)s
		order by date desc""",
		{"f": f, "t": t},
	)


def human_resource(f, t):
	return [col("employee_name", "Staff"), col("department", "Department"), col("present", "Present"), col("absent", "Absent"), col("leave", "On leave"), col("half_day", "Half day")], q(
		"""select employee_name, substring_index(department, ' - ', 1) as department, sum(status = 'Present') as present, sum(status = 'Absent') as absent,
			sum(status = 'On Leave') as `leave`, sum(status = 'Half Day') as half_day
		from `tabAttendance` where docstatus = 1 and attendance_date between %(f)s and %(t)s
		group by employee, employee_name, department order by employee_name""",
		{"f": f, "t": t},
	)


def tpa(f, t):
	return [col("organisation_name", "TPA"), col("contact_person", "Contact"), col("phone", "Phone"), col("discount_percent", "Agreed discount %")], q(
		"select organisation_name, contact_person, phone, discount_percent from `tabTPA Organisation` order by organisation_name", {}
	)


def inventory(f, t):
	return [col("item_name", "Item"), col("warehouse", "Store"), col("actual_qty", "In stock"), col("stock_value", "Value", MONEY)], q(
		"""select i.item_name, b.warehouse, b.actual_qty, b.stock_value from `tabBin` b join `tabItem` i on i.name = b.item_code
		order by i.item_name, b.warehouse""",
		{},
	)


def live(f, t):
	return [col("meeting_date", "Date"), col("name", "No"), col("title", "Title"), col("meeting_type", "Type"), col("doctor_name", "Doctor"), col("patient_name", "Patient"), col("status", "Status")], q(
		"""select meeting_date, name, title, meeting_type, doctor_name, patient_name, status from `tabLive Meeting`
		where meeting_date between %(f)s and %(t)s order by meeting_date desc""",
		{"f": f, "t": t},
	)


def ot(f, t):
	return [col("operation_date", "Date"), col("name", "OT No"), col("patient_name", "Patient"), col("operation_name", "Operation"), col("surgeon_name", "Surgeon"), col("status", "Status"), col("charge", "Charge", MONEY)], q(
		"""select operation_date, name, patient_name, operation_name, surgeon_name, status, charge from `tabPatient Operation`
		where operation_date between %(f)s and %(t)s order by operation_date desc""",
		{"f": f, "t": t},
	)


def patient(f, t):
	return [col("name", "Patient ID"), col("patient_name", "Name"), col("sex", "Gender"), col("mobile", "Mobile"), col("blood_group", "Blood group"), col("registered", "Registered")], q(
		"""select name, patient_name, sex, mobile, blood_group, date(creation) as registered from `tabPatient`
		where date(creation) between %(f)s and %(t)s order by creation desc""",
		{"f": f, "t": t},
	)


def audit_log(f, t):
	return [col("creation", "When"), col("owner", "User"), col("ref_doctype", "Record type"), col("docname", "Record")], q(
		"""select creation, owner, ref_doctype, docname from `tabVersion`
		where date(creation) between %(f)s and %(t)s order by creation desc limit 500""",
		{"f": f, "t": t},
	)


# key: (title, group, function, jobs allowed or None for every staff job)
ADMIN = ("Super Admin", "Admin")
REPORTS = {
	"finance": ("Income by module", "Finance", finance, ADMIN + ("Accountant",)),
	"appointment": ("Appointments", "Appointment", appointment, None),
	"opd": ("OPD consultations", "OPD", opd, None),
	"ipd": ("IPD admissions", "IPD", ipd, None),
	"pharmacy": ("Medicine sales", "Pharmacy", pharmacy, ADMIN + ("Accountant", "Pharmacist")),
	"pathology": ("Pathology tests", "Pathology", lab("Pathology"), None),
	"radiology": ("Radiology examinations", "Radiology", lab("Radiology"), None),
	"blood-bank": ("Blood issues", "Blood Bank", blood_bank, None),
	"ambulance": ("Ambulance calls", "Ambulance", ambulance, None),
	"birth-death": ("Births and deaths", "Birth Death", birth_death, None),
	"human-resource": ("Attendance summary", "Human Resource", human_resource, ADMIN),
	"tpa": ("TPA organisations", "TPA", tpa, ADMIN + ("Accountant", "Receptionist", "Doctor")),
	"inventory": ("Stock by store", "Inventory", inventory, ADMIN + ("Accountant", "Pharmacist", "Receptionist")),
	"live": ("Live consultations", "Live Consultation", live, None),
	"log": ("Audit log", "Log", audit_log, ADMIN),
	"ot": ("Operations", "OT", ot, None),
	"patient": ("Patient registrations", "Patient", patient, None),
}


def allowed(key):
	jobs = REPORTS[key][3]
	return jobs is None or get_job() in jobs


@frappe.whitelist()
def get_catalogue():
	require_staff()
	return [{"key": k, "title": v[0], "group": v[1]} for k, v in REPORTS.items() if allowed(k)]


@frappe.whitelist()
def run_report(key: str, from_date: str | None = None, to_date: str | None = None):
	require_staff()
	if key not in REPORTS or not allowed(key):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	to_date = getdate(to_date or nowdate())
	from_date = getdate(from_date or add_days(to_date, -29))
	if (to_date - from_date).days > 366:
		frappe.throw(_("Please choose a range of one year or less."))
	title, group, fn, _jobs = REPORTS[key]
	columns, rows = fn(from_date, to_date)
	return {"title": title, "group": group, "columns": columns, "rows": rows, "from_date": from_date, "to_date": to_date}
