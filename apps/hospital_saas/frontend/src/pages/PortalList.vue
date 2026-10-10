<template>
	<div class="mx-auto max-w-6xl space-y-4 p-4 sm:p-6">
		<div class="flex flex-wrap items-center gap-3">
			<h1 class="flex-1 text-xl font-semibold text-gray-900">{{ conf.title }}</h1>
			<Button v-if="kind === 'appointments'" variant="solid" @click="showBook = true">
				<template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
				Book appointment
			</Button>
		</div>
		<DataTable :columns="conf.columns" :rows="list.data" :empty-text="conf.empty">
			<template #cell-status="{ row }">
				<Badge :label="row.docstatus !== undefined && kind !== 'appointments' ? (row.docstatus === 1 ? 'Report ready' : 'In progress') : row.status" :theme="STATUS_THEMES[row.status] || (row.docstatus === 1 ? 'green' : 'blue')" variant="subtle" />
			</template>
			<template #cell-outstanding_amount="{ row }">
				<span :class="row.outstanding_amount > 0 ? 'text-red-600' : 'text-green-700'">{{ row.outstanding_amount > 0 ? formatCurrency(row.outstanding_amount) : "Paid" }}</span>
			</template>
			<template #actions="{ row }">
				<div class="flex justify-end gap-1">
					<Button v-if="kind === 'appointments' && ['Scheduled', 'Open'].includes(row.status) && !row.paid_amount" size="sm" @click="cancel.submit({ appointment: row.name })">Cancel</Button>
					<Button v-if="['pathology', 'radiology'].includes(kind) && row.docstatus === 1" size="sm" @click="$router.push(`/portal/report/${encodeURIComponent(row.name)}`)">View report</Button>
					<Button v-if="['pharmacy', 'bills'].includes(kind)" size="sm" variant="ghost" @click="$router.push(`/portal/receipt/${encodeURIComponent(row.name)}`)"><FeatherIcon name="printer" class="h-4 w-4" /></Button>
					<Button v-if="kind === 'live' && row.join_url && row.status === 'Scheduled'" size="sm" variant="solid" @click="open(row.join_url)">Join</Button>
					<Button v-if="kind === 'downloads' && (row.file || row.url)" size="sm" @click="open(row.file || row.url)">Open</Button>
					<Button v-if="kind === 'surveys'" size="sm" variant="solid" @click="$router.push(`/portal/survey/${encodeURIComponent(row.name)}`)">Take survey</Button>
				</div>
			</template>
		</DataTable>
		<p v-if="conf.soon" class="flex items-center gap-2 text-xs text-gray-500">{{ conf.soon }} <SoonBadge /></p>
		<PortalBookDialog v-model="showBook" @booked="list.reload()" />
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { Badge, Button, createResource, FeatherIcon, toast } from "frappe-ui"
import DataTable from "@/components/DataTable.vue"
import PortalBookDialog from "@/components/PortalBookDialog.vue"
import SoonBadge from "@/components/SoonBadge.vue"
import { formatCurrency, STATUS_THEMES } from "@/utils"

const props = defineProps({ kind: { type: String, required: true } })
const showBook = ref(false)
const C = (key, label, extra = {}) => ({ key, label, ...extra })
const CONF = {
	appointments: { title: "My appointments", columns: [C("name", "No"), C("appointment_date", "Date"), C("appointment_time", "Time"), C("practitioner_name", "Doctor"), C("department", "Department"), C("status", "Status")], empty: "No appointments" },
	opd: { title: "OPD visits", columns: [C("name", "OPD No"), C("appointment_date", "Date"), C("practitioner_name", "Doctor"), C("department", "Department"), C("diagnosis", "Diagnosis"), C("status", "Status")], empty: "No visits", soon: "Prescription download" },
	ipd: { title: "IPD admissions", columns: [C("name", "IPD No"), C("admitted_datetime", "Admitted", { format: "datetime" }), C("discharge_datetime", "Discharged", { format: "datetime" }), C("consultant", "Consultant"), C("medical_department", "Department"), C("status", "Status")], empty: "No admissions", soon: "Discharge summary download" },
	pharmacy: { title: "Pharmacy bills", columns: [C("name", "Bill No"), C("posting_date", "Date"), C("grand_total", "Amount", { format: "currency" }), C("outstanding_amount", "Due")], empty: "No pharmacy bills" },
	pathology: { title: "Pathology reports", columns: [C("name", "Test No"), C("lab_test_name", "Test"), C("date", "Date"), C("practitioner_name", "Referred by"), C("status", "Status")], empty: "No lab tests" },
	radiology: { title: "Radiology reports", columns: [C("name", "Test No"), C("lab_test_name", "Examination"), C("date", "Date"), C("practitioner_name", "Referred by"), C("status", "Status")], empty: "No radiology tests" },
	"blood-bank": { title: "Blood bank", columns: [C("name", "Issue No"), C("issue_date", "Date"), C("blood_group", "Blood group"), C("component", "Component"), C("charge", "Charge", { format: "currency" })], empty: "No blood issued" },
	ambulance: { title: "Ambulance", columns: [C("name", "Call No"), C("call_date", "Date"), C("pickup", "From"), C("destination", "To"), C("charge", "Charge", { format: "currency" }), C("status", "Status")], empty: "No ambulance calls" },
	live: { title: "Live consultation", columns: [C("name", "No"), C("doctor_name", "Doctor"), C("meeting_date", "Date"), C("meeting_time", "Time"), C("status", "Status")], empty: "No video consultations" },
	downloads: { title: "Download center", columns: [C("title", "Title"), C("content_type", "Type"), C("upload_date", "Date")], empty: "Nothing shared yet" },
	surveys: { title: "Survey forms", columns: [C("title", "Survey"), C("description", "About")], empty: "No surveys right now" },
}
const conf = computed(() => CONF[props.kind] || CONF.appointments)
const list = createResource({ url: "hospital_saas.api.portal.get_records", makeParams: () => ({ kind: props.kind }), auto: true })
watch(() => props.kind, () => list.reload())
const cancel = createResource({
	url: "hospital_saas.api.portal.cancel",
	onSuccess() {
		toast.success("Appointment cancelled")
		list.reload()
	},
	onError: (e) => toast.error(e.messages?.[0] || "Could not cancel"),
})
function open(url) {
	if (/^(https?:\/\/|\/(private\/)?files\/)/i.test(url)) window.open(url, "_blank", "noopener")
}
</script>
