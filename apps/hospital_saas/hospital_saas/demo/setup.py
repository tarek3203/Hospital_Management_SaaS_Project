"""Build a realistic demo hospital.

Run on a fresh site:
    bench --site hms.localhost execute hospital_saas.demo.setup.run

Each step is idempotent where practical, so a failed run can be resumed.
"""

import random
from datetime import datetime, time, timedelta

import frappe
from frappe.utils import add_days, add_months, flt, getdate, now_datetime, nowdate
from frappe.utils.password import update_password

from hospital_saas.demo import data as D
from hospital_saas.demo.rolling_dates import set_anchor
from hospital_saas.install import apply_branding
from hospital_saas.roles import demo_profile_name, setup_roles

rng = random.Random(2026)


def run():
	frappe.flags.in_demo = True
	frappe.flags.mute_emails = True
	steps = [
		complete_setup_wizard,
		setup_masters,
		setup_accounts_and_payments,
		setup_healthcare_settings,
		setup_service_units,
		setup_practitioners,
		setup_lab_templates,
		setup_clinical_masters,
		setup_pharmacy,
		setup_patients,
		setup_opd_activity,
		setup_inpatients,
		setup_staff,
		setup_users,
		apply_branding,
		set_anchor,
	]
	for step in steps:
		print(f"-> {step.__name__}")
		step()
		frappe.db.commit()
	print("Demo data ready.")


# ---------------------------------------------------------------- helpers


def ensure(doctype, name=None, **values):
	"""Insert a doc unless one with `name` (or matching values) already exists."""
	if name and frappe.db.exists(doctype, name):
		return frappe.get_doc(doctype, name)
	doc = frappe.get_doc({"doctype": doctype, **values})
	doc.insert(ignore_permissions=True)
	return doc


def company_account(account_name):
	return f"{account_name} - {D.ABBR}"


def random_phone():
	return f"+8801{rng.choice('3456789')}{rng.randint(10000000, 99999999)}"


