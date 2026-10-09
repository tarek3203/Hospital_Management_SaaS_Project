<template>
	<div class="rounded-lg border bg-white p-4">
		<p class="mb-2 text-sm font-semibold text-gray-900">{{ chart.title }}</p>
		<div v-if="!chart.data?.length" class="flex h-64 items-center justify-center text-sm text-gray-500">
			No data yet
		</div>
		<div v-else class="h-64">
			<DonutChart v-if="chart.type === 'donut'" :config="donutConfig" />
			<AxisChart v-else :config="axisConfig" />
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue"
import { AxisChart, DonutChart } from "frappe-ui"

const props = defineProps({ chart: { type: Object, required: true } })
const COLORS = ["#0e7c6b", "#f59e0b", "#3b82f6", "#ef4444", "#8b5cf6", "#14b8a6", "#64748b", "#ec4899"]

const donutConfig = computed(() => ({
	data: props.chart.data,
	title: "",
	categoryColumn: "label",
	valueColumn: "value",
	colors: COLORS,
}))

const axisConfig = computed(() => ({
	data: props.chart.data,
	title: "",
	colors: COLORS,
	xAxis: { key: props.chart.x, type: "category" },
	yAxis: { title: "" },
	series: props.chart.y.map((name) => ({
		name,
		type: props.chart.type === "bar" ? "bar" : "line",
		showDataPoints: false,
	})),
}))
</script>
