"""Pharmacy for /hms: medicine stock by store, prescriptions to bill, and
pharmacy bills that issue stock from the chosen store."""

import re

import frappe
from frappe import _
from frappe.utils import cint, flt

from hospital_saas.billing import create_invoice, default_company

GROUP = "Pharmacy"


@frappe.whitelist()
def get_stores():
	return frappe.get_all(
		"Warehouse",
		filters={"company": default_company(), "is_group": 0, "warehouse_name": ["like", "Pharmacy%"]},
		pluck="name",
		order_by="name",
	)


@frappe.whitelist()
def get_medicines(warehouse: str | None = None, search: str | None = None):
	frappe.has_permission("Item", "read", throw=True)
	conditions, values = ["i.item_group = %(group)s", "i.disabled = 0"], {"group": GROUP, "warehouse": warehouse}
	if search:
		conditions.append("(i.item_name like %(like)s or i.name like %(like)s)")
		values["like"] = f"%{search}%"
	rows = frappe.db.sql(
		f"""
		select i.name as item_code, i.item_name, i.stock_uom,
			coalesce(ip.price_list_rate, 0) as rate,
			coalesce((select sum(b.actual_qty) from `tabBin` b where b.item_code = i.name
				and (%(warehouse)s is null or b.warehouse = %(warehouse)s)), 0) as stock,
			coalesce((select max(r.warehouse_reorder_level) from `tabItem Reorder` r where r.parent = i.name), 0) as reorder_level
		from `tabItem` i
		left join `tabItem Price` ip on ip.item_code = i.name and ip.price_list = 'Standard Selling'
		where {" and ".join(conditions)}
		order by i.item_name
		""",
		values,
		as_dict=True,
	)
	for r in rows:
		r.low = flt(r.stock) <= flt(r.reorder_level)
	return rows


def qty_for(dosage, period):
	"""Tablets for a course: "1-0-1" for "5 Day" -> 10."""
	per_day = sum(cint(x) for x in re.findall(r"\d+", dosage or "")) if dosage and "-" in dosage else {"BID": 2, "TID": 3, "QID": 4}.get(dosage or "", 1)
	number, unit = (re.findall(r"(\d+)\s*(\w+)", period or "") or [("1", "Day")])[0]
	days = cint(number) * {"Day": 1, "Week": 7, "Month": 30}.get(unit, 1)
	return max(1, per_day * days if unit in ("Day", "Week", "Month") else per_day)


@frappe.whitelist()
def get_prescription(patient: str):
	"""Medicines from the patient's latest consultation or ward round."""
	frappe.has_permission("Patient", "read", patient, throw=True)
	enc = frappe.get_all(
		"Patient Encounter",
		filters={"patient": patient, "docstatus": 1},
		fields=["name", "encounter_date", "practitioner_name"],
		order_by="encounter_date desc, encounter_time desc",
		limit=1,
	)
	if not enc:
		return None
	lines = frappe.get_all("Drug Prescription", filters={"parent": enc[0].name}, fields=["drug_code", "drug_name", "dosage", "period"], order_by="idx")
	rates = {r.item_code: r.rate for r in get_medicines()}
	return {
		"encounter": enc[0],
		"items": [
			{"item_code": l.drug_code, "item_name": l.drug_name, "qty": qty_for(l.dosage, l.period), "rate": rates.get(l.drug_code, 0), "note": f"{l.dosage} · {l.period}"}
			for l in lines
			if l.drug_code
		],
	}


@frappe.whitelist(methods=["POST"])
def create_pharmacy_bill(patient: str, warehouse: str, items: list | str, discount: float = 0, mode_of_payment: str | None = None, paid_amount: float | None = None):
	items = frappe.parse_json(items)
	lines = [{"item_code": i["item_code"], "qty": flt(i.get("qty") or 1), "rate": flt(i.get("rate"))} for i in items if i.get("item_code")]
	if not lines:
		frappe.throw(_("Add at least one medicine."))
	return create_invoice(
		patient, lines, mode_of_payment=mode_of_payment, paid_amount=paid_amount, discount_amount=discount, warehouse=warehouse, remarks="Pharmacy bill"
	)


@frappe.whitelist()
def get_pharmacy_summary():
	from frappe.utils import get_first_day, nowdate

	def total(since):
		return flt(
			frappe.db.sql(
				"""select coalesce(sum(sii.base_net_amount), 0) from `tabSales Invoice Item` sii
				join `tabSales Invoice` si on si.name = sii.parent
				where si.docstatus = 1 and sii.item_group = %s and si.posting_date >= %s""",
				(GROUP, since),
			)[0][0]
		)

	medicines = get_medicines()
	return {
		"sales_today": total(nowdate()),
		"sales_month": total(get_first_day(nowdate())),
		"medicines": len(medicines),
		"low_stock": sum(1 for m in medicines if m.low),
	}
