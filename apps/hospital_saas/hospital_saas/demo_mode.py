"""Public demo mode.

Turned on per site with `bench --site <site> set-config hms_demo_mode 1`.
A customer install never sets it, so none of this runs there.

While on:
- the login page lists one-click demo logins for every role
- demo accounts cannot change their password, email or roles, so the next
  visitor can still log in (the site is also reset on a schedule)
"""

import frappe
from frappe import _

from hospital_saas.demo import data as D


def is_demo_mode():
	return bool(frappe.conf.get("hms_demo_mode"))


@frappe.whitelist(allow_guest=True)
def get_demo_logins():
	if not is_demo_mode():
		return []
	logins = []
	for email, _first, _last, profile, _doctor in D.DEMO_USERS:
		user = frappe.db.get_value("User", email, ["enabled", "full_name"], as_dict=True)
		if user and user.enabled:
			logins.append({"role": profile, "name": user.full_name, "email": email, "password": D.DEMO_PASSWORD})
	return logins


def protect_demo_user(doc, method=None):
	"""User.before_validate hook (User.validate clears new_password before other hooks run)."""
	if not is_demo_mode() or frappe.session.user == "Administrator" or frappe.flags.in_demo:
		return
	if doc.name not in {u[0] for u in D.DEMO_USERS} or doc.is_new():
		return
	if doc.new_password or doc.has_value_changed("enabled") or doc.has_value_changed("email"):
		frappe.throw(_("Demo accounts cannot be changed. The demo resets automatically."))
	before = doc.get_doc_before_save()
	if before and {r.role for r in before.roles} != {r.role for r in doc.roles}:
		frappe.throw(_("Demo accounts cannot be changed. The demo resets automatically."))


def block_demo_user_delete(doc, method=None):
	if is_demo_mode() and doc.name in {u[0] for u in D.DEMO_USERS} and frappe.session.user != "Administrator":
		frappe.throw(_("Demo accounts cannot be deleted."))


@frappe.whitelist(allow_guest=True, methods=["POST"])
def update_password(new_password, logout_all_sessions=0, key=None, old_password=None):
	"""Wraps Frappe's change-password endpoint, which saves without User.validate."""
	from frappe.core.doctype.user.user import update_password as frappe_update_password

	if is_demo_mode() and frappe.session.user in {u[0] for u in D.DEMO_USERS}:
		frappe.throw(_("Demo accounts cannot be changed. The demo resets automatically."))
	return frappe_update_password(new_password, logout_all_sessions, key, old_password)
