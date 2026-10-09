"""Patient and staff ID cards with QR code and barcode (SVG, generated server side)."""

import io

import frappe
from frappe import _

from hospital_saas.api.patients import age_from_dob


def qr_svg(text):
	import pyqrcode

	buffer = io.BytesIO()
	pyqrcode.create(text, error="M").svg(buffer, scale=3, quiet_zone=1, xmldecl=False, svgns=True)
	return buffer.getvalue().decode()


def barcode_svg(text):
	from barcode import Code128
	from barcode.writer import SVGWriter

	buffer = io.BytesIO()
	Code128(text, writer=SVGWriter()).write(buffer, options={"module_height": 8, "font_size": 0, "quiet_zone": 1, "write_text": False})
	svg = buffer.getvalue().decode()
	return svg[svg.find("<svg") :]


@frappe.whitelist()
def patient_cards(patients: list | str):
	patients = frappe.parse_json(patients)[:30]
	cards = []
	for name in patients:
		if not frappe.has_permission("Patient", "read", name):
			frappe.throw(_("Not permitted"), frappe.PermissionError)
		p = frappe.db.get_value("Patient", name, ["name", "patient_name", "sex", "dob", "blood_group", "mobile", "creation"], as_dict=True)
		cards.append(
			{
				"id": p.name,
				"name": p.patient_name,
				"line1": f"{p.sex or ''} · {age_from_dob(p.dob) or '-'} y · Blood {p.blood_group or '-'}",
				"line2": p.mobile,
				"since": str(p.creation)[:10],
				"qr": qr_svg(p.name),
				"barcode": barcode_svg(p.name),
			}
		)
	return cards


@frappe.whitelist()
def staff_cards(employees: list | str):
	frappe.has_permission("Employee", "read", throw=True)
	employees = frappe.parse_json(employees)[:30]
	cards = []
	for name in employees:
		e = frappe.db.get_value(
			"Employee", name, ["name", "employee_name", "designation", "department", "branch", "cell_number", "date_of_joining"], as_dict=True
		)
		if not e:
			continue
		cards.append(
			{
				"id": e.name,
				"name": e.employee_name,
				"line1": e.designation,
				"line2": f"{(e.department or '').rsplit(' - ', 1)[0]} · {e.branch or ''}",
				"since": str(e.date_of_joining or ""),
				"qr": qr_svg(e.name),
				"barcode": barcode_svg(e.name),
			}
		)
	return cards


@frappe.whitelist()
def search_employees(txt: str = ""):
	like = f"%{txt}%"
	return frappe.get_list(
		"Employee",
		fields=["name as value", "employee_name as label", "designation as description"],
		or_filters={"employee_name": ["like", like], "name": ["like", like]},
		filters={"status": "Active"},
		page_length=15,
	)
