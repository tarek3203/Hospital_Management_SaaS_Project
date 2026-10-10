"""Sidebar menu of the /hms app, per job.

Mirrors the module list and per-role visibility of the Smart Hospital demo
(PLAN.md section 2). Each entry opens one of:
- `route`: a page of the /hms app
- `desk`: the matching Frappe Desk page, until the /hms page is built
- neither: a "being built" page naming the phase that delivers it
"""

SA, AD, DOC, PH, PATH, RAD, ACC, REC, NUR = (
	"Super Admin",
	"Admin",
	"Doctor",
	"Pharmacist",
	"Pathologist",
	"Radiologist",
	"Accountant",
	"Receptionist",
	"Nurse",
)
STAFF = [SA, AD, DOC, PH, PATH, RAD, ACC, REC, NUR]

MENU = [
	{"key": "dashboard", "label": "Dashboard", "icon": "home", "jobs": STAFF, "route": "/"},
	{"key": "patients", "label": "Patient", "icon": "users", "jobs": STAFF, "route": "/patients"},
	{"key": "billing", "label": "Billing", "icon": "file-text", "jobs": [SA, AD, DOC, PH, PATH, RAD, ACC, REC], "route": "/billing"},
	{"key": "appointments", "label": "Appointment", "icon": "calendar", "jobs": [SA, AD, DOC, ACC, REC], "route": "/appointments"},
	{"key": "opd", "label": "OPD - Out Patient", "icon": "activity", "jobs": STAFF, "route": "/opd"},
	{"key": "ipd", "label": "IPD - In Patient", "icon": "layers", "jobs": STAFF, "route": "/ipd"},
	{"key": "pharmacy", "label": "Pharmacy", "icon": "package", "jobs": [SA, AD, PH, ACC, REC], "route": "/pharmacy"},
	{"key": "pathology", "label": "Pathology", "icon": "droplet", "jobs": [SA, AD, DOC, PATH, ACC, REC], "route": "/pathology"},
	{"key": "radiology", "label": "Radiology", "icon": "aperture", "jobs": [SA, AD, DOC, RAD, ACC, REC], "route": "/radiology"},
	{
		"key": "blood-bank",
		"label": "Blood Bank",
		"icon": "heart",
		"jobs": [SA, AD, DOC, PH, PATH, ACC, REC],
		"children": [
			{"key": "blood-bags", "label": "Blood Stock", "route": "/r/blood-bags"},
			{"key": "blood-issues", "label": "Blood Issue", "route": "/r/blood-issues"},
			{"key": "blood-donors", "label": "Donors", "route": "/r/blood-donors"},
		],
	},
	{
		"key": "ambulance",
		"label": "Ambulance",
		"icon": "truck",
		"jobs": [SA, AD, DOC, ACC, REC],
		"children": [
			{"key": "ambulance-calls", "label": "Ambulance Calls", "route": "/r/ambulance-calls"},
			{"key": "ambulances", "label": "Vehicles", "route": "/r/ambulances"},
		],
	},
	{
		"key": "front-office",
		"label": "Front Office",
		"icon": "user-check",
		"jobs": [SA, AD, REC],
		"children": [
			{"key": "visitors", "label": "Visitor Book", "route": "/r/visitors"},
			{"key": "calls", "label": "Phone Call Log", "route": "/r/calls"},
			{"key": "postal", "label": "Postal Receive / Dispatch", "route": "/r/postal"},
			{"key": "complaints", "label": "Complaints", "route": "/r/complaints"},
			{"key": "web-enquiries", "label": "Website Enquiries", "route": "/r/web-enquiries"},
		],
	},
	{
		"key": "birth-death",
		"label": "Birth & Death Record",
		"icon": "file",
		"jobs": [SA, AD, DOC, REC],
		"children": [
			{"key": "births", "label": "Birth Record", "route": "/r/births"},
			{"key": "deaths", "label": "Death Record", "route": "/r/deaths"},
		],
	},
	{
		"key": "multi-branch",
		"label": "Multi Branch",
		"icon": "git-branch",
		"jobs": [SA, AD],
		"children": [
			{"key": "branch-overview", "label": "Overview", "route": "/branches"},
			{"key": "branch-report", "label": "Report", "route": "/branches/report"},
			{"key": "branch-settings", "label": "Settings", "desk": "/desk/branch"},
		],
	},
	{
		"key": "hr",
		"label": "Human Resource",
		"icon": "user",
		"jobs": STAFF,
		"desk": "/desk/employee",
		"children": [
			{"key": "staff", "label": "Staff Directory", "desk": "/desk/employee"},
			{"key": "qr-attendance", "label": "QR Code Attendance", "jobs": [SA, AD, DOC], "route": "/attendance?kiosk=1"},
			{"key": "attendance", "label": "Attendance", "route": "/attendance"},
			{"key": "duty-roster", "label": "Duty Roster", "jobs": [SA, AD], "route": "/duty-roster"},
			{"key": "annual-calendar", "label": "Annual Calendar", "jobs": [SA, AD], "route": "/annual-calendar"},
		],
	},
	{
		"key": "referral",
		"label": "Referral",
		"icon": "share-2",
		"jobs": [SA, AD, ACC],
		"children": [
			{"key": "referral-payments", "label": "Referral Payments", "route": "/r/referral-payments"},
			{"key": "referral-persons", "label": "Referral Persons", "route": "/r/referral-persons"},
		],
	},
	{"key": "tpa", "label": "TPA Management", "icon": "shield", "jobs": [SA, AD, DOC, ACC, REC], "route": "/r/tpa"},
	{
		"key": "finance",
		"label": "Finance",
		"icon": "dollar-sign",
		"jobs": [SA, AD, ACC],
		"children": [
			{"key": "income", "label": "Income", "route": "/r/income"},
			{"key": "expenses", "label": "Expenses", "route": "/r/expenses"},
		],
	},
	{"key": "survey", "label": "Survey Forms", "icon": "clipboard", "jobs": [SA, AD], "route": "/r/surveys"},
	{"key": "messaging", "label": "Messaging", "icon": "message-square", "jobs": STAFF, "route": "/r/notices"},
	{"key": "inventory", "label": "Inventory", "icon": "archive", "jobs": [SA, AD, ACC, REC], "desk": "/desk/item"},
	{"key": "download-center", "label": "Download Center", "icon": "download", "jobs": STAFF, "route": "/r/downloads"},
	{
		"key": "certificate",
		"label": "Certificate",
		"icon": "award",
		"jobs": [SA, AD, DOC],
		"children": [
			{"key": "certificates", "label": "Certificate", "phase": 4},
			{"key": "patient-id-card", "label": "Patient ID Card", "route": "/cards/patient"},
			{"key": "staff-id-card", "label": "Staff ID Card", "jobs": [SA, AD], "route": "/cards/staff"},
		],
	},
	{
		"key": "front-cms",
		"label": "Front CMS",
		"icon": "globe",
		"jobs": [SA, AD],
		"children": [
			{"key": "web-site", "label": "View website", "desk": "/home"},
			{"key": "web-enquiries", "label": "Enquiries", "route": "/r/web-enquiries"},
			{"key": "web-events", "label": "Events", "route": "/r/web-events"},
			{"key": "web-gallery", "label": "Gallery", "route": "/r/web-gallery"},
			{"key": "web-faq", "label": "FAQ", "route": "/r/web-faq"},
			{"key": "web-testimonials", "label": "Testimonials", "route": "/r/web-testimonials"},
		],
	},
	{
		"key": "live-consultation",
		"label": "Live Consultation",
		"icon": "video",
		"jobs": STAFF,
		"children": [
			{"key": "live-consult", "label": "Live Consultation", "jobs": [SA, AD, DOC, ACC], "route": "/r/live-meetings"},
			{"key": "live-meeting", "label": "Live Meeting", "route": "/r/live-meetings?type=Meeting"},
		],
	},
	{"key": "reports", "label": "Reports", "icon": "bar-chart-2", "jobs": STAFF, "desk": "/desk/healthcare", "phase": 8},
	{"key": "setup", "label": "Setup", "icon": "settings", "jobs": STAFF, "desk": "/desk", "phase": 2},
]


