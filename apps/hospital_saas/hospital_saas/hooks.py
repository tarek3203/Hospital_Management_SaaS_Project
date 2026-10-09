app_name = "hospital_saas"
app_title = "Hospital SaaS"
app_publisher = "KompileX"
app_description = "Configurable multi-branch Hospital Management SaaS built on Frappe"
app_email = "mostafizur@wafisolutions.com"
app_license = "mit"

required_apps = ["erpnext", "hrms", "healthcare"]

app_include_css = "/assets/hospital_saas/css/hospital_saas.css"

website_context = {
	"favicon": "/assets/hospital_saas/images/logo.svg",
	"splash_image": "/assets/hospital_saas/images/logo.svg",
}

web_include_js = "/assets/hospital_saas/js/demo_login.js"

website_route_rules = [
	{"from_route": "/hms/<path:app_path>", "to_route": "hms"},
]

after_install = "hospital_saas.install.after_install"
after_migrate = "hospital_saas.roles.setup_roles"

doc_events = {
	"User": {
		"before_validate": "hospital_saas.demo_mode.protect_demo_user",
		"validate": "hospital_saas.demo_mode.protect_demo_user_roles",
		"before_rename": "hospital_saas.demo_mode.block_demo_user_rename",
		"on_trash": "hospital_saas.demo_mode.block_demo_user_delete",
	},
}

scheduler_events = {
	"cron": {
		# Just after midnight, so the demo's "today" moves with the calendar.
		"5 0 * * *": ["hospital_saas.demo.rolling_dates.roll_forward"],
	},
}

override_whitelisted_methods = {
	"frappe.core.doctype.user.user.update_password": "hospital_saas.demo_mode.update_password",
}
