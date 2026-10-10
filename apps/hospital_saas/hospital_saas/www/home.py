from hospital_saas.website import base_context, departments, doctors, published, stats


def get_context(context):
	base_context(context, "Home", "/home")
	context.stats = stats()
	context.departments = departments()[:8]
	context.doctors = doctors()[:4]
	context.testimonials = published("Patient Testimonial", ["patient_name", "designation", "rating", "testimonial"], "creation desc", 3)
	context.events = published("Hospital Event", ["title", "event_date", "venue", "summary"], "event_date desc", 3)
	return context
