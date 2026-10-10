from hospital_saas.website import base_context, departments, stats


def get_context(context):
	base_context(context, "About us", "/about")
	context.stats = stats()
	context.departments = departments()
	return context
