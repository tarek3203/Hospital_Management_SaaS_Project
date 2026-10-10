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
		setup_hospital_profile,
		setup_patient_ids,
		enrich_clinical_data,
		bill_todays_queue,
		enrich_inpatients,
		setup_lab_worklists,
		setup_operations,
		setup_pharmacy_bills,
		restock_pharmacy,
		setup_registers,
		setup_hr_extras,
		setup_finance_entries,
		setup_communication,
		enrich_demo_patient,
		setup_website_content,
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
			"patient_name_by": "Naming Series",
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
		("Ward Round", "Practitioner", 15, "#8b5cf6"),
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
			"encounter_comment": rng.choice(D.CLINICAL_NOTES),
			"symptoms": [{"complaint": c} for c in rng.sample(D.COMPLAINTS, 2)],
			"diagnosis": [{"diagnosis": rng.choice(D.DIAGNOSES)}],
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


# ---------------------------------------------------------------- polish


def setup_patient_ids():
	"""Give every patient a hospital number (HLC-PAT-YYYY-#####) instead of their name."""
	from frappe.model.naming import make_autoname

	frappe.db.set_single_value("Healthcare Settings", "patient_name_by", "Naming Series")
	for name in frappe.get_all("Patient", filters={"name": ["not like", "HLC-PAT-%"]}, order_by="creation asc", pluck="name"):
		frappe.rename_doc("Patient", name, make_autoname("HLC-PAT-.YYYY.-.#####"), force=True, show_alert=False)
	frappe.db.commit()


def enrich_clinical_data():
	"""Structured symptoms, diagnoses, allergies and a few walk-ins registered today.

	Stage 0 encounters kept these as free text; the OPD pages show them as lists.
	"""
	encounters = frappe.get_all("Patient Encounter", filters={"docstatus": 1}, fields=["name", "encounter_comment"])
	for enc in encounters:
		if frappe.db.exists("Patient Encounter Symptom", {"parent": enc.name}):
			continue
		comment = enc.encounter_comment or ""
		diagnosis = next((d for d in D.DIAGNOSES if d in comment), rng.choice(D.DIAGNOSES))
		complaints = [c for c in D.COMPLAINTS if c in comment] or rng.sample(D.COMPLAINTS, 2)
		for idx, complaint in enumerate(complaints, 1):
			add_child(enc.name, "symptoms", "Patient Encounter Symptom", idx, complaint=complaint)
		add_child(enc.name, "diagnosis", "Patient Encounter Diagnosis", 1, diagnosis=diagnosis)
		frappe.db.set_value("Patient Encounter", enc.name, "encounter_comment", rng.choice(D.CLINICAL_NOTES), update_modified=False)

	for patient in frappe.get_all("Patient", filters={"allergies": ["in", ["", None]]}, pluck="name"):
		if rng.random() < 0.35:
			frappe.db.set_value("Patient", patient, "allergies", ", ".join(rng.sample(D.ALLERGIES, rng.choice([1, 1, 2]))), update_modified=False)

	# Walk-ins registered this morning, so "new patients today" is not zero.
	if not frappe.db.count("Patient", {"creation": [">=", nowdate()]}):
		for i in range(3):
			gender = "Female" if i % 2 else "Male"
			patient = frappe.get_doc(
				{
					"doctype": "Patient",
					"first_name": rng.choice(D.FEMALE_FIRST if gender == "Female" else D.MALE_FIRST),
					"last_name": rng.choice(D.LAST_NAMES),
					"sex": gender,
					"dob": add_days(add_months(nowdate(), -12 * rng.randint(20, 60)), -rng.randint(0, 360)),
					"blood_group": rng.choice(D.BLOOD_GROUPS),
					"mobile": random_phone(),
					"patient_details": f"Address: {rng.choice(D.AREAS)}",
				}
			).insert(ignore_permissions=True)
			set_creation(patient, datetime.combine(getdate(), time(9 + i, 10)))


def add_child(parent, parentfield, doctype, idx, **values):
	row = frappe.get_doc(
		{"doctype": doctype, "parent": parent, "parenttype": "Patient Encounter", "parentfield": parentfield, "idx": idx, **values}
	)
	row.name = frappe.generate_hash(length=10)
	row.db_insert()


def bill_todays_queue():
	"""Today's patients paid the consultation fee at the front desk, as in a real OPD."""
	appointments = frappe.get_all(
		"Patient Appointment",
		filters={"appointment_date": nowdate(), "invoiced": 0, "status": ["!=", "Cancelled"]},
		fields=["name", "patient", "practitioner"],
	)
	for appt in appointments:
		fee = flt(frappe.db.get_value("Healthcare Practitioner", appt.practitioner, "op_consulting_charge"))
		invoice = make_invoice(appt.patient, getdate(), [{"item_code": "OPD-CONSULT", "qty": 1, "rate": fee}], paid=rng.random() > 0.15)
		paid = fee - flt(frappe.db.get_value("Sales Invoice", invoice, "outstanding_amount"))
		frappe.db.set_value("Patient Appointment", appt.name, {"invoiced": 1, "ref_sales_invoice": invoice, "paid_amount": paid})


def setup_hospital_profile():
	c = D.HOSPITAL_CONTACT
	frappe.db.set_value("Company", D.COMPANY, {k: c[k] for k in ("phone_no", "email", "website")})
	if not frappe.db.exists("Dynamic Link", {"link_doctype": "Company", "link_name": D.COMPANY, "parenttype": "Address"}):
		frappe.get_doc(
			{
				"doctype": "Address",
				"address_title": D.COMPANY,
				"address_type": "Billing",
				"address_line1": c["address_line1"],
				"city": c["city"],
				"pincode": c["pincode"],
				"country": D.COUNTRY,
				"is_your_company_address": 1,
				"links": [{"link_doctype": "Company", "link_name": D.COMPANY}],
			}
		).insert(ignore_permissions=True)


