from urllib.parse import urlparse

import frappe
from frappe import _
from frappe.model.document import Document


class SharedContent(Document):
	def validate(self):
		if self.url and urlparse(self.url).scheme not in ("http", "https"):
			frappe.throw(_("Links must start with http:// or https://"))
		if not self.file and not self.url:
			frappe.throw(_("Upload a file or add a link."))
