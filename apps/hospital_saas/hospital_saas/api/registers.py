"""Generic list-and-form screens ("registers") for the simpler modules:
front office, birth and death records, ambulance, blood bank, TPA, referral.

Each register is one DocType. The page, form and permissions all come from the
DocType's meta, so adding a register is one entry in REGISTERS.
"""

import frappe
from frappe import _
from frappe.utils import cint

REGISTERS = {
	"visitors": {"doctype": "Visitor Entry", "title": "Visitor Book", "module": "Front Office", "stat": "purpose"},
	"calls": {"doctype": "Phone Call Log", "title": "Phone Call Log", "module": "Front Office", "stat": "call_type"},
	"postal": {"doctype": "Postal Record", "title": "Postal Receive / Dispatch", "module": "Front Office", "stat": "direction"},
	"complaints": {"doctype": "Complaint Entry", "title": "Complaints", "module": "Front Office", "stat": "status"},
	"births": {"doctype": "Birth Record", "title": "Birth Record", "module": "Birth & Death Record", "stat": "gender", "certificate": True},
	"deaths": {"doctype": "Death Record", "title": "Death Record", "module": "Birth & Death Record", "certificate": True},
	"ambulance-calls": {"doctype": "Ambulance Call", "title": "Ambulance Calls", "module": "Ambulance", "stat": "status"},
	"ambulances": {"doctype": "Ambulance Vehicle", "title": "Ambulance Vehicles", "module": "Ambulance", "stat": "status"},
	"blood-bags": {"doctype": "Blood Bag", "title": "Blood Stock", "module": "Blood Bank", "stat": "blood_group", "stat_filter": {"status": "Available"}, "stat_label": "Available bags by group"},
	"blood-donors": {"doctype": "Blood Donor", "title": "Blood Donors", "module": "Blood Bank", "stat": "blood_group"},
	"blood-issues": {"doctype": "Blood Issue", "title": "Blood Issue", "module": "Blood Bank"},
	"income": {"doctype": "Hospital Income", "title": "Income", "module": "Finance", "stat": "income_head"},
	"expenses": {"doctype": "Hospital Expense", "title": "Expenses", "module": "Finance", "stat": "expense_head"},
	"notices": {"doctype": "Hospital Notice", "title": "Messaging", "module": "Messaging", "stat": "channel"},
	"downloads": {"doctype": "Shared Content", "title": "Download Center", "module": "Download Center", "stat": "content_type", "links": [{"label": "Open", "field": "file"}, {"label": "Open link", "field": "url"}]},
	"live-meetings": {"doctype": "Live Meeting", "title": "Live Consultation and Meetings", "module": "Live Consultation", "stat": "meeting_type", "links": [{"label": "Join", "field": "join_url"}]},
	"surveys": {"doctype": "Survey Form", "title": "Survey Forms", "module": "Survey Forms", "stat": "audience", "survey": True},
	"tpa": {"doctype": "TPA Organisation", "title": "TPA Management", "module": "TPA Management"},
	"referral-persons": {"doctype": "Referral Person", "title": "Referral Persons", "module": "Referral", "stat": "category"},
	"referral-payments": {"doctype": "Referral Payment", "title": "Referral Payments", "module": "Referral", "stat": "status"},
}

SKIP_TYPES = ("Section Break", "Column Break", "Tab Break", "HTML", "Button")


def get_config(key):
	config = REGISTERS.get(key)
	if not config:
		frappe.throw(_("Unknown register {0}").format(key), frappe.DoesNotExistError)
	frappe.has_permission(config["doctype"], "read", throw=True)
	return config


def field_meta(doctype):
	meta = frappe.get_meta(doctype)
	fields = []
	for df in meta.fields:
		if df.fieldtype in SKIP_TYPES or df.hidden:
			continue
		fields.append(
			{
				"fieldname": df.fieldname,
				"label": df.label,
				"fieldtype": df.fieldtype,
				"options": df.options,
				"reqd": df.reqd,
				"read_only": df.read_only or bool(df.fetch_from),
				"default": df.default,
				"in_list_view": df.in_list_view,
			}
		)
	return meta, fields


