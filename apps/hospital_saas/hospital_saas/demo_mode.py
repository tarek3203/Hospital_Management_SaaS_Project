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


LOCKED_MESSAGE = "Demo accounts cannot be changed. The demo resets automatically."
LOCKED_FIELDS = ["enabled", "email", "user_type", "module_profile"]


def demo_user_emails():
	return {u[0] for u in D.DEMO_USERS}


def is_protected(doc):
	return (
		is_demo_mode()
		and frappe.session.user != "Administrator"
		and not frappe.flags.in_demo
		and doc.name in demo_user_emails()
		and not doc.is_new()
	)


def protect_demo_user(doc, method=None):
	"""User.before_validate: User.validate clears new_password, so check it first."""
	if not is_protected(doc):
		return
	before = doc.get_doc_before_save()
	profiles_changed = before and {r.role_profile for r in before.role_profiles} != {
		r.role_profile for r in doc.role_profiles
	}
	if doc.new_password or profiles_changed or any(doc.has_value_changed(f) for f in LOCKED_FIELDS):
		frappe.throw(_(LOCKED_MESSAGE))


def protect_demo_user_roles(doc, method=None):
	"""User.validate: runs after roles are rebuilt from role profiles, so this also
	catches edits to a Role Profile that would cascade to demo accounts."""
	if not is_protected(doc):
		return
	before = doc.get_doc_before_save()
	if before and {r.role for r in before.roles} != {r.role for r in doc.roles}:
		frappe.throw(_(LOCKED_MESSAGE))


def block_demo_user_rename(doc, method=None, *args, **kwargs):
	if is_protected(doc):
		frappe.throw(_(LOCKED_MESSAGE))


def block_demo_user_delete(doc, method=None):
	if is_protected(doc):
		frappe.throw(_("Demo accounts cannot be deleted."))


@frappe.whitelist(allow_guest=True, methods=["POST"])
def update_password(new_password, logout_all_sessions=0, key=None, old_password=None):
	"""Wraps Frappe's change-password endpoint, which saves without User.validate."""
	from frappe.core.doctype.user.user import update_password as frappe_update_password

	# Reset links (key) are refused too: nobody on the public demo needs them.
	if is_demo_mode() and (key or frappe.session.user in demo_user_emails()):
		frappe.throw(_(LOCKED_MESSAGE))
	return frappe_update_password(new_password, logout_all_sessions, key, old_password)
