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
	{"key": "pharmacy", "label": "Pharmacy", "icon": "package", "jobs": [SA, AD, PH, ACC, REC], "desk": "/desk/item?item_group=Pharmacy", "phase": 3},
	{"key": "pathology", "label": "Pathology", "icon": "droplet", "jobs": [SA, AD, DOC, PATH, ACC, REC], "route": "/pathology"},
	{"key": "radiology", "label": "Radiology", "icon": "aperture", "jobs": [SA, AD, DOC, RAD, ACC, REC], "route": "/radiology"},
	{"key": "blood-bank", "label": "Blood Bank", "icon": "heart", "jobs": [SA, AD, DOC, PH, PATH, ACC, REC], "phase": 4},
	{"key": "ambulance", "label": "Ambulance", "icon": "truck", "jobs": [SA, AD, DOC, ACC, REC], "phase": 4},
	{"key": "front-office", "label": "Front Office", "icon": "user-check", "jobs": [SA, AD, REC], "phase": 4},
	{
		"key": "birth-death",
		"label": "Birth & Death Record",
		"icon": "file",
		"jobs": [SA, AD, DOC, REC],
		"phase": 4,
		"children": [
			{"key": "birth-record", "label": "Birth Record", "phase": 4},
			{"key": "death-record", "label": "Death Record", "phase": 4},
		],
	},
	{
		"key": "multi-branch",
		"label": "Multi Branch",
		"icon": "git-branch",
		"jobs": [SA, AD],
		"phase": 5,
		"children": [
			{"key": "branch-overview", "label": "Overview", "phase": 5},
			{"key": "branch-report", "label": "Report", "phase": 5},
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
			{"key": "qr-attendance", "label": "QR Code Attendance", "jobs": [SA, AD, DOC], "phase": 5},
			{"key": "attendance", "label": "Attendance", "desk": "/desk/attendance"},
			{"key": "duty-roster", "label": "Duty Roster", "jobs": [SA, AD], "phase": 5},
			{"key": "annual-calendar", "label": "Annual Calendar", "jobs": [SA, AD], "desk": "/desk/holiday-list"},
		],
	},
	{"key": "referral", "label": "Referral", "icon": "share-2", "jobs": [SA, AD, ACC], "phase": 3},
	{"key": "tpa", "label": "TPA Management", "icon": "shield", "jobs": [SA, AD, DOC, ACC, REC], "phase": 3},
	{
		"key": "finance",
		"label": "Finance",
		"icon": "dollar-sign",
		"jobs": [SA, AD, ACC],
		"children": [
			{"key": "income", "label": "Income", "desk": "/desk/payment-entry?payment_type=Receive"},
			{"key": "expenses", "label": "Expenses", "desk": "/desk/journal-entry"},
		],
	},
	{"key": "survey", "label": "Survey Forms", "icon": "clipboard", "jobs": [SA, AD], "phase": 6},
	{"key": "messaging", "label": "Messaging", "icon": "message-square", "jobs": STAFF, "phase": 6},
	{"key": "inventory", "label": "Inventory", "icon": "archive", "jobs": [SA, AD, ACC, REC], "desk": "/desk/item"},
	{"key": "download-center", "label": "Download Center", "icon": "download", "jobs": STAFF, "phase": 6},
	{
		"key": "certificate",
		"label": "Certificate",
		"icon": "award",
		"jobs": [SA, AD, DOC],
		"phase": 4,
		"children": [
			{"key": "certificates", "label": "Certificate", "phase": 4},
			{"key": "patient-id-card", "label": "Patient ID Card", "phase": 4},
			{"key": "staff-id-card", "label": "Staff ID Card", "jobs": [SA, AD], "phase": 4},
		],
	},
	{"key": "front-cms", "label": "Front CMS", "icon": "globe", "jobs": [SA, AD], "phase": 7},
	{
		"key": "live-consultation",
		"label": "Live Consultation",
		"icon": "video",
		"jobs": STAFF,
		"phase": 6,
		"children": [
			{"key": "live-consult", "label": "Live Consultation", "jobs": [SA, AD, DOC, ACC], "phase": 6},
			{"key": "live-meeting", "label": "Live Meeting", "phase": 6},
		],
	},
	{"key": "reports", "label": "Reports", "icon": "bar-chart-2", "jobs": STAFF, "desk": "/desk/healthcare", "phase": 8},
	{"key": "setup", "label": "Setup", "icon": "settings", "jobs": STAFF, "desk": "/desk", "phase": 2},
]


def menu_for(job):
	"""Menu entries (and children) visible to `job`."""
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
