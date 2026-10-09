<template>
	<div class="mx-auto max-w-7xl space-y-4 p-4 sm:p-6">
		<nav class="text-xs text-gray-500">
			<router-link to="/ipd" class="hover:text-gray-800">IPD</router-link>
			<span class="mx-1">/</span>
			<span>{{ record }}</span>
		</nav>

		<div v-if="stay.loading && !d" class="flex justify-center py-20"><LoadingIndicator class="h-6 w-6 text-brand-600" /></div>
		<ErrorMessage v-else-if="stay.error" :message="stay.error" />

		<template v-else-if="d">
			<div class="rounded-lg border bg-white p-4 sm:p-5">
				<PatientHeader :patient="d.patient" :extra="headerFacts">
					<template #actions>
						<div class="flex flex-wrap gap-2">
							<Badge :label="d.stay.status" :theme="d.stay.status === 'Discharged' ? 'gray' : 'green'" variant="subtle" size="lg" />
							<Button v-if="d.can.round && d.can.manage" variant="solid" @click="showRound = true">
								<template #prefix><FeatherIcon name="edit-3" class="h-4 w-4" /></template>
								Ward round
							</Button>
							<Dropdown v-if="actions.length" :options="actions" placement="right">
								<Button>
									<template #prefix><FeatherIcon name="more-horizontal" class="h-4 w-4" /></template>
									Actions
								</Button>
							</Dropdown>
						</div>
					</template>
				</PatientHeader>
				<div class="mt-4"><TabBar v-model="tab" :tabs="tabs" /></div>
			</div>

			<div v-if="tab === 'overview'" class="space-y-4">
				<InfoGrid title="Admission" :items="admissionInfo" />
				<div class="rounded-lg border bg-white p-4">
					<div class="flex flex-wrap items-center justify-between gap-2 text-sm">
						<p class="font-semibold text-gray-900">IPD payment and billing</p>
						<p class="tabular-nums text-gray-700">
							Bill {{ formatCurrency(d.billing.total) }} · Paid {{ formatCurrency(d.billing.paid) }} ·
							<span :class="d.billing.outstanding ? 'text-red-600' : 'text-green-700'">{{ d.billing.outstanding ? `Due ${formatCurrency(d.billing.outstanding)}` : `Balance ${formatCurrency(d.billing.paid - d.billing.total)}` }}</span>
						</p>
					</div>
					<div class="mt-2 h-2 overflow-hidden rounded-full bg-gray-100">
						<div class="h-full rounded-full bg-brand-500" :style="{ width: `${paidPct}%` }" />
					</div>
					<div class="mt-3 grid grid-cols-2 gap-2 text-xs text-gray-500 sm:grid-cols-5">
						<span v-for="m in ['Pharmacy', 'Pathology', 'Radiology', 'Blood Bank', 'Ambulance']" :key="m" class="flex items-center gap-1">{{ m }} billing <SoonBadge /></span>
					</div>
				</div>
				<div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
					<div class="rounded-lg border bg-white p-4">
						<p class="mb-2 text-sm font-semibold text-gray-900">Latest nurse notes</p>
						<p v-if="!d.nurse_notes.length" class="text-sm text-gray-500">No nurse notes yet</p>
						<div v-for="n in d.nurse_notes.slice(0, 3)" :key="n.name" class="border-b py-2 text-sm last:border-0">
							<p class="text-xs text-gray-500">{{ n.date }} · {{ n.owner }}</p>
							<p class="text-gray-800">{{ stripHtml(n.subject) }}</p>
						</div>
					</div>
					<div class="rounded-lg border bg-white p-4">
						<p class="mb-2 text-sm font-semibold text-gray-900">Latest ward round</p>
						<p v-if="!d.rounds.length" class="text-sm text-gray-500">No rounds yet</p>
						<template v-else>
							<p class="text-xs text-gray-500">{{ d.rounds[0].encounter_date }} {{ d.rounds[0].encounter_time }} · {{ d.rounds[0].practitioner_name }}</p>
							<p class="mt-1 text-sm text-gray-800"><b>Diagnosis:</b> {{ d.rounds[0].diagnoses.join(", ") || "-" }}</p>
							<p class="text-sm text-gray-800"><b>Medicines:</b> {{ d.rounds[0].medicines.map((m) => `${m.drug_name} ${m.dosage}`).join(", ") || "-" }}</p>
							<p class="text-sm text-gray-600">{{ d.rounds[0].encounter_comment }}</p>
						</template>
					</div>
				</div>
			</div>

			<div v-else-if="tab === 'nurse'" class="space-y-3">
				<div v-if="d.can.note && d.can.manage" class="flex justify-end"><Button variant="solid" @click="showNote = true">Add nurse note</Button></div>
				<DataTable :columns="[{ key: 'date', label: 'Date' }, { key: 'owner', label: 'By' }, { key: 'subject', label: 'Note' }]" :rows="d.nurse_notes" empty-text="No nurse notes">
					<template #cell-subject="{ row }"><span class="whitespace-normal">{{ stripHtml(row.subject) }}</span></template>
				</DataTable>
			</div>

			<DataTable v-else-if="tab === 'medication'" :columns="medColumns" :rows="medicationRows" empty-text="No medicines prescribed" />

			<DataTable v-else-if="tab === 'register'" :columns="roundColumns" :rows="d.rounds" empty-text="No ward rounds yet">
				<template #cell-encounter_date="{ row }">{{ row.encounter_date }} {{ row.encounter_time }}</template>
				<template #cell-diagnoses="{ row }"><span class="whitespace-normal">{{ row.diagnoses.join(", ") || "-" }}</span></template>
				<template #cell-encounter_comment="{ row }"><span class="whitespace-normal">{{ row.encounter_comment || "-" }}</span></template>
			</DataTable>

			<DataTable v-else-if="tab === 'labs'" :columns="labColumns" :rows="d.labs" empty-text="No lab tests during this stay">
				<template #cell-status="{ row }">
					<Badge :label="row.docstatus === 1 ? 'Completed' : row.status || 'Draft'" :theme="row.docstatus === 1 ? 'green' : 'orange'" variant="subtle" />
				</template>
			</DataTable>

			<OperationsPanel v-else-if="tab === 'operations'" :patient="d.patient.name" :record="record" :default-surgeon="d.stay.practitioner" :editable="d.can.manage" />

			<DataTable v-else-if="tab === 'charges'" :columns="chargeColumns" :rows="d.charges" empty-text="No charges yet">
				<template #footer>
					<div class="flex justify-end gap-6 border-t px-4 py-2.5 text-sm">
						<span class="text-gray-600">{{ d.billing.invoice ? `Final bill ${d.billing.invoice}` : "Running bill" }}</span>
						<span class="font-semibold tabular-nums">{{ formatCurrency(d.billing.total) }}</span>
					</div>
				</template>
			</DataTable>

			<div v-else-if="tab === 'payments'" class="space-y-3">
				<div class="flex flex-wrap items-center gap-4 rounded-lg border bg-white px-4 py-3 text-sm">
					<span>Bill <b class="tabular-nums">{{ formatCurrency(d.billing.total) }}</b></span>
					<span>Paid <b class="tabular-nums text-green-700">{{ formatCurrency(d.billing.paid) }}</b></span>
					<Button v-if="d.can.pay && d.can.manage" class="ml-auto" variant="solid" @click="showAdvance = true">Add advance</Button>
				</div>
				<DataTable :columns="payColumns" :rows="d.payments" empty-text="No payments yet" />
			</div>

			<SoonPanel v-else-if="tab === 'live'" title="Live consultation" description="Video consultation between the ward and a specialist doctor, linked to this admission." />

			<DataTable v-else-if="tab === 'beds'" :columns="bedColumns" :rows="d.beds" empty-text="No bed history">
				<template #cell-check_in="{ row }">{{ String(row.check_in || "").slice(0, 16) }}</template>
				<template #cell-check_out="{ row }">{{ row.current ? "Current" : String(row.check_out || "").slice(0, 16) }}</template>
			</DataTable>

			<Timeline v-else-if="tab === 'timeline'" :patient="d.patient.name" :entries="timeline.data" :can-add="d.can.note" @added="timeline.reload()" />

			<VitalsTable v-else-if="tab === 'vitals'" :rows="d.vitals" />

			<ConsultationDialog v-model="showRound" round :record="record" @saved="stay.reload()" />
			<VitalsDialog v-model="showVitals" :record="record" @saved="stay.reload()" />
			<NoteDialog v-model="showNote" title="Add nurse note" url="hospital_saas.api.ipd.add_nurse_note" :params="{ record }" success="Nurse note added" @saved="stay.reload()" />
			<TransferDialog v-model="showTransfer" :record="record" :current="d.stay.bed" @saved="stay.reload()" />
			<DischargeDialog v-model="showDischarge" :record="record" :billing="d.billing" @saved="stay.reload()" />
			<AdvanceDialog v-model="showAdvance" :record="record" @saved="stay.reload()" />
		</template>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { Badge, Button, createResource, Dropdown, ErrorMessage, FeatherIcon, LoadingIndicator } from "frappe-ui"
