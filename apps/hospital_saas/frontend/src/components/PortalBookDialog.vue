<template>
	<Dialog v-model="show" :options="{ title: 'Book an appointment', size: '2xl' }">
		<template #body-content>
			<div class="space-y-4">
				<FormControl v-model="doctor" type="select" label="Doctor" :options="doctorOptions" />
				<FormControl v-model="date" type="date" label="Date" :min="todayISO()" />
				<div>
					<p class="mb-1.5 text-xs text-gray-600">Time</p>
					<div v-if="!doctor" class="rounded-md bg-gray-50 px-3 py-4 text-center text-sm text-gray-500">Pick a doctor first</div>
					<div v-else-if="slots.loading" class="py-4 text-center"><LoadingIndicator class="mx-auto h-5 w-5" /></div>
					<div v-else-if="slots.error" class="rounded-md bg-orange-50 px-3 py-3 text-sm text-orange-700">{{ slots.error.messages?.[0] || "Doctor is not available on this date" }}</div>
					<div v-else-if="!slots.data?.length" class="rounded-md bg-gray-50 px-3 py-4 text-center text-sm text-gray-500">No free times on this date</div>
					<div v-else class="grid grid-cols-4 gap-1.5 sm:grid-cols-6">
						<button v-for="s in slots.data" :key="s.time" class="rounded-md border px-2 py-1.5 text-sm tabular-nums" :class="time === s.time ? 'border-brand-600 bg-brand-600 text-white' : 'bg-white hover:border-brand-500'" @click="time = s.time">{{ s.time }}</button>
					</div>
				</div>
				<p class="text-xs text-gray-500">Consultation fee {{ fee ? `Tk ${fee}` : "" }} is paid at the hospital counter.</p>
				<ErrorMessage :message="book.error" />
			</div>
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button @click="show = false">Cancel</Button>
				<Button variant="solid" :disabled="!(doctor && date && time)" :loading="book.loading" @click="book.submit({ practitioner: doctor, date, time })">Book</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { Button, createResource, Dialog, ErrorMessage, FormControl, LoadingIndicator, toast } from "frappe-ui"
import { todayISO } from "@/utils"

const show = defineModel({ type: Boolean })
const emit = defineEmits(["booked"])
const doctor = ref("")
const date = ref(todayISO())
const time = ref("")
const opts = createResource({ url: "hospital_saas.api.portal.get_booking_options" })
const slots = createResource({ url: "hospital_saas.api.portal.get_slots" })
const doctorOptions = computed(() => [
	{ label: "Select a doctor", value: "" },
	...(opts.data?.practitioners || []).map((p) => ({ label: `${p.practitioner_name} (${p.department})`, value: p.name })),
])
const fee = computed(() => opts.data?.practitioners.find((p) => p.name === doctor.value)?.op_consulting_charge)
watch([doctor, date], () => {
	time.value = ""
	if (doctor.value && date.value) slots.submit({ practitioner: doctor.value, date: date.value })
})
watch(show, (open) => {
	if (!open) return
	opts.fetch()
	doctor.value = ""
	date.value = todayISO()
	time.value = ""
	book.reset()
})
const book = createResource({
	url: "hospital_saas.api.portal.book",
	onSuccess(name) {
		toast.success(`Appointment ${name} booked`)
		show.value = false
		emit("booked")
	},
})
</script>
