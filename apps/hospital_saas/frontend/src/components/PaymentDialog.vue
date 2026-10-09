<template>
	<Dialog v-model="show" :options="{ title: 'Add payment' }">
		<template #body-content>
			<div class="space-y-3">
				<p class="text-sm text-gray-600">Due: <span class="font-semibold text-gray-900">{{ formatCurrency(due) }}</span></p>
				<FormControl v-model="amount" type="number" label="Amount (Tk)" />
				<FormControl v-model="mode" type="select" label="Payment mode" :options="modes.data || ['Cash']" />
				<FormControl v-if="mode !== 'Cash'" v-model="reference" label="Transaction ID" placeholder="e.g. bKash TrxID" />
				<ErrorMessage :message="pay.error" />
			</div>
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button @click="show = false">Cancel</Button>
				<Button variant="solid" :loading="pay.loading" :disabled="!(amount > 0)" @click="submit">Save payment</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { ref, watch } from "vue"
import { Button, createResource, Dialog, ErrorMessage, FormControl, toast } from "frappe-ui"
import { formatCurrency } from "@/utils"

const show = defineModel({ type: Boolean })
const props = defineProps({ invoice: String, due: Number })
const emit = defineEmits(["saved"])
const amount = ref(0)
const mode = ref("Cash")
const reference = ref("")

const modes = createResource({
	url: "hospital_saas.api.appointments.get_booking_options",
	transform: (d) => d.modes_of_payment,
})
watch(show, (open) => {
	if (!open) return
	amount.value = props.due
	mode.value = "Cash"
	reference.value = ""
	pay.reset()
	if (!modes.data) modes.fetch()
})

const pay = createResource({
	url: "hospital_saas.api.opd.add_payment",
	onSuccess() {
		toast.success("Payment saved")
		show.value = false
		emit("saved")
	},
})
function submit() {
	pay.submit({ invoice: props.invoice, amount: amount.value, mode_of_payment: mode.value, reference_no: reference.value || null })
}
</script>
