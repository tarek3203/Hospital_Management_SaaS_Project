<template>
	<div class="mx-auto max-w-6xl space-y-5 p-4 sm:p-6">
		<div v-if="d" class="flex flex-wrap items-center gap-4 rounded-lg border bg-white p-5">
			<PatientHeader :patient="{ ...d.patient, visits: null }" />
			<Button variant="solid" @click="showBook = true">
				<template #prefix><FeatherIcon name="calendar" class="h-4 w-4" /></template>
				Book appointment
			</Button>
		</div>
		<div v-if="d" class="grid grid-cols-2 gap-3 lg:grid-cols-5">
			<StatCard v-for="(v, k) in d.counts" :key="k" :label="k" :value="v" :icon="ICONS[k]" />
			<StatCard label="Due to pay" :value="d.due" format="currency" icon="credit-card" :hint="d.due ? 'Pay at the counter' : 'All paid'" />
		</div>
		<p class="flex items-center gap-2 text-xs text-gray-500">Online payment by bKash, Nagad or card <SoonBadge /></p>
		<DataTable v-if="d" title="Upcoming appointments" :columns="cols" :rows="d.upcoming" link="/portal/appointments" empty-text="No upcoming appointments" />
		<PortalBookDialog v-model="showBook" @booked="dash.reload()" />
	</div>
</template>

<script setup>
import { computed, ref } from "vue"
import { Button, createResource, FeatherIcon } from "frappe-ui"
import DataTable from "@/components/DataTable.vue"
import PatientHeader from "@/components/PatientHeader.vue"
import PortalBookDialog from "@/components/PortalBookDialog.vue"
import SoonBadge from "@/components/SoonBadge.vue"
import StatCard from "@/components/StatCard.vue"

const showBook = ref(false)
const dash = createResource({ url: "hospital_saas.api.portal.get_dashboard", auto: true })
const d = computed(() => dash.data)
const ICONS = { Appointments: "calendar", "Lab reports": "droplet", Admissions: "layers", Bills: "file-text" }
const cols = [
	{ key: "appointment_date", label: "Date" },
	{ key: "appointment_time", label: "Time" },
	{ key: "practitioner_name", label: "Doctor" },
	{ key: "department", label: "Department" },
	{ key: "status", label: "Status", badge: true },
]
</script>
