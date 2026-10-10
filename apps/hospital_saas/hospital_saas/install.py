import frappe

APP_NAME = "CityCare HMS"
LOGO = "/assets/hospital_saas/images/logo.svg"


def after_install():
	from hospital_saas.fixes import apply_fixes
	from hospital_saas.roles import setup_roles

	setup_roles()
	apply_fixes()
	apply_branding()


def apply_branding():
	"""Brand the desk and login page so the demo looks like our product."""
	frappe.db.set_single_value(
		"Website Settings",
		{"app_name": APP_NAME, "app_logo": LOGO, "favicon": LOGO, "splash_image": LOGO},
	)
	frappe.db.set_single_value("Navbar Settings", "app_logo", LOGO)
	# The public website (www/home.html) is the landing page for visitors.
	frappe.db.set_single_value("Website Settings", "home_page", "home")
	frappe.db.set_single_value("System Settings", "app_name", APP_NAME)
	frappe.clear_cache()
