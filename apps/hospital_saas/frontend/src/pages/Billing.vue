<template>
	<div class="mx-auto max-w-7xl space-y-4 p-4 sm:p-6">
		<div class="flex flex-wrap items-center gap-3">
			<div class="flex-1">
				<h1 class="text-xl font-semibold text-gray-900">Billing</h1>
				<p class="text-sm text-gray-600">All patient bills, collections and dues</p>
			</div>
			<Button v-if="canBill" variant="solid" @click="openNew('OPD')">
				<template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
				New bill
			</Button>
		</div>

		<div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
			<StatCard label="Collected today" :value="summary.data?.collected_today" format="currency" icon="dollar-sign" />
			<StatCard label="Billed today" :value="summary.data?.billed_today" format="currency" icon="file-text" :hint="`${summary.data?.bills_today ?? 0} bills`" />
			<StatCard label="Billed this month" :value="summary.data?.billed_month" format="currency" icon="trending-up" />
			<StatCard label="Outstanding dues" :value="summary.data?.outstanding" format="currency" icon="alert-circle" />
		</div>

		<div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
			<div class="rounded-lg border bg-white p-4 lg:col-span-2">
				<p class="mb-3 text-sm font-semibold text-gray-900">Single module billing</p>
				<div class="grid grid-cols-2 gap-2 sm:grid-cols-4">
					<button
						v-for="m in modules"
						:key="m.key"
						class="flex flex-col items-start gap-2 rounded-lg border p-3 text-left transition-colors hover:border-brand-500"
						:class="module === m.key ? 'border-brand-600 bg-brand-50' : 'bg-white'"
						@click="pickModule(m)"
					>
						<FeatherIcon :name="m.icon" class="h-5 w-5 text-brand-600" />
						<span class="flex items-center gap-1.5 text-sm font-medium text-gray-900">{{ m.label }} <SoonBadge v-if="m.soon" /></span>
					</button>
				</div>
			</div>
			<div class="rounded-lg border bg-white p-4">
				<p class="mb-1 text-sm font-semibold text-gray-900">OPD / IPD billing by number</p>
				<p class="mb-3 text-xs text-gray-500">Open a visit or admission to see its charges and take payment</p>
				<form class="flex gap-2" @submit.prevent="findCase.submit({ number: caseNo })">
					<TextInput v-model="caseNo" placeholder="HLC-APP-... or HLC-INP-..." class="flex-1" />
					<Button type="submit" :loading="findCase.loading">Search</Button>
				</form>
				<ErrorMessage class="mt-2" :message="findCase.error" />
			</div>
		</div>

		<div class="flex flex-wrap items-center gap-2">
			<div class="max-w-sm flex-1">
				<TextInput v-model="search" type="search" placeholder="Search bill no, patient name or ID" @update:modelValue="onSearch">
					<template #prefix><FeatherIcon name="search" class="h-4 w-4 text-gray-500" /></template>
				</TextInput>
			</div>
			<div class="ml-auto flex flex-wrap gap-1">
				<button
					v-for="s in ['', 'Unpaid', 'Paid']"
					:key="s"
					class="rounded-full px-3 py-1 text-xs font-medium"
					:class="status === s ? 'bg-gray-900 text-white' : 'bg-white text-gray-700 ring-1 ring-gray-200 hover:bg-gray-100'"
					@click="setStatus(s)"
				>
					{{ s || "All" }}
				</button>
				<button v-if="module" class="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700 ring-1 ring-brand-200" @click="pickModule({ key: '' })">
					{{ module }} ✕
				</button>
			</div>
		</div>

		<DataTable :columns="columns" :rows="bills.data" empty-text="No bills found">
			<template #cell-patient_name="{ row }">
				<p class="font-medium text-gray-900">{{ row.patient_name }}</p>
				<p class="text-xs text-gray-500">{{ row.patient }}</p>
			</template>
			<template #cell-modules="{ row }">
				<div class="flex flex-wrap gap-1"><Badge v-for="m in row.modules" :key="m" :label="m" variant="subtle" /></div>
			</template>
			<template #cell-outstanding_amount="{ row }">
				<span :class="row.outstanding_amount > 0 ? 'font-medium text-red-600' : 'text-green-700'">
					{{ row.outstanding_amount > 0 ? formatCurrency(row.outstanding_amount) : "Paid" }}
				</span>
			</template>
			<template #actions="{ row }">
				<div class="flex justify-end gap-1">
					<Button v-if="canCollect && row.outstanding_amount > 0" size="sm" @click="collect(row)">Collect</Button>
					<Button size="sm" variant="ghost" @click="$router.push(`/billing/${encodeURIComponent(row.name)}/receipt`)">
						<FeatherIcon name="printer" class="h-4 w-4" />
					</Button>
				</div>
			</template>
			<template #footer>
				<div class="flex items-center justify-between border-t px-4 py-2 text-sm text-gray-600">
					<span>Showing {{ start + 1 }}-{{ start + (bills.data?.length || 0) }}</span>
					<div class="flex gap-2">
						<Button size="sm" :disabled="start === 0" @click="page(-1)">Previous</Button>
						<Button size="sm" :disabled="(bills.data?.length || 0) < pageLength" @click="page(1)">Next</Button>
					</div>
				</div>
			</template>
		</DataTable>

		<NewBillDialog v-model="showNew" :module="newModule" @saved="refresh" />
		<PaymentDialog v-model="showPay" :invoice="payInvoice?.name" :due="payInvoice?.outstanding_amount" @saved="refresh" />
	</div>
