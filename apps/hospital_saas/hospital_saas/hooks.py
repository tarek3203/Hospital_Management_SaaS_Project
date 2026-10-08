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

after_install = "hospital_saas.install.after_install"
