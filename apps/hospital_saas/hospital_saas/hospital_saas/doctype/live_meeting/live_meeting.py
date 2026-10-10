import frappe
from frappe.model.document import Document


class LiveMeeting(Document):
	def validate(self):
		if not self.join_url and self.platform == "Jitsi Meet":
			# Jitsi needs no account: an unguessable room name is the meeting.
			self.join_url = f"https://meet.jit.si/CityCare-{frappe.generate_hash(length=12)}"
