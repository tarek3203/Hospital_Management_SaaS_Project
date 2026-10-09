import frappe
from frappe import _
from frappe.model.document import Document


class PatientOperation(Document):
	"""An operation theatre booking for an OPD visit or IPD stay."""

	def validate(self):
		if not self.inpatient_record and self.patient:
			self.inpatient_record = frappe.db.get_value("Patient", self.patient, "inpatient_record") or None
		self.validate_links()

	def validate_links(self):
		"""The OPD visit and IPD stay must belong to the same patient, and new
		bookings need an admission that is still open."""
		if self.inpatient_record:
			patient, status = frappe.db.get_value("Inpatient Record", self.inpatient_record, ["patient", "status"])
			if patient != self.patient:
				frappe.throw(_("IPD {0} belongs to another patient.").format(self.inpatient_record))
			if self.is_new() and status == "Discharged":
				frappe.throw(_("Patient has been discharged from {0}.").format(self.inpatient_record))
		if self.appointment and frappe.db.get_value("Patient Appointment", self.appointment, "patient") != self.patient:
			frappe.throw(_("OPD visit {0} belongs to another patient.").format(self.appointment))
