<template>
	<div class="mx-auto max-w-7xl space-y-4 p-4 sm:p-6">
		<nav class="text-xs text-gray-500">
			<router-link to="/opd" class="hover:text-gray-800">OPD</router-link>
			<span class="mx-1">/</span>
			<router-link v-if="data" :to="`/opd/patient/${encodeURIComponent(data.patient.name)}`" class="hover:text-gray-800">{{ data.patient.patient_name }}</router-link>
			<span class="mx-1">/</span>
			<span>{{ appointment }}</span>
		</nav>

		<div v-if="visit.loading && !data" class="flex justify-center py-20"><LoadingIndicator class="h-6 w-6 text-brand-600" /></div>
		<ErrorMessage v-else-if="visit.error" :message="visit.error" />

		<template v-else-if="data">
			<div class="rounded-lg border bg-white p-4 sm:p-5">
				<PatientHeader :patient="data.patient" :extra="[data.visit.name, `Dr. ${data.visit.practitioner_name}`]">
					<template #actions>
						<div class="flex flex-wrap gap-2">
							<Button v-if="data.can.vitals" @click="showVitals = true">
								<template #prefix><FeatherIcon name="heart" class="h-4 w-4" /></template>
								Record vitals
							</Button>
							<Button v-if="data.can.consult && !completed" variant="solid" @click="showConsult = true">
								<template #prefix><FeatherIcon name="edit-3" class="h-4 w-4" /></template>
								{{ data.consultation ? "Continue consultation" : "Start consultation" }}
							</Button>
						</div>
					</template>
				</PatientHeader>
				<div class="mt-4"><TabBar v-model="tab" :tabs="tabs" /></div>
			</div>

			<!-- Overview -->
			<div v-if="tab === 'overview'" class="space-y-4">
				<InfoGrid title="Visit" :items="visitInfo" />
				<div class="rounded-lg border bg-white p-4">
					<p class="mb-3 text-sm font-semibold text-gray-900">Payment and billing</p>
					<div class="flex items-center justify-between text-sm">
						<span class="text-gray-600">OPD</span>
						<span class="tabular-nums text-gray-900">{{ paidPct }}% · {{ formatCurrency(data.billing.paid) }} / {{ formatCurrency(data.billing.total) }}</span>
					</div>
					<div class="mt-1.5 h-2 overflow-hidden rounded-full bg-gray-100">
						<div class="h-full rounded-full bg-brand-500" :style="{ width: `${paidPct}%` }" />
					</div>
				</div>
				<div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
					<div class="rounded-lg border border-red-100 bg-white">
						<p class="flex items-center gap-2 rounded-t-lg bg-red-50 px-4 py-2.5 text-sm font-semibold text-red-700">
							<FeatherIcon name="alert-circle" class="h-4 w-4" /> Known allergies and findings
						</p>
						<div class="space-y-3 p-4 text-sm">
							<div><p class="label">Allergies</p><p class="text-gray-800">{{ data.patient.allergies || "None recorded" }}</p></div>
							<div><p class="label">Symptoms</p><p class="text-gray-800">{{ c?.symptoms.join(", ") || "-" }}</p></div>
							<div><p class="label">Diagnosis</p><p class="text-gray-800">{{ c?.diagnoses.join(", ") || "-" }}</p></div>
						</div>
					</div>
					<div class="rounded-lg border bg-white p-4 text-sm">
						<p class="mb-3 text-sm font-semibold text-gray-900">Consultation</p>
						<template v-if="c">
							<p class="label">Doctor</p>
							<p class="mb-2 text-gray-800">{{ c.practitioner_name }} · {{ c.docstatus === 1 ? "Completed" : "Draft" }}</p>
							<p class="label">Advice</p>
							<p class="text-gray-800">{{ c.notes || "-" }}</p>
						</template>
						<p v-else class="text-gray-500">The doctor has not started the consultation yet.</p>
					</div>
				</div>
			</div>

			<!-- Medication -->
			<DataTable v-else-if="tab === 'medication'" :columns="medColumns" :rows="c?.medicines" empty-text="No medicines prescribed for this visit" />

			<!-- Lab investigation -->
			<div v-else-if="tab === 'labs'" class="space-y-4">
				<DataTable title="Ordered in consultation" :columns="[{ key: 'lab_test_name', label: 'Test' }, { key: 'comment', label: 'Note' }]" :rows="c?.lab_tests" empty-text="No tests ordered" />
				<DataTable title="Tests on this date" :columns="labColumns" :rows="data.labs" empty-text="No lab tests for this visit">
					<template #cell-status="{ row }">
						<Badge :label="row.docstatus === 1 ? 'Completed' : row.status || 'Draft'" :theme="row.docstatus === 1 ? 'green' : 'orange'" variant="subtle" />
					</template>
				</DataTable>
			</div>

			<!-- Charges -->
			<DataTable v-else-if="tab === 'charges'" :columns="chargeColumns" :rows="data.charges" empty-text="No charges billed for this visit">
				<template #footer>
					<div v-if="data.charges.length" class="flex justify-end gap-6 border-t px-4 py-2.5 text-sm">
						<span class="text-gray-600">Total</span>
						<span class="font-semibold tabular-nums">{{ formatCurrency(data.billing.total) }}</span>
					</div>
				</template>
			</DataTable>

			<!-- Payments -->
			<div v-else-if="tab === 'payments'" class="space-y-3">
				<div class="flex flex-wrap items-center gap-4 rounded-lg border bg-white px-4 py-3 text-sm">
					<span>Total <b class="tabular-nums">{{ formatCurrency(data.billing.total) }}</b></span>
					<span>Paid <b class="tabular-nums text-green-700">{{ formatCurrency(data.billing.paid) }}</b></span>
					<span>Due <b class="tabular-nums" :class="data.billing.outstanding ? 'text-red-600' : ''">{{ formatCurrency(data.billing.outstanding) }}</b></span>
					<Button v-if="data.can.pay && data.billing.outstanding > 0" class="ml-auto" variant="solid" @click="showPay = true">Add payment</Button>
				</div>
				<DataTable :columns="payColumns" :rows="data.payments" empty-text="No payments yet" />
			</div>

			<Timeline v-else-if="tab === 'timeline'" :patient="data.patient.name" :entries="timeline.data" :can-add="canNote" @added="timeline.reload()" />
			<VitalsTable v-else-if="tab === 'vitals'" :rows="data.vitals" />

			<ConsultationDialog v-model="showConsult" :appointment="appointment" :consultation="c" @saved="visit.reload()" />
			<VitalsDialog v-model="showVitals" :appointment="appointment" @saved="visit.reload()" />
			<PaymentDialog v-model="showPay" :invoice="data.visit.invoice" :due="data.billing.outstanding" @saved="visit.reload()" />
		</template>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { Badge, Button, createResource, ErrorMessage, FeatherIcon, LoadingIndicator } from "frappe-ui"
