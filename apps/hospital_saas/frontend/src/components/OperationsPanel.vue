<template>
	<div class="space-y-3">
		<div v-if="ops.data?.can.write && editable" class="flex justify-end">
			<Button variant="solid" @click="open(null)">
				<template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
				Add operation
			</Button>
		</div>
		<DataTable :columns="columns" :rows="ops.data?.rows" clickable empty-text="No operations booked" @row-click="open">
			<template #cell-operation_name="{ row }">
				<p class="font-medium text-gray-900">{{ row.operation_name }}</p>
				<p class="text-xs text-gray-500">{{ row.category }}</p>
			</template>
			<template #cell-operation_date="{ row }">{{ row.operation_date }} {{ row.operation_time || "" }}</template>
			<template #cell-surgeon_name="{ row }">
				<p>{{ row.surgeon_name }}</p>
				<p class="text-xs text-gray-500">{{ [row.anaesthesia_type, row.anaesthetist].filter(Boolean).join(" · ") }}</p>
			</template>
		</DataTable>

		<Dialog v-model="show" :options="{ title: form.name ? `Operation ${form.name}` : 'Book operation', size: '3xl' }">
			<template #body-content>
				<div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
					<FormControl v-model="form.operation_name" label="Operation" class="sm:col-span-2" placeholder="e.g. Laparoscopic cholecystectomy" />
					<FormControl v-model="form.category" type="select" label="Category" :options="ops.data?.categories || []" />
					<FormControl v-model="form.operation_date" type="date" label="Date" />
					<FormControl v-model="form.operation_time" type="time" label="Time" />
					<FormControl v-model="form.ot_room" label="OT room" placeholder="OT-1" />
					<FormControl v-model="form.surgeon" type="select" label="Surgeon" :options="[{ label: 'Select', value: '' }, ...doctors]" />
					<FormControl v-model="form.assistant" label="Assistant" />
					<FormControl v-model="form.anaesthetist" label="Anaesthetist" />
					<FormControl v-model="form.anaesthesia_type" type="select" label="Anaesthesia" :options="[{ label: 'Select', value: '' }, ...(ops.data?.anaesthesia || [])]" />
					<FormControl v-model="form.status" type="select" label="Status" :options="['Scheduled', 'In Progress', 'Completed', 'Cancelled']" />
					<FormControl v-model="form.charge" type="number" label="OT charge (Tk)" />
					<FormControl v-model="form.pre_op_notes" type="textarea" label="Pre-operative notes" class="sm:col-span-3" />
					<FormControl v-model="form.operation_notes" type="textarea" label="Operation notes" class="sm:col-span-3" />
					<FormControl v-model="form.result" label="Outcome" class="sm:col-span-3" />
					<p class="flex items-center gap-2 text-xs text-gray-500 sm:col-span-3">Consent form upload and OT charge billing <SoonBadge /></p>
				</div>
				<ErrorMessage class="mt-2" :message="save.error" />
			</template>
			<template #actions>
				<div class="flex justify-end gap-2">
					<Button @click="show = false">Close</Button>
					<Button v-if="ops.data?.can.write" variant="solid" :loading="save.loading" :disabled="!(form.operation_name && form.surgeon && form.operation_date)" @click="save.submit({ data: { ...form } })">Save</Button>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { computed, reactive, ref } from "vue"
import { Button, createResource, Dialog, ErrorMessage, FeatherIcon, FormControl, toast } from "frappe-ui"
import DataTable from "@/components/DataTable.vue"
import SoonBadge from "@/components/SoonBadge.vue"
import { todayISO } from "@/utils"

const props = defineProps({ patient: String, record: String, appointment: String, defaultSurgeon: String, editable: { type: Boolean, default: true } })
const show = ref(false)
const form = reactive({})
const ops = createResource({
	url: "hospital_saas.api.ot.get_operations",
	makeParams: () => ({ patient: props.patient, record: props.record, appointment: props.appointment }),
	auto: true,
})
const docs = createResource({ url: "hospital_saas.api.appointments.get_booking_options", auto: true })
const doctors = computed(() => (docs.data?.practitioners || []).map((d) => ({ label: `${d.practitioner_name} (${d.department})`, value: d.name })))

const columns = [
	{ key: "name", label: "OT No" },
	{ key: "operation_name", label: "Operation" },
	{ key: "operation_date", label: "Date" },
	{ key: "surgeon_name", label: "Surgeon" },
	{ key: "ot_room", label: "OT room" },
	{ key: "status", label: "Status", badge: true },
]

function open(row) {
	Object.keys(form).forEach((k) => delete form[k])
	Object.assign(
		form,
		row || {
			patient: props.patient,
			inpatient_record: props.record,
			appointment: props.appointment,
			operation_name: "",
			category: "General Surgery",
			status: "Scheduled",
			operation_date: todayISO(),
			operation_time: "10:00",
			ot_room: "OT-1",
			surgeon: props.defaultSurgeon || "",
			anaesthesia_type: "General",
			charge: 0,
		},
	)
	save.reset()
	show.value = true
}

const save = createResource({
	url: "hospital_saas.api.ot.save_operation",
	onSuccess(name) {
		toast.success(`Operation ${name} saved`)
		show.value = false
		ops.reload()
	},
})
</script>
