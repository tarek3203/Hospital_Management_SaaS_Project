<template>
	<DataTable :title="title" :columns="columns" :rows="rows" clickable empty-text="No visits yet" @row-click="$emit('open', $event)">
		<template #cell-name="{ row }"><span class="font-mono text-xs">{{ row.name }}</span></template>
		<template #cell-appointment_date="{ row }">{{ row.appointment_date }} {{ row.appointment_time }}</template>
		<template #cell-practitioner_name="{ row }">
			<p>{{ row.practitioner_name }}</p>
			<p class="text-xs text-gray-500">{{ row.department }}</p>
		</template>
		<template #cell-symptoms="{ row }">
			<span class="whitespace-normal text-sm">{{ row.symptoms.join(", ") || "-" }}</span>
		</template>
	</DataTable>
</template>

<script setup>
import DataTable from "@/components/DataTable.vue"

defineProps({ title: String, rows: Array })
defineEmits(["open"])
const columns = [
	{ key: "name", label: "OPD No" },
	{ key: "appointment_date", label: "Date" },
	{ key: "practitioner_name", label: "Consultant" },
	{ key: "appointment_type", label: "Type" },
	{ key: "symptoms", label: "Symptoms" },
	{ key: "status", label: "Status", badge: true },
]
</script>