import AdvanceDialog from "@/components/AdvanceDialog.vue"
import ConsultationDialog from "@/components/ConsultationDialog.vue"
import DataTable from "@/components/DataTable.vue"
import DischargeDialog from "@/components/DischargeDialog.vue"
import InfoGrid from "@/components/InfoGrid.vue"
import NoteDialog from "@/components/NoteDialog.vue"
import OperationsPanel from "@/components/OperationsPanel.vue"
import PatientHeader from "@/components/PatientHeader.vue"
import SoonBadge from "@/components/SoonBadge.vue"
import SoonPanel from "@/components/SoonPanel.vue"
import TabBar from "@/components/TabBar.vue"
import Timeline from "@/components/Timeline.vue"
import TransferDialog from "@/components/TransferDialog.vue"
import VitalsDialog from "@/components/VitalsDialog.vue"
import VitalsTable from "@/components/VitalsTable.vue"
import { formatCurrency } from "@/utils"

const props = defineProps({ record: { type: String, required: true } })
const tab = ref("overview")
const showRound = ref(false)
const showVitals = ref(false)
const showNote = ref(false)
const showTransfer = ref(false)
const showDischarge = ref(false)
const showAdvance = ref(false)

const stay = createResource({ url: "hospital_saas.api.ipd.get_stay", makeParams: () => ({ record: props.record }), auto: true })
const timeline = createResource({ url: "hospital_saas.api.opd.get_patient_timeline", makeParams: () => ({ patient: stay.data.patient.name }) })
watch(tab, (t) => t === "timeline" && timeline.reload())
watch(() => props.record, () => {
	tab.value = "overview"
	stay.reload()
})

