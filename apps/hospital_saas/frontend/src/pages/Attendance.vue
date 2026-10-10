<template>
	<div class="mx-auto max-w-7xl space-y-4 p-4 sm:p-6">
		<div class="flex flex-wrap items-center gap-3">
			<div class="flex-1">
				<h1 class="text-xl font-semibold text-gray-900">{{ kiosk ? "QR code attendance" : "Attendance" }}</h1>
				<p class="text-sm text-gray-600">{{ data?.date }}</p>
			</div>
			<input v-model="date" type="date" class="h-8 rounded-md border-gray-300 text-sm" @change="att.reload()" />
		</div>

		<div v-if="kiosk" class="rounded-lg border bg-white p-5">
			<div class="flex flex-wrap items-center gap-4">
				<div class="flex h-14 w-14 items-center justify-center rounded-lg bg-brand-50 text-brand-600"><FeatherIcon name="maximize" class="h-7 w-7" /></div>
				<div class="min-w-0 flex-1">
					<p class="font-semibold text-gray-900">Scan a staff ID card</p>
					<p class="text-sm text-gray-600">Use a barcode/QR scanner: it types the staff ID and presses Enter. You can also type the ID.</p>
				</div>
				<p class="flex items-center gap-2 text-xs text-gray-500">Phone camera scanning <SoonBadge /></p>
			</div>
			<form class="mt-4 flex gap-2" @submit.prevent="scan">
				<input ref="scanInput" v-model="code" placeholder="HR-EMP-00001" class="h-10 flex-1 rounded-md border-gray-300 font-mono focus:border-brand-500 focus:ring-brand-500" autofocus />
				<Button type="submit" variant="solid" size="lg" :loading="checkin.loading">Check in / out</Button>
			</form>
			<div v-if="lastScan" class="mt-3 rounded-md px-3 py-2 text-sm" :class="lastScan.error ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-800'">
				{{ lastScan.error || `${lastScan.employee_name} checked ${lastScan.log_type === "IN" ? "in" : "out"} at ${lastScan.time}` }}
			</div>
		</div>

		<div class="grid grid-cols-2 gap-3 lg:grid-cols-5">
			<StatCard v-for="s in ['Present', 'Absent', 'On Leave', 'Half Day', 'Not marked']" :key="s" :label="s" :value="data?.counts[s] || 0" :icon="ICONS[s]" />
		</div>

		<DataTable :columns="columns" :rows="data?.rows" empty-text="No staff">
			<template #cell-employee_name="{ row }">
				<p class="font-medium text-gray-900">{{ row.employee_name }}</p>
				<p class="text-xs text-gray-500">{{ row.name }}</p>
			</template>
			<template #cell-status="{ row }">
				<Badge :label="row.status" :theme="{ Present: 'green', Absent: 'red', 'On Leave': 'orange', 'Half Day': 'orange' }[row.status] || 'gray'" variant="subtle" />
			</template>
			<template v-if="data?.can_mark && !kiosk" #actions="{ row }">
				<Dropdown :options="['Present', 'Absent', 'On Leave', 'Half Day'].map((s) => ({ label: `Mark ${s.toLowerCase()}`, onClick: () => mark.submit({ employee: row.name, status: s, date }) }))" placement="right">
					<Button size="sm" variant="ghost"><FeatherIcon name="more-horizontal" class="h-4 w-4" /></Button>
				</Dropdown>
			</template>
		</DataTable>
	</div>
</template>

<script setup>
import { computed, nextTick, ref } from "vue"
import { useRoute } from "vue-router"
import { Badge, Button, createResource, Dropdown, FeatherIcon, toast } from "frappe-ui"
import DataTable from "@/components/DataTable.vue"
import SoonBadge from "@/components/SoonBadge.vue"
import StatCard from "@/components/StatCard.vue"
import { todayISO } from "@/utils"

const route = useRoute()
const kiosk = computed(() => !!route.query.kiosk)
const date = ref(todayISO())
const code = ref("")
const scanInput = ref(null)
const lastScan = ref(null)
const ICONS = { Present: "user-check", Absent: "user-x", "On Leave": "sun", "Half Day": "clock", "Not marked": "help-circle" }
const columns = [
	{ key: "employee_name", label: "Staff" },
	{ key: "designation", label: "Designation" },
	{ key: "department", label: "Department" },
	{ key: "branch", label: "Branch" },
	{ key: "in", label: "In" },
	{ key: "out", label: "Out" },
	{ key: "status", label: "Status" },
]
const att = createResource({ url: "hospital_saas.api.hr.get_attendance", makeParams: () => ({ date: date.value }), auto: true })
const data = computed(() => att.data)
const checkin = createResource({
	url: "hospital_saas.api.hr.qr_checkin",
	onSuccess(r) {
		lastScan.value = r
		att.reload()
	},
	onError(e) {
		lastScan.value = { error: e.messages?.[0] || "Could not check in" }
	},
})
function scan() {
	if (!code.value.trim()) return
	checkin.submit({ code: code.value })
	code.value = ""
	nextTick(() => scanInput.value?.focus())
}
const mark = createResource({
	url: "hospital_saas.api.hr.mark_attendance",
	onSuccess(s) {
		toast.success(`Marked ${s}`)
		att.reload()
	},
})
</script>
