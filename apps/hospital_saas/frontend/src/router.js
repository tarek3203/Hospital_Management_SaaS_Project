import { createRouter, createWebHistory } from "vue-router"

const routes = [
	{ path: "/", name: "Dashboard", component: () => import("./pages/Dashboard.vue") },
	{ path: "/patients", name: "Patients", component: () => import("./pages/Patients.vue") },
	{ path: "/appointments", name: "Appointments", component: () => import("./pages/Appointments.vue") },
	{ path: "/opd", name: "Opd", component: () => import("./pages/Opd.vue") },
	{ path: "/opd/patient/:patient", name: "OpdPatient", component: () => import("./pages/OpdPatient.vue"), props: true },
	{ path: "/opd/visit/:appointment", name: "OpdVisit", component: () => import("./pages/OpdVisit.vue"), props: true },
	{ path: "/module/:moduleKey", name: "ComingSoon", component: () => import("./pages/ComingSoon.vue"), props: true },
	{ path: "/:pathMatch(.*)*", redirect: "/" },
]

export default createRouter({ history: createWebHistory("/hms"), routes })
