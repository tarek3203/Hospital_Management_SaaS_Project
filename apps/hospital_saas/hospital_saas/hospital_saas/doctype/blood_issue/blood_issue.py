import frappe
from frappe import _
from frappe.model.document import Document


class BloodIssue(Document):
	def validate(self):
		if self.is_new() and frappe.db.get_value("Blood Bag", self.bag, "status") != "Available":
			frappe.throw(_("Blood bag {0} is not available.").format(self.bag))

	def after_insert(self):
		frappe.db.set_value("Blood Bag", self.bag, "status", "Issued")

	def on_trash(self):
		frappe.db.set_value("Blood Bag", self.bag, "status", "Available")