def past_datetime(days_ago, start_hour=9, end_hour=20):
	day = add_days(nowdate(), -days_ago)
	minutes = rng.randint(start_hour * 60, end_hour * 60 - 1)
	return getdate(day), time(minutes // 60, (minutes // 15 % 4) * 15)


def set_creation(doc, dt):
	"""Back-date audit timestamps so lists and reports look lived-in."""
	frappe.db.set_value(doc.doctype, doc.name, {"creation": dt, "modified": dt}, update_modified=False)


# ---------------------------------------------------------------- setup


def complete_setup_wizard():
	if frappe.db.get_single_value("System Settings", "setup_complete"):
		return
	from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

	today = getdate()
	fy_start_year = today.year if today.month >= 7 else today.year - 1
	setup_complete(
		{
			"language": "English",
			"country": D.COUNTRY,
			"timezone": D.TIMEZONE,
			"currency": D.CURRENCY,
			"company_name": D.COMPANY,
			"company_abbr": D.ABBR,
			"chart_of_accounts": "Standard",
			"fy_start_date": f"{fy_start_year}-07-01",
			"fy_end_date": f"{fy_start_year + 1}-06-30",
			"setup_demo": 0,
		}
	)
	frappe.db.set_single_value("System Settings", {"time_zone": D.TIMEZONE, "date_format": "dd-mm-yyyy"})


def setup_masters():
	for branch in D.BRANCHES:
		ensure("Branch", branch, branch=branch)

	for dept in D.EXTRA_DEPARTMENTS:
		ensure("Medical Department", dept, department=dept)

	for dept in {s[4] for s in D.STAFF} | {"Medical"}:
		ensure("Department", f"{dept} - {D.ABBR}", department_name=dept, company=D.COMPANY)

	for designation in {s[3] for s in D.STAFF} | {d[7] for d in D.DOCTORS}:
		ensure("Designation", designation, designation_name=designation)

	for group in ["Healthcare Services", "Pharmacy"]:
		ensure("Item Group", group, item_group_name=group, parent_item_group="All Item Groups")

	for code, name, rate in [
		("OPD-CONSULT", "OPD Consultation", 1000),
		("IPD-VISIT", "Inpatient Doctor Visit", 1500),
		("REG-FEE", "Patient Registration Fee", 200),
	]:
		ensure(
			"Item",
			code,
			item_code=code,
			item_name=name,
			item_group="Healthcare Services",
			stock_uom="Nos",
			is_stock_item=0,
			include_item_in_manufacturing=0,
		)
		set_selling_price(code, rate)


def set_selling_price(item_code, rate):
	existing = frappe.db.get_value("Item Price", {"item_code": item_code, "price_list": "Standard Selling"})
	if existing:
		frappe.db.set_value("Item Price", existing, "price_list_rate", rate)
	else:
		ensure("Item Price", item_code=item_code, price_list="Standard Selling", price_list_rate=rate)


def setup_accounts_and_payments():
	parent = frappe.db.get_value("Account", {"account_name": "Bank Accounts", "company": D.COMPANY})
	for mop in D.MODES_OF_PAYMENT:
		if mop == "Cash":
			account = frappe.db.get_value("Company", D.COMPANY, "default_cash_account")
		else:
			account = company_account(f"{mop} Settlement")
			if not frappe.db.exists("Account", account):
				ensure(
					"Account",
					account_name=f"{mop} Settlement",
					parent_account=parent,
					account_type="Bank",
					company=D.COMPANY,
				)
		mode = frappe.get_doc("Mode of Payment", mop) if frappe.db.exists("Mode of Payment", mop) else None
		if not mode:
			mode = frappe.get_doc(
				{"doctype": "Mode of Payment", "mode_of_payment": mop, "type": "Cash" if mop == "Cash" else "Bank"}
			)
		if not any(a.company == D.COMPANY for a in mode.accounts):
			mode.append("accounts", {"company": D.COMPANY, "default_account": account})
		mode.save(ignore_permissions=True)


def setup_healthcare_settings():
	settings = frappe.get_doc("Healthcare Settings")
	settings.update(
		{
			"link_customer_to_patient": 1,
			"show_payment_popup": 0,
			"collect_registration_fee": 0,
			"op_consulting_charge_item": "OPD-CONSULT",
			"inpatient_visit_charge_item": "IPD-VISIT",
			"lab_test_approval_required": 0,
			"create_lab_test_on_si_submit": 0,
			"enable_free_follow_ups": 1,
			"max_visits": 1,
			"valid_days": 7,
			"allow_discharge_despite_unbilled_services": 1,
		}
	)
	settings.save(ignore_permissions=True)

	for name, booking_for, duration, color in [
		("Consultation", "Practitioner", 15, "#0e7c6b"),
		("Follow Up", "Practitioner", 10, "#3b82f6"),
		("Lab Visit", "Service Unit", 10, "#f59e0b"),
	]:
		ensure(
			"Appointment Type",
			name,
			appointment_type=name,
			allow_booking_for=booking_for,
			default_duration=duration,
			color=color,
		)
	frappe.db.set_single_value("Healthcare Settings", "default_appointment_type", "Consultation")


def setup_service_units():
	for name, inpatient, appointments, rate in D.SERVICE_UNIT_TYPES:
		values = {
			"service_unit_type": name,
			"inpatient_occupancy": inpatient,
			"allow_appointments": appointments,
		}
		if inpatient:
			values.update(
				{
					"is_billable": 1,
					"item_code": name.upper().replace(" ", "-"),
					"item_group": "Healthcare Services",
					"uom": "Nos",
					"no_of_hours": 24,
					"rate": rate,
				}
			)
		ensure("Healthcare Service Unit Type", name, **values)

	root = frappe.db.get_value(
		"Healthcare Service Unit", {"is_group": 1, "parent_healthcare_service_unit": ["in", ["", None]], "company": D.COMPANY}
	)
	for branch, wards in D.WARDS.items():
		branch_unit = unit(f"{branch} Branch", root, is_group=1)
		unit(f"OPD Chambers {short(branch)}", branch_unit, is_group=0, service_unit_type="OPD Chamber", allow_appointments=1, overlap_appointments=1, service_unit_capacity=20)
		unit(f"Laboratory {short(branch)}", branch_unit, is_group=0, service_unit_type="Laboratory", allow_appointments=1, overlap_appointments=1, service_unit_capacity=30)
		for floor, ward, unit_type, count in wards:
			floor_unit = unit(f"{floor} {short(branch)}", branch_unit, is_group=1)
			ward_unit = unit(f"{ward} {short(branch)}", floor_unit, is_group=1)
			prefix = "Cabin" if unit_type == "Private Cabin" else "Bed"
			for i in range(1, count + 1):
				unit(
					f"{ward} {prefix} {i:02d} {short(branch)}",
					ward_unit,
					is_group=0,
					service_unit_type=unit_type,
					inpatient_occupancy=1,
				)


def short(branch):
	return "DHN" if branch.startswith("Dhanmondi") else "UTR"


def unit(name, parent, **values):
	existing = frappe.db.get_value("Healthcare Service Unit", {"healthcare_service_unit_name": name, "company": D.COMPANY})
	if existing:
		return existing
	doc = frappe.get_doc(
		{
			"doctype": "Healthcare Service Unit",
			"healthcare_service_unit_name": name,
			"parent_healthcare_service_unit": parent,
			"company": D.COMPANY,
			**values,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def setup_practitioners():
	for idx, (first, last, gender, dept, branch, fee, ipd_fee, designation) in enumerate(D.DOCTORS):
		evening = idx % 2 == 0
		schedule_name = f"Dr. {first} {last} Chamber"
		slots = []
		# Bangladesh work week: Saturday to Thursday.
		for day in ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]:
			start = 17 if evening else 10
			for half_hour in range(8):
				t = datetime.combine(getdate(), time(start, 0)) + timedelta(minutes=15 * half_hour * 2)
				slots.append({"day": day, "from_time": t.time(), "to_time": (t + timedelta(minutes=15)).time()})
		ensure("Practitioner Schedule", schedule_name, schedule_name=schedule_name, time_slots=slots)

		if frappe.db.exists("Healthcare Practitioner", {"first_name": first, "last_name": last}):
			continue
		ensure(
			"Healthcare Practitioner",
			first_name=first,
			last_name=last,
			gender=gender,
			department=dept,
			designation=designation,
			hospital=f"{D.COMPANY}, {branch}",
			mobile_phone=random_phone(),
			op_consulting_charge_item="OPD-CONSULT",
			op_consulting_charge=fee,
			inpatient_visit_charge_item="IPD-VISIT",
			inpatient_visit_charge=ipd_fee,
			practitioner_schedules=[
				{"schedule": schedule_name, "service_unit": opd_unit(branch)}
			],
		)


def opd_unit(branch):
	return frappe.db.get_value(
		"Healthcare Service Unit", {"healthcare_service_unit_name": f"OPD Chambers {short(branch)}", "company": D.COMPANY}
	)


def setup_lab_templates():
	for name, dept, rate, events in D.LAB_TESTS:
		if frappe.db.exists("Lab Test Template", name):
			continue
		for _event, uom, *_ in events:
			if uom:
				ensure("Lab Test UOM", uom, lab_test_uom=uom)
		compound = len(events) > 1
		ensure(
			"Lab Test Template",
			lab_test_name=name,
			lab_test_code=name.split("(")[-1].rstrip(")").upper().replace(" ", "-")[:20],
			lab_test_group="Laboratory",
			department=dept,
			lab_test_template_type="Compound" if compound else "Single",
			is_billable=1,
			lab_test_rate=rate,
			lab_test_uom=None if compound else (events[0][1] or None),
			lab_test_normal_range=None if compound else events[0][2],
			normal_test_templates=[
				{"lab_test_event": e[0], "lab_test_uom": e[1] or None, "normal_range": e[2]} for e in events
			]
			if compound
			else [],
		)


def setup_clinical_masters():
	for diagnosis in D.DIAGNOSES:
		ensure("Diagnosis", diagnosis, diagnosis=diagnosis)
	for complaint in D.COMPLAINTS:
		ensure("Complaint", complaint, complaints=complaint)


def setup_pharmacy():
	warehouses = {}
	for branch in D.BRANCHES:
		wh_name = f"Pharmacy {short(branch)}"
		warehouses[branch] = frappe.db.get_value("Warehouse", {"warehouse_name": wh_name, "company": D.COMPANY}) or ensure(
			"Warehouse", warehouse_name=wh_name, company=D.COMPANY, parent_warehouse=company_account("All Warehouses")
		).name

	for supplier in D.SUPPLIERS:
		ensure("Supplier", supplier, supplier_name=supplier, supplier_group="All Supplier Groups", country=D.COUNTRY)

	for code, name, form, rate, qty, reorder in D.PHARMACY_ITEMS:
		if not frappe.db.exists("Item", code):
			ensure(
				"Item",
				item_code=code,
				item_name=name,
				item_group="Pharmacy",
				stock_uom="Nos",
				is_stock_item=1,
				valuation_rate=round(rate * 0.75, 2),
				reorder_levels=[
					{
						"warehouse": warehouses[D.BRANCHES[0]],
						"warehouse_group": company_account("All Warehouses"),
						"warehouse_reorder_level": reorder,
						"warehouse_reorder_qty": reorder * 2,
						"material_request_type": "Purchase",
					}
				],
			)
		set_selling_price(code, rate)

	if not frappe.db.exists("Stock Entry", {"stock_entry_type": "Material Receipt", "docstatus": 1}):
		for branch, share in [(D.BRANCHES[0], 1.0), (D.BRANCHES[1], 0.4)]:
			se = frappe.get_doc(
				{
					"doctype": "Stock Entry",
					"stock_entry_type": "Material Receipt",
					"company": D.COMPANY,
					"set_posting_time": 1,
					"posting_date": add_days(nowdate(), -60),
					"items": [
						{
							"item_code": code,
							"qty": max(1, int(qty * share)),
							"t_warehouse": warehouses[branch],
							"basic_rate": round(rate * 0.75, 2),
						}
						for code, _n, _f, rate, qty, _r in D.PHARMACY_ITEMS
					],
				}
			)
			se.insert(ignore_permissions=True)
			se.submit()

	if not frappe.db.exists("Purchase Order", {"company": D.COMPANY}):
		for i, supplier in enumerate(D.SUPPLIERS):
			po = frappe.get_doc(
				{
					"doctype": "Purchase Order",
					"supplier": supplier,
					"company": D.COMPANY,
					"transaction_date": add_days(nowdate(), -10 + i * 3),
					"schedule_date": add_days(nowdate(), 3 + i),
					"set_warehouse": warehouses[D.BRANCHES[0]],
					"items": [
						{"item_code": item[0], "qty": item[5] * 2, "rate": round(item[3] * 0.7, 2)}
						for item in rng.sample(D.PHARMACY_ITEMS, 3)
					],
				}
			)
			po.insert(ignore_permissions=True)
			if i < 2:
				po.submit()


def setup_patients(count=90):
	existing = frappe.db.count("Patient")
	for i in range(existing, count):
		gender = "Male" if i % 2 == 0 else "Female"
		first = rng.choice(D.MALE_FIRST if gender == "Male" else D.FEMALE_FIRST)
		last = rng.choice(D.LAST_NAMES)
		age = rng.choice([rng.randint(1, 12), rng.randint(18, 45), rng.randint(46, 80)])
		patient = frappe.get_doc(
			{
				"doctype": "Patient",
				"first_name": first,
				"last_name": last,
				"sex": gender,
				"dob": add_days(add_months(nowdate(), -12 * age), -rng.randint(0, 360)),
				"blood_group": rng.choice(D.BLOOD_GROUPS),
				"mobile": random_phone(),
				"phone": "",
				"email": "",
				"marital_status": "Married" if age > 25 else "Single",
				"occupation": rng.choice(["Service", "Business", "Student", "Homemaker", "Teacher", "Driver", "Retired"]),
				"patient_details": f"Address: {rng.choice(D.AREAS)}",
			}
		)
		patient.insert(ignore_permissions=True)
		set_creation(patient, datetime.combine(getdate(add_days(nowdate(), -rng.randint(1, 120))), time(10, 0)))


# ---------------------------------------------------------------- activity


def practitioners():
	return frappe.get_all(
		"Healthcare Practitioner",
		fields=["name", "department", "op_consulting_charge"],
		order_by="creation",
	)


def setup_opd_activity():
	if frappe.db.count("Patient Appointment"):
		return
	docs = practitioners()
	patients = frappe.get_all("Patient", pluck="name")

	# Past 45 days: completed visits with encounters, vitals, invoices and lab work.
	for days_ago in range(45, 0, -1):
		day = getdate(add_days(nowdate(), -days_ago))
		if day.strftime("%A") == "Friday":
			continue
		for _ in range(rng.randint(4, 9)):
			doctor = rng.choice(docs)
			outcome = rng.choices(["done", "no_show", "cancelled"], weights=[85, 9, 6])[0]
			appt = make_appointment(rng.choice(patients), doctor, day, past=True, status_override=outcome)
			if appt and outcome == "done":
				complete_visit(appt, doctor)

	# Today: a live queue for the front-desk demo.
	today = getdate(nowdate())
	for i in range(14):
		doctor = docs[i % len(docs)]
		appt = make_appointment(rng.choice(patients), doctor, today)
		if appt and i < 5:
			appt.db_set("status", "Checked In")
		if appt and i < 2:
			complete_visit(appt, doctor)

	# Upcoming week.
	for days_ahead in range(1, 8):
		day = getdate(add_days(nowdate(), days_ahead))
		if day.strftime("%A") == "Friday":
			continue
		for _ in range(rng.randint(3, 7)):
			make_appointment(rng.choice(patients), rng.choice(docs), day)


def make_appointment(patient, doctor, day, past=False, status_override=None):
	appt_time = time(rng.choice([10, 11, 12, 17, 18, 19, 20]), rng.choice([0, 15, 30, 45]))
	frappe.db.savepoint("appointment")
	try:
		appt = frappe.get_doc(
			{
				"doctype": "Patient Appointment",
				"patient": patient,
				"practitioner": doctor.name,
				"department": doctor.department,
				"appointment_type": rng.choice(["Consultation", "Consultation", "Follow Up"]),
				"appointment_for": "Practitioner",
				"appointment_date": day,
				"appointment_time": appt_time,
				"duration": 15,
				"company": D.COMPANY,
				"status": {"done": "Closed", "no_show": "No Show", "cancelled": "Cancelled"}.get(status_override),
			}
		)
		appt.insert(ignore_permissions=True)
	except frappe.ValidationError:
		# Slot clash or holiday: skip this booking, keep everything else.
		frappe.db.rollback(save_point="appointment")
		frappe.clear_last_message()
		return None
	set_creation(appt, datetime.combine(add_days(day, -rng.randint(0, 3)), time(9, 30)))
	return appt


def complete_visit(appt, doctor):
	day = getdate(appt.appointment_date)
	visit_dt = datetime.combine(day, datetime.strptime(str(appt.appointment_time), "%H:%M:%S").time())

	vitals = frappe.get_doc(
		{
			"doctype": "Vital Signs",
			"patient": appt.patient,
			"appointment": appt.name,
			"company": D.COMPANY,
			"signs_date": day,
			"signs_time": visit_dt.time(),
			"temperature": str(round(rng.uniform(97.4, 101.8), 1)),
			"pulse": str(rng.randint(64, 108)),
			"respiratory_rate": str(rng.randint(14, 22)),
			"bp_systolic": str(rng.randint(105, 165)),
			"bp_diastolic": str(rng.randint(68, 102)),
			"height": round(rng.uniform(1.48, 1.80), 2),
			"weight": round(rng.uniform(45, 92), 1),
		}
	)
	vitals.insert(ignore_permissions=True)
	vitals.submit()

	labs = rng.sample(D.LAB_TESTS, rng.choice([0, 0, 1, 1, 2]))
	meds = rng.sample(D.PHARMACY_ITEMS[:6], rng.randint(1, 3))
	encounter = frappe.get_doc(
		{
			"doctype": "Patient Encounter",
			"patient": appt.patient,
			"appointment": appt.name,
			"appointment_type": appt.appointment_type,
			"practitioner": doctor.name,
			"medical_department": doctor.department,
			"company": D.COMPANY,
			"encounter_date": day,
			"encounter_time": visit_dt.time(),
			"encounter_comment": f"Provisional diagnosis: {rng.choice(D.DIAGNOSES)}. "
			f"Presenting complaint: {', '.join(rng.sample(D.COMPLAINTS, 2))}.",
			"drug_prescription": [
				{
					"drug_code": code,
					"drug_name": name,
					"dosage": rng.choice(["1-0-1", "1-1-1", "0-0-1", "1-0-0"]),
					"period": rng.choice(["5 Day", "1 Week", "2 Week", "1 Month"]),
					"dosage_form": form,
				}
				for code, name, form, *_ in meds
			],
			"lab_test_prescription": [{"lab_test_code": lab[0]} for lab in labs],
		}
	)
	encounter.insert(ignore_permissions=True)
	encounter.submit()
	frappe.db.set_value("Patient Appointment", appt.name, "status", "Closed" if day < getdate() else "Checked Out")

	invoice_items = [
		{"item_code": "OPD-CONSULT", "qty": 1, "rate": flt(doctor.op_consulting_charge)},
	]
	for lab in labs:
		invoice_items.append({"item_code": lab_item(lab[0]), "qty": 1, "rate": lab[2]})
	invoice = make_invoice(appt.patient, day, invoice_items, paid=rng.random() > 0.12)
	frappe.db.set_value("Patient Appointment", appt.name, {"invoiced": 1, "ref_sales_invoice": invoice})

	for lab in labs:
		make_lab_test(appt.patient, doctor.name, lab, day, complete=day < getdate() or rng.random() > 0.5)


def lab_item(template):
	return frappe.db.get_value("Lab Test Template", template, "item") or frappe.db.get_value(
		"Lab Test Template", template, "lab_test_code"
	)


def make_invoice(patient, day, items, paid=True):
	customer = frappe.db.get_value("Patient", patient, "customer")
	invoice = frappe.get_doc(
		{
			"doctype": "Sales Invoice",
			"customer": customer,
			"patient": patient,
			"company": D.COMPANY,
			"set_posting_time": 1,
			"posting_date": day,
			"due_date": add_days(day, 7),
			"items": items,
		}
	)
	invoice.insert(ignore_permissions=True)
	invoice.submit()
	if paid:
		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

		pe = get_payment_entry("Sales Invoice", invoice.name)
		pe.mode_of_payment = rng.choices(D.MODES_OF_PAYMENT, weights=[55, 25, 10, 10])[0]
		pe.paid_to = frappe.db.get_value(
			"Mode of Payment Account", {"parent": pe.mode_of_payment, "company": D.COMPANY}, "default_account"
		)
		pe.posting_date = day
		pe.reference_no = f"TRX{rng.randint(100000, 999999)}"
		pe.reference_date = day
		pe.insert(ignore_permissions=True)
		pe.submit()
	return invoice.name


def make_lab_test(patient, practitioner, lab, day, complete=True):
	name, dept, _rate, events = lab
	test = frappe.get_doc(
		{
			"doctype": "Lab Test",
			"patient": patient,
			"patient_sex": frappe.db.get_value("Patient", patient, "sex"),
			"practitioner": practitioner,
			"template": name,
			"company": D.COMPANY,
			"date": day,
			"result_date": day,
		}
	)
	test.insert(ignore_permissions=True)
	if not complete:
		return
	results = {e[0]: e for e in events}
	for row in test.normal_test_items:
		event = results.get(row.lab_test_event) or results.get(row.lab_test_name) or events[0]
		_e, _uom, _range, low, high, decimals = event
		if low is None:
			row.result_value = rng.choices(["Negative", "Positive"], weights=[80, 20])[0]
		else:
			value = rng.uniform(low, high)
			row.result_value = f"{value:,.{decimals}f}" if decimals else f"{int(value):,}"
	test.save(ignore_permissions=True)
	test.submit()


def setup_inpatients():
	if frappe.db.count("Inpatient Record"):
		return
	from healthcare.healthcare.doctype.inpatient_record.inpatient_record import admit_patient

	docs = practitioners()
	patients = frappe.get_all("Patient", filters={"inpatient_status": ["in", ["", None]]}, pluck="name")
	beds = frappe.get_all(
		"Healthcare Service Unit",
		filters={"inpatient_occupancy": 1, "is_group": 0, "company": D.COMPANY},
		fields=["name", "service_unit_type"],
	)
	rng.shuffle(beds)
	rng.shuffle(patients)

	# ~55% occupancy, plus a few discharged stays for history.
	for i, bed in enumerate(beds[: int(len(beds) * 0.55)] + beds[-4:]):
		patient = patients[i]
		doctor = rng.choice(docs)
		days_ago = rng.randint(1, 9)
		admitted_on = datetime.combine(getdate(add_days(nowdate(), -days_ago)),time(rng.randint(8, 22), 0))
		record = frappe.get_doc(
			{
				"doctype": "Inpatient Record",
				"patient": patient,
				"company": D.COMPANY,
				"primary_practitioner": doctor.name,
				"admission_practitioner": doctor.name,
				"medical_department": doctor.department,
				"admission_service_unit_type": bed.service_unit_type,
				"scheduled_date": admitted_on.date(),
				"admission_instruction": f"Admit for {rng.choice(D.DIAGNOSES).lower()} management and observation.",
				"expected_length_of_stay": rng.randint(2, 7),
			}
		)
		record.insert(ignore_permissions=True)
		admit_patient(record, bed.name, admitted_on, None)
		set_creation(record, admitted_on)


# ---------------------------------------------------------------- HR & users


def setup_staff():
	people = [(s[0], s[1], s[2], s[3], s[4], s[5]) for s in D.STAFF] + [
		(d[0], d[1], d[2], d[7], "Medical", d[4]) for d in D.DOCTORS
	]
	for first, last, gender, designation, dept, branch in people:
		if frappe.db.exists("Employee", {"first_name": first, "last_name": last, "company": D.COMPANY}):
			continue
		employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": first,
				"last_name": last,
				"gender": gender,
				"date_of_birth": add_days(add_months(nowdate(), -12 * rng.randint(24, 55)), -rng.randint(0, 360)),
				"date_of_joining": add_days(nowdate(), -rng.randint(120, 2400)),
				"company": D.COMPANY,
				"department": f"{dept} - {D.ABBR}",
				"designation": designation,
				"branch": branch,
				"cell_number": random_phone(),
				"status": "Active",
			}
		)
		employee.insert(ignore_permissions=True)
		doctor = frappe.db.get_value("Healthcare Practitioner", {"first_name": first, "last_name": last})
		if doctor:
			frappe.db.set_value("Healthcare Practitioner", doctor, "employee", employee.name)

	# Two weeks of attendance so the HR dashboards have something to show.
	if frappe.db.exists("Attendance", {"company": D.COMPANY}):
		return
	employees = frappe.get_all("Employee", filters={"company": D.COMPANY}, pluck="name")
	for days_ago in range(14, 0, -1):
		day = getdate(add_days(nowdate(), -days_ago))
		if day.strftime("%A") == "Friday":
			continue
		for emp in employees:
			status = rng.choices(["Present", "Absent", "On Leave", "Half Day"], weights=[86, 4, 6, 4])[0]
			if status == "On Leave":
				status = "Present"  # leave needs allocations; keep attendance simple
			att = frappe.get_doc(
				{"doctype": "Attendance", "employee": emp, "attendance_date": day, "status": status, "company": D.COMPANY}
			)
			att.insert(ignore_permissions=True)
			att.submit()