@frappe.whitelist()
def get_register(key: str, search: str | None = None, start: int = 0, page_length: int = 50):
	config = get_config(key)
	doctype = config["doctype"]
	meta, fields = field_meta(doctype)
	columns = [f["fieldname"] for f in fields if f["in_list_view"]]
	or_filters = None
	if search:
		like = f"%{search}%"
		text_fields = [f["fieldname"] for f in fields if f["fieldtype"] in ("Data", "Link") and f["in_list_view"]]
		or_filters = {fn: ["like", like] for fn in [*text_fields, "name"]}
	rows = frappe.get_list(
		doctype,
		fields=["name", *[f["fieldname"] for f in fields]],
		or_filters=or_filters,
		order_by="creation desc",
		start=cint(start),
		page_length=cint(page_length),
	)
	stats = []
	if config.get("stat"):
		stats = frappe.get_list(
			doctype,
			filters=config.get("stat_filter") or {},
			fields=[config["stat"], {"COUNT": "*", "as": "count"}],
			group_by=config["stat"],
			order_by=f"{config['stat']} asc",
		)
	return {
		"title": config["title"],
		"module": config["module"],
		"doctype": doctype,
		"fields": fields,
		"columns": columns,
		"rows": rows,
		"total": frappe.db.count(doctype),
		"stats": {"field": config.get("stat"), "label": config.get("stat_label"), "rows": stats},
		"certificate": bool(config.get("certificate")),
		"links": config.get("links") or [],
		"survey": bool(config.get("survey")),
		"can": {
			"create": bool(frappe.has_permission(doctype, "create")),
			"write": bool(frappe.has_permission(doctype, "write")),
		},
	}


@frappe.whitelist(methods=["POST"])
def save_record(key: str, data: dict | str):
	config = get_config(key)
	data = frappe.parse_json(data)
	_meta, fields = field_meta(config["doctype"])
	editable = {f["fieldname"] for f in fields if not f["read_only"]}
	values = {k: v for k, v in data.items() if k in editable}
	if data.get("name"):
		doc = frappe.get_doc(config["doctype"], data["name"])
		doc.update(values)
		doc.save()
	else:
		doc = frappe.get_doc({"doctype": config["doctype"], **values})
		doc.insert()
	return doc.name


@frappe.whitelist()
def get_record(key: str, name: str):
	config = get_config(key)
	doc = frappe.get_doc(config["doctype"], name)
	doc.check_permission("read")
	return doc.as_dict()


@frappe.whitelist()
def search_link(doctype: str, txt: str = ""):
	"""Options for a Link field in a register form."""
	allowed = {f["options"] for c in REGISTERS.values() for f in field_meta(c["doctype"])[1] if f["fieldtype"] == "Link"}
	if doctype not in allowed:
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	meta = frappe.get_meta(doctype)
	title = meta.title_field or "name"
	like = f"%{txt}%"
	filters = {"status": "Available"} if doctype == "Blood Bag" else {}
	rows = frappe.get_list(
		doctype,
		fields=["name", f"{title} as title"] if title != "name" else ["name"],
		or_filters={"name": ["like", like], title: ["like", like]} if txt else None,
		filters=filters,
		order_by="modified desc",
		page_length=15,
	)
	return [{"value": r.name, "label": r.get("title") or r.name, "description": r.name if r.get("title") else None} for r in rows]


# ---------------------------------------------------------------- surveys


@frappe.whitelist()
def get_survey(name: str):
	survey = frappe.get_doc("Survey Form", name)
	survey.check_permission("read")
	questions = [q.strip() for q in (survey.questions or "").splitlines() if q.strip()]
	responses = frappe.get_all("Survey Response", filters={"survey": name}, fields=["answers", "average_rating", "respondent", "comment", "response_date"], order_by="creation desc")
	totals = [0.0] * len(questions)
	for r in responses:
		answers = frappe.parse_json(r.answers or "[]")
		for i, value in enumerate(answers[: len(questions)]):
			totals[i] += float(value or 0)
	count = len(responses)
	return {
		"name": survey.name,
		"title": survey.title,
		"audience": survey.audience,
		"description": survey.description,
		"questions": [{"text": q, "average": round(totals[i] / count, 2) if count else None} for i, q in enumerate(questions)],
		"responses": count,
		"average": round(sum(r.average_rating or 0 for r in responses) / count, 2) if count else None,
		"comments": [r for r in responses if r.comment][:10],
	}


@frappe.whitelist(methods=["POST"])
def submit_survey(name: str, answers: list | str, respondent: str | None = None, comment: str | None = None):
	answers = [max(1, min(5, int(a))) for a in frappe.parse_json(answers)]
	survey = frappe.get_doc("Survey Form", name)
	survey.check_permission("read")
	doc = frappe.get_doc(
		{
			"doctype": "Survey Response",
			"survey": name,
			"respondent": respondent or frappe.db.get_value("User", frappe.session.user, "full_name"),
			"answers": frappe.as_json(answers),
			"average_rating": round(sum(answers) / len(answers), 2) if answers else 0,
			"comment": comment,
		}
	)
	doc.insert()
	return doc.name