const d = computed(() => stay.data)
const stripHtml = (html) => new DOMParser().parseFromString(html || "", "text/html").body.textContent
const paidPct = computed(() => (d.value.billing.total ? Math.min(100, Math.round((d.value.billing.paid / d.value.billing.total) * 100)) : 100))
const headerFacts = computed(() => [d.value.stay.name, d.value.stay.bed, `Dr. ${d.value.stay.consultant}`, `Day ${d.value.stay.los}`])

const actions = computed(() => {
	const c = d.value.can
	if (!c.manage) return []
	const list = []
	if (c.vitals) list.push({ label: "Record vitals", icon: "heart", onClick: () => (showVitals.value = true) })
	if (c.note) list.push({ label: "Add nurse note", icon: "file-text", onClick: () => (showNote.value = true) })
	if (c.pay) list.push({ label: "Add advance", icon: "credit-card", onClick: () => (showAdvance.value = true) })
	list.push({ label: "Transfer bed", icon: "repeat", onClick: () => (showTransfer.value = true) })
	list.push({ label: "Discharge", icon: "log-out", onClick: () => (showDischarge.value = true) })
	return list
})

const admissionInfo = computed(() => [
	{ label: "IPD No", value: d.value.stay.name },
	{ label: "Admission date", value: String(d.value.stay.admitted || "").slice(0, 16) },
	{ label: "Bed", value: `${d.value.stay.bed || "-"}${d.value.stay.bed_type ? ` (${d.value.stay.bed_type})` : ""}` },
	{ label: "Length of stay", value: `${d.value.stay.los} days (expected ${d.value.stay.expected_length_of_stay || "-"})` },
	{ label: "Consultant", value: d.value.stay.consultant },
	{ label: "Department", value: d.value.stay.department },
	{ label: "Allergies", value: d.value.patient.allergies },
	{ label: d.value.stay.status === "Discharged" ? "Discharged" : "Admission note", value: d.value.stay.status === "Discharged" ? String(d.value.stay.discharged || "").slice(0, 16) : d.value.stay.admission_note },
])

