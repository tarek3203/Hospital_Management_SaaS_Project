<template>
	<Dialog v-model="show" :options="{ title: `New ${section.toLowerCase()} test` }">
		<template #body-content>
			<div class="space-y-3">
				<Autocomplete v-model="patient" label="Patient" placeholder="Search by name, ID or mobile" :options="patientOptions" @update:query="onQuery" />
				<FormControl v-model="template" type="select" label="Test" :options="[{ label: 'Select a test', value: '' }, ...(templates.data || []).map((t) => ({ label: `${t.label} (Tk ${t.rate})`, value: t.value }))]" />
				<p class="text-xs text-gray-500">Bill the test from Billing, {{ section }}.</p>
				<ErrorMessage :message="save.error" />
			</div>
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button @click="show = false">Cancel</Button>
				<Button variant="solid" :loading="save.loading" :disabled="!(patient && template)" @click="save.submit({ patient: patient.value, template })">Create</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { useRouter } from "vue-router"
import { Autocomplete, Button, createResource, debounce, Dialog, ErrorMessage, FormControl, toast } from "frappe-ui"

const show = defineModel({ type: Boolean })
const props = defineProps({ section: { type: String, default: "Pathology" } })
const emit = defineEmits(["saved"])
const router = useRouter()
const patient = ref(null)
const template = ref("")
const templates = createResource({ url: "hospital_saas.api.lab.get_templates", makeParams: () => ({ section: props.section }) })
const search = createResource({ url: "hospital_saas.api.patients.search_patients" })
const onQuery = debounce((txt) => search.submit({ txt }), 250)
const patientOptions = computed(() => {
	const found = (search.data || []).map((p) => ({ label: p.patient_name, value: p.name, description: p.name }))
	if (patient.value && !found.some((o) => o.value === patient.value.value)) found.unshift(patient.value)
	return found
})
watch(show, (open) => {
	if (!open) return
	patient.value = null
	template.value = ""
	save.reset()
	templates.reload()
})
const save = createResource({
	url: "hospital_saas.api.lab.create_test",
	onSuccess(name) {
		toast.success(`Test ${name} created`)
		show.value = false
		emit("saved")
		router.push(`/lab/${encodeURIComponent(name)}`)
	},
})
</script>
