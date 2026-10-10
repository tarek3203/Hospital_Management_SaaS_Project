from frappe.model.document import Document

from hospital_saas.finance import cancel, post


class HospitalExpense(Document):
	def after_insert(self):
		post(self, self.expense_head, self.expense_date, income=False)

	def on_trash(self):
		cancel(self)
