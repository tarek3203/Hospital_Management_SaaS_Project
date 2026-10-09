"""Who is logged in to /hms and what they may see."""

import frappe

from hospital_saas.install import APP_NAME, LOGO
from hospital_saas.menu import STAFF, menu_for

# Profiles (or roles, for users without a profile) that map to each job,
# most specific first.
JOB_ROLES = [
	("Super Admin", "Super Admin"),
	("Admin", "Hospital Admin"),
	("Pharmacist", "Pharmacist"),
	("Pathologist", "Pathologist"),
	("Radiologist", "Radiologist"),
	("Accountant", "Accountant"),
	("Receptionist", "Receptionist"),
	("Doctor", "Physician"),
	("Nurse", "Nursing User"),
]


def get_job(user=None):
	"""The user's hospital job: Doctor, Receptionist, ... or None."""
	user = user or frappe.session.user
	if user == "Administrator":
		return "Super Admin"
	profiles = frappe.get_all("User Role Profile", filters={"parent": user}, pluck="role_profile")
	for profile in profiles:
		job = profile.removeprefix("Demo ")
		if job in STAFF:
			return job
	roles = set(frappe.get_roles(user))
	return next((job for job, role in JOB_ROLES if role in roles), None)


@frappe.whitelist()
def get_session():
	user = frappe.session.user
	job = get_job(user)
	if not job:
		frappe.throw(frappe._("Your account has no hospital role."), frappe.PermissionError)
	info = frappe.db.get_value("User", user, ["full_name", "user_image", "email"], as_dict=True)
	practitioner = frappe.db.get_value("Healthcare Practitioner", {"user_id": user}, "name")
	return {
		"user": user,
		"full_name": info.full_name,
		"user_image": info.user_image,
		"job": job,
		"practitioner": practitioner,
		"menu": menu_for(job),
		"hospital": {
			"name": frappe.db.get_single_value("System Settings", "app_name") or APP_NAME,
			"company": frappe.defaults.get_global_default("company"),
			"logo": LOGO,
			"currency": frappe.defaults.get_global_default("currency"),
		},
		"demo_mode": bool(frappe.conf.get("hms_demo_mode")),
	}
