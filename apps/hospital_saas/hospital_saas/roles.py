"""Hospital roles and role profiles.

Each hospital job (receptionist, pharmacist, ...) is a Role Profile. A profile
bundles our own marker role (used by the custom UI and workspaces) with the
standard ERPNext / HRMS / Healthcare roles that grant the actual permissions.

Runs on install and on every migrate, so editing this file and running
`bench migrate` is enough to update an existing site.
"""

import frappe
from frappe.permissions import add_permission, update_permission_property

# Roles we own. Doctor, Nurse and Patient reuse Healthcare's Physician,
# Nursing User and Patient roles.
CUSTOM_ROLES = [
	"Super Admin",
	"Hospital Admin",
	"Pharmacist",
	"Pathologist",
	"Radiologist",
	"Accountant",
	"Receptionist",
]

# Profile name -> roles. Profile names match the job titles staff see.
ROLE_PROFILES = {
	"Super Admin": [
		"Super Admin", "System Manager", "Healthcare Administrator", "Physician", "Nursing User",
		"Laboratory User", "LabTest Approver", "Accounts Manager", "Accounts User", "HR Manager",
		"HR User", "Stock Manager", "Stock User", "Item Manager", "Purchase Manager", "Purchase User",
		"Sales Manager", "Sales User", "Website Manager", "Report Manager", "Dashboard Manager",
		"Workspace Manager", "Employee",
	],
	"Admin": [
		"Hospital Admin", "Healthcare Administrator", "Physician", "Nursing User", "Laboratory User",
		"LabTest Approver", "Accounts Manager", "Accounts User", "HR Manager", "HR User",
		"Stock Manager", "Stock User", "Item Manager", "Purchase Manager", "Purchase User",
		"Sales User", "Website Manager", "Report Manager", "Dashboard Manager", "Employee",
	],
	"Doctor": ["Physician", "Employee"],
	"Pharmacist": [
		"Pharmacist", "Stock User", "Stock Manager", "Item Manager", "Purchase User", "Sales User",
		"Accounts User", "Employee",
	],
	"Pathologist": ["Pathologist", "Laboratory User", "LabTest Approver", "Employee"],
	"Radiologist": ["Radiologist", "Laboratory User", "Employee"],
	"Accountant": [
		"Accountant", "Accounts Manager", "Accounts User", "Sales User", "Purchase User", "Employee",
	],
	"Receptionist": ["Receptionist", "Nursing User", "Accounts User", "Sales User", "Employee"],
	"Nurse": ["Nursing User", "Employee"],
}

# Extra access the standard roles do not give our custom roles.
# doctype -> {role: [permission types]}
PATIENT_READ = ["read", "report"]
EXTRA_PERMISSIONS = {
	"Patient Encounter": {r: PATIENT_READ for r in ["Pharmacist", "Pathologist", "Radiologist"]},
	"Inpatient Record": {r: PATIENT_READ for r in ["Pharmacist", "Pathologist", "Radiologist", "Accountant"]},
	"Healthcare Practitioner": {r: PATIENT_READ for r in ["Pharmacist", "Pathologist", "Radiologist", "Accountant"]},
	"Patient Appointment": {"Receptionist": ["read", "write", "create", "report", "print", "email"]},
	"Patient": {
		**{r: PATIENT_READ for r in ["Pharmacist", "Pathologist", "Radiologist", "Accountant"]},
		"Receptionist": ["read", "write", "create", "report", "print", "email"],
	},
}


def setup_roles():
	for role in CUSTOM_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)

	# Patients use Healthcare's portal, never the Desk.
	frappe.db.set_value("Role", "Patient", {"desk_access": 0, "home_page": "/patient-portal"})

	for profile, roles in ROLE_PROFILES.items():
		roles = [r for r in roles if frappe.db.exists("Role", r)]
		doc = (
			frappe.get_doc("Role Profile", profile)
			if frappe.db.exists("Role Profile", profile)
			else frappe.new_doc("Role Profile")
		)
		doc.role_profile = profile
		doc.set("roles", [{"role": r} for r in roles])
		doc.save(ignore_permissions=True)

	for doctype, grants in EXTRA_PERMISSIONS.items():
		for role, ptypes in grants.items():
			if not frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0}):
				add_permission(doctype, role, 0)
			for ptype in ptypes:
				update_permission_property(doctype, role, 0, ptype, 1, validate=False)
