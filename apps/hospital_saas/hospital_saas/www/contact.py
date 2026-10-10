from hospital_saas.website import base_context


def get_context(context):
	base_context(context, "Contact us", "/contact")
	return context
