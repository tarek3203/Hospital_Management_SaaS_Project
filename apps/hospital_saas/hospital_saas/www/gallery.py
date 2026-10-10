from hospital_saas.website import base_context, published


def get_context(context):
	base_context(context, "Gallery", "/gallery")
	context.photos = published("Gallery Photo", ["caption", "image", "category"], "creation desc")
	return context
