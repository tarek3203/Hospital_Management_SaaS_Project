<template>
	<div class="mx-auto max-w-7xl space-y-4 p-4 sm:p-6">
		<div class="flex flex-wrap items-center gap-3">
			<div class="flex-1">
				<h1 class="text-xl font-semibold text-gray-900">Appointments</h1>
				<p class="text-sm text-gray-600">{{ total }} on {{ prettyDate }}</p>
			</div>
			<Button v-if="canBook" variant="solid" @click="openNew()">
				<template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
				Book appointment
			</Button>
		</div>

		<div class="flex flex-wrap items-center gap-2">
			<Button size="sm" @click="shiftDay(-1)"><FeatherIcon name="chevron-left" class="h-4 w-4" /></Button>
			<input v-model="date" type="date" class="h-7 rounded-md border-gray-300 text-sm" @change="appointments.reload()" />
			<Button size="sm" @click="shiftDay(1)"><FeatherIcon name="chevron-right" class="h-4 w-4" /></Button>
			<Button size="sm" variant="ghost" @click="goToday">Today</Button>
			<div class="ml-auto flex flex-wrap gap-1">
				<button
					v-for="tab in tabs"
					:key="tab.value"
					class="rounded-full px-3 py-1 text-xs font-medium transition-colors"
					:class="status === tab.value ? 'bg-gray-900 text-white' : 'bg-white text-gray-700 ring-1 ring-gray-200 hover:bg-gray-100'"
					@click="setStatus(tab.value)"
				>
					{{ tab.label }} <span class="ml-1 opacity-70">{{ tab.count }}</span>
				</button>
			</div>
		</div>

		<DataTable :columns="columns" :rows="appointments.data?.rows" empty-text="No appointments for this day">
			<template #cell-patient_name="{ row }">
				<p class="font-medium text-gray-900">{{ row.patient_name }}</p>
				<p class="text-xs text-gray-500">{{ row.patient }}</p>
			</template>
			<template #cell-practitioner_name="{ row }">
				<p>{{ row.practitioner_name }}</p>
				<p class="text-xs text-gray-500">{{ row.department }}</p>
			</template>
			<template #cell-paid_amount="{ row }">
				<span v-if="row.invoiced" class="text-gray-800">{{ formatCurrency(row.paid_amount) }}</span>
				<span v-else class="text-gray-400">Not billed</span>
			</template>
			<template v-if="canAct" #actions="{ row }">
				<Dropdown v-if="actionsFor(row).length" :options="actionsFor(row)" placement="right">
					<Button size="sm" variant="ghost"><FeatherIcon name="more-horizontal" class="h-4 w-4" /></Button>
				</Dropdown>
			</template>
		</DataTable>

		<NewAppointmentDialog v-model="showNew" :initial-patient="initialPatient" @booked="onBooked" @new-patient="newPatient" />
		<NewPatientDialog v-model="showNewPatient" @created="onPatientCreated" />
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { Button, createResource, Dropdown, FeatherIcon, toast } from "frappe-ui"
import DataTable from "@/components/DataTable.vue"
import NewAppointmentDialog from "@/components/NewAppointmentDialog.vue"
import NewPatientDialog from "@/components/NewPatientDialog.vue"
import { session } from "@/data/session"
import { formatCurrency, todayISO } from "@/utils"

const route = useRoute()
const router = useRouter()
const date = ref(todayISO())
const status = ref("")
const showNew = ref(false)
const showNewPatient = ref(false)
const initialPatient = ref(null)

const job = computed(() => session.data.job)
const canBook = computed(() => ["Super Admin", "Admin", "Receptionist"].includes(job.value))
const canAct = computed(() => ["Super Admin", "Admin", "Receptionist", "Doctor"].includes(job.value))

const columns = [
	{ key: "appointment_time", label: "Time" },
	{ key: "name", label: "ID" },
	{ key: "patient_name", label: "Patient" },
	{ key: "practitioner_name", label: "Doctor" },
	{ key: "appointment_type", label: "Type" },
	{ key: "paid_amount", label: "Paid" },
	{ key: "status", label: "Status", badge: true },
]

const appointments = createResource({
	url: "hospital_saas.api.appointments.get_appointments",
	makeParams: () => ({
		date: date.value,
		status: status.value,
		practitioner: job.value === "Doctor" ? session.data.practitioner : null,
	}),
	auto: true,
})

const counts = computed(() => appointments.data?.counts || {})
const total = computed(() => Object.values(counts.value).reduce((a, b) => a + b, 0))
const tabs = computed(() => [
	{ label: "All", value: "", count: total.value },
	...["Scheduled", "Open", "Checked In", "Checked Out", "Closed", "No Show", "Cancelled"]
		.filter((s) => counts.value[s])
		.map((s) => ({ label: s, value: s, count: counts.value[s] })),
])
const prettyDate = computed(() =>
	new Date(date.value + "T00:00").toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short", year: "numeric" }),
)

function setStatus(value) {
	status.value = value
	appointments.reload()
}
function shiftDay(n) {
	const d = new Date(date.value + "T00:00")
	d.setDate(d.getDate() + n)
	date.value = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
	appointments.reload()
}
function goToday() {
	date.value = todayISO()
	appointments.reload()
}

const setStatusResource = createResource({
	url: "hospital_saas.api.appointments.set_status",
	onSuccess(newStatus) {
		toast.success(`Marked ${newStatus}`)
		appointments.reload()
	},
	onError(err) {
		toast.error(err.messages?.[0] || "Could not update the appointment")
	},
})

function actionsFor(row) {
	const act = (label, icon, next) => ({ label, icon, onClick: () => setStatusResource.submit({ appointment: row.name, status: next }) })
	const open = ["Scheduled", "Open", "Confirmed"].includes(row.status)
	const actions = []
	if (open) actions.push(act("Check in", "log-in", "Checked In"))
	if (row.status === "Checked In") actions.push(act("Check out", "log-out", "Checked Out"))
	if (open) actions.push(act("No show", "user-x", "No Show"))
	if (open && canBook.value) actions.push(act("Cancel", "x-circle", "Cancelled"))
	actions.push({ label: "Open in Desk", icon: "external-link", onClick: () => (window.location.href = `/desk/patient-appointment/${row.name}`) })
	return actions
}

function openNew(patient = null) {
	initialPatient.value = patient
	showNew.value = true
}
function onBooked() {
	appointments.reload()
	router.replace({ query: {} })
}
function newPatient() {
	showNew.value = false
	showNewPatient.value = true
}
function onPatientCreated(p) {
	openNew({ label: p.patient_name, value: p.name, description: p.name })
}

watch(
	() => route.query,
	(q) => {
		if (q.new && canBook.value) {
			openNew(q.patient ? { label: q.patient_name || q.patient, value: q.patient, description: q.patient } : null)
		}
	},
	{ immediate: true },
)
</script>
