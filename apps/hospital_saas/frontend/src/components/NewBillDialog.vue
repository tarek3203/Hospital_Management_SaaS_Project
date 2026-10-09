<template>
	<Dialog v-model="show" :options="{ title: `New ${module} bill`, size: '3xl' }">
		<template #body-content>
			<div class="space-y-4">
				<Autocomplete v-model="patient" label="Patient" placeholder="Search by name, ID or mobile" :options="patientOptions" @update:query="onQuery" />
				<div>
					<div class="mb-1.5 flex items-center justify-between">
						<p class="text-xs text-gray-600">Charges</p>
						<Button size="sm" variant="ghost" @click="addLine">
							<template #prefix><FeatherIcon name="plus" class="h-3.5 w-3.5" /></template>
							Add charge
						</Button>
					</div>
					<div class="overflow-x-auto rounded-md border">
						<table class="w-full text-sm">
							<thead class="bg-gray-50 text-left text-xs text-gray-500">
								<tr><th class="px-2 py-1.5 font-medium">Charge</th><th class="w-20 px-2 py-1.5 font-medium">Qty</th><th class="w-32 px-2 py-1.5 font-medium">Rate (Tk)</th><th class="w-32 px-2 py-1.5 text-right font-medium">Amount</th><th /></tr>
							</thead>
							<tbody>
								<tr v-for="(line, i) in lines" :key="i" class="border-t">
									<td class="p-1.5">
										<select v-model="line.item_code" class="cell" @change="setRate(line)">
											<option value="">Select</option>
											<option v-for="it in items.data || []" :key="it.item_code" :value="it.item_code">{{ it.item_name }}</option>
										</select>
									</td>
									<td class="p-1.5"><input v-model.number="line.qty" type="number" min="1" class="cell" /></td>
									<td class="p-1.5"><input v-model.number="line.rate" type="number" min="0" class="cell" /></td>
									<td class="p-1.5 text-right tabular-nums">{{ formatCurrency(line.qty * line.rate) }}</td>
									<td class="p-1.5 text-right">
										<button class="rounded p-1 text-gray-400 hover:text-red-600" @click="lines.splice(i, 1)"><FeatherIcon name="trash-2" class="h-4 w-4" /></button>
									</td>
								</tr>
							</tbody>
						</table>
					</div>
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
import { formatCurrency } from "@/utils"

const show = defineModel({ type: Boolean })
const props = defineProps({ module: { type: String, default: "OPD" } })
const emit = defineEmits(["saved"])
const router = useRouter()

const patient = ref(null)
const lines = ref([])
const discount = ref(0)
const mode = ref("Cash")
const paid = ref(0)

const items = createResource({ url: "hospital_saas.api.billing.get_billable_items", makeParams: () => ({ module: props.module }) })
const search = createResource({ url: "hospital_saas.api.patients.search_patients" })
const onQuery = debounce((txt) => search.submit({ txt }), 250)
const patientOptions = computed(() => {
	const found = (search.data || []).map((p) => ({ label: p.patient_name, value: p.name, description: [p.name, p.mobile].filter(Boolean).join(" · ") }))
	if (patient.value && !found.some((o) => o.value === patient.value.value)) found.unshift(patient.value)
	return found
})

const total = computed(() => lines.value.reduce((s, l) => s + (Number(l.qty) || 0) * (Number(l.rate) || 0), 0))
const net = computed(() => Math.max(total.value - (Number(discount.value) || 0), 0))
const valid = computed(() => patient.value?.value && lines.value.some((l) => l.item_code))
watch(net, (n) => (paid.value = n))

function addLine() {
	lines.value.push({ item_code: "", qty: 1, rate: 0 })
}
function setRate(line) {
	const it = (items.data || []).find((i) => i.item_code === line.item_code)
	if (it) line.rate = it.rate
}
watch(show, (open) => {
	if (!open) return
	items.reload()
	patient.value = null
	lines.value = [{ item_code: "", qty: 1, rate: 0 }]
	discount.value = 0
	mode.value = "Cash"
	save.reset()
})

const save = createResource({
	url: "hospital_saas.api.billing.create_bill",
	onSuccess(invoice) {
		toast.success(`Bill ${invoice} created`)
		show.value = false
		emit("saved")
		router.push(`/billing/${encodeURIComponent(invoice)}/receipt`)
	},
})
function submit() {
	save.submit({
		patient: patient.value.value,
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
