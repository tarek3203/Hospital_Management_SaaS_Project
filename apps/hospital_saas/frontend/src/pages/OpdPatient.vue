<template>
	<div class="mx-auto max-w-7xl space-y-4 p-4 sm:p-6">
		<nav class="text-xs text-gray-500">
			<router-link to="/opd" class="hover:text-gray-800">OPD</router-link>
			<span class="mx-1">/</span>
			<span>{{ profile.data?.patient.patient_name || patient }}</span>
		</nav>

		<div v-if="profile.loading && !profile.data" class="flex justify-center py-20"><LoadingIndicator class="h-6 w-6 text-brand-600" /></div>
		<ErrorMessage v-else-if="profile.error" :message="profile.error" />

		<template v-else-if="profile.data">
			<div class="rounded-lg border bg-white p-4 sm:p-5">
				<PatientHeader :patient="p" :extra="[`${p.visits} visits`]">
					<template #actions>
						<Button v-if="canBook" variant="solid" @click="newVisit">
							<template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
							New visit
						</Button>
					</template>
				</PatientHeader>
				<div class="mt-4"><TabBar v-model="tab" :tabs="tabs" /></div>
			</div>

			<!-- Overview -->
			<div v-if="tab === 'overview'" class="space-y-4">
				<InfoGrid title="Patient details" :items="details" />
				<div class="rounded-lg border bg-white p-4">
					<p class="mb-3 text-sm font-semibold text-gray-900">Medical history</p>
					<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
						<div v-for="(count, label) in profile.data.history" :key="label" class="flex items-center gap-3 rounded-lg border p-3">
							<div class="flex h-9 w-9 items-center justify-center rounded-lg" :class="HISTORY[label].bg">
								<FeatherIcon :name="HISTORY[label].icon" class="h-4 w-4" />
							</div>
							<div>
								<p class="text-lg font-semibold leading-tight text-gray-900">{{ count }}</p>
								<p class="flex items-center gap-1 text-xs text-gray-500">{{ label }} <SoonBadge v-if="SOON_HISTORY.includes(label)" /></p>
							</div>
						</div>
					</div>
				</div>
				<div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
					<div class="rounded-lg border bg-white p-4 lg:col-span-2">
						<p class="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900">
							<FeatherIcon name="alert-triangle" class="h-4 w-4 text-amber-500" />
							Known allergies, symptoms and diagnoses
						</p>
						<p class="text-xs font-medium uppercase tracking-wide text-gray-500">Known allergies</p>
						<div class="mb-3 mt-1 flex flex-wrap gap-1.5">
							<Badge v-for="a in allergies" :key="a" :label="a" theme="orange" variant="outline" />
							<span v-if="!allergies.length" class="text-sm text-gray-500">None recorded</span>
						</div>
						<p class="text-xs font-medium uppercase tracking-wide text-gray-500">Symptoms</p>
						<div class="mb-3 mt-1 flex flex-wrap gap-1.5">
							<Badge v-for="s in profile.data.symptoms" :key="s" :label="s" variant="subtle" />
							<span v-if="!profile.data.symptoms.length" class="text-sm text-gray-500">None recorded</span>
						</div>
						<p class="text-xs font-medium uppercase tracking-wide text-gray-500">Diagnoses</p>
						<div class="mt-1 flex flex-wrap gap-1.5">
							<Badge v-for="d in profile.data.diagnoses" :key="d" :label="d" theme="blue" variant="subtle" />
							<span v-if="!profile.data.diagnoses.length" class="text-sm text-gray-500">None recorded</span>
						</div>
					</div>
					<div class="rounded-lg border bg-white p-4">
						<p class="mb-3 text-sm font-semibold text-gray-900">Consultant doctors</p>
						<ul class="space-y-2">
							<li v-for="c in profile.data.consultants" :key="c.practitioner" class="flex items-center gap-2">
								<Avatar :label="c.practitioner_name" size="sm" />
								<span class="flex-1 text-sm text-gray-800">{{ c.practitioner_name }}</span>
								<span class="text-xs text-gray-500">{{ c.visits }} visits</span>
							</li>
						</ul>
					</div>
				</div>
				<VisitsTable title="Recent visits" :rows="profile.data.recent_visits" @open="openVisit" />
			</div>

			<VisitsTable v-else-if="tab === 'visits'" :rows="visits.data" @open="openVisit" />

			<DataTable v-else-if="tab === 'labs'" :columns="labColumns" :rows="labs.data" empty-text="No lab investigations">
				<template #cell-status="{ row }">
					<Badge :label="row.docstatus === 1 ? 'Completed' : row.status || 'Draft'" :theme="row.docstatus === 1 ? 'green' : 'orange'" variant="subtle" />
				</template>
			</DataTable>

			<DataTable v-else-if="tab === 'treatment'" :columns="treatmentColumns" :rows="treated" clickable empty-text="No completed consultations" @row-click="openVisit">
				<template #cell-diagnoses="{ row }">{{ row.diagnoses.join(", ") || "-" }}</template>
				<template #cell-symptoms="{ row }">{{ row.symptoms.join(", ") || "-" }}</template>
			</DataTable>

			<Timeline v-else-if="tab === 'timeline'" :patient="patient" :entries="timeline.data" :can-add="canNote" @added="timeline.reload()" />

			<VitalsTable v-else-if="tab === 'vitals'" :rows="vitals.data" />
		</template>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { useRouter } from "vue-router"
