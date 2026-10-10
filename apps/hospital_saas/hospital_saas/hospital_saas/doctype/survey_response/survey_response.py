import frappe
from frappe import _
from frappe.model.document import Document


class SurveyResponse(Document):
	def validate(self):
		# The average is derived from the answers, never trusted from the client.
		answers = frappe.parse_json(self.answers or "[]")
		if not isinstance(answers, list) or any(not isinstance(a, int) or not 1 <= a <= 5 for a in answers):
			frappe.throw(_("Each answer must be a rating from 1 to 5."))
		self.average_rating = round(sum(answers) / len(answers), 2) if answers else 0
