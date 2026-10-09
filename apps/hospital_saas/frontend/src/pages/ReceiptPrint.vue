<template>
	<div class="min-h-screen bg-gray-100 py-6 print:bg-white print:py-0">
		<div class="mx-auto mb-4 flex max-w-[148mm] items-center justify-between px-2 print:hidden">
			<Button @click="$router.back()"><template #prefix><FeatherIcon name="arrow-left" class="h-4 w-4" /></template>Back</Button>
			<Button variant="solid" :disabled="!r" @click="print()"><template #prefix><FeatherIcon name="printer" class="h-4 w-4" /></template>Print</Button>
		</div>
		<div v-if="!r" class="py-20 text-center"><LoadingIndicator class="mx-auto h-6 w-6" /></div>
		<article v-else class="mx-auto max-w-[148mm] bg-white px-8 py-6 text-[12px] text-gray-900 shadow print:shadow-none">
			<header class="flex items-start justify-between border-b-2 border-brand-600 pb-3">
				<div class="flex items-center gap-2">
					<img :src="hospital.logo" class="h-10 w-10" alt="" />
					<div>
						<p class="text-base font-bold text-brand-700">{{ hospital.company }}</p>
						<p class="text-[11px] text-gray-600">{{ hospital.address }}</p>
						<p class="text-[11px] text-gray-600">{{ hospital.phone }}</p>
					</div>
				</div>
				<div class="text-right">
					<p class="text-sm font-semibold uppercase tracking-wide">{{ r.outstanding > 0 ? "Bill" : "Money receipt" }}</p>
					<p class="font-mono text-[11px]">{{ r.name }}</p>
					<p class="text-[11px] text-gray-600">{{ r.date }}</p>
				</div>
			</header>
			<p class="mt-3"><span class="text-gray-500">Patient:</span> <b>{{ r.patient_name }}</b> ({{ r.patient }})</p>
			<table class="mt-3 w-full">
				<thead><tr class="border-b text-left text-[11px] uppercase text-gray-500"><th class="py-1">Description</th><th class="py-1 text-right">Qty</th><th class="py-1 text-right">Rate</th><th class="py-1 text-right">Amount</th></tr></thead>
				<tbody>
					<tr v-for="(i, n) in r.items" :key="n" class="border-b border-dashed">
						<td class="py-1.5">{{ i.description && i.description !== i.item_name ? i.description : i.item_name }}</td>
						<td class="py-1.5 text-right">{{ i.qty }}</td>
						<td class="py-1.5 text-right tabular-nums">{{ formatCurrency(i.rate) }}</td>
						<td class="py-1.5 text-right tabular-nums">{{ formatCurrency(i.amount) }}</td>
					</tr>
				</tbody>
			</table>
			<div class="ml-auto mt-3 w-60 space-y-1 tabular-nums">
				<p class="flex justify-between"><span>Total</span><span>{{ formatCurrency(r.total) }}</span></p>
				<p v-if="r.discount" class="flex justify-between"><span>Discount</span><span>- {{ formatCurrency(r.discount) }}</span></p>
				<p class="flex justify-between border-t pt-1 font-semibold"><span>Net payable</span><span>{{ formatCurrency(r.grand_total) }}</span></p>
				<p class="flex justify-between text-green-700"><span>Paid</span><span>{{ formatCurrency(r.paid) }}</span></p>
				<p class="flex justify-between font-semibold" :class="r.outstanding > 0 ? 'text-red-600' : ''"><span>Due</span><span>{{ formatCurrency(r.outstanding) }}</span></p>
			</div>
			<div v-if="r.payments.length" class="mt-4">
				<p class="mb-1 text-[11px] font-semibold uppercase text-gray-500">Payments</p>
				<p v-for="p in r.payments" :key="p.name" class="flex justify-between text-[11px]">
					<span>{{ p.posting_date || "" }} {{ p.mode_of_payment }} {{ p.reference_no && p.reference_no !== r.name ? `(${p.reference_no})` : "" }}</span>
					<span class="tabular-nums">{{ formatCurrency(p.amount) }}</span>
				</p>
			</div>
			<footer class="mt-8 flex items-end justify-between text-[11px] text-gray-500">
				<p>Received by {{ r.cashier }}</p>
				<div class="text-center"><div class="mb-1 w-36 border-b border-gray-400" /><p>Authorised signature</p></div>
			</footer>
		</article>
	</div>
</template>

<script setup>
import { computed } from "vue"
import { Button, createResource, FeatherIcon, LoadingIndicator } from "frappe-ui"
import { session } from "@/data/session"
import { formatCurrency } from "@/utils"

const props = defineProps({ invoice: { type: String, required: true } })
const receipt = createResource({ url: "hospital_saas.api.billing.get_receipt", makeParams: () => ({ invoice: props.invoice }), auto: true })
const r = computed(() => receipt.data)
const hospital = computed(() => session.data?.hospital || {})
const print = () => window.print()
</script>

<style scoped>
@media print {
	@page { size: A5; margin: 8mm; }
}
</style>