import { Avatar, Badge, Button, createResource, ErrorMessage, FeatherIcon, LoadingIndicator } from "frappe-ui"
import DataTable from "@/components/DataTable.vue"
import InfoGrid from "@/components/InfoGrid.vue"
import PatientHeader from "@/components/PatientHeader.vue"
import SoonBadge from "@/components/SoonBadge.vue"
import TabBar from "@/components/TabBar.vue"
import Timeline from "@/components/Timeline.vue"
import VisitsTable from "@/components/VisitsTable.vue"
import VitalsTable from "@/components/VitalsTable.vue"
import { session } from "@/data/session"

const props = defineProps({ patient: { type: String, required: true } })
const router = useRouter()
const tab = ref("overview")
const canBook = computed(() => ["Super Admin", "Admin", "Receptionist"].includes(session.data.job))
const canNote = computed(() => ["Super Admin", "Admin", "Doctor", "Nurse", "Receptionist"].includes(session.data.job))

// Modules not built yet: their counts stay 0 until they land.
const SOON_HISTORY = ["Ambulance"]
const HISTORY = {
	Visits: { icon: "activity", bg: "bg-blue-50 text-blue-600" },
	IPD: { icon: "layers", bg: "bg-emerald-50 text-emerald-600" },
	Pharmacy: { icon: "package", bg: "bg-amber-50 text-amber-600" },
	Pathology: { icon: "droplet", bg: "bg-purple-50 text-purple-600" },
	Radiology: { icon: "aperture", bg: "bg-teal-50 text-teal-600" },
	Ambulance: { icon: "truck", bg: "bg-red-50 text-red-600" },
}

const params = () => ({ patient: props.patient })
const profile = createResource({ url: "hospital_saas.api.opd.get_patient_profile", makeParams: params, auto: true })
const visits = createResource({ url: "hospital_saas.api.opd.get_patient_visits", makeParams: params })
const labs = createResource({ url: "hospital_saas.api.opd.get_patient_labs", makeParams: params })
const vitals = createResource({ url: "hospital_saas.api.opd.get_patient_vitals", makeParams: params })
const timeline = createResource({ url: "hospital_saas.api.opd.get_patient_timeline", makeParams: params })

const loaders = { visits, treatment: visits, labs, vitals, timeline }
watch(tab, (t) => loaders[t] && !loaders[t].data && loaders[t].reload())
watch(() => props.patient, () => {
	tab.value = "overview"
	for (const r of [profile, visits, labs, vitals, timeline]) r.reset()
	profile.reload()
})

const p = computed(() => profile.data.patient)
const allergies = computed(() => (p.value.allergies || "").split(",").map((a) => a.trim()).filter(Boolean))
const details = computed(() => [
	{ label: "Patient", value: `${p.value.patient_name} (${p.value.name})` },
	{ label: "Gender", value: p.value.sex },
	{ label: "Age", value: p.value.age != null ? `${p.value.age} years` : null },
	{ label: "Phone", value: p.value.mobile },
	{ label: "Blood group", value: p.value.blood_group },
	{ label: "Marital status", value: p.value.marital_status },
	{ label: "Occupation", value: p.value.occupation },
	{ label: "Address", value: p.value.address },
])
const tabs = computed(() => [
	{ key: "overview", label: "Overview", icon: "grid" },
	{ key: "visits", label: "Visits", icon: "check-square", count: p.value.visits },
	{ key: "labs", label: "Lab Investigation", icon: "droplet" },
	{ key: "treatment", label: "Treatment History", icon: "clipboard" },
	{ key: "timeline", label: "Timeline", icon: "clock" },
	{ key: "vitals", label: "Vitals", icon: "heart" },
])
const treated = computed(() => (visits.data || []).filter((v) => v.consulted))

const labColumns = [
	{ key: "lab_test_name", label: "Test" },
	{ key: "date", label: "Date" },
	{ key: "practitioner_name", label: "Ordered by" },
	{ key: "result_date", label: "Result date" },
	{ key: "status", label: "Status" },
]
const treatmentColumns = [
	{ key: "name", label: "OPD No" },
	{ key: "appointment_date", label: "Date" },
	{ key: "symptoms", label: "Symptoms" },
	{ key: "diagnoses", label: "Diagnosis" },
	{ key: "practitioner_name", label: "Consultant" },
]

function openVisit(row) {
	router.push(`/opd/visit/${encodeURIComponent(row.name)}`)
}
function newVisit() {
	router.push({ path: "/appointments", query: { new: 1, patient: p.value.name, patient_name: p.value.patient_name } })
}
</script>
