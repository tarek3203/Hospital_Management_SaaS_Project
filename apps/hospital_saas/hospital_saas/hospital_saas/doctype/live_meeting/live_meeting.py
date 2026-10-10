from urllib.parse import urlparse

import frappe
from frappe import _
from frappe.model.document import Document

# Join links may only point at the meeting services we support.
ALLOWED_HOSTS = {"Jitsi Meet": ("meet.jit.si",), "Zoom": ("zoom.us",), "Google Meet": ("meet.google.com",)}


class LiveMeeting(Document):
	def validate(self):
		if self.platform == "Jitsi Meet" and not self.join_url:
			# Jitsi needs no account: an unguessable room name is the meeting.
			self.join_url = f"https://meet.jit.si/CityCare-{frappe.generate_hash(length=12)}"
		if self.join_url:
			url = urlparse(self.join_url)
			hosts = ALLOWED_HOSTS.get(self.platform, ())
			if url.scheme != "https" or not any(url.hostname == h or (url.hostname or "").endswith("." + h) for h in hosts):
				frappe.throw(_("The join link must be an https link on {0}.").format(", ".join(hosts) or self.platform))
