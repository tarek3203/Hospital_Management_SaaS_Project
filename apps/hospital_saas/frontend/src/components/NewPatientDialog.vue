<template>
	<Dialog v-model="show" :options="{ title: 'Register patient', size: '2xl' }">
		<template #body-content>
			<form class="grid grid-cols-1 gap-4 sm:grid-cols-2" @submit.prevent="submit">
				<FormControl v-model="form.first_name" label="First name" required autofocus />
				<FormControl v-model="form.last_name" label="Last name" />
				<FormControl v-model="form.sex" type="select" label="Gender" :options="options.genders" required />
				<div class="grid grid-cols-2 gap-2">
					<FormControl v-model="form.dob" type="date" label="Date of birth" />
					<FormControl v-model="form.age" type="number" label="or age (years)" :disabled="!!form.dob" />
				</div>
				<FormControl v-model="form.mobile" label="Mobile" placeholder="01XXXXXXXXX" required />
				<FormControl v-model="form.email" type="email" label="Email" />
				<FormControl v-model="form.blood_group" type="select" label="Blood group" :options="[{ label: 'Not known', value: '' }, ...options.blood_groups]" />
				<FormControl v-model="form.marital_status" type="select" label="Marital status" :options="[{ label: 'Not set', value: '' }, ...options.marital_statuses]" />
				<FormControl v-model="form.address" type="textarea" label="Address" class="sm:col-span-2" />
				<ErrorMessage class="sm:col-span-2" :message="register.error" />
			</form>
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button @click="show = false">Cancel</Button>
				<Button variant="solid" :loading="register.loading" :disabled="!valid" @click="submit">Register</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, reactive, watch } from "vue"
import { Button, createResource, Dialog, ErrorMessage, FormControl, toast } from "frappe-ui"

const show = defineModel({ type: Boolean })
const emit = defineEmits(["created"])

const blank = () => ({
	first_name: "",
	last_name: "",
	sex: "Male",
	dob: "",
	age: "",
	mobile: "",
	email: "",
	blood_group: "",
	marital_status: "",
	address: "",
})
const form = reactive(blank())

const optionsResource = createResource({ url: "hospital_saas.api.patients.get_form_options", auto: true })
const options = computed(
	() => optionsResource.data || { genders: ["Male", "Female"], blood_groups: [], marital_statuses: [] },
)

const valid = computed(() => form.first_name.trim() && form.sex && form.mobile.trim())

const register = createResource({
	url: "hospital_saas.api.patients.register_patient",
	onSuccess(patient) {
		toast.success(`${patient.patient_name} registered (${patient.name})`)
		emit("created", patient)
		show.value = false
	},
})

watch(show, (open) => open && Object.assign(form, blank()))

function submit() {
	if (!valid.value) return
	const params = Object.fromEntries(Object.entries(form).filter(([, v]) => v !== "" && v !== null))
	register.submit(params)
}
</script>