def enrich_inpatients():
	"""Daily rounds, vitals, nurse notes and an advance deposit for each admitted
	patient, then discharge the three longest stays so history exists."""
	from hospital_saas.api.ipd import discharge, make_advance

	ensure("Appointment Type", "Ward Round", appointment_type="Ward Round", allow_booking_for="Practitioner", default_duration=15, color="#8b5cf6")
	nurse = next((u[0] for u in D.DEMO_USERS if u[3] == "Nurse"), "Administrator")
	records = frappe.get_all(
		"Inpatient Record",
		filters={"status": "Admitted"},
		fields=["name", "patient", "primary_practitioner", "medical_department", "admitted_datetime", "admission_service_unit_type"],
		order_by="admitted_datetime asc",
	)
	for rec in records:
		if frappe.db.exists("Patient Encounter", {"inpatient_record": rec.name}):
			continue
		admitted = getdate(rec.admitted_datetime)
		diagnosis = rng.choice(D.DIAGNOSES)
		meds = rng.sample(D.PHARMACY_ITEMS, 2)
		day = admitted
		while day <= getdate():
			if day > admitted or rec.admitted_datetime.hour < 12:
				round_ = frappe.get_doc(
					{
						"doctype": "Patient Encounter",
						"patient": rec.patient,
						"inpatient_record": rec.name,
						"appointment_type": "Ward Round",
						"practitioner": rec.primary_practitioner,
						"medical_department": rec.medical_department,
						"company": D.COMPANY,
						"encounter_date": day,
						"encounter_time": time(10, rng.choice([0, 15, 30, 45])),
						"encounter_comment": rng.choice(D.CLINICAL_NOTES),
						"symptoms": [{"complaint": c} for c in rng.sample(D.COMPLAINTS, 1)],
						"diagnosis": [{"diagnosis": diagnosis}],
						"drug_prescription": [
							{"drug_code": code, "drug_name": name, "dosage": rng.choice(["1-0-1", "1-1-1", "0-0-1"]), "period": "1 Week", "dosage_form": form}
							for code, name, form, *_ in meds
						],
					}
				)
				round_.insert(ignore_permissions=True)
				round_.submit()
			vitals = frappe.get_doc(
				{
					"doctype": "Vital Signs",
					"patient": rec.patient,
					"inpatient_record": rec.name,
					"company": D.COMPANY,
					"signs_date": day,
					"signs_time": time(8, 0),
					"temperature": str(round(rng.uniform(97.6, 100.8), 1)),
					"pulse": str(rng.randint(68, 104)),
					"respiratory_rate": str(rng.randint(14, 22)),
					"bp_systolic": str(rng.randint(108, 150)),
					"bp_diastolic": str(rng.randint(70, 95)),
				}
			)
			vitals.insert(ignore_permissions=True)
			vitals.submit()
			note = frappe.get_doc(
				{
					"doctype": "Patient Medical Record",
					"patient": rec.patient,
					"subject": rng.choice(D.NURSE_NOTES),
					"communication_date": day,
					"status": "Open",
					"reference_doctype": "Inpatient Record",
					"reference_name": rec.name,
				}
			).insert(ignore_permissions=True)
			frappe.db.set_value("Patient Medical Record", note.name, "owner", nurse, update_modified=False)
			day = add_days(day, 1)

		amount = D.IPD_ADVANCE.get(rec.admission_service_unit_type, 5000)
		make_advance(rec.name, amount, rng.choices(D.MODES_OF_PAYMENT, weights=[50, 30, 10, 10])[0], posting_date=admitted)
		frappe.db.commit()

	if not frappe.db.exists("Inpatient Record", {"status": "Discharged"}):
		for rec in records[:3]:
			discharge(rec.name, summary="Condition improved. Continue medicines as advised and review in OPD.", followup_date=add_days(nowdate(), 7), mode_of_payment="Cash")
			frappe.db.commit()



