<template>
	<Dialog v-model="show" :options="{ title: 'Transfer bed' }">
		<template #body-content>
			<p class="mb-3 text-sm text-gray-600">Current bed: <b>{{ current }}</b></p>
			<FormControl v-model="bed" type="select" label="New bed" :options="bedOptions" />
			<ErrorMessage class="mt-2" :message="move.error" />
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button @click="show = false">Cancel</Button>
				<Button variant="solid" :loading="move.loading" :disabled="!bed" @click="move.submit({ record, bed })">Transfer</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { Button, createResource, Dialog, ErrorMessage, FormControl, toast } from "frappe-ui"

const show = defineModel({ type: Boolean })
const props = defineProps({ record: String, current: String })
const emit = defineEmits(["saved"])
const bed = ref("")
const opts = createResource({ url: "hospital_saas.api.ipd.get_admission_options" })
const bedOptions = computed(() => [
	{ label: "Select a vacant bed", value: "" },
	...(opts.data?.beds || []).map((b) => ({ label: `${b.label} (${b.type})`, value: b.value })),
])
watch(show, (open) => {
	if (!open) return
	bed.value = ""
	move.reset()
	opts.fetch()
})
const move = createResource({
	url: "hospital_saas.api.ipd.transfer",
	onSuccess(label) {
		toast.success(`Moved to ${label}`)
		show.value = false
		emit("saved")
	},
})
</script>
