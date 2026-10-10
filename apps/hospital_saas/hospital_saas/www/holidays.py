import frappe

from hospital_saas.billing import default_company
from hospital_saas.website import base_context


def get_context(context):
	base_context(context, "Annual calendar", "/holidays")
	holiday_list = frappe.db.get_value("Company", default_company(), "default_holiday_list")
	context.holidays = (
		frappe.get_all("Holiday", filters={"parent": holiday_list, "weekly_off": 0}, fields=["holiday_date", "description"], order_by="holiday_date")
		if holiday_list
		else []
	)
	return context