def setup_lab_worklists():
	"""Radiology templates and reports, and a live pending queue for both labs."""
	from healthcare.healthcare.doctype.lab_test.lab_test import update_status

	ensure("Item Group", "Radiology", item_group_name="Radiology", parent_item_group="All Item Groups")
	ensure("Medical Department", "Radiology", department="Radiology")
	for name, rate, particulars in D.RADIOLOGY_TESTS:
		if frappe.db.exists("Lab Test Template", name):
			continue
		ensure(
			"Lab Test Template",
			lab_test_name=name,
			lab_test_code=name.upper().replace(" ", "-")[:20],
			lab_test_group="Radiology",
			department="Radiology",
			lab_test_template_type="Descriptive",
			is_billable=1,
			lab_test_rate=rate,
			descriptive_test_templates=[{"particulars": p, "allow_blank": 1} for p, _ in particulars],
		)

	if frappe.db.exists("Lab Test", {"lab_test_group": "Radiology"}):
		return
	patients = frappe.get_all("Patient", pluck="name")
	docs = practitioners()
	findings = {name: dict(parts) for name, _r, parts in D.RADIOLOGY_TESTS}
	approver = next((u[0] for u in D.DEMO_USERS if u[3] == "Radiologist"), None)

	def new_test(template, day, complete):
		patient = rng.choice(patients)
		test = frappe.get_doc(
			{
				"doctype": "Lab Test",
				"patient": patient,
				"patient_sex": frappe.db.get_value("Patient", patient, "sex"),
				"template": template,
				"practitioner": rng.choice(docs).name,
				"company": D.COMPANY,
				"date": day,
				"time": time(rng.randint(9, 19), rng.choice([0, 15, 30, 45])),
			}
		)
		test.insert(ignore_permissions=True)
		if complete:
			for row in test.descriptive_test_items:
				row.result_value = findings.get(template, {}).get(row.lab_test_particulars, "Within normal limits.")
			for row in test.normal_test_items:
				lab = next((x for x in D.LAB_TESTS if x[0] == template), None)
				event = next((e for e in lab[3] if e[0] == row.lab_test_event), lab[3][0]) if lab else None
				if event and event[3] is not None:
					row.result_value = f"{rng.uniform(event[3], event[4]):.{event[5]}f}"
				else:
					row.result_value = "Negative"
			test.result_date = day
			test.save(ignore_permissions=True)
			test.submit()
		return test

	# Radiology: four weeks of reports, most approved, plus today's queue.
	for days_ago in range(28, 0, -1):
		day = getdate(add_days(nowdate(), -days_ago))
		for _ in range(rng.choice([0, 1, 1, 2])):
			test = new_test(rng.choice(D.RADIOLOGY_TESTS)[0], day, True)
			if rng.random() < 0.8:
				update_status("Approved", test.name)
				if approver:
					frappe.db.set_value("Lab Test", test.name, "modified_by", approver, update_modified=False)
	for i, (name, *_rest) in enumerate(rng.sample(D.RADIOLOGY_TESTS, 4)):
		new_test(name, getdate(), i == 0)

	# Pathology: today's samples waiting for results, and approve older reports.
	for lab in rng.sample(D.LAB_TESTS, 5):
		new_test(lab[0], getdate(), False)
	for name in frappe.get_all("Lab Test", filters={"docstatus": 1, "status": "Completed", "lab_test_group": ["!=", "Radiology"]}, pluck="name"):
		if rng.random() < 0.7:
			update_status("Approved", name)


def setup_operations():
	"""Completed operations for some admitted patients and a few booked for tomorrow."""
	if frappe.db.count("Patient Operation"):
		return
	surgeons = {d.department: d.name for d in practitioners()}
	surgeon_for = {
		"General Surgery": surgeons.get("General Surgery"),
		"Orthopaedic": surgeons.get("Orthopaedics"),
		"Gynaecology and Obstetrics": surgeons.get("Gynaecology"),
		"ENT": surgeons.get("ENT"),
	}
	records = frappe.get_all(
		"Inpatient Record", filters={"status": "Admitted"}, fields=["name", "patient", "admitted_datetime"], order_by="admitted_datetime asc"
	)
	for i, rec in enumerate(records[:8]):
		name, category, anaesthesia, charge = D.OPERATIONS[i % len(D.OPERATIONS)]
		admitted = getdate(rec.admitted_datetime)
		done = i < 5
		frappe.get_doc(
			{
				"doctype": "Patient Operation",
				"patient": rec.patient,
				"inpatient_record": rec.name,
				"operation_name": name,
				"category": category,
				"status": "Completed" if done else "Scheduled",
				"operation_date": add_days(admitted, 1) if done else add_days(nowdate(), 1),
				"operation_time": time(rng.choice([9, 11, 14]), 0),
				"ot_room": rng.choice(["OT-1", "OT-2", "OT-3"]),
				"surgeon": surgeon_for.get(category) or rng.choice(practitioners()).name,
				"assistant": rng.choice(["Dr. Tanvir Ahmed", "Dr. Nusrat Jahan", "Dr. Imran Hossain"]),
				"anaesthetist": rng.choice(D.ANAESTHETISTS),
				"anaesthesia_type": anaesthesia,
				"pre_op_notes": "Consent taken. NPO from midnight. Pre-op investigations reviewed.",
				"operation_notes": "Procedure done under aseptic precautions. No intra-operative complications." if done else None,
				"result": "Stable, shifted to post-op ward." if done else None,
				"charge": charge,
			}
		).insert(ignore_permissions=True)


def setup_pharmacy_bills():
	"""A month of pharmacy sales from consultation prescriptions, issued from stock."""
	from hospital_saas.api.pharmacy import qty_for
	from hospital_saas.billing import create_invoice

	if frappe.db.exists("Sales Invoice", {"remarks": "Pharmacy bill"}):
		return
	store = frappe.db.get_value("Warehouse", {"warehouse_name": "Pharmacy DHN", "company": D.COMPANY})
	rates = {code: rate for code, _n, _f, rate, *_ in D.PHARMACY_ITEMS}
	encounters = frappe.get_all(
		"Patient Encounter",
		filters={"docstatus": 1, "inpatient_record": ["is", "not set"], "encounter_date": [">=", add_days(nowdate(), -30)]},
		fields=["name", "patient", "encounter_date"],
		order_by="encounter_date asc",
	)
	for enc in encounters:
		if rng.random() > 0.6:
			continue
		lines = [
			{"item_code": d.drug_code, "qty": min(qty_for(d.dosage, d.period), 30), "rate": rates.get(d.drug_code, 1)}
			for d in frappe.get_all("Drug Prescription", filters={"parent": enc.name}, fields=["drug_code", "dosage", "period"])
			if d.drug_code
		]
		if not lines:
			continue
		frappe.db.savepoint("pharmacy_bill")
		try:
			create_invoice(
				enc.patient,
				lines,
				posting_date=enc.encounter_date,
				mode_of_payment=rng.choices(D.MODES_OF_PAYMENT, weights=[60, 25, 10, 5])[0],
				warehouse=store,
				remarks="Pharmacy bill",
			)
		except frappe.ValidationError:
			# Not enough stock for this one; skip it.
			frappe.db.rollback(save_point="pharmacy_bill")
			frappe.clear_last_message()


