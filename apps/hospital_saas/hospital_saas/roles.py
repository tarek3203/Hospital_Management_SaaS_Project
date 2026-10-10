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

# Roles whose users start on /hms instead of /desk.
HMS_HOME_ROLES = CUSTOM_ROLES + ["Physician", "Nursing User"]

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
	"Radiologist": ["Radiologist", "Laboratory User", "LabTest Approver", "Employee"],
	"Accountant": [
		"Accountant", "Accounts Manager", "Accounts User", "Sales User", "Purchase User", "Employee",
	],
	"Receptionist": ["Receptionist", "Nursing User", "Accounts User", "Sales User", "Employee"],
	"Nurse": ["Nursing User", "Employee"],
}

# Roles a public demo visitor must never hold: they allow running code or
# injecting script into pages other visitors load (Client Script, Website
# Script, custom HTML, server settings). Demo logins use a "Demo <profile>"
# copy of each profile without them; customer installs use the full profiles.
DEMO_UNSAFE_ROLES = {"System Manager", "Website Manager", "Workspace Manager", "Script Manager"}


def demo_profile_name(profile):
	if DEMO_UNSAFE_ROLES & set(ROLE_PROFILES.get(profile, [])):
		return f"Demo {profile}"
	return profile


# Extra access the standard roles do not give our custom roles.
# doctype -> {role: [permission types]}
PATIENT_READ = ["read", "report"]
EXTRA_PERMISSIONS = {
	"Patient Encounter": {r: PATIENT_READ for r in ["Pharmacist", "Pathologist", "Radiologist", "Receptionist", "Accountant", "Nursing User"]},
	"Lab Test": {
		**{r: PATIENT_READ for r in ["Accountant", "Nursing User", "Pharmacist", "Radiologist"]},
		"Receptionist": ["read", "write", "create", "report", "print"],
	},
	"Patient Medical Record": {"Nursing User": ["read", "write", "create"]},
	# Registers: read access mirrors who sees each module in Smart Hospital.
	**{dt: {r: PATIENT_READ for r in ["Physician", "Pharmacist", "Pathologist", "Accountant", "Receptionist"]} for dt in ("Blood Bag",)},
	**{dt: {r: PATIENT_READ for r in ["Physician", "Pharmacist", "Pathologist", "Accountant"]} for dt in ("Blood Donor", "Blood Issue")},
	**{dt: {r: PATIENT_READ for r in ["Physician", "Accountant"]} for dt in ("Ambulance Call", "Ambulance Vehicle", "TPA Organisation")},
	"Live Meeting": {r: PATIENT_READ for r in ["Accounts User", "Laboratory User", "Stock User"]},
	"Sales Invoice": {r: PATIENT_READ for r in ["Physician", "Pathologist", "Radiologist"]},
	"Vital Signs": {r: PATIENT_READ for r in ["Pharmacist", "Pathologist", "Radiologist", "Accountant"]},
	"Inpatient Record": {r: PATIENT_READ for r in ["Pharmacist", "Pathologist", "Radiologist", "Accountant"]},
	"Healthcare Practitioner": {r: PATIENT_READ for r in ["Pharmacist", "Pathologist", "Radiologist", "Accountant"]},
	"Patient Appointment": {
		"Receptionist": ["read", "write", "create", "report", "print", "email"],
		**{r: PATIENT_READ for r in ["Pharmacist", "Pathologist", "Radiologist", "Accountant"]},
	},
	"Patient": {
		**{r: PATIENT_READ for r in ["Pharmacist", "Pathologist", "Radiologist", "Accountant"]},
		"Receptionist": ["read", "write", "create", "report", "print", "email"],
	},
}


# Fields above permission level 0 (Inpatient Record keeps admission times at
# level 2, clinical tables at level 1) need their own read rules. doctype -> roles
EXTRA_HIGHER_LEVEL_READ = {
	"Inpatient Record": ["Pharmacist", "Pathologist", "Radiologist", "Accountant"],
}


def setup_roles():
	for role in CUSTOM_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)

	# Staff land on the /hms app after login.
	for role in HMS_HOME_ROLES:
		if frappe.db.exists("Role", role):
			frappe.db.set_value("Role", role, "home_page", "/hms")

	# Patients use the /hms patient portal, never the Desk.
	frappe.db.set_value("Role", "Patient", {"desk_access": 0, "home_page": "/hms"})

	profiles = dict(ROLE_PROFILES)
	for profile, roles in ROLE_PROFILES.items():
		if demo_profile_name(profile) != profile:
			profiles[demo_profile_name(profile)] = [r for r in roles if r not in DEMO_UNSAFE_ROLES]

	for profile, roles in profiles.items():
		roles = [r for r in roles if frappe.db.exists("Role", r)]
		doc = (
			frappe.get_doc("Role Profile", profile)
			if frappe.db.exists("Role Profile", profile)
			else frappe.new_doc("Role Profile")
		)
		if not doc.is_new() and {r.role for r in doc.roles} == set(roles):
			continue  # saving queues a job that re-saves every user on the profile
		doc.role_profile = profile
		doc.set("roles", [{"role": r} for r in roles])
		doc.save(ignore_permissions=True)

	for doctype, grants in EXTRA_PERMISSIONS.items():
		for role, ptypes in grants.items():
			if not frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0}):
				add_permission(doctype, role, 0)
			for ptype in ptypes:
				update_permission_property(doctype, role, 0, ptype, 1, validate=False)

	for doctype, roles in EXTRA_HIGHER_LEVEL_READ.items():
		levels = set(frappe.get_all("DocField", filters={"parent": doctype, "permlevel": [">", 0]}, pluck="permlevel"))
		for role in roles:
			for level in levels:
				if not frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role, "permlevel": level}):
					add_permission(doctype, role, level)
