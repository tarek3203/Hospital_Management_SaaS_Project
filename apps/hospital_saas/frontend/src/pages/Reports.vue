<template>
	<div class="mx-auto max-w-7xl p-4 sm:p-6">
		<h1 class="mb-4 text-xl font-semibold text-gray-900">Reports</h1>
		<div class="grid grid-cols-1 gap-4 lg:grid-cols-[230px_1fr]">
			<nav class="h-fit rounded-lg border bg-white p-2">
				<button
					v-for="r in catalogue.data || []"
					:key="r.key"
					class="flex w-full flex-col rounded-md px-3 py-2 text-left hover:bg-gray-50"
					:class="r.key === current ? 'bg-brand-50' : ''"
					@click="pick(r.key)"
				>
					<span class="text-[11px] uppercase tracking-wide text-gray-500">{{ r.group }}</span>
					<span class="text-sm font-medium" :class="r.key === current ? 'text-brand-700' : 'text-gray-900'">{{ r.title }}</span>
				</button>
			</nav>
			<div class="min-w-0 space-y-3">
				<div class="flex flex-wrap items-end gap-2 rounded-lg border bg-white p-3">
					<div class="flex-1">
						<p class="text-xs text-gray-500">{{ report.data?.group }}</p>
						<p class="font-semibold text-gray-900">{{ report.data?.title || "Pick a report" }}</p>
					</div>
					<label class="text-xs text-gray-600">From <input v-model="from" type="date" class="ml-1 h-8 rounded-md border-gray-300 text-sm" /></label>
					<label class="text-xs text-gray-600">To <input v-model="to" type="date" class="ml-1 h-8 rounded-md border-gray-300 text-sm" /></label>
					<Button :loading="report.loading" @click="run">Run</Button>
					<Button :disabled="!report.data?.rows.length" @click="exportCsv"><template #prefix><FeatherIcon name="download" class="h-4 w-4" /></template>CSV</Button>
					<Button :disabled="!report.data?.rows.length" @click="print()"><template #prefix><FeatherIcon name="printer" class="h-4 w-4" /></template>Print</Button>
				</div>
				<ErrorMessage :message="report.error" />
				<DataTable v-if="report.data" :columns="report.data.columns" :rows="report.data.rows" empty-text="No records in this period">
					<template #footer>
						<div class="border-t px-4 py-2 text-xs text-gray-500">{{ report.data.rows.length }} rows · {{ report.data.from_date }} to {{ report.data.to_date }}</div>
					</template>
				</DataTable>
				<p class="flex items-center gap-2 text-xs text-gray-500">Custom report builder and scheduled email reports <SoonBadge /> (available today in Desk's Report Builder)</p>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue"
import { Button, createResource, ErrorMessage, FeatherIcon } from "frappe-ui"
import DataTable from "@/components/DataTable.vue"
import SoonBadge from "@/components/SoonBadge.vue"
import { todayISO } from "@/utils"

const current = ref("")
const to = ref(todayISO())
const d = new Date()
d.setDate(d.getDate() - 29)
const from = ref(new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10))
const catalogue = createResource({ url: "hospital_saas.api.reports.get_catalogue", auto: true, onSuccess: (c) => c.length && pick(c[0].key) })
const report = createResource({ url: "hospital_saas.api.reports.run_report" })
function pick(key) {
	current.value = key
	run()
}
function run() {
	report.submit({ key: current.value, from_date: from.value, to_date: to.value })
}
function exportCsv() {
	const { columns, rows, title } = report.data
	const cell = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`
	const lines = [columns.map((c) => cell(c.label)).join(","), ...rows.map((r) => columns.map((c) => cell(r[c.key])).join(","))]
	const url = URL.createObjectURL(new Blob([lines.join("\n")], { type: "text/csv" }))
	const a = Object.assign(document.createElement("a"), { href: url, download: `${title} ${from.value} to ${to.value}.csv` })
	a.click()
	URL.revokeObjectURL(url)
}
const print = () => window.print()
</script>
