"""Small corrections to upstream configuration, applied on install and migrate."""

import json

import frappe


def apply_fixes():
	fix_lab_test_history_fields()


def fix_lab_test_history_fields():
	"""Healthcare ships Lab Test's "Comments" field as a Table in Patient History
	Settings. Submitting a lab test with a comment then fails while building the
	medical record ("DocType None not found"). It is a text field."""
	row = frappe.db.get_value(
		"Patient History Standard Document Type", {"document_type": "Lab Test"}, ["name", "selected_fields"], as_dict=True
	)
	if not row or not row.selected_fields:
		return
	fields = json.loads(row.selected_fields)
	changed = False
	for field in fields:
		if field.get("fieldname") == "lab_test_comment" and field.get("fieldtype") == "Table":
			field["fieldtype"] = "Text"
			changed = True
	if changed:
		frappe.db.set_value("Patient History Standard Document Type", row.name, "selected_fields", json.dumps(fields))
