import frappe
from frappe import _
from frappe.model.document import Document


class BloodIssue(Document):
	def validate(self):
		if self.is_new():
			if frappe.db.get_value("Blood Bag", self.bag, "status") != "Available":
				frappe.throw(_("Blood bag {0} is not available.").format(self.bag))
		elif self.has_value_changed("bag"):
			# Swapping bags would leave one bag wrongly issued and skip the check above.
			frappe.throw(_("The bag of an issue cannot be changed. Delete the issue and issue again."))

	def after_insert(self):
		frappe.db.set_value("Blood Bag", self.bag, "status", "Issued")

	def on_trash(self):
		frappe.db.set_value("Blood Bag", self.bag, "status", "Available")
