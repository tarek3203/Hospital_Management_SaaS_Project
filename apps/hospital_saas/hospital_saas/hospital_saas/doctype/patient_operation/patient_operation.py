import frappe
from frappe.model.document import Document


class PatientOperation(Document):
	"""An operation theatre booking for an OPD visit or IPD stay."""

	def validate(self):
		if not self.inpatient_record and self.patient:
			self.inpatient_record = frappe.db.get_value("Patient", self.patient, "inpatient_record") or None
