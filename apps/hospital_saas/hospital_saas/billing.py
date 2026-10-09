"""Invoices and payments shared by the /hms screens and the demo seeder."""

import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
from frappe.utils import add_days, flt, nowdate


def default_company():
	return frappe.defaults.get_user_default("company") or frappe.defaults.get_global_default("company")


def create_invoice(patient, items, posting_date=None, mode_of_payment=None, paid_amount=None, reference_no=None, discount_amount=0):
	"""Submit a Sales Invoice for `patient` and, if paid, a Payment Entry against it.

	items: [{"item_code", "qty", "rate"}]. paid_amount None with a mode of
	payment means paid in full. Returns the invoice name.
	"""
	posting_date = posting_date or nowdate()
	company = default_company()
	invoice = frappe.get_doc(
		{
			"doctype": "Sales Invoice",
			"customer": frappe.db.get_value("Patient", patient, "customer"),
			"patient": patient,
			"company": company,
			"set_posting_time": 1,
			"posting_date": posting_date,
			"due_date": add_days(posting_date, 7),
			"items": items,
			"apply_discount_on": "Grand Total",
			"discount_amount": flt(discount_amount),
		}
	)
	invoice.insert()
	invoice.submit()

	if mode_of_payment and paid_amount is None:
		paid_amount = invoice.grand_total
	if mode_of_payment and flt(paid_amount) > 0:
		payment = get_payment_entry("Sales Invoice", invoice.name)
		payment.mode_of_payment = mode_of_payment
		payment.paid_to = frappe.db.get_value(
			"Mode of Payment Account", {"parent": mode_of_payment, "company": company}, "default_account"
		)
		payment.paid_amount = payment.received_amount = min(flt(paid_amount), invoice.grand_total)
		payment.references[0].allocated_amount = payment.paid_amount
		payment.posting_date = posting_date
		payment.reference_no = reference_no or invoice.name
		payment.reference_date = posting_date
		payment.insert()
		payment.submit()
	return invoice.name
