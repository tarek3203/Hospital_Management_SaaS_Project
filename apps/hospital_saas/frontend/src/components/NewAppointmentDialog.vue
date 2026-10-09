<template>
	<Dialog v-model="show" :options="{ title: 'Book appointment', size: '3xl' }">
		<template #body-content>
			<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
				<div class="sm:col-span-2">
					<Autocomplete
						v-model="patient"
						label="Patient"
						placeholder="Search by name, ID or mobile"
						:options="patientOptions"
						:loading="patientSearch.loading"
						@update:query="onPatientQuery"
					/>
					<button class="mt-1 text-xs font-medium text-brand-600 hover:underline" @click="$emit('new-patient')">
						+ Register a new patient
					</button>
				</div>
				<FormControl v-model="department" type="select" label="Department" :options="departmentOptions" />
				<FormControl v-model="practitioner" type="select" label="Doctor" :options="doctorOptions" required />
				<FormControl v-model="date" type="date" label="Date" :min="todayISO()" required />
				<FormControl v-model="appointmentType" type="select" label="Appointment type" :options="options.data?.appointment_types || []" />

				<div class="sm:col-span-2">
					<p class="mb-1.5 text-xs text-gray-600">Time slot</p>
					<div v-if="!practitioner" class="rounded-md bg-gray-50 px-3 py-4 text-center text-sm text-gray-500">Pick a doctor to see free slots</div>
					<div v-else-if="slots.loading" class="py-4 text-center"><LoadingIndicator class="mx-auto h-5 w-5" /></div>
					<div v-else-if="slots.error" class="rounded-md bg-orange-50 px-3 py-3 text-sm text-orange-700">{{ slotError }}</div>
					<div v-else-if="!slots.data?.length" class="rounded-md bg-gray-50 px-3 py-4 text-center text-sm text-gray-500">No free slots on this date</div>
					<div v-else class="grid grid-cols-4 gap-1.5 sm:grid-cols-8">
						<button
							v-for="slot in slots.data"
							:key="slot.time + slot.service_unit"
							:disabled="slot.full"
							class="rounded-md border px-2 py-1.5 text-sm tabular-nums transition-colors disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-400"
							:class="selectedSlot === slot ? 'border-brand-600 bg-brand-600 text-white' : 'bg-white hover:border-brand-500'"
							:title="slot.booked ? `${slot.booked} already booked` : 'Free'"
							@click="selectedSlot = slot"
						>
							{{ slot.time }}
						</button>
					</div>
				</div>

				<FormControl v-model="fee" type="number" label="Consultation fee (Tk)" />
				<FormControl v-model="modeOfPayment" type="select" label="Payment" :options="paymentOptions" />
				<FormControl v-model="notes" type="textarea" label="Notes" class="sm:col-span-2" />
				<ErrorMessage class="sm:col-span-2" :message="book.error" />
			</div>
		</template>
		<template #actions>
			<div class="flex items-center justify-end gap-2">
				<Button @click="show = false">Cancel</Button>
				<Button variant="solid" :loading="book.loading" :disabled="!valid" @click="submit">Book appointment</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import {
	Autocomplete,
	Button,
	createResource,
	debounce,
	Dialog,
	ErrorMessage,
	FormControl,
	LoadingIndicator,
	toast,
} from "frappe-ui"
import { todayISO } from "@/utils"

const show = defineModel({ type: Boolean })
const props = defineProps({ initialPatient: Object })
const emit = defineEmits(["booked", "new-patient"])

const patient = ref(null)
const department = ref("")
const practitioner = ref("")
const date = ref(todayISO())
const appointmentType = ref("Consultation")
const selectedSlot = ref(null)
const fee = ref(0)
const modeOfPayment = ref("Cash")
const notes = ref("")

const options = createResource({ url: "hospital_saas.api.appointments.get_booking_options", auto: true })

const patientSearch = createResource({ url: "hospital_saas.api.patients.search_patients" })
const onPatientQuery = debounce((txt) => patientSearch.submit({ txt }), 250)
const patientOptions = computed(() => {
	const found = (patientSearch.data || []).map((p) => ({
		label: p.patient_name,
		value: p.name,
		description: [p.name, p.mobile].filter(Boolean).join(" · "),
	}))
	if (patient.value && !found.some((o) => o.value === patient.value.value)) found.unshift(patient.value)
	return found
})

const doctors = computed(() =>
	(options.data?.practitioners || []).filter((d) => !department.value || d.department === department.value),
)
const departmentOptions = computed(() => [
	{ label: "All departments", value: "" },
	...(options.data?.departments || []).map((d) => ({ label: d, value: d })),
])
const doctorOptions = computed(() => [
	{ label: "Select a doctor", value: "" },
	...doctors.value.map((d) => ({ label: `${d.practitioner_name} (${d.department})`, value: d.name })),
])
const paymentOptions = computed(() => [
	{ label: "Not paid yet", value: "" },
	...(options.data?.modes_of_payment || []).map((m) => ({ label: m, value: m })),
])

const slots = createResource({ url: "hospital_saas.api.appointments.get_slots" })
const slotError = computed(() => slots.error?.messages?.[0] || "Doctor is not available on this date")

watch([practitioner, date], () => {
	selectedSlot.value = null
	if (practitioner.value && date.value) slots.submit({ practitioner: practitioner.value, date: date.value })
	const doctor = doctors.value.find((d) => d.name === practitioner.value)
	if (doctor) fee.value = doctor.op_consulting_charge
})

const valid = computed(() => patient.value?.value && practitioner.value && date.value && selectedSlot.value)

const book = createResource({
	url: "hospital_saas.api.appointments.book_appointment",
	onSuccess(result) {
		toast.success(`Appointment ${result.name} booked`)
		emit("booked", result)
		show.value = false
	},
})

function submit() {
	if (!valid.value) return
	book.submit({
		patient: patient.value.value,
		practitioner: practitioner.value,
		date: date.value,
		time: selectedSlot.value.time,
		service_unit: selectedSlot.value.service_unit,
		appointment_type: appointmentType.value,
		notes: notes.value,
		fee: fee.value,
		mode_of_payment: modeOfPayment.value || null,
	})
}

// flush "post": the parent sets initialPatient and opens the dialog in the same tick;
// immediate: the dialog can already be open on mount (?new=1 links).
watch(show, (open) => {
	if (!open) return
	patient.value = props.initialPatient || null
	practitioner.value = ""
	department.value = ""
	date.value = todayISO()
	selectedSlot.value = null
	notes.value = ""
	modeOfPayment.value = "Cash"
	book.reset()
}, { flush: "post", immediate: true })
</script>
