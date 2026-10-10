"""Public website (Smart Hospital's front site) data and the guest enquiry form."""

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import getdate, nowdate

from hospital_saas.api.session import get_hospital_info

NAV = [
	("Home", "/home"),
	("About", "/about"),
	("Departments", "/departments"),
	("Doctors", "/doctors"),
	("Events", "/events"),
	("Gallery", "/gallery"),
	("FAQ", "/faq"),
	("Contact", "/contact"),
]


def base_context(context, title, path):
	context.no_cache = 1
	context.title = title
	context.hospital = get_hospital_info()
	context.nav = NAV
	context.path = path
	context.year = getdate().year
	return context


def doctors():
	rows = frappe.get_all(
		"Healthcare Practitioner",
		filters={"status": "Active"},
		fields=["name", "practitioner_name", "department", "designation", "op_consulting_charge", "hospital"],
		order_by="department, practitioner_name",
	)
	for r in rows:
		r.branch = (r.hospital or "").split(", ")[-1]
		r.initials = "".join(w[0] for w in r.practitioner_name.split()[:2]).upper()
	return rows


def departments():
	counts = {}
	for d in doctors():
		counts[d.department] = counts.get(d.department, 0) + 1
	return [{"name": k, "doctors": v} for k, v in sorted(counts.items())]


def published(doctype, fields, order_by, limit=50, filters=None):
	return frappe.get_all(doctype, filters={"published": 1, **(filters or {})}, fields=fields, order_by=order_by, limit=limit)


def stats():
	return {
		"Specialist doctors": frappe.db.count("Healthcare Practitioner", {"status": "Active"}),
		"Beds": frappe.db.count("Healthcare Service Unit", {"inpatient_occupancy": 1, "is_group": 0}),
		"Patients served": frappe.db.count("Patient"),
		"Branches": frappe.db.count("Branch"),
	}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=5, seconds=60 * 60)
def submit_enquiry(full_name: str, phone: str, enquiry_type: str = "General enquiry", email: str | None = None, doctor: str | None = None, preferred_date: str | None = None, message: str | None = None):
	"""Contact and appointment-request form. Reception follows up by phone."""
	if enquiry_type not in ("Appointment request", "General enquiry"):
		frappe.throw(_("Invalid request"))
	if doctor and not frappe.db.exists("Healthcare Practitioner", {"name": doctor, "status": "Active"}):
		doctor = None
	if preferred_date and getdate(preferred_date) < getdate(nowdate()):
		frappe.throw(_("Please choose today or a later date."))
	frappe.get_doc(
		{
			"doctype": "Website Enquiry",
			"enquiry_type": enquiry_type,
			"full_name": (full_name or "").strip()[:140],
			"phone": (phone or "").strip()[:30],
			"email": (email or "").strip()[:140] or None,
			"doctor": doctor,
			"preferred_date": preferred_date or None,
			"message": (message or "").strip()[:2000] or None,
			"status": "New",
		}
	).insert(ignore_permissions=True)
	return "ok"