def restock_pharmacy():
	"""Top stores up to a healthy level after a month of sales, keeping two
	items just under their reorder level so the low-stock alerts show."""
	low_items = {"MONTE-10", "INS-RAPID"}
	for wh_name in ("Pharmacy DHN", "Pharmacy UTR"):
		store = frappe.db.get_value("Warehouse", {"warehouse_name": wh_name, "company": D.COMPANY})
		rows = []
		for code, _n, _f, rate, qty, reorder in D.PHARMACY_ITEMS:
			current = flt(frappe.db.get_value("Bin", {"item_code": code, "warehouse": store}, "actual_qty"))
			target = reorder - 5 if code in low_items else max(qty, reorder * 4)
			if target > current:
				rows.append({"item_code": code, "qty": target - current, "t_warehouse": store, "basic_rate": round(rate * 0.75, 2)})
		if rows:
			se = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "company": D.COMPANY, "items": rows})
			se.insert(ignore_permissions=True)
			se.submit()


def setup_registers():
	"""Front office, ambulance, blood bank, birth/death, TPA and referral records."""
	if frappe.db.count("Visitor Entry"):
		return
	patients = frappe.get_all("Patient", fields=["name", "patient_name", "sex"], filters={"inpatient_status": ["in", ["", None]]})
	docs = practitioners()

	def ins(doctype, **values):
		return frappe.get_doc({"doctype": doctype, **values}).insert(ignore_permissions=True)

	def recent(days=30):
		return getdate(add_days(nowdate(), -rng.randint(0, days)))

	def person():
		return f"{rng.choice(D.MALE_FIRST + D.FEMALE_FIRST)} {rng.choice(D.LAST_NAMES)}"

	# Front office
	for i in range(30):
		day = getdate() if i < 6 else recent(10)
		ins(
			"Visitor Entry",
			purpose=rng.choice(["Patient visit", "Patient visit", "Meeting", "Delivery", "Interview"]),
			visitor_name=person(),
			phone=random_phone(),
			number_of_persons=rng.choice([1, 1, 2, 3]),
			person_to_meet=rng.choice([p.patient_name for p in patients[:20]] + ["Accounts office", "HR office"]),
			visit_date=day,
			in_time=time(rng.randint(9, 18), rng.choice([0, 15, 30, 45])),
		)
	for _ in range(20):
		ins(
			"Phone Call Log",
			caller_name=person(),
			phone=random_phone(),
			call_date=recent(14),
			call_type=rng.choice(["Incoming", "Incoming", "Outgoing"]),
			description=rng.choice(["Asked about cardiology chamber time", "Appointment rescheduling", "Lab report availability", "Ambulance enquiry", "Bed availability for ICU"]),
		)
	for _ in range(15):
		ins(
			"Postal Record",
			direction=rng.choice(["Receive", "Dispatch"]),
			title=rng.choice(["DGHS, Dhaka", "Square Pharmaceuticals Ltd.", "Delta Health Cover", "City Corporation", "Patient family"]),
			reference_no=f"REF/{rng.randint(1000, 9999)}",
			postal_date=recent(30),
		)
	for status in ["Open", "Open", "In Progress", "Resolved", "Resolved", "Resolved", "Resolved", "In Progress"]:
		ins(
			"Complaint Entry",
			complaint_type=rng.choice(["Billing", "Cleanliness", "Waiting time", "Staff behaviour", "Food"]),
			source=rng.choice(["In person", "Phone", "Email"]),
			complainant=person(),
			phone=random_phone(),
			complaint_date=recent(20),
			description=rng.choice(["Waited more than an hour for the doctor.", "Washroom on level 3 needs cleaning.", "Charged twice for a lab test.", "Food served cold in the cabin."]),
			assigned_to=rng.choice(["Front desk supervisor", "Housekeeping", "Accounts"]),
			action_taken="Apologised and resolved." if status == "Resolved" else None,
			status=status,
		)

	# Ambulance
	vehicles = []
	for number, model, kind, driver in [
		("DHAKA METRO-CHA-11-2345", "Toyota HiAce", "Advanced life support", "Abdul Karim"),
		("DHAKA METRO-CHA-15-8812", "Toyota HiAce", "Basic life support", "Jalal Uddin"),
		("DHAKA METRO-CHA-19-4471", "Nissan Urvan", "Patient transport", "Sohrab Hossain"),
		("DHAKA METRO-CHA-21-0098", "Toyota HiAce", "Basic life support", "Mizanur Rahman"),
	]:
		vehicles.append(ins("Ambulance Vehicle", vehicle_number=number, vehicle_model=model, year_made=rng.randint(2016, 2023), vehicle_type=kind, driver_name=driver, driver_phone=random_phone(), status="Available").name)
	for i in range(22):
		ins(
			"Ambulance Call",
			patient=rng.choice(patients).name,
			vehicle=rng.choice(vehicles),
			call_date=getdate() if i < 2 else recent(30),
			call_time=time(rng.randint(0, 23), rng.choice([0, 15, 30, 45])),
			pickup=rng.choice(D.AREAS),
			destination=rng.choice(["CityCare Dhanmondi", "CityCare Uttara", "Patient home"]),
			distance_km=rng.randint(3, 40),
			charge=rng.choice([1500, 2000, 2500, 3500, 5000]),
			status="Booked" if i < 2 else rng.choice(["Completed", "Completed", "Completed", "Cancelled"]),
		)

	# Blood bank
	groups = ["A Positive", "B Positive", "O Positive", "AB Positive", "A Negative", "B Negative", "O Negative", "AB Negative"]
	weights = [22, 30, 30, 8, 2, 3, 3, 2]
	donors = []
	for _ in range(25):
		gender = rng.choice(["Male", "Male", "Female"])
		donors.append(
			ins(
				"Blood Donor",
				donor_name=f"{rng.choice(D.MALE_FIRST if gender == 'Male' else D.FEMALE_FIRST)} {rng.choice(D.LAST_NAMES)}",
				blood_group=rng.choices(groups, weights)[0],
				gender=gender,
				date_of_birth=add_days(nowdate(), -365 * rng.randint(19, 50)),
				phone=random_phone(),
				address=rng.choice(D.AREAS),
				last_donation=recent(60),
			)
		)
	bags = []
	for i in range(45):
		donor = rng.choice(donors)
		collected = recent(35)
		component = rng.choices(["Whole Blood", "Packed Red Cells", "Platelets", "Fresh Frozen Plasma"], [45, 30, 15, 10])[0]
		life = {"Whole Blood": 35, "Packed Red Cells": 42, "Platelets": 5, "Fresh Frozen Plasma": 365}[component]
		expiry = add_days(collected, life)
		bags.append(
			ins(
				"Blood Bag",
				bag_no=f"BB-{collected.strftime('%y%m')}-{i + 1:03d}",
				blood_group=donor.blood_group,
				component=component,
				donor=donor.name,
				collection_date=collected,
				expiry_date=expiry,
				volume_ml=450 if component == "Whole Blood" else 250,
				status="Expired" if getdate(expiry) < getdate() else "Available",
			)
		)
	for bag in rng.sample([b for b in bags if b.status == "Available"], 10):
		ins("Blood Issue", patient=rng.choice(patients).name, bag=bag.name, issue_date=recent(20), doctor=rng.choice(docs).name, charge=rng.choice([1200, 1500, 2500]))

	# Birth and death
	mothers = [p for p in patients if p.sex == "Female"]
	for i in range(6):
		gender = rng.choice(["Male", "Female"])
		mother = rng.choice(mothers)
		ins(
			"Birth Record",
			child_name=f"Baby of {mother.patient_name.split()[0]}" if i % 2 else f"{rng.choice(D.MALE_FIRST if gender == 'Male' else D.FEMALE_FIRST)} {mother.patient_name.split()[-1]}",
			gender=gender,
			weight=round(rng.uniform(2.4, 3.8), 2),
			birth_date=recent(40),
			birth_time=time(rng.randint(0, 23), rng.choice([0, 10, 25, 40, 55])),
			mother=mother.name,
			father_name=f"{rng.choice(D.MALE_FIRST)} {mother.patient_name.split()[-1]}",
			delivery_type=rng.choice(["Normal", "Caesarean", "Caesarean"]),
			attending_doctor=next((d.name for d in docs if d.department == "Gynaecology"), docs[0].name),
			address=rng.choice(D.AREAS),
		)
	for cause in ["Cardiac arrest following acute myocardial infarction", "Septic shock with multi-organ failure"]:
		ins(
			"Death Record",
			patient=rng.choice(patients).name,
			death_date=recent(45),
			death_time=time(rng.randint(0, 23), rng.choice([5, 20, 35, 50])),
			guardian_name=person(),
			cause=cause,
			certified_by=next((d.name for d in docs if d.department == "Cardiology"), docs[0].name),
		)

	# TPA and referral
	for name, code, contact, disc in [
		("Delta Health Cover", "DHC", "Nahid Hasan", 10),
		("Shield Life Insurance", "SLI", "Farida Yasmin", 8),
		("Padma Care TPA", "PCT", "Rezwan Ahmed", 12),
		("Meghna Health Assurance", "MHA", "Sharif Uddin", 5),
		("Corporate Staff Health Plan", "CSHP", "Lubna Karim", 15),
	]:
		ins("TPA Organisation", organisation_name=name, code=code, contact_person=contact, phone=random_phone(), email=f"claims@{code.lower()}.test", discount_percent=disc)
	persons = [
		ins("Referral Person", person_name=name, category=cat, phone=random_phone(), address=rng.choice(D.AREAS), commission_percent=pct)
		for name, cat, pct in [
			("Dr. Abul Kalam (GP, Mirpur)", "Doctor", 10),
			("Shapla Diagnostic Centre", "Clinic", 8),
			("Dr. Rina Sultana (GP, Savar)", "Doctor", 10),
			("Mohammad Ali (agent)", "Agent", 5),
			("Gazipur Community Hospital", "Hospital", 7),
			("Dr. Faisal Rahman (GP, Badda)", "Doctor", 12),
		]
	]
	invoices = frappe.get_all("Sales Invoice", filters={"docstatus": 1}, fields=["name", "patient", "grand_total", "posting_date"], order_by="posting_date desc", limit=40)
	for inv in rng.sample(invoices, 14):
		ins(
			"Referral Payment",
			referral_person=rng.choice(persons).name,
			patient=inv.patient,
			bill=inv.name,
			bill_amount=inv.grand_total,
			payment_date=inv.posting_date,
			status=rng.choice(["Paid", "Paid", "Unpaid"]),
		)


