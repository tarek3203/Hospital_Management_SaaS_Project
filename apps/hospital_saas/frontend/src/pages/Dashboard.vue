<template>
	<div class="mx-auto max-w-7xl space-y-5 p-4 sm:p-6">
		<div>
			<h1 class="text-xl font-semibold text-gray-900">Good {{ greeting }}, {{ firstName }}</h1>
			<p class="text-sm text-gray-600">{{ session.data.job }} dashboard · {{ today }}</p>
		</div>

		<div v-if="dashboard.loading && !dashboard.data" class="flex justify-center py-20">
			<LoadingIndicator class="h-6 w-6 text-brand-600" />
		</div>
		<ErrorMessage v-else-if="dashboard.error" :message="dashboard.error" />

		<template v-else-if="dashboard.data">
			<div class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
				<StatCard v-for="card in dashboard.data.cards" :key="card.label" v-bind="card" />
			</div>
			<div v-if="dashboard.data.charts.length" class="grid grid-cols-1 gap-3 xl:grid-cols-2">
				<ChartCard v-for="chart in dashboard.data.charts" :key="chart.title" :chart="chart" />
			</div>
			<DataTable v-for="list in dashboard.data.lists" :key="list.title" v-bind="list" />
		</template>
	</div>
</template>

<script setup>
import { computed } from "vue"
import { createResource, ErrorMessage, LoadingIndicator } from "frappe-ui"
import StatCard from "@/components/StatCard.vue"
import ChartCard from "@/components/ChartCard.vue"
import DataTable from "@/components/DataTable.vue"
import { session } from "@/data/session"

const dashboard = createResource({ url: "hospital_saas.api.dashboard.get_dashboard", auto: true })

const firstName = computed(() => session.data.full_name.split(" ")[0])
const greeting = computed(() => {
	const h = new Date().getHours()
	return h < 12 ? "morning" : h < 17 ? "afternoon" : "evening"
})
const today = new Date().toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long", year: "numeric" })
</script>
