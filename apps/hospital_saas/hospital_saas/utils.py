from frappe.utils import get_time


def hhmm(value):
	"""Time or timedelta from the database as "HH:MM" ("9:05:00" -> "09:05")."""
	if value in (None, ""):
		return None
	return get_time(value).strftime("%H:%M")