</template>

<script setup>
import { computed, ref } from "vue"
import { useRouter } from "vue-router"
import { Badge, Button, createResource, debounce, ErrorMessage, FeatherIcon, TextInput, toast } from "frappe-ui"
import DataTable from "@/components/DataTable.vue"
import NewBillDialog from "@/components/NewBillDialog.vue"
import PaymentDialog from "@/components/PaymentDialog.vue"
import SoonBadge from "@/components/SoonBadge.vue"
import StatCard from "@/components/StatCard.vue"
import { session } from "@/data/session"
import { formatCurrency } from "@/utils"

const router = useRouter()
const pageLength = 25
const start = ref(0)
const search = ref("")
const status = ref("")
const module = ref("")
const caseNo = ref("")
const showNew = ref(false)
const newModule = ref("OPD")
const showPay = ref(false)
const payInvoice = ref(null)

const canBill = computed(() => ["Super Admin", "Admin", "Receptionist", "Accountant"].includes(session.data.job))
const canCollect = computed(() => ["Super Admin", "Admin", "Receptionist", "Accountant", "Pharmacist"].includes(session.data.job))

const modules = [
	{ key: "Appointment", label: "Appointment", icon: "calendar", route: "/appointments" },
	{ key: "OPD", label: "OPD", icon: "activity", bill: true },
	{ key: "IPD", label: "IPD", icon: "layers", route: "/ipd" },
	{ key: "Pathology", label: "Pathology", icon: "droplet", bill: true },
	{ key: "Radiology", label: "Radiology", icon: "aperture", bill: true },
	{ key: "Pharmacy", label: "Pharmacy", icon: "package", route: "/pharmacy" },
	{ key: "Blood Issue", label: "Blood Issue", icon: "heart", soon: true },
	{ key: "Blood Component", label: "Blood Component Issue", icon: "droplet", soon: true },
]

const summary = createResource({ url: "hospital_saas.api.billing.get_billing_summary", auto: true })
const bills = createResource({
	url: "hospital_saas.api.billing.get_bills",
	makeParams: () => ({ module: module.value, search: search.value, status: status.value, start: start.value, page_length: pageLength }),
	auto: true,
})
const columns = [
	{ key: "name", label: "Bill No" },
	{ key: "posting_date", label: "Date" },
	{ key: "patient_name", label: "Patient" },
	{ key: "modules", label: "Module" },
	{ key: "grand_total", label: "Amount", format: "currency" },
	{ key: "paid", label: "Paid", format: "currency" },
	{ key: "outstanding_amount", label: "Due" },
]

const onSearch = debounce(() => {
	start.value = 0
	bills.reload()
}, 300)
function setStatus(s) {
	status.value = s
	start.value = 0
	bills.reload()
}
function page(dir) {
	start.value += dir * pageLength
	bills.reload()
}
function pickModule(m) {
	if (m.soon) {
		toast.info(`${m.label} billing is coming soon`)
		return
	}
	if (m.route) {
		router.push(m.route)
		return
	}
	module.value = m.key
	start.value = 0
	bills.reload()
	if (m.bill && canBill.value) openNew(m.key)
}
function openNew(m) {
	newModule.value = m
	showNew.value = true
}
function collect(row) {
	payInvoice.value = row
	showPay.value = true
}
function refresh() {
	bills.reload()
	summary.reload()
}

const findCase = createResource({
	url: "hospital_saas.api.billing.find_case",
	onSuccess(r) {
		router.push(r.type === "opd" ? `/opd/visit/${encodeURIComponent(r.name)}` : `/ipd/${encodeURIComponent(r.name)}`)
	},
})
</script>
