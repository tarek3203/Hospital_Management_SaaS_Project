<template>
	<Dialog v-model="show" :options="{ title: 'New pharmacy bill', size: '4xl' }">
		<template #body-content>
			<div class="space-y-4">
				<div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
					<div class="sm:col-span-2">
						<Autocomplete v-model="patient" label="Patient" placeholder="Search by name, ID or mobile" :options="patientOptions" @update:query="onQuery" />
					</div>
					<FormControl v-model="store" type="select" label="Store" :options="stores.data || []" />
				</div>
				<div v-if="patient" class="flex flex-wrap items-center gap-2 rounded-md bg-gray-50 px-3 py-2 text-sm">
					<template v-if="rx.data">
						<span class="text-gray-700">Latest prescription: {{ rx.data.encounter.encounter_date }}, Dr. {{ rx.data.encounter.practitioner_name }} ({{ rx.data.items.length }} medicines)</span>
						<Button size="sm" class="ml-auto" @click="loadRx">Add to bill</Button>
					</template>
					<span v-else-if="rx.loading" class="text-gray-500">Looking for a prescription...</span>
					<span v-else class="text-gray-500">No prescription on record</span>
				</div>
				<div>
					<div class="mb-1.5 flex items-center justify-between">
						<p class="text-xs text-gray-600">Medicines</p>
						<Button size="sm" variant="ghost" @click="add()"><template #prefix><FeatherIcon name="plus" class="h-3.5 w-3.5" /></template>Add medicine</Button>
					</div>
					<div class="overflow-x-auto rounded-md border">
						<table class="w-full text-sm">
							<thead class="bg-gray-50 text-left text-xs text-gray-500">
								<tr><th class="px-2 py-1.5 font-medium">Medicine</th><th class="w-24 px-2 py-1.5 font-medium">In stock</th><th class="w-20 px-2 py-1.5 font-medium">Qty</th><th class="w-28 px-2 py-1.5 font-medium">Rate</th><th class="w-28 px-2 py-1.5 text-right font-medium">Amount</th><th /></tr>
							</thead>
							<tbody>
								<tr v-for="(l, i) in lines" :key="i" class="border-t">
									<td class="p-1.5">
										<select v-model="l.item_code" class="cell" @change="setRate(l)">
											<option value="">Select</option>
											<option v-for="m in meds.data || []" :key="m.item_code" :value="m.item_code">{{ m.item_name }}</option>
										</select>
										<p v-if="l.note" class="mt-0.5 text-xs text-gray-500">{{ l.note }}</p>
									</td>
									<td class="p-1.5 tabular-nums" :class="stockOf(l) < l.qty ? 'text-red-600' : 'text-gray-600'">{{ stockOf(l) }}</td>
									<td class="p-1.5"><input v-model.number="l.qty" type="number" min="1" class="cell" /></td>
									<td class="p-1.5"><input v-model.number="l.rate" type="number" min="0" step="0.01" class="cell" /></td>
									<td class="p-1.5 text-right tabular-nums">{{ formatCurrency(l.qty * l.rate) }}</td>
									<td class="p-1.5 text-right"><button class="rounded p-1 text-gray-400 hover:text-red-600" @click="lines.splice(i, 1)"><FeatherIcon name="trash-2" class="h-4 w-4" /></button></td>
								</tr>
							</tbody>
						</table>
					</div>
					<p class="mt-1 flex items-center gap-2 text-xs text-gray-500">Batch and expiry selection <SoonBadge /></p>
				</div>
				<div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
					<FormControl v-model="discount" type="number" label="Discount (Tk)" />
					<div><p class="mb-1.5 text-xs text-gray-600">Net amount</p><p class="text-lg font-semibold tabular-nums">{{ formatCurrency(net) }}</p></div>
					<FormControl v-model="mode" type="select" label="Payment" :options="[{ label: 'Not paid yet', value: '' }, 'Cash', 'bKash', 'Nagad', 'Card']" />
					<FormControl v-if="mode" v-model="paid" type="number" label="Paid now (Tk)" />
				</div>
				<ErrorMessage :message="save.error" />
			</div>
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button @click="show = false">Cancel</Button>
				<Button variant="solid" :loading="save.loading" :disabled="!valid" @click="submit">Create bill</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { useRouter } from "vue-router"
import { Autocomplete, Button, createResource, debounce, Dialog, ErrorMessage, FeatherIcon, FormControl, toast } from "frappe-ui"
import SoonBadge from "@/components/SoonBadge.vue"
import { formatCurrency } from "@/utils"

const show = defineModel({ type: Boolean })
const emit = defineEmits(["saved"])
const router = useRouter()
const patient = ref(null)
const store = ref("")
const lines = ref([])
const discount = ref(0)
const mode = ref("Cash")
const paid = ref(0)

const stores = createResource({ url: "hospital_saas.api.pharmacy.get_stores", onSuccess: (s) => !store.value && (store.value = s[0]) })
const meds = createResource({ url: "hospital_saas.api.pharmacy.get_medicines", makeParams: () => ({ warehouse: store.value }) })
const rx = createResource({ url: "hospital_saas.api.pharmacy.get_prescription" })
const search = createResource({ url: "hospital_saas.api.patients.search_patients" })
const onQuery = debounce((txt) => search.submit({ txt }), 250)
const patientOptions = computed(() => {
	const found = (search.data || []).map((p) => ({ label: p.patient_name, value: p.name, description: [p.name, p.mobile].filter(Boolean).join(" · ") }))
	if (patient.value && !found.some((o) => o.value === patient.value.value)) found.unshift(patient.value)
	return found
})
watch(patient, (p) => p?.value && rx.submit({ patient: p.value }))
watch(store, () => store.value && meds.reload())

const net = computed(() => Math.max(lines.value.reduce((s, l) => s + (Number(l.qty) || 0) * (Number(l.rate) || 0), 0) - (Number(discount.value) || 0), 0))
watch(net, (n) => (paid.value = Math.round(n * 100) / 100))
const valid = computed(() => patient.value?.value && store.value && lines.value.some((l) => l.item_code))
const stockOf = (l) => (meds.data || []).find((m) => m.item_code === l.item_code)?.stock ?? "-"

function add(line = { item_code: "", qty: 1, rate: 0 }) {
	lines.value.push(line)
}
function setRate(l) {
	const m = (meds.data || []).find((x) => x.item_code === l.item_code)
	if (m) l.rate = m.rate
}
function loadRx() {
	lines.value = lines.value.filter((l) => l.item_code)
	for (const it of rx.data.items) add({ ...it })
}
watch(show, (open) => {
	if (!open) return
	stores.fetch()
	if (store.value) meds.reload()
	patient.value = null
	rx.reset()
	lines.value = [{ item_code: "", qty: 1, rate: 0 }]
	discount.value = 0
	mode.value = "Cash"
	save.reset()
})

const save = createResource({
	url: "hospital_saas.api.pharmacy.create_pharmacy_bill",
	onSuccess(invoice) {
		toast.success(`Pharmacy bill ${invoice} created`)
		show.value = false
		emit("saved")
		router.push(`/billing/${encodeURIComponent(invoice)}/receipt`)
	},
})
function submit() {
	save.submit({
		patient: patient.value.value,
		warehouse: store.value,
		items: lines.value.filter((l) => l.item_code),
		discount: discount.value,
		mode_of_payment: mode.value || null,
		paid_amount: mode.value ? paid.value : null,
	})
}
</script>

<style scoped>
.cell {
	@apply h-8 w-full rounded border-gray-200 bg-white px-2 text-sm focus:border-brand-500 focus:ring-brand-500;
}
</style>