def setup_users():
	"""Create or refresh one demo login per role profile."""
	setup_roles()
	for email, first, last, profile, doctor_idx in D.DEMO_USERS:
		if profile == "Patient":
			setup_patient_user(email)
			continue
		user = frappe.get_doc("User", email) if frappe.db.exists("User", email) else frappe.new_doc("User")
		user.update(
			{
				"email": email,
				"first_name": first,
				"last_name": last,
				"enabled": 1,
				"send_welcome_email": 0,
				"new_password": D.DEMO_PASSWORD,
			}
		)
		user.set("roles", [])
		user.set("role_profiles", [{"role_profile": demo_profile_name(profile)}])
		user.save(ignore_permissions=True)
		employee = frappe.db.get_value("Employee", {"first_name": first, "last_name": last, "company": D.COMPANY})
		if employee:
			frappe.db.set_value("Employee", employee, "user_id", email)
		if doctor_idx is not None:
			first_name, last_name = D.DOCTORS[doctor_idx][:2]
			doctor = frappe.db.get_value(
				"Healthcare Practitioner", {"first_name": first_name, "last_name": last_name}
			)
			frappe.db.set_value("Healthcare Practitioner", doctor, "user_id", email)

	for email in D.LEGACY_DEMO_USERS:
		if frappe.db.exists("User", email):
			frappe.db.set_value("User", email, "enabled", 0)


def setup_patient_user(email):
	"""Portal login for a patient who already has visits, labs and bills."""
	patient = frappe.db.get_value("Patient", {"email": email}) or frappe.db.get_value(
		"Patient Encounter", {"docstatus": 1}, "patient", order_by="encounter_date desc"
	)
	first, last = frappe.db.get_value("Patient", patient, ["first_name", "last_name"])
	frappe.db.set_value("Patient", patient, "email", email)
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first,
				"last_name": last,
				"user_type": "Website User",
				"send_welcome_email": 0,
				"roles": [{"role": "Patient"}],
			}
		).insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	user.save(ignore_permissions=True)  # recompute user_type from roles
	update_password(email, D.DEMO_PASSWORD)
	frappe.db.set_value("Patient", patient, "user_id", email)
