<template>
	<div class="mx-auto max-w-7xl space-y-4 p-4 sm:p-6">
		<div class="flex flex-wrap items-center gap-3">
			<div class="flex-1">
				<h1 class="text-xl font-semibold text-gray-900">Pharmacy</h1>
				<p class="text-sm text-gray-600">Medicine bills, stock and purchase</p>
			</div>
			<Button v-if="canBill" variant="solid" @click="showBill = true">
				<template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
				New pharmacy bill
			</Button>
		</div>
		<div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
			<StatCard label="Sales today" :value="summary.data?.sales_today" format="currency" icon="shopping-bag" />
			<StatCard label="Sales this month" :value="summary.data?.sales_month" format="currency" icon="trending-up" />
			<StatCard label="Medicines" :value="summary.data?.medicines" icon="package" />
			<StatCard label="Below reorder level" :value="summary.data?.low_stock" icon="alert-triangle" />
		</div>
		<div class="rounded-lg border bg-white px-4"><TabBar v-model="tab" :tabs="tabs" /></div>

		<DataTable v-if="tab === 'bills'" :columns="billColumns" :rows="bills.data" empty-text="No pharmacy bills">
			<template #cell-patient_name="{ row }">
				<p class="font-medium text-gray-900">{{ row.patient_name }}</p>
				<p class="text-xs text-gray-500">{{ row.patient }}</p>
			</template>
			<template #cell-outstanding_amount="{ row }">
				<span :class="row.outstanding_amount > 0 ? 'font-medium text-red-600' : 'text-green-700'">{{ row.outstanding_amount > 0 ? formatCurrency(row.outstanding_amount) : "Paid" }}</span>
			</template>
			<template #actions="{ row }">
				<Button size="sm" variant="ghost" @click="$router.push(`/billing/${encodeURIComponent(row.name)}/receipt`)"><FeatherIcon name="printer" class="h-4 w-4" /></Button>
			</template>
		</DataTable>

		<div v-else-if="tab === 'stock'" class="space-y-3">
			<div class="flex flex-wrap gap-2">
				<FormControl v-model="store" type="select" :options="[{ label: 'All stores', value: '' }, ...(stores.data || [])]" class="w-56" @update:modelValue="meds.reload()" />
				<TextInput v-model="medSearch" type="search" placeholder="Search medicine" class="max-w-xs" @update:modelValue="onMedSearch" />
			</div>
			<DataTable :columns="medColumns" :rows="meds.data" empty-text="No medicines">
				<template #cell-stock="{ row }">
					<span :class="row.low ? 'font-semibold text-red-600' : ''">{{ Number(row.stock).toLocaleString("en-IN") }} {{ row.stock_uom }}</span>
					<Badge v-if="row.low" class="ml-2" label="Reorder" theme="red" variant="subtle" />
				</template>
			</DataTable>
		</div>

		<div v-else-if="tab === 'purchase'" class="space-y-3">
			<SoonPanel title="Purchase from /hms" description="Purchase orders, goods receipt and supplier bills are available today in the admin screens (Desk). A pharmacy purchase screen here is coming soon." />
			<div class="text-center"><Button @click="goDesk('/desk/purchase-order')">Open purchase orders in Desk</Button></div>
		</div>

		<PharmacyBillDialog v-model="showBill" @saved="refresh" />
	</div>
</template>

<script setup>
import { computed, ref } from "vue"
import { Badge, Button, createResource, debounce, FeatherIcon, FormControl, TextInput } from "frappe-ui"
import DataTable from "@/components/DataTable.vue"
import PharmacyBillDialog from "@/components/PharmacyBillDialog.vue"
import SoonPanel from "@/components/SoonPanel.vue"
import StatCard from "@/components/StatCard.vue"
import TabBar from "@/components/TabBar.vue"
import { session } from "@/data/session"
import { formatCurrency } from "@/utils"

const tab = ref("bills")
const showBill = ref(false)
const store = ref("")
const medSearch = ref("")
const canBill = computed(() => ["Super Admin", "Admin", "Pharmacist", "Receptionist"].includes(session.data.job))
const tabs = [
	{ key: "bills", label: "Pharmacy bills", icon: "file-text" },
	{ key: "stock", label: "Medicine stock", icon: "package" },
	{ key: "purchase", label: "Purchase", icon: "shopping-cart", soon: true },
]
const summary = createResource({ url: "hospital_saas.api.pharmacy.get_pharmacy_summary", auto: true })
const bills = createResource({ url: "hospital_saas.api.billing.get_bills", params: { module: "Pharmacy", page_length: 50 }, auto: true })
const stores = createResource({ url: "hospital_saas.api.pharmacy.get_stores", auto: true })
const meds = createResource({ url: "hospital_saas.api.pharmacy.get_medicines", makeParams: () => ({ warehouse: store.value || null, search: medSearch.value }), auto: true })
const onMedSearch = debounce(() => meds.reload(), 300)
const billColumns = [
	{ key: "name", label: "Bill No" },
	{ key: "posting_date", label: "Date" },
	{ key: "patient_name", label: "Patient" },
	{ key: "grand_total", label: "Amount", format: "currency" },
	{ key: "paid", label: "Paid", format: "currency" },
	{ key: "outstanding_amount", label: "Due" },
]
const medColumns = [
	{ key: "item_name", label: "Medicine" },
	{ key: "item_code", label: "Code" },
	{ key: "rate", label: "Price", format: "currency" },
	{ key: "stock", label: "In stock" },
	{ key: "reorder_level", label: "Reorder at" },
]
function refresh() {
	bills.reload()
	summary.reload()
	meds.reload()
}
const goDesk = (path) => (window.location.href = path)
</script>
