from hospital_saas.website import base_context, doctors


def get_context(context):
	base_context(context, "Book an appointment", "/appointment")
	context.doctors = doctors()
	return context
