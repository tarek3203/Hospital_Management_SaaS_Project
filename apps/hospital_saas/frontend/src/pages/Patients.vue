<template>
	<div class="mx-auto max-w-7xl space-y-4 p-4 sm:p-6">
		<div class="flex flex-wrap items-center gap-3">
			<div class="flex-1">
				<h1 class="text-xl font-semibold text-gray-900">Patients</h1>
				<p class="text-sm text-gray-600">{{ patients.data?.total ?? "-" }} registered</p>
			</div>
			<Button v-if="canRegister" variant="solid" @click="showNew = true">
				<template #prefix><FeatherIcon name="user-plus" class="h-4 w-4" /></template>
				New patient
			</Button>
		</div>

		<div class="max-w-sm">
			<TextInput v-model="search" type="search" placeholder="Search by name, ID or mobile" @update:modelValue="onSearch">
				<template #prefix><FeatherIcon name="search" class="h-4 w-4 text-gray-500" /></template>
			</TextInput>
		</div>

		<DataTable :columns="columns" :rows="patients.data?.rows" empty-text="No patients found">
			<template #cell-patient_name="{ row }">
				<div>
					<p class="font-medium text-gray-900">{{ row.patient_name }}</p>
					<p class="text-xs text-gray-500">{{ row.name }}</p>
				</div>
			</template>
			<template #cell-age="{ row }">{{ row.age ?? "-" }}{{ row.age !== null ? " y" : "" }}</template>
			<template #cell-inpatient_status="{ row }">
				<Badge v-if="row.inpatient_status" :label="row.inpatient_status" :theme="STATUS_THEMES[row.inpatient_status] || 'gray'" variant="subtle" />
				<span v-else class="text-gray-400">OPD</span>
			</template>
			<template v-if="canBook" #actions="{ row }">
				<Button size="sm" @click="book(row)">Book</Button>
			</template>
			<template #footer>
				<div class="flex items-center justify-between border-t px-4 py-2 text-sm text-gray-600">
					<span>Showing {{ start + 1 }}-{{ start + (patients.data?.rows.length || 0) }}</span>
					<div class="flex gap-2">
						<Button size="sm" :disabled="start === 0" @click="page(-1)">Previous</Button>
						<Button size="sm" :disabled="start + pageLength >= (patients.data?.total || 0)" @click="page(1)">Next</Button>
					</div>
				</div>
			</template>
		</DataTable>

		<NewPatientDialog v-model="showNew" @created="onCreated" />
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { Badge, Button, createResource, debounce, FeatherIcon, TextInput } from "frappe-ui"
import DataTable from "@/components/DataTable.vue"
import NewPatientDialog from "@/components/NewPatientDialog.vue"
import { session } from "@/data/session"
import { STATUS_THEMES } from "@/utils"

const route = useRoute()
const router = useRouter()
const pageLength = 20
const start = ref(0)
const search = ref(route.query.q || "")
const showNew = ref(false)

const canRegister = computed(() => ["Super Admin", "Admin", "Receptionist"].includes(session.data.job))
const canBook = computed(() => session.data.menu.some((m) => m.key === "appointments"))

const columns = [
	{ key: "patient_name", label: "Patient" },
	{ key: "sex", label: "Gender" },
	{ key: "age", label: "Age" },
	{ key: "mobile", label: "Mobile" },
	{ key: "blood_group", label: "Blood group" },
	{ key: "inpatient_status", label: "Status" },
]

const patients = createResource({
	url: "hospital_saas.api.patients.get_patients",
	makeParams: () => ({ search: search.value, start: start.value, page_length: pageLength }),
	auto: true,
})

const onSearch = debounce(() => {
	start.value = 0
	patients.reload()
}, 300)

function page(dir) {
	start.value += dir * pageLength
	patients.reload()
}

function book(row) {
	router.push({ path: "/appointments", query: { new: 1, patient: row.name, patient_name: row.patient_name } })
}

function onCreated(patient) {
	search.value = ""
	start.value = 0
	patients.reload()
	if (canBook.value) book(patient)
}

watch(
	() => route.query,
	(q) => {
		if (q.new && canRegister.value) showNew.value = true
		if (q.q !== undefined && q.q !== search.value) {
			search.value = q.q
			onSearch()
		}
	},
	{ immediate: true },
)
</script>
