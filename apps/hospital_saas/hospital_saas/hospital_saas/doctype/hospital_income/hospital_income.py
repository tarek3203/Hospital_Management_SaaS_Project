from frappe.model.document import Document

from hospital_saas.finance import cancel, post


class HospitalIncome(Document):
	def after_insert(self):
		post(self, self.income_head, self.income_date, income=True)

	def on_trash(self):
		cancel(self)
