from hospital_saas.website import base_context, published


def get_context(context):
	base_context(context, "FAQ", "/faq")
	context.faqs = published("FAQ Entry", ["question", "answer"], "sort_order asc")
	context.testimonials = published("Patient Testimonial", ["patient_name", "designation", "rating", "testimonial"], "creation desc")
	return context
