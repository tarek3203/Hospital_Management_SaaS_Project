<template>
	<div class="mx-auto max-w-6xl space-y-4 p-4 sm:p-6">
		<div>
			<h1 class="text-xl font-semibold text-gray-900">Setup</h1>
			<p class="text-sm text-gray-600">Masters and settings. Most open in the admin screens (Desk), where every list can be filtered, imported and exported.</p>
		</div>
		<div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
			<button
				v-for="item in items"
				:key="item.label"
				class="flex items-start gap-3 rounded-lg border bg-white p-4 text-left transition-colors hover:border-brand-500"
				@click="open(item)"
			>
				<div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600"><FeatherIcon :name="item.icon" class="h-4 w-4" /></div>
				<div class="min-w-0">
					<p class="flex items-center gap-2 font-medium text-gray-900">{{ item.label }} <SoonBadge v-if="item.soon" /></p>
					<p class="text-sm text-gray-600">{{ item.text }}</p>
				</div>
			</button>
		</div>
	</div>
</template>

<script setup>
import { useRouter } from "vue-router"
import { FeatherIcon, toast } from "frappe-ui"
import SoonBadge from "@/components/SoonBadge.vue"

const router = useRouter()
const items = [
	{ label: "Hospital settings", icon: "sliders", text: "Hospital name, logo, timezone, date format", desk: "/desk/system-settings" },
	{ label: "Hospital charges", icon: "dollar-sign", text: "Consultation, bed, test and service prices", desk: "/desk/item-price" },
	{ label: "Beds and wards", icon: "grid", text: "Floors, wards, rooms and beds per branch", desk: "/desk/healthcare-service-unit/view/tree" },
	{ label: "Bed types", icon: "layers", text: "General ward, cabin, ICU and their daily rates", desk: "/desk/healthcare-service-unit-type" },
	{ label: "Print header and footer", icon: "printer", text: "Letter heads for bills, prescriptions and reports", desk: "/desk/letter-head" },
	{ label: "Doctors and schedules", icon: "user-plus", text: "Practitioners, fees and chamber times", desk: "/desk/healthcare-practitioner" },
	{ label: "Departments", icon: "briefcase", text: "Medical departments", desk: "/desk/medical-department" },
	{ label: "Appointment types", icon: "calendar", text: "Consultation, follow up, ward round", desk: "/desk/appointment-type" },
	{ label: "Medicines", icon: "package", text: "Pharmacy items, prices and reorder levels", desk: "/desk/item?item_group=Pharmacy" },
	{ label: "Pathology tests", icon: "droplet", text: "Test templates, units and normal ranges", desk: "/desk/lab-test-template?lab_test_group=Laboratory" },
	{ label: "Radiology tests", icon: "aperture", text: "Imaging templates and report sections", desk: "/desk/lab-test-template?lab_test_group=Radiology" },
	{ label: "Symptoms", icon: "thermometer", text: "Complaint list used in consultations", desk: "/desk/complaint" },
	{ label: "Diagnoses", icon: "clipboard", text: "Diagnosis list used in consultations", desk: "/desk/diagnosis" },
	{ label: "ICD-10 catalogue", icon: "book", text: "Import ICD-10 codes and map them to diagnoses", soon: true },
	{ label: "Findings", icon: "search", text: "Standard clinical findings by category", soon: true },
	{ label: "Operation types", icon: "scissors", text: "Operation catalogue with standard OT charges", soon: true },
	{ label: "Blood bank components", icon: "heart", text: "Components, shelf life and issue charges", soon: true },
	{ label: "Zoom and SMS settings", icon: "video", text: "Zoom API keys and the SMS gateway for notices", soon: true },
	{ label: "Staff designations", icon: "user", text: "Designations, leave types and shifts", desk: "/desk/designation" },
	{ label: "Shift types", icon: "clock", text: "Morning, evening and night shifts", desk: "/desk/shift-type" },
	{ label: "Referral persons", icon: "share-2", text: "Referring doctors and agents with commission", route: "/r/referral-persons" },
	{ label: "TPA organisations", icon: "shield", text: "Insurers and corporate health plans", route: "/r/tpa" },
	{ label: "Suppliers", icon: "truck", text: "Medicine and equipment suppliers", desk: "/desk/supplier" },
	{ label: "Custom fields", icon: "edit", text: "Add or change fields on any form (System Manager)", desk: "/desk/customize-form" },
]
function open(item) {
	if (item.soon) toast.info(`${item.label} is coming soon`)
	else if (item.route) router.push(item.route)
	else window.location.href = item.desk
}
</script>
