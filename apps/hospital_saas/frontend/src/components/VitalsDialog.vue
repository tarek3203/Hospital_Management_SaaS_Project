<template>
	<Dialog v-model="show" :options="{ title: 'Record vitals', size: 'xl' }">
		<template #body-content>
			<div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
				<FormControl v-model="form.bp_systolic" type="number" label="BP systolic" placeholder="120" />
				<FormControl v-model="form.bp_diastolic" type="number" label="BP diastolic" placeholder="80" />
				<FormControl v-model="form.pulse" type="number" label="Pulse (bpm)" placeholder="72" />
				<FormControl v-model="form.temperature" type="number" label="Temperature (F)" placeholder="98.6" />
				<FormControl v-model="form.respiratory_rate" type="number" label="Resp. rate" placeholder="16" />
				<FormControl v-model="form.height" type="number" label="Height (m)" placeholder="1.65" />
				<FormControl v-model="form.weight" type="number" label="Weight (kg)" placeholder="62" />
				<FormControl v-model="form.note" label="Note" class="col-span-2" />
			</div>
			<ErrorMessage class="mt-3" :message="save.error" />
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button @click="show = false">Cancel</Button>
				<Button variant="solid" :loading="save.loading" @click="save.submit(record ? { record, ...form } : { appointment, ...form })">Save vitals</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { reactive, watch } from "vue"
import { Button, createResource, Dialog, ErrorMessage, FormControl, toast } from "frappe-ui"

const show = defineModel({ type: Boolean })
// Either an OPD visit (appointment) or an IPD stay (record).
const props = defineProps({ appointment: String, record: String })
const emit = defineEmits(["saved"])
const blank = { bp_systolic: "", bp_diastolic: "", pulse: "", temperature: "", respiratory_rate: "", height: "", weight: "", note: "" }
const form = reactive({ ...blank })
watch(show, (open) => open && Object.assign(form, blank))

const save = createResource({
	url: props.record ? "hospital_saas.api.ipd.add_ipd_vitals" : "hospital_saas.api.opd.add_vitals",
	onSuccess() {
		toast.success("Vitals recorded")
		show.value = false
		emit("saved")
	},
})
</script>
