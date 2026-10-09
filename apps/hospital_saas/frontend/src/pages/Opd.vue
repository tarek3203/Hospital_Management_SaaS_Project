<template>
	<div class="mx-auto max-w-7xl space-y-4 p-4 sm:p-6">
		<div class="flex flex-wrap items-center gap-3">
			<div class="flex-1">
				<h1 class="text-xl font-semibold text-gray-900">OPD - Out Patient</h1>
				<p class="text-sm text-gray-600">{{ list.data?.total ?? "-" }} patients with OPD visits</p>
			</div>
			<Button v-if="canBook" variant="solid" @click="$router.push({ path: '/appointments', query: { new: 1 } })">
				<template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
				New OPD visit
			</Button>
		</div>
		<div class="max-w-sm">
			<TextInput v-model="search" type="search" placeholder="Search by name, ID or mobile" @update:modelValue="onSearch">
				<template #prefix><FeatherIcon name="search" class="h-4 w-4 text-gray-500" /></template>
			</TextInput>
		</div>
		<DataTable :columns="columns" :rows="list.data?.rows" clickable empty-text="No OPD patients found" @row-click="open">
			<template #cell-patient_name="{ row }">
				<p class="font-medium text-gray-900">{{ row.patient_name }}</p>
				<p class="text-xs text-gray-500">{{ row.name }}</p>
			</template>
			<template #cell-age="{ row }">{{ row.age ?? "-" }}</template>
			<template #cell-last_visit="{ row }">{{ String(row.last_visit).slice(0, 16) }}</template>
			<template #footer>
				<div class="flex items-center justify-between border-t px-4 py-2 text-sm text-gray-600">
					<span>Showing {{ start + 1 }}-{{ start + (list.data?.rows.length || 0) }}</span>
					<div class="flex gap-2">
						<Button size="sm" :disabled="start === 0" @click="page(-1)">Previous</Button>
						<Button size="sm" :disabled="start + pageLength >= (list.data?.total || 0)" @click="page(1)">Next</Button>
					</div>
				</div>
			</template>
		</DataTable>
	</div>
</template>

<script setup>
import { computed, ref } from "vue"
import { useRouter } from "vue-router"
import { Button, createResource, debounce, FeatherIcon, TextInput } from "frappe-ui"
import DataTable from "@/components/DataTable.vue"
import { session } from "@/data/session"

const router = useRouter()
const pageLength = 20
const start = ref(0)
const search = ref("")
const canBook = computed(() => ["Super Admin", "Admin", "Receptionist"].includes(session.data.job))

const columns = [
	{ key: "patient_name", label: "Patient" },
	{ key: "sex", label: "Gender" },
	{ key: "age", label: "Age" },
	{ key: "mobile", label: "Phone" },
	{ key: "consultant", label: "Consultant" },
	{ key: "last_visit", label: "Last visit" },
	{ key: "visits", label: "Total visits" },
]

const list = createResource({
	url: "hospital_saas.api.opd.get_opd_patients",
	makeParams: () => ({ search: search.value, start: start.value, page_length: pageLength }),
	auto: true,
})
const onSearch = debounce(() => {
	start.value = 0
	list.reload()
}, 300)
function page(dir) {
	start.value += dir * pageLength
	list.reload()
}
function open(row) {
	router.push(`/opd/patient/${encodeURIComponent(row.name)}`)
}
</script>
