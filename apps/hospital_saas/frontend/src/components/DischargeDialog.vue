<template>
	<Dialog v-model="show" :options="{ title: 'Discharge patient', size: 'xl' }">
		<template #body-content>
			<div class="space-y-3">
				<div class="grid grid-cols-3 gap-2 rounded-md bg-gray-50 p-3 text-sm">
					<div><p class="text-xs text-gray-500">Bill</p><p class="font-semibold tabular-nums">{{ formatCurrency(billing.total) }}</p></div>
					<div><p class="text-xs text-gray-500">Advance paid</p><p class="font-semibold tabular-nums text-green-700">{{ formatCurrency(billing.paid) }}</p></div>
					<div><p class="text-xs text-gray-500">{{ balance >= 0 ? "To collect" : "Refund due" }}</p><p class="font-semibold tabular-nums" :class="balance > 0 ? 'text-red-600' : ''">{{ formatCurrency(Math.abs(balance)) }}</p></div>
				</div>
				<FormControl v-if="balance > 0" v-model="mode" type="select" label="Collect balance by" :options="['Cash', 'bKash', 'Nagad', 'Card']" />
				<FormControl v-model="summary" type="textarea" label="Discharge summary and advice" :rows="4" />
				<FormControl v-model="followup" type="date" label="Follow-up date" />
				<p class="flex items-center gap-2 text-xs text-gray-500">Printable discharge summary <SoonBadge /></p>
				<ErrorMessage :message="discharge.error" />
			</div>
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button @click="show = false">Cancel</Button>
				<Button variant="solid" theme="red" :loading="discharge.loading" @click="submit">Discharge and bill</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { Button, createResource, Dialog, ErrorMessage, FormControl, toast } from "frappe-ui"
import SoonBadge from "@/components/SoonBadge.vue"
import { formatCurrency } from "@/utils"

const show = defineModel({ type: Boolean })
const props = defineProps({ record: String, billing: { type: Object, default: () => ({}) } })
const emit = defineEmits(["saved"])
const summary = ref("")
const followup = ref("")
const mode = ref("Cash")
const balance = computed(() => (props.billing.total || 0) - (props.billing.paid || 0))
watch(show, (open) => {
	if (!open) return
	summary.value = "Condition improved. Continue medicines as advised and review in OPD."
	followup.value = ""
	discharge.reset()
})

const discharge = createResource({
	url: "hospital_saas.api.ipd.discharge",
	onSuccess(r) {
		toast.success(r?.invoice ? `Discharged. Final bill ${r.invoice}` : "Discharged")
		show.value = false
		emit("saved")
	},
})
function submit() {
	discharge.submit({ record: props.record, summary: summary.value, followup_date: followup.value || null, mode_of_payment: balance.value > 0 ? mode.value : null })
}
</script>
