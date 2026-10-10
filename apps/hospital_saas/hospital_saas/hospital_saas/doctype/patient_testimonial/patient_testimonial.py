from frappe.model.document import Document


class PatientTestimonial(Document):
	def validate(self):
		self.rating = min(max(int(self.rating or 5), 1), 5)
