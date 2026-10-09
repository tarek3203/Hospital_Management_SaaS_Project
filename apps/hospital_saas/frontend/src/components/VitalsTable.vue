<template>
	<DataTable :columns="columns" :rows="rows" empty-text="No vitals recorded">
		<template #cell-signs_date="{ row }">{{ row.signs_date }} {{ row.signs_time || "" }}</template>
		<template #cell-bp="{ row }">{{ row.bp_systolic ? `${row.bp_systolic}/${row.bp_diastolic}` : "-" }}</template>
		<template #cell-temperature="{ row }">{{ row.temperature ? `${row.temperature} F` : "-" }}</template>
	</DataTable>
</template>

<script setup>
import DataTable from "@/components/DataTable.vue"

defineProps({ rows: Array })
const columns = [
	{ key: "signs_date", label: "Date" },
	{ key: "bp", label: "BP (mmHg)" },
	{ key: "pulse", label: "Pulse" },
	{ key: "temperature", label: "Temperature" },
	{ key: "respiratory_rate", label: "Resp. rate" },
	{ key: "height", label: "Height (m)" },
	{ key: "weight", label: "Weight (kg)" },
	{ key: "bmi", label: "BMI" },
]
</script>
