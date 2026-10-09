<template>
	<div class="mx-auto max-w-7xl space-y-4 p-4 sm:p-6">
		<div class="flex flex-wrap items-center gap-3">
			<div class="flex-1">
				<h1 class="text-xl font-semibold text-gray-900">IPD - In Patient</h1>
				<p class="text-sm text-gray-600">{{ list.data?.length ?? "-" }} {{ status === "Admitted" ? "admitted now" : "discharged" }}</p>
			</div>
			<Button @click="$router.push('/beds')">
				<template #prefix><FeatherIcon name="grid" class="h-4 w-4" /></template>
				Bed status
			</Button>
			<Button v-if="canAdmit" variant="solid" @click="showAdmit = true">
				<template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
				Admit patient
			</Button>
		</div>
		<div class="flex flex-wrap items-center gap-2">
			<div class="max-w-sm flex-1">
				<TextInput v-model="search" type="search" placeholder="Search by name, patient ID or IPD No" @update:modelValue="onSearch">
					<template #prefix><FeatherIcon name="search" class="h-4 w-4 text-gray-500" /></template>
				</TextInput>
			</div>
			<div class="ml-auto flex gap-1">
				<button
					v-for="s in ['Admitted', 'Discharged']"
					:key="s"
					class="rounded-full px-3 py-1 text-xs font-medium"
					:class="status === s ? 'bg-gray-900 text-white' : 'bg-white text-gray-700 ring-1 ring-gray-200 hover:bg-gray-100'"
					@click="setStatus(s)"
				>
					{{ s }}
				</button>
			</div>
		</div>
		<DataTable :columns="columns" :rows="list.data" clickable empty-text="No patients" @row-click="(r) => $router.push(`/ipd/${encodeURIComponent(r.name)}`)">
			<template #cell-name="{ row }"><span class="font-mono text-xs">{{ row.name }}</span></template>
			<template #cell-patient_name="{ row }">
				<p class="font-medium text-gray-900">{{ row.patient_name }}</p>
				<p class="text-xs text-gray-500">{{ row.patient }}</p>
			</template>
			<template #cell-consultant="{ row }">
				<p>{{ row.consultant }}</p>
				<p class="text-xs text-gray-500">{{ row.medical_department }}</p>
			</template>
			<template #cell-admitted_datetime="{ row }">{{ String(row.admitted_datetime || "").slice(0, 16) }}</template>
			<template #cell-los="{ row }">{{ row.los }} d</template>
		</DataTable>
		<AdmitDialog v-model="showAdmit" />
	</div>
</template>

<script setup>
import { computed, ref } from "vue"
import { Button, createResource, debounce, FeatherIcon, TextInput } from "frappe-ui"
import AdmitDialog from "@/components/AdmitDialog.vue"
import DataTable from "@/components/DataTable.vue"
import { session } from "@/data/session"

const status = ref("Admitted")
const search = ref("")
const showAdmit = ref(false)
const canAdmit = computed(() => ["Super Admin", "Admin", "Receptionist", "Doctor", "Nurse"].includes(session.data.job))
const columns = [
	{ key: "name", label: "IPD No" },
	{ key: "patient_name", label: "Patient" },
	{ key: "gender", label: "Gender" },
	{ key: "mobile", label: "Phone" },
	{ key: "consultant", label: "Consultant" },
	{ key: "bed", label: "Bed" },
	{ key: "admitted_datetime", label: "Admitted" },
	{ key: "los", label: "Stay" },
	{ key: "status", label: "Status", badge: true },
]
const list = createResource({
	url: "hospital_saas.api.ipd.get_ipd_patients",
	makeParams: () => ({ status: status.value, search: search.value }),
	auto: true,
})
const onSearch = debounce(() => list.reload(), 300)
function setStatus(s) {
	status.value = s
	list.reload()
}
</script>