def setup_hr_extras():
	"""Holiday calendar, shifts and this week's duty roster, and this morning's check-ins."""
	name = "Bangladesh 2026-27"
	if not frappe.db.exists("Holiday List", name):
		holidays = [{"holiday_date": d, "description": desc} for d, desc in D.PUBLIC_HOLIDAYS]
		day = getdate("2026-07-01")
		while day <= getdate("2027-06-30"):
			if day.strftime("%A") == "Friday":
				holidays.append({"holiday_date": day, "description": "Friday", "weekly_off": 1})
			day = add_days(day, 1)
		frappe.get_doc(
			{"doctype": "Holiday List", "holiday_list_name": name, "from_date": "2026-07-01", "to_date": "2027-06-30", "holidays": holidays}
		).insert(ignore_permissions=True)
		frappe.db.set_value("Company", D.COMPANY, "default_holiday_list", name)

	for shift, start, end, color in D.SHIFTS:
		ensure("Shift Type", shift, __newname=shift, start_time=start, end_time=end, color=color, holiday_list=name)

	if not frappe.db.exists("Shift Assignment", {"docstatus": 1}):
		staff = frappe.get_all(
			"Employee",
			filters={"company": D.COMPANY, "designation": ["in", ["Senior Staff Nurse", "Staff Nurse", "Front Desk Executive", "Lab Technologist", "Pharmacist", "Radiologist"]]},
			pluck="name",
		)
		week_start = add_days(nowdate(), -((getdate().weekday() + 2) % 7))
		for i, emp in enumerate(staff):
			for d in range(7):
				day = add_days(week_start, d)
				if d == 6 and i % 2:
					continue  # alternate staff are off on Friday
				shift = D.SHIFTS[(i + d // 2) % 3][0]
				sa = frappe.get_doc(
					{"doctype": "Shift Assignment", "employee": emp, "shift_type": shift, "company": D.COMPANY, "start_date": day, "end_date": day, "status": "Active"}
				)
				sa.insert(ignore_permissions=True)
				sa.submit()

	today = getdate()
	if not frappe.db.exists("Employee Checkin", {"time": [">=", f"{today} 00:00:00"]}):
		for emp in frappe.get_all("Employee", filters={"company": D.COMPANY, "status": "Active"}, pluck="name"):
			if rng.random() < 0.15:
				continue
			frappe.get_doc(
				{"doctype": "Employee Checkin", "employee": emp, "log_type": "IN", "time": datetime.combine(today, time(7, rng.randint(40, 59))) + timedelta(minutes=rng.randint(0, 35)), "device_id": "QR kiosk"}
			).insert(ignore_permissions=True)
			if not frappe.db.exists("Attendance", {"employee": emp, "attendance_date": today}):
				att = frappe.get_doc({"doctype": "Attendance", "employee": emp, "attendance_date": today, "status": "Present", "company": D.COMPANY})
				att.insert(ignore_permissions=True)
				att.submit()


def setup_finance_entries():
	"""A month of running costs and other income, posted to the books."""
	if frappe.db.count("Hospital Expense"):
		return
	monthly = [
		("Electricity bill", "DESCO", 185000), ("Water bill", "Dhaka WASA", 22000), ("Internet and phone", "Link3 Technologies", 18000),
		("Medical waste disposal", "PRISM Bangladesh", 35000),
	]
	frequent = [
		("Generator fuel", "Padma Oil depot", 8000, 25000), ("Cleaning supplies", "ACI Consumer", 3000, 12000),
		("Stationery", "Nilkhet Paper House", 1500, 6000), ("Equipment maintenance", "BioMed Services Ltd.", 5000, 40000),
	]
	for head, payee, amount in monthly:
		frappe.get_doc(
			{"doctype": "Hospital Expense", "expense_head": head, "paid_to": payee, "expense_date": add_days(nowdate(), -rng.randint(5, 25)), "amount": amount, "mode_of_payment": "Card", "reference_no": f"BILL-{rng.randint(10000, 99999)}"}
		).insert(ignore_permissions=True)
	for _ in range(18):
		head, payee, low, high = rng.choice(frequent)
		frappe.get_doc(
			{"doctype": "Hospital Expense", "expense_head": head, "paid_to": payee, "expense_date": add_days(nowdate(), -rng.randint(0, 29)), "amount": rng.randint(low, high) // 100 * 100, "mode_of_payment": "Cash"}
		).insert(ignore_permissions=True)
	for head, payer, amount in [
		("Canteen rent", "Rahman Food Corner", 60000), ("Pharmacy shop rent", "Lazz Pharma outlet", 85000),
		("Training fee", "Nursing interns batch 12", 45000), ("Scrap sale", "Old Dhaka scrap dealer", 7500), ("Donation", "Anonymous donor", 100000),
	]:
		frappe.get_doc(
			{"doctype": "Hospital Income", "income_head": head, "received_from": payer, "income_date": add_days(nowdate(), -rng.randint(1, 28)), "amount": amount, "mode_of_payment": "bKash" if amount < 50000 else "Card"}
		).insert(ignore_permissions=True)


def setup_communication():
	"""Notices, shared documents, live consultations and surveys with responses."""
	if frappe.db.count("Hospital Notice"):
		return
	for title, audience, channel, msg, days_ago in [
		("Dengue preparedness", "All staff", "Notice board", "Dengue cases are rising. Keep NS1 kits stocked and report every positive case to the duty manager.", 1),
		("Fire drill on Thursday", "All staff", "Notice board", "A fire drill will be held at 11:00 on Thursday. Please follow the floor wardens.", 2),
		("New ICU duty roster", "Nurses", "Notice board", "The ICU roster for next month is on the duty roster page. Swap requests to the nursing supervisor.", 3),
		("Cardiology CME session", "Doctors", "Notice board", "CME on heart failure management, Saturday 6 pm, conference room level 6.", 4),
		("Lab report turnaround", "Laboratory", "Notice board", "Routine reports must be approved within 6 hours of sample collection.", 5),
		("Free diabetes camp", "Patients", "SMS", "CityCare free diabetes check-up camp this Friday 9am-1pm at Dhanmondi branch.", 6),
		("Month-end closing", "Accounts", "Email", "Please close all pending bills before the 30th.", 8),
	]:
		frappe.get_doc(
			{"doctype": "Hospital Notice", "title": title, "audience": audience, "channel": channel, "message": msg, "publish_date": add_days(nowdate(), -days_ago)}
		).insert(ignore_permissions=True)

	for title, ctype, audience, url in [
		("Hand hygiene guidelines (WHO)", "Policy", "All staff", "https://www.who.int/publications/i/item/9789241597906"),
		("Dengue clinical management guideline", "Training material", "Doctors", "https://www.who.int/publications/i/item/9789241547871"),
		("Patient admission consent form", "Form", "Reception", "https://citycare.test/forms/admission-consent"),
		("Infection prevention and control circular", "Circular", "Nurses", "https://citycare.test/circulars/ipc-2026"),
		("Monthly quality report - September", "Report", "All staff", "https://citycare.test/reports/quality-2026-09"),
	]:
		frappe.get_doc(
			{"doctype": "Shared Content", "title": title, "content_type": ctype, "audience": audience, "url": url, "upload_date": add_days(nowdate(), -rng.randint(1, 30))}
		).insert(ignore_permissions=True)

	patients = frappe.get_all("Patient", pluck="name")
	docs = practitioners()
	for i in range(8):
		frappe.get_doc(
			{
				"doctype": "Live Meeting",
				"title": "Follow-up video consultation",
				"meeting_type": "Consultation",
				"patient": rng.choice(patients),
				"doctor": rng.choice(docs).name,
				"meeting_date": add_days(nowdate(), rng.randint(-10, 3)) if i else getdate(),
				"meeting_time": time(rng.choice([16, 17, 18, 19, 20]), rng.choice([0, 30])),
				"duration": 20,
				"status": "Scheduled",
			}
		).insert(ignore_permissions=True)
	for title, day in [("Weekly department heads meeting", 2), ("Quality committee review", 5)]:
		frappe.get_doc(
			{"doctype": "Live Meeting", "title": title, "meeting_type": "Meeting", "meeting_date": add_days(nowdate(), day), "meeting_time": time(15, 0), "duration": 60, "status": "Scheduled"}
		).insert(ignore_permissions=True)
	frappe.db.sql("""update `tabLive Meeting` set status = 'Completed' where meeting_date < %s""", nowdate())

	surveys = [
		("Patient satisfaction survey", "Patients", "How easy was it to book your appointment?\nHow long did you wait to see the doctor?\nHow well did the doctor explain your treatment?\nHow clean was the hospital?\nHow likely are you to recommend CityCare?"),
		("Staff canteen feedback", "Staff", "Food quality\nVariety of menu\nPrice\nCleanliness"),
	]
	for title, audience, questions in surveys:
		form = frappe.get_doc({"doctype": "Survey Form", "title": title, "audience": audience, "questions": questions, "is_active": 1}).insert(ignore_permissions=True)
		n = len(questions.split("\n"))
		for _ in range(rng.randint(12, 25)):
			answers = [rng.choices([2, 3, 4, 5], [5, 15, 45, 35])[0] for _ in range(n)]
			frappe.get_doc(
				{
					"doctype": "Survey Response",
					"survey": form.name,
					"respondent": f"{rng.choice(D.MALE_FIRST + D.FEMALE_FIRST)} {rng.choice(D.LAST_NAMES)}",
					"answers": frappe.as_json(answers),
					"average_rating": round(sum(answers) / n, 2),
					"comment": rng.choice([None, None, "Doctors were very caring.", "Waiting area was crowded.", "Billing took too long.", "Very clean and well managed."]),
					"response_date": add_days(nowdate(), -rng.randint(0, 30)),
				}
			).insert(ignore_permissions=True)


def enrich_demo_patient():
	"""Give the patient demo login something in every portal section."""
	email = next(u[0] for u in D.DEMO_USERS if u[3] == "Patient")
	patient = frappe.db.get_value("Patient", {"user_id": email})
	if not patient or frappe.db.exists("Live Meeting", {"patient": patient}):
		return
	docs = practitioners()
	frappe.get_doc(
		{"doctype": "Live Meeting", "title": "Follow-up video consultation", "meeting_type": "Consultation", "patient": patient, "doctor": docs[0].name, "meeting_date": getdate(), "meeting_time": time(19, 30), "duration": 20}
	).insert(ignore_permissions=True)
	vehicle = frappe.db.get_value("Ambulance Vehicle", {})
	if vehicle:
		frappe.get_doc(
			{"doctype": "Ambulance Call", "patient": patient, "vehicle": vehicle, "call_date": add_days(nowdate(), -12), "pickup": "Mirpur, Dhaka", "destination": "CityCare Dhanmondi", "charge": 2000, "status": "Completed"}
		).insert(ignore_permissions=True)
	bag = frappe.db.get_value("Blood Bag", {"status": "Available"})
	if bag:
		frappe.get_doc({"doctype": "Blood Issue", "patient": patient, "bag": bag, "issue_date": add_days(nowdate(), -11), "charge": 1500}).insert(ignore_permissions=True)
	test = frappe.get_doc(
		{"doctype": "Lab Test", "patient": patient, "patient_sex": frappe.db.get_value("Patient", patient, "sex"), "template": "USG Whole Abdomen", "practitioner": docs[0].name, "company": D.COMPANY, "date": add_days(nowdate(), -3)}
	).insert(ignore_permissions=True)
	findings = dict(next(p for n, _r, p in D.RADIOLOGY_TESTS if n == "USG Whole Abdomen"))
	for row in test.descriptive_test_items:
		row.result_value = findings.get(row.lab_test_particulars, "Normal.")
	test.result_date = add_days(nowdate(), -3)
	test.save(ignore_permissions=True)
	test.submit()
	from hospital_saas.billing import create_invoice

	store = frappe.db.get_value("Warehouse", {"warehouse_name": "Pharmacy DHN", "company": D.COMPANY})
	create_invoice(
		patient,
		[{"item_code": "NAPA-500", "qty": 20, "rate": 1.2}, {"item_code": "SECLO-20", "qty": 14, "rate": 6}],
		posting_date=add_days(nowdate(), -3),
		mode_of_payment="bKash",
		warehouse=store,
		remarks="Pharmacy bill",
	)
	for title, ctype, url in [
		("Diet chart for people with diabetes", "Training material", "https://citycare.test/patients/diabetes-diet"),
		("Before your operation: what to expect", "Form", "https://citycare.test/patients/pre-op-guide"),
	]:
		frappe.get_doc({"doctype": "Shared Content", "title": title, "content_type": ctype, "audience": "Patients", "url": url}).insert(ignore_permissions=True)
	slot_doctor = docs[1]
	frappe.get_doc(
		{
			"doctype": "Patient Appointment", "patient": patient, "practitioner": slot_doctor.name, "department": slot_doctor.department,
			"appointment_type": "Follow Up", "appointment_for": "Practitioner", "appointment_date": add_days(nowdate(), 3),
			"appointment_time": time(18, 15), "duration": 15, "company": D.COMPANY,
		}
	).insert(ignore_permissions=True)


def setup_website_content():
	"""Front CMS content for the public website and a few enquiries from it."""
	if frappe.db.count("FAQ Entry"):
		return

	def ins(doctype, **values):
		frappe.get_doc({"doctype": doctype, **values}).insert(ignore_permissions=True)

	for title, days, venue, summary in [
		("Free diabetes screening camp", 4, "Dhanmondi branch, ground floor", "Free blood sugar and HbA1c screening with diet counselling by our diabetologists."),
		("World Heart Day walk", -11, "Dhanmondi Lake", "Over 300 people joined our cardiologists for a 3 km walk and free BP checks."),
		("Dengue awareness session", -20, "Uttara community centre", "How to recognise warning signs of dengue and when to come to hospital."),
		("Basic life support training", 12, "Conference room, level 6", "Hands-on CPR training for the public, certified by our emergency team."),
	]:
		ins("Hospital Event", title=title, event_date=add_days(nowdate(), days), venue=venue, summary=summary, published=1)
	for caption, category in [
		("Main reception, Dhanmondi", "Facilities"), ("Intensive care unit", "Facilities"), ("Private cabin", "Facilities"),
		("Operation theatre complex", "Facilities"), ("Nursing team", "Team"), ("Free health camp, Savar", "Community"),
	]:
		ins("Gallery Photo", caption=caption, category=category, image="/assets/hospital_saas/images/logo.svg", published=1)
	for i, (q, a) in enumerate(
		[
			("What are the visiting hours?", "Wards and cabins: 4pm to 7pm every day. ICU: one visitor at a time, 5pm to 6pm."),
			("How do I book an appointment?", "Call the hotline, use the appointment request form on this website or book a time in the patient portal."),
			("Do I pay the doctor's fee in advance?", "The consultation fee is paid at the front desk before the visit, by cash, bKash, Nagad or card."),
			("How do I collect my lab report?", "Reports are available in the patient portal once approved, or at the lab counter with your receipt."),
			("Do you accept insurance?", "Yes. We work with several TPAs and corporate health plans. Bring your card to the front desk."),
			("Is there an emergency service?", "Our emergency department and ambulance service are open 24 hours, every day."),
			("Can I get a copy of my prescription?", "Yes. Ask at the front desk or download it from the patient portal."),
			("Is parking available?", "Limited parking is available at the Dhanmondi branch. Uttara has a public car park next door."),
		]
	):
		ins("FAQ Entry", question=q, answer=a, sort_order=i + 1, published=1)
	for name, role, rating, text in [
		("Nasrin Akter", "Mother of a patient", 5, "The paediatric team treated my son like their own. Thank you, CityCare."),
		("Abdul Karim", "Cardiology patient", 5, "My angiogram and follow-up were well organised and the doctors explained everything."),
		("Farzana Haque", "Maternity patient", 4, "Caring nurses and a very clean cabin. Billing took a little long."),
		("Rashed Khan", "Orthopaedic patient", 5, "Walking again three weeks after my knee surgery. Excellent physiotherapy team."),
		("Sumaiya Rahman", "Outpatient", 4, "Easy booking and short waiting time in the evening chamber."),
	]:
		ins("Patient Testimonial", patient_name=name, designation=role, rating=rating, testimonial=text, published=1)
	for i in range(6):
		ins(
			"Website Enquiry",
			enquiry_type=rng.choice(["Appointment request", "Appointment request", "General enquiry"]),
			full_name=f"{rng.choice(D.MALE_FIRST + D.FEMALE_FIRST)} {rng.choice(D.LAST_NAMES)}",
			phone=random_phone(),
			preferred_date=add_days(nowdate(), rng.randint(0, 5)),
			message=rng.choice(["Need a gynae appointment this week.", "Is the cardiology chamber open on Friday?", None, "Want a health check-up package."]),
			status=rng.choice(["New", "New", "Contacted", "Booked"]),
		)
