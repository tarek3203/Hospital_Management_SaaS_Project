"""Central billing for /hms: every patient bill, new bills, collections, receipts."""

import frappe
from frappe import _
from frappe.utils import cint, flt, get_first_day, nowdate

from hospital_saas.api.dashboard import MODULE_SQL
from hospital_saas.billing import create_invoice
from hospital_saas.api.session import require_staff

# Billable item groups per billing module (Smart Hospital's "single module billing").
MODULE_ITEM_GROUPS = {"OPD": ["Healthcare Services"], "Pathology": ["Laboratory"], "Radiology": ["Radiology"]}


@frappe.whitelist()
def get_billing_summary():
	require_staff()
	frappe.has_permission("Sales Invoice", "read", throw=True)
	today = nowdate()
	month_start = get_first_day(today)

	def one(sql, *args):
		return flt(frappe.db.sql(sql, args)[0][0])

	return {
		"collected_today": one(
			"select coalesce(sum(paid_amount),0) from `tabPayment Entry` where docstatus=1 and payment_type='Receive' and posting_date=%s", today
		),
		"billed_today": one("select coalesce(sum(grand_total),0) from `tabSales Invoice` where docstatus=1 and posting_date=%s", today),
		"billed_month": one("select coalesce(sum(grand_total),0) from `tabSales Invoice` where docstatus=1 and posting_date>=%s", month_start),
		"outstanding": one("select coalesce(sum(outstanding_amount),0) from `tabSales Invoice` where docstatus=1"),
		"bills_today": cint(one("select count(*) from `tabSales Invoice` where docstatus=1 and posting_date=%s", today)),
	}


@frappe.whitelist()
def get_bills(module: str | None = None, search: str | None = None, status: str | None = None, start: int = 0, page_length: int = 25):
	require_staff()
	frappe.has_permission("Sales Invoice", "read", throw=True)
	conditions = ["si.docstatus = 1"]
	values = {"start": cint(start), "page_length": cint(page_length)}
	if search:
		conditions.append("(si.name like %(like)s or si.patient_name like %(like)s or si.patient like %(like)s)")
		values["like"] = f"%{search}%"
	if status == "Unpaid":
		conditions.append("si.outstanding_amount > 0")
	elif status == "Paid":
		conditions.append("si.outstanding_amount <= 0")
	having = ""
	if module:
		having = "having find_in_set(%(module)s, modules)"
		values["module"] = module
	rows = frappe.db.sql(
		f"""
		select si.name, si.posting_date, si.patient, si.patient_name, si.grand_total,
			si.outstanding_amount, si.grand_total - si.outstanding_amount as paid,
			group_concat(distinct {MODULE_SQL}) as modules
		from `tabSales Invoice` si
		join `tabSales Invoice Item` sii on sii.parent = si.name
		where {" and ".join(conditions)}
		group by si.name {having}
		order by si.posting_date desc, si.creation desc
		limit %(page_length)s offset %(start)s
		""",
		values,
		as_dict=True,
	)
	for row in rows:
		row.modules = (row.modules or "").split(",")
	return rows


@frappe.whitelist()
def get_billable_items(module: str = "OPD"):
	require_staff()
	groups = MODULE_ITEM_GROUPS.get(module)
	if not groups:
		frappe.throw(_("Billing for {0} is coming soon.").format(module))
	return frappe.db.sql(
		"""select i.name as item_code, i.item_name, coalesce(ip.price_list_rate, 0) as rate
		from `tabItem` i
		left join `tabItem Price` ip on ip.item_code = i.name and ip.price_list = 'Standard Selling'
		where i.disabled = 0 and i.item_group in %s
		order by i.item_name""",
		[groups],
		as_dict=True,
	)


@frappe.whitelist(methods=["POST"])
def create_bill(patient: str, items: list | str, discount: float = 0, mode_of_payment: str | None = None, paid_amount: float | None = None, reference_no: str | None = None):
	require_staff()
	items = frappe.parse_json(items)
	lines = [{"item_code": i["item_code"], "qty": flt(i.get("qty") or 1), "rate": flt(i.get("rate"))} for i in items if i.get("item_code")]
	if not lines:
		frappe.throw(_("Add at least one charge."))
	return create_invoice(patient, lines, mode_of_payment=mode_of_payment, paid_amount=paid_amount, reference_no=reference_no, discount_amount=discount)


@frappe.whitelist()
def find_case(number: str):
	"""OPD number (appointment) or IPD number (inpatient record) -> where to bill it."""
	require_staff()
	number = (number or "").strip()
	if frappe.db.exists("Patient Appointment", number):
		return {"type": "opd", "name": number}
	if frappe.db.exists("Inpatient Record", number):
		return {"type": "ipd", "name": number}
	frappe.throw(_("No OPD or IPD number {0}").format(number))


@frappe.whitelist()
def get_receipt(invoice: str):
	require_staff()
	si = frappe.get_doc("Sales Invoice", invoice)
	si.check_permission("read")
	return receipt_data(si)


def receipt_data(si):
	invoice = si.name
	payments = frappe.db.sql(
		"""select pe.name, pe.posting_date, pe.mode_of_payment, pe.reference_no, per.allocated_amount as amount
		from `tabPayment Entry Reference` per join `tabPayment Entry` pe on pe.name = per.parent
		where per.reference_name = %s and pe.docstatus = 1 order by pe.posting_date""",
		invoice,
		as_dict=True,
	)
	payments += [
		frappe._dict(name=a.reference_name, posting_date=None, mode_of_payment="Advance", reference_no=None, amount=a.allocated_amount)
		for a in si.advances
	]
	return {
		"name": si.name,
		"date": si.posting_date,
		"patient": si.patient,
		"patient_name": si.patient_name,
		"items": [{"item_name": i.item_name, "description": i.description, "qty": i.qty, "rate": i.rate, "amount": i.amount} for i in si.items],
		"total": si.total,
		"discount": si.discount_amount,
		"grand_total": si.grand_total,
		"paid": si.grand_total - si.outstanding_amount,
		"outstanding": si.outstanding_amount,
		"payments": payments,
		"cashier": frappe.db.get_value("User", si.owner, "full_name"),
	}
