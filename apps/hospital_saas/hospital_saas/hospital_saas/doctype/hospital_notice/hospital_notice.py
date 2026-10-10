from frappe.model.document import Document


class HospitalNotice(Document):
	def validate(self):
		# SMS and email go through a gateway that is not connected yet; the notice board is live.
		self.status = "Published" if self.channel == "Notice board" else "Queued for gateway"
