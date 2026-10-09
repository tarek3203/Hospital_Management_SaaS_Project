<template>
	<Dialog v-model="show" :options="{ title: 'Admit to IPD', size: '2xl' }">
		<template #body-content>
			<div v-if="!opts.data" class="py-8 text-center"><LoadingIndicator class="mx-auto h-5 w-5" /></div>
			<div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2">
				<div v-if="!patient" class="sm:col-span-2">
					<Autocomplete v-model="picked" label="Patient" placeholder="Search by name, ID or mobile" :options="patientOptions" @update:query="onQuery" />
				</div>
				<p v-else class="text-sm text-gray-700 sm:col-span-2">Patient: <b>{{ patientName }}</b> ({{ patient }})</p>
				<FormControl v-model="bedType" type="select" label="Bed type" :options="bedTypeOptions" />
				<FormControl v-model="bed" type="select" label="Bed" :options="bedOptions" required />
				<FormControl v-model="practitioner" type="select" label="Consultant doctor" :options="opts.data.practitioners" required />
				<FormControl v-model="los" type="number" label="Expected stay (days)" />
				<FormControl v-model="advance" type="number" label="Advance deposit (Tk)" />
				<FormControl v-model="mode" type="select" label="Payment mode" :options="modes" />
				<FormControl v-model="note" type="textarea" label="Admission note" class="sm:col-span-2" />
				<ErrorMessage class="sm:col-span-2" :message="admit.error" />
			</div>
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button @click="show = false">Cancel</Button>
				<Button variant="solid" :loading="admit.loading" :disabled="!valid" @click="submit">Admit patient</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { useRouter } from "vue-router"
import { Autocomplete, Button, createResource, debounce, Dialog, ErrorMessage, FormControl, LoadingIndicator, toast } from "frappe-ui"

const show = defineModel({ type: Boolean })
const props = defineProps({ patient: String, patientName: String, practitioner: String, appointment: String })
const router = useRouter()

const opts = createResource({ url: "hospital_saas.api.ipd.get_admission_options" })
const picked = ref(null)
const bedType = ref("")
const bed = ref("")
const practitioner = ref("")
const los = ref(3)
const advance = ref(0)
const mode = ref("Cash")
const note = ref("")
const modes = ["Cash", "bKash", "Nagad", "Card"]

const search = createResource({ url: "hospital_saas.api.patients.search_patients" })
const onQuery = debounce((txt) => search.submit({ txt }), 250)
const patientOptions = computed(() => (search.data || []).map((p) => ({ label: p.patient_name, value: p.name, description: p.name })))

const bedTypeOptions = computed(() => [
	{ label: "Any bed type", value: "" },
	...(opts.data?.bed_types || []).map((t) => ({ label: `${t.name} (Tk ${t.rate.toLocaleString("en-IN")}/day)`, value: t.name })),
])
const bedOptions = computed(() => [
	{ label: `Select a vacant bed (${filteredBeds.value.length} free)`, value: "" },
	...filteredBeds.value,
])
const filteredBeds = computed(() => (opts.data?.beds || []).filter((b) => !bedType.value || b.type === bedType.value))
const patientId = computed(() => props.patient || picked.value?.value)
const valid = computed(() => patientId.value && bed.value && practitioner.value)

watch(bedType, () => (bed.value = ""))
watch(bed, (b) => {
	const found = (opts.data?.beds || []).find((x) => x.value === b)
	if (found && !advance.value) advance.value = { "General Ward Bed": 5000, "Private Cabin": 15000, "ICU Bed": 30000 }[found.type] || 5000
})
watch(
	show,
	(open) => {
		if (!open) return
		opts.fetch()
		picked.value = null
		bedType.value = ""
		bed.value = ""
		practitioner.value = props.practitioner || ""
		los.value = 3
		advance.value = 0
		note.value = ""
		admit.reset()
	},
	{ immediate: true },
)

const admit = createResource({
	url: "hospital_saas.api.ipd.admit",
	onSuccess(record) {
		toast.success(`Admitted (${record})`)
		show.value = false
		router.push(`/ipd/${encodeURIComponent(record)}`)
	},
})
function submit() {
	admit.submit({
		patient: patientId.value,
		bed: bed.value,
		practitioner: practitioner.value,
		expected_length_of_stay: los.value,
		note: note.value,
		appointment: props.appointment,
		advance: advance.value,
		mode_of_payment: mode.value,
	})
}
</script>
