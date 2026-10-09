import { createRouter, createWebHistory } from "vue-router"

const routes = [
	{ path: "/", name: "Dashboard", component: () => import("./pages/Dashboard.vue") },
	{ path: "/patients", name: "Patients", component: () => import("./pages/Patients.vue") },
	{ path: "/appointments", name: "Appointments", component: () => import("./pages/Appointments.vue") },
	{ path: "/opd", name: "Opd", component: () => import("./pages/Opd.vue") },
	{ path: "/opd/patient/:patient", name: "OpdPatient", component: () => import("./pages/OpdPatient.vue"), props: true },
	{
		path: "/opd/visit/:appointment/print",
		name: "PrescriptionPrint",
		component: () => import("./pages/PrescriptionPrint.vue"),
		props: true,
		meta: { bare: true },
	},
	{ path: "/opd/visit/:appointment", name: "OpdVisit", component: () => import("./pages/OpdVisit.vue"), props: true },
	{ path: "/ipd", name: "Ipd", component: () => import("./pages/Ipd.vue") },
	{ path: "/ipd/:record", name: "IpdStay", component: () => import("./pages/IpdStay.vue"), props: true },
	{ path: "/beds", name: "BedBoard", component: () => import("./pages/BedBoard.vue") },
	{ path: "/billing", name: "Billing", component: () => import("./pages/Billing.vue") },
	{
		path: "/billing/:invoice/receipt",
		name: "Receipt",
		component: () => import("./pages/ReceiptPrint.vue"),
		props: true,
		meta: { bare: true },
	},
	{ path: "/pathology", name: "Pathology", component: () => import("./pages/LabWorklist.vue"), props: { section: "Pathology" } },
	{ path: "/radiology", name: "Radiology", component: () => import("./pages/LabWorklist.vue"), props: { section: "Radiology" } },
	{ path: "/lab/:name", name: "LabTest", component: () => import("./pages/LabTest.vue"), props: true },
	{ path: "/lab/:name/report", name: "LabReport", component: () => import("./pages/LabReport.vue"), props: true, meta: { bare: true } },
	{ path: "/pharmacy", name: "Pharmacy", component: () => import("./pages/Pharmacy.vue") },
	{ path: "/r/:registerKey", name: "Register", component: () => import("./pages/RegisterPage.vue"), props: true },
	{
		path: "/r/:registerKey/:name/certificate",
		name: "Certificate",
		component: () => import("./pages/CertificatePrint.vue"),
		props: true,
		meta: { bare: true },
	},
	{ path: "/module/:moduleKey", name: "ComingSoon", component: () => import("./pages/ComingSoon.vue"), props: true },
	{ path: "/:pathMatch(.*)*", redirect: "/" },
]

export default createRouter({ history: createWebHistory("/hms"), routes })
