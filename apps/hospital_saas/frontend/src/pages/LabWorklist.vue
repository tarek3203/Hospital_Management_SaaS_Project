<template>
	<div class="mx-auto max-w-7xl space-y-4 p-4 sm:p-6">
		<div class="flex flex-wrap items-center gap-3">
			<div class="flex-1">
				<h1 class="text-xl font-semibold text-gray-900">{{ section }}</h1>
				<p class="text-sm text-gray-600">{{ section === "Radiology" ? "Imaging requests and reports" : "Lab tests, results and approvals" }}</p>
			</div>
			<Button v-if="canAdd" variant="solid" @click="showAdd = true">
				<template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
				New test
			</Button>
		</div>

		<div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
			<StatCard label="Today" :value="counts.Today" icon="calendar" />
			<StatCard label="Pending" :value="counts.Pending" icon="clock" />
			<StatCard label="Report ready" :value="counts['Report ready']" icon="file-text" hint="Waiting for approval" />
			<StatCard label="Approved" :value="counts.Approved" icon="check-circle" />
		</div>
		<p class="flex items-center gap-2 text-xs text-gray-500">
			Sample collection tracking <SoonBadge />
			<template v-if="section === 'Radiology'"> · Image upload and DICOM viewer <SoonBadge /></template>
		</p>

		<div class="flex flex-wrap items-center gap-2">
			<div class="max-w-sm flex-1">
				<TextInput v-model="search" type="search" placeholder="Search patient, test or ID" @update:modelValue="onSearch">
					<template #prefix><FeatherIcon name="search" class="h-4 w-4 text-gray-500" /></template>
				</TextInput>
			</div>
			<div class="ml-auto flex flex-wrap gap-1">
				<button
					v-for="s in ['', 'Pending', 'Report ready', 'Approved']"
					:key="s"
					class="rounded-full px-3 py-1 text-xs font-medium"
					:class="status === s ? 'bg-gray-900 text-white' : 'bg-white text-gray-700 ring-1 ring-gray-200 hover:bg-gray-100'"
					@click="setStatus(s)"
				>
					{{ s || "All" }}
				</button>
			</div>
		</div>

		<DataTable :columns="columns" :rows="list.data?.rows" clickable empty-text="No tests" @row-click="(r) => $router.push(`/lab/${encodeURIComponent(r.name)}`)">
			<template #cell-name="{ row }"><span class="font-mono text-xs">{{ row.name }}</span></template>
			<template #cell-patient_name="{ row }">
				<p class="font-medium text-gray-900">{{ row.patient_name }}</p>
				<p class="text-xs text-gray-500">{{ row.patient }}{{ row.inpatient_record ? " · IPD" : "" }}</p>
			</template>
			<template #cell-date="{ row }">{{ row.date }} {{ row.time || "" }}</template>
			<template #cell-display_status="{ row }">
				<Badge :label="row.display_status" :theme="{ Pending: 'orange', 'Report ready': 'blue', Approved: 'green' }[row.display_status] || 'gray'" variant="subtle" />
			</template>
		</DataTable>
		<AddTestDialog v-model="showAdd" :section="section" @saved="list.reload()" />
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { Badge, Button, createResource, debounce, FeatherIcon, TextInput } from "frappe-ui"
import AddTestDialog from "@/components/AddTestDialog.vue"
import DataTable from "@/components/DataTable.vue"
import SoonBadge from "@/components/SoonBadge.vue"
import StatCard from "@/components/StatCard.vue"
import { session } from "@/data/session"

const props = defineProps({ section: { type: String, default: "Pathology" } })
const status = ref("")
const search = ref("")
const showAdd = ref(false)
const canAdd = computed(() => ["Super Admin", "Admin", "Receptionist", "Pathologist", "Radiologist", "Doctor"].includes(session.data.job))
const columns = [
	{ key: "name", label: "Test No" },
	{ key: "patient_name", label: "Patient" },
	{ key: "lab_test_name", label: "Test" },
	{ key: "practitioner_name", label: "Referred by" },
	{ key: "date", label: "Date" },
	{ key: "display_status", label: "Status" },
]
const list = createResource({
	url: "hospital_saas.api.lab.get_worklist",
	makeParams: () => ({ section: props.section, status: status.value, search: search.value }),
	auto: true,
})
const counts = computed(() => list.data?.counts || {})
const onSearch = debounce(() => list.reload(), 300)
function setStatus(s) {
	status.value = s
	list.reload()
}
watch(() => props.section, () => {
	status.value = ""
	list.reload()
})
</script>
