"""Keep the public demo looking current.

Demo data is generated relative to one day, the "anchor" (stored as the
`hms_demo_anchor` default when the seeder runs). Every night, and after each
demo reset, every date in the hospital's transactional data is moved forward
by (today - anchor) days and the anchor becomes today. The anchor-day's live
queue is therefore always "today", the 45 days of history always end
yesterday and the upcoming bookings always start tomorrow.

Only runs on sites with `hms_demo_mode` set.
"""

import frappe
from frappe.utils import date_diff, getdate, nowdate

from hospital_saas.demo_mode import is_demo_mode

ANCHOR_KEY = "hms_demo_anchor"

# Apps whose data is shifted, plus a few framework doctypes users see dated.
SHIFT_APPS = ("erpnext", "hrms", "healthcare", "hospital_saas")
EXTRA_DOCTYPES = ("ToDo", "Event", "Notification Log", "Communication", "Comment")

# Calendar and period setup: moving these by an odd number of days would put
# weekly holidays on the wrong weekday or posting dates outside their period.
SKIP_DOCTYPES = {
	"Fiscal Year",
	"Fiscal Year Company",
	"Accounting Period",
	"Period Closing Voucher",
	"Process Period Closing Voucher",
	"Process Period Closing Voucher Detail",
	"Holiday List",
	"Holiday",
	"Holiday List Assignment",
	"Leave Period",
	"Payroll Period",
	"Payroll Period Date",
	"Supplier Scorecard Period",
}


def set_anchor(day=None):
	frappe.db.set_default(ANCHOR_KEY, str(getdate(day or nowdate())))


def get_anchor():
	# Read the table directly: the defaults cache can lag behind a restore.
	return frappe.db.get_value("DefaultValue", {"parent": "__default", "defkey": ANCHOR_KEY}, "defvalue")


def roll_forward():
	"""Scheduler and reset entry point: shift demo data so the anchor is today."""
	if not is_demo_mode():
		return
	anchor = get_anchor()
	if not anchor:
		return
	days = date_diff(nowdate(), anchor)
	if days <= 0:
		return
	shift_dates(days)
	sync_fiscal_years()
	reopen_current_appointments()
	expire_blood_bags()
	set_anchor()
	frappe.db.commit()
	frappe.clear_cache()


def shift_dates(days):
	for doctype, columns in date_columns().items():
		table = f"tab{doctype}"
		assignments = ", ".join(f"`{c}` = `{c}` + interval {int(days)} day" for c in columns)
		frappe.db.sql(f"update `{table}` set {assignments}")  # nosemgrep: names come from DocType meta


def date_columns():
	"""{doctype: [date and datetime columns, plus creation and modified]}"""
	doctypes = frappe.db.sql(
		"""
		select dt.name from `tabDocType` dt
		join `tabModule Def` m on m.name = dt.module
		where dt.issingle = 0 and coalesce(dt.is_virtual, 0) = 0
			and (m.app_name in %(apps)s or dt.name in %(extra)s)
		""",
		{"apps": SHIFT_APPS, "extra": EXTRA_DOCTYPES},
		pluck=True,
	)
	result = {}
	for doctype in doctypes:
		if doctype in SKIP_DOCTYPES or not frappe.db.table_exists(doctype):
			continue
		meta = frappe.get_meta(doctype)
		columns = [
			df.fieldname
			for df in meta.fields
			if df.fieldtype in ("Date", "Datetime") and frappe.db.has_column(doctype, df.fieldname)
		]
		result[doctype] = ["creation", "modified", *columns]
	return result


def sync_fiscal_years():
	"""Ledger rows also store their fiscal year; keep it right once posting
	dates cross into the next year (ERPNext creates that year itself)."""
	for doctype in ("GL Entry", "Stock Ledger Entry"):
		if not frappe.db.has_column(doctype, "fiscal_year"):
			continue
		frappe.db.sql(
			f"""update `tab{doctype}` l
			join `tabFiscal Year` fy on l.posting_date between fy.year_start_date and fy.year_end_date
			set l.fiscal_year = fy.name
			where l.fiscal_year != fy.name"""
		)


def reopen_current_appointments():
	"""The nightly Healthcare job turns the anchor-day's open bookings into No
	Show and the next day's into Open. After the shift those dates are today
	and tomorrow again, so put the statuses back."""
	today = nowdate()
	frappe.db.sql(
		"""update `tabPatient Appointment` set status = 'Open'
		where status = 'No Show' and appointment_date = %s""",
		today,
	)
	frappe.db.sql(
		"""update `tabPatient Appointment` set status = 'Scheduled'
		where status in ('No Show', 'Open') and appointment_date > %s""",
		today,
	)


def expire_blood_bags():
	"""Bags past their expiry date leave the available stock, as they would in a real bank."""
	frappe.db.sql(
		"""update `tabBlood Bag` set status = 'Expired'
		where status = 'Available' and expiry_date < %s""",
		nowdate(),
	)
