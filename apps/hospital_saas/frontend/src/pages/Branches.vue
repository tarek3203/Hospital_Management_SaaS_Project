<template>
	<div class="mx-auto max-w-7xl space-y-4 p-4 sm:p-6">
		<div>
			<h1 class="text-xl font-semibold text-gray-900">{{ report ? "Branch report" : "Multi branch overview" }}</h1>
			<p class="text-sm text-gray-600">Key numbers for every branch of {{ session.data.hospital.company }}</p>
		</div>
		<div v-if="!report" class="grid grid-cols-1 gap-4 md:grid-cols-2">
			<div v-for="b in data.data || []" :key="b.branch" class="rounded-lg border bg-white p-4">
				<div class="mb-3 flex items-center gap-2">
					<FeatherIcon name="git-branch" class="h-4 w-4 text-brand-600" />
					<p class="font-semibold text-gray-900">{{ b.branch }}</p>
				</div>
				<div class="grid grid-cols-3 gap-3 text-center">
					<div v-for="m in metrics(b)" :key="m.label" class="rounded-md bg-gray-50 p-2">
						<p class="text-lg font-semibold tabular-nums text-gray-900">{{ m.value }}</p>
						<p class="text-[11px] text-gray-500">{{ m.label }}</p>
					</div>
				</div>
				<div class="mt-3">
					<p class="mb-1 flex justify-between text-xs text-gray-600"><span>Bed occupancy</span><span>{{ b.occupied }}/{{ b.beds }}</span></p>
					<div class="h-2 overflow-hidden rounded-full bg-gray-100"><div class="h-full rounded-full bg-brand-500" :style="{ width: `${b.beds ? (b.occupied / b.beds) * 100 : 0}%` }" /></div>
				</div>
			</div>
		</div>
		<DataTable v-else :columns="columns" :rows="data.data" empty-text="No branches" />
		<p class="flex items-center gap-2 text-xs text-gray-500">Branch-wise profit and loss and stock transfer between branches <SoonBadge /></p>
	</div>
</template>

<script setup>
import { computed } from "vue"
import { useRoute } from "vue-router"
import { createResource, FeatherIcon } from "frappe-ui"
import DataTable from "@/components/DataTable.vue"
import SoonBadge from "@/components/SoonBadge.vue"
import { session } from "@/data/session"
import { formatCurrency } from "@/utils"

const route = useRoute()
const report = computed(() => route.path.endsWith("/report"))
const data = createResource({ url: "hospital_saas.api.branches.get_overview", auto: true })
const metrics = (b) => [
	{ label: "Doctors", value: b.doctors },
	{ label: "Staff", value: b.staff },
	{ label: "Admitted", value: b.occupied },
	{ label: "Appointments today", value: b.appointments_today },
	{ label: "Appointments this month", value: b.appointments_month },
	{ label: "OPD income this month", value: formatCurrency(b.opd_income_month) },
]
const columns = [
	{ key: "branch", label: "Branch" },
	{ key: "doctors", label: "Doctors" },
	{ key: "staff", label: "Staff" },
	{ key: "beds", label: "Beds" },
	{ key: "occupied", label: "Occupied" },
	{ key: "appointments_today", label: "Appointments today" },
	{ key: "appointments_month", label: "This month" },
	{ key: "opd_income_month", label: "OPD income (month)", format: "currency" },
]
</script>
