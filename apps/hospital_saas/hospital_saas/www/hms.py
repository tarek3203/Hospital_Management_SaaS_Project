"""Serves the /hms single page app (built from apps/hospital_saas/frontend)."""

import frappe
from frappe.boot import load_translations

from hospital_saas.api.session import get_job

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/hms"
		raise frappe.Redirect
	if not get_job():
		# Patients and users without a hospital job use their own home page.
		frappe.local.flags.redirect_location = "/patient-portal" if "Patient" in frappe.get_roles() else "/desk"
		raise frappe.Redirect

	csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()  # nosemgrep: the csrf token must be saved before the page renders
	# Each boot key becomes a window global (frappe-ui reads window.csrf_token).
	context.boot = get_boot()
	context.boot.csrf_token = csrf_token
	return context


def get_boot():
	boot = frappe._dict({"site_name": frappe.local.site})
	load_translations(boot)
	boot.lang = str(frappe.local.lang)  # load_translations stores the proxy, which json cannot encode
	return boot
