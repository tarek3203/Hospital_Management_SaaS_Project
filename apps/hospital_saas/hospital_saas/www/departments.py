from hospital_saas.website import base_context, departments, doctors


def get_context(context):
	base_context(context, "Departments", "/departments")
	context.departments = departments()
	context.doctors = doctors()
	return context
