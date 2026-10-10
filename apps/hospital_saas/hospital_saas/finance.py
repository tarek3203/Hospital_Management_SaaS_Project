"""Post Hospital Income / Hospital Expense entries to the books as Journal Entries."""

import frappe
from frappe import _
from frappe.utils import flt

from hospital_saas.billing import default_company


def head_account(head, root_type):
	"""Ledger for an income or expense head, created under Indirect Income/Expenses on first use."""
	company = default_company()
	abbr = frappe.db.get_value("Company", company, "abbr")
	name = f"{head} - {abbr}"
	if not frappe.db.exists("Account", name):
		parent = frappe.db.get_value(
			"Account", {"company": company, "account_name": "Indirect Income" if root_type == "Income" else "Indirect Expenses", "is_group": 1}
		)
		frappe.get_doc({"doctype": "Account", "account_name": head, "parent_account": parent, "company": company, "root_type": root_type}).insert(
			ignore_permissions=True
		)
	return name


def post(doc, head, date, income):
	company = default_company()
	cash = frappe.db.get_value("Mode of Payment Account", {"parent": doc.mode_of_payment, "company": company}, "default_account")
	if not cash:
		frappe.throw(_("Mode of payment {0} has no account for {1}").format(doc.mode_of_payment, company))
	ledger = head_account(head, "Income" if income else "Expense")
	amount = flt(doc.amount)
	je = frappe.get_doc(
		{
			"doctype": "Journal Entry",
			"voucher_type": "Bank Entry" if frappe.db.get_value("Account", cash, "account_type") == "Bank" else "Cash Entry",
			"company": company,
			"posting_date": date,
			"cheque_no": doc.reference_no or doc.name,
			"cheque_date": date,
			"user_remark": f"{doc.doctype} {doc.name}: {head}",
			"accounts": [
				{"account": cash, "debit_in_account_currency": amount if income else 0, "credit_in_account_currency": 0 if income else amount},
				{"account": ledger, "debit_in_account_currency": 0 if income else amount, "credit_in_account_currency": amount if income else 0},
			],
		}
	)
	je.insert(ignore_permissions=True)
	je.submit()
	doc.db_set("journal_entry", je.name)


def cancel(doc):
	if doc.journal_entry and frappe.db.get_value("Journal Entry", doc.journal_entry, "docstatus") == 1:
		frappe.get_doc("Journal Entry", doc.journal_entry).cancel()