import ConsultationDialog from "@/components/ConsultationDialog.vue"
import DataTable from "@/components/DataTable.vue"
import InfoGrid from "@/components/InfoGrid.vue"
import PatientHeader from "@/components/PatientHeader.vue"
import PaymentDialog from "@/components/PaymentDialog.vue"
import TabBar from "@/components/TabBar.vue"
import Timeline from "@/components/Timeline.vue"
import VitalsDialog from "@/components/VitalsDialog.vue"
import VitalsTable from "@/components/VitalsTable.vue"
import { session } from "@/data/session"
import { formatCurrency } from "@/utils"

const props = defineProps({ appointment: { type: String, required: true } })
const tab = ref("overview")
const showConsult = ref(false)
const showVitals = ref(false)
const showPay = ref(false)
const canNote = computed(() => ["Super Admin", "Admin", "Doctor", "Nurse", "Receptionist"].includes(session.data.job))

const visit = createResource({
	url: "hospital_saas.api.opd.get_visit",
	makeParams: () => ({ appointment: props.appointment }),
	auto: true,
})
const timeline = createResource({
	url: "hospital_saas.api.opd.get_patient_timeline",
	makeParams: () => ({ patient: visit.data.patient.name }),
})
watch(tab, (t) => t === "timeline" && timeline.reload())
watch(() => props.appointment, () => {
	tab.value = "overview"
	visit.reload()
})

const data = computed(() => visit.data)
const c = computed(() => data.value?.consultation)
const completed = computed(() => c.value?.docstatus === 1)
const paidPct = computed(() => {
	const b = data.value.billing
	return b.total ? Math.round((b.paid / b.total) * 100) : 0
})
const visitInfo = computed(() => [
	{ label: "OPD No", value: data.value.visit.name },
	{ label: "Date", value: `${data.value.visit.date} ${data.value.visit.time}` },
	{ label: "Consultant", value: data.value.visit.practitioner_name },
	{ label: "Department", value: data.value.visit.department },
	{ label: "Type", value: data.value.visit.appointment_type },
	{ label: "Status", value: data.value.visit.status },
	{ label: "Blood group", value: data.value.patient.blood_group },
	{ label: "Invoice", value: data.value.visit.invoice },
])
const tabs = computed(() => [
	{ key: "overview", label: "Overview", icon: "grid" },
	{ key: "medication", label: "Medication", icon: "package", count: c.value?.medicines.length || 0 },
	{ key: "labs", label: "Lab Investigation", icon: "droplet" },
	{ key: "charges", label: "Charges", icon: "file-text" },
	{ key: "payments", label: "Payments", icon: "credit-card" },
	{ key: "timeline", label: "Timeline", icon: "clock" },
	{ key: "vitals", label: "Vitals", icon: "heart", count: data.value.vitals.length },
])

const medColumns = [
	{ key: "drug_name", label: "Medicine" },
	{ key: "dosage", label: "Dose" },
	{ key: "period", label: "Duration" },
	{ key: "dosage_form", label: "Form" },
	{ key: "comment", label: "Instruction" },
]
const labColumns = [
	{ key: "lab_test_name", label: "Test" },
	{ key: "date", label: "Date" },
	{ key: "practitioner_name", label: "Ordered by" },
	{ key: "status", label: "Status" },
]
const chargeColumns = [
	{ key: "item_name", label: "Charge" },
	{ key: "item_group", label: "Category" },
	{ key: "qty", label: "Qty" },
	{ key: "rate", label: "Rate", format: "currency" },
	{ key: "amount", label: "Amount", format: "currency" },
]
const payColumns = [
	{ key: "name", label: "Receipt" },
	{ key: "posting_date", label: "Date" },
	{ key: "mode_of_payment", label: "Mode" },
	{ key: "reference_no", label: "Transaction ID" },
	{ key: "amount", label: "Amount", format: "currency" },
]
</script>

<style scoped>
.label {
	@apply text-[11px] font-medium uppercase tracking-wide text-gray-500;
}
</style>