# Patient portal: the eleven patient menus of the Smart Hospital demo.
PATIENT_MENU = [
	{"key": "dashboard", "label": "Dashboard", "icon": "home", "route": "/"},
	{"key": "my-appointments", "label": "My Appointments", "icon": "calendar", "route": "/portal/appointments"},
	{"key": "my-opd", "label": "OPD", "icon": "activity", "route": "/portal/opd"},
	{"key": "my-ipd", "label": "IPD", "icon": "layers", "route": "/portal/ipd"},
	{"key": "my-pharmacy", "label": "Pharmacy", "icon": "package", "route": "/portal/pharmacy"},
	{"key": "my-pathology", "label": "Pathology", "icon": "droplet", "route": "/portal/pathology"},
	{"key": "my-radiology", "label": "Radiology", "icon": "aperture", "route": "/portal/radiology"},
	{"key": "my-blood-bank", "label": "Blood Bank", "icon": "heart", "route": "/portal/blood-bank"},
	{"key": "my-ambulance", "label": "Ambulance", "icon": "truck", "route": "/portal/ambulance"},
	{"key": "my-live", "label": "Live Consultation", "icon": "video", "route": "/portal/live"},
	{"key": "my-downloads", "label": "Download Center", "icon": "download", "route": "/portal/downloads"},
	{"key": "my-surveys", "label": "Survey Forms", "icon": "clipboard", "route": "/portal/surveys"},
]


def menu_for(job):
	"""Menu entries (and children) visible to `job`."""
	if job == "Patient":
		return PATIENT_MENU
	items = []
	for item in MENU:
		if job not in item["jobs"]:
			continue
		entry = {k: v for k, v in item.items() if k not in ("jobs", "children")}
		children = [
			{k: v for k, v in child.items() if k != "jobs"}
			for child in item.get("children", [])
			if job in child.get("jobs", item["jobs"])
		]
		if children:
			entry["children"] = children
		items.append(entry)
	return items
