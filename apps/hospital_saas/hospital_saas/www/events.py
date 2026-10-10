from hospital_saas.website import base_context, published


def get_context(context):
	base_context(context, "Events", "/events")
	context.events = published("Hospital Event", ["title", "event_date", "venue", "summary", "image"], "event_date desc")
	return context
