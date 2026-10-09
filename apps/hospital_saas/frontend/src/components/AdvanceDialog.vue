<template>
	<Dialog v-model="show" :options="{ title: 'Add advance payment' }">
		<template #body-content>
			<div class="space-y-3">
				<FormControl v-model="amount" type="number" label="Amount (Tk)" />
				<FormControl v-model="mode" type="select" label="Payment mode" :options="['Cash', 'bKash', 'Nagad', 'Card']" />
				<FormControl v-if="mode !== 'Cash'" v-model="reference" label="Transaction ID" />
				<ErrorMessage :message="pay.error" />
			</div>
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button @click="show = false">Cancel</Button>
				<Button variant="solid" :loading="pay.loading" :disabled="!(amount > 0)" @click="pay.submit({ record, amount, mode_of_payment: mode, reference_no: reference || null })">Save</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { ref, watch } from "vue"
import { Button, createResource, Dialog, ErrorMessage, FormControl, toast } from "frappe-ui"

const show = defineModel({ type: Boolean })
defineProps({ record: String })
const emit = defineEmits(["saved"])
const amount = ref(0)
const mode = ref("Cash")
const reference = ref("")
watch(show, (open) => {
	if (!open) return
	amount.value = 0
	mode.value = "Cash"
	reference.value = ""
	pay.reset()
})
const pay = createResource({
	url: "hospital_saas.api.ipd.add_advance",
	onSuccess() {
		toast.success("Advance saved")
		show.value = false
		emit("saved")
	},
})
</script>