const tabs = computed(() => [
	{ key: "overview", label: "Overview", icon: "grid" },
	{ key: "nurse", label: "Nurse Notes", icon: "file-text", count: d.value.nurse_notes.length },
	{ key: "medication", label: "Medication", icon: "package" },
	{ key: "register", label: "Consultant Register", icon: "clipboard", count: d.value.rounds.length },
	{ key: "labs", label: "Lab Investigation", icon: "droplet" },
	{ key: "operations", label: "Operations", icon: "scissors" },
	{ key: "charges", label: "Charges", icon: "file-text" },
	{ key: "payments", label: "Payments", icon: "credit-card" },
	{ key: "live", label: "Live Consultation", icon: "video", soon: true },
	{ key: "beds", label: "Bed History", icon: "layers" },
	{ key: "timeline", label: "Timeline", icon: "clock" },
	{ key: "vitals", label: "Vitals", icon: "heart" },
])

const medicationRows = computed(() =>
	d.value.rounds.flatMap((r) => r.medicines.map((m) => ({ ...m, date: r.encounter_date, doctor: r.practitioner_name }))),
)
const medColumns = [
	{ key: "date", label: "Date" },
	{ key: "drug_name", label: "Medicine" },
	{ key: "dosage", label: "Dose" },
	{ key: "period", label: "Duration" },
	{ key: "doctor", label: "Prescribed by" },
]
const roundColumns = [
	{ key: "encounter_date", label: "Date" },
	{ key: "practitioner_name", label: "Doctor" },
	{ key: "diagnoses", label: "Diagnosis" },
	{ key: "encounter_comment", label: "Instruction" },
]
const labColumns = [
	{ key: "lab_test_name", label: "Test" },
	{ key: "date", label: "Date" },
	{ key: "practitioner_name", label: "Ordered by" },
	{ key: "status", label: "Status" },
]
const chargeColumns = [
	{ key: "date", label: "Date" },
	{ key: "description", label: "Charge" },
	{ key: "category", label: "Category" },
	{ key: "qty", label: "Qty" },
	{ key: "rate", label: "Rate", format: "currency" },
	{ key: "amount", label: "Amount", format: "currency" },
]
const payColumns = [
	{ key: "name", label: "Receipt" },
	{ key: "posting_date", label: "Date" },
	{ key: "mode_of_payment", label: "Mode" },
	{ key: "reference_no", label: "Reference" },
	{ key: "amount", label: "Amount", format: "currency" },
]
const bedColumns = [
	{ key: "bed", label: "Bed" },
	{ key: "type", label: "Type" },
	{ key: "check_in", label: "From" },
	{ key: "check_out", label: "To" },
]
</script>
