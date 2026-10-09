from frappe.model.document import Document
from frappe.utils import flt


class ReferralPayment(Document):
	def validate(self):
		self.commission = round(flt(self.bill_amount) * flt(self.commission_percent) / 100, 2)
