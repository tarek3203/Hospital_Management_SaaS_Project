<template>
	<div class="min-h-screen bg-gray-100 py-6 print:bg-white print:py-0">
		<div class="mx-auto mb-4 flex max-w-[210mm] items-center justify-between px-2 print:hidden">
			<Button @click="$router.back()">
				<template #prefix><FeatherIcon name="arrow-left" class="h-4 w-4" /></template>
				Back
			</Button>
			<Button variant="solid" :disabled="!data" @click="print">
				<template #prefix><FeatherIcon name="printer" class="h-4 w-4" /></template>
				Print
			</Button>
		</div>

		<div v-if="!data" class="py-20 text-center"><LoadingIndicator class="mx-auto h-6 w-6" /></div>
		<article v-else class="mx-auto flex min-h-[297mm] max-w-[210mm] flex-col bg-white px-10 py-8 text-[13px] text-gray-900 shadow print:min-h-0 print:shadow-none">
			<!-- Letterhead -->
			<header class="flex items-start justify-between border-b-2 border-brand-600 pb-4">
				<div class="flex items-center gap-3">
					<img :src="hospital.logo" class="h-12 w-12" alt="" />
					<div>
						<p class="text-lg font-bold text-brand-700">{{ hospital.company }}</p>
						<p class="text-xs text-gray-600">{{ hospital.address }}</p>
						<p class="text-xs text-gray-600">{{ [hospital.phone, hospital.email].filter(Boolean).join(" · ") }}</p>
					</div>
				</div>
				<div class="text-right">
					<p class="font-semibold">Dr. {{ data.visit.practitioner_name }}</p>
					<p class="text-xs text-gray-600">{{ data.visit.practitioner_designation }}, {{ data.visit.department }}</p>
				</div>
			</header>

			<!-- Patient -->
			<section class="mt-4 grid grid-cols-4 gap-x-4 gap-y-1 rounded border px-3 py-2 text-xs">
				<p class="col-span-2"><span class="text-gray-500">Patient:</span> <b>{{ data.patient.patient_name }}</b></p>
				<p><span class="text-gray-500">ID:</span> {{ data.patient.name }}</p>
				<p><span class="text-gray-500">Date:</span> {{ data.visit.date }}</p>
				<p><span class="text-gray-500">Age/Sex:</span> {{ data.patient.age ?? "-" }} y / {{ data.patient.sex }}</p>
				<p><span class="text-gray-500">Phone:</span> {{ data.patient.mobile }}</p>
				<p><span class="text-gray-500">OPD No:</span> {{ data.visit.name }}</p>
				<p><span class="text-gray-500">Blood group:</span> {{ data.patient.blood_group || "-" }}</p>
			</section>

			<div class="mt-5 grid flex-1 grid-cols-3 gap-6">
				<!-- Left column: findings -->
				<aside class="space-y-4 border-r pr-4 text-xs">
					<div v-if="vitals">
						<p class="heading">Vitals</p>
						<p v-if="vitals.bp_systolic">BP: {{ vitals.bp_systolic }}/{{ vitals.bp_diastolic }} mmHg</p>
						<p v-if="vitals.pulse">Pulse: {{ vitals.pulse }} /min</p>
						<p v-if="vitals.temperature">Temp: {{ vitals.temperature }} F</p>
						<p v-if="vitals.weight">Weight: {{ vitals.weight }} kg</p>
					</div>
					<div>
						<p class="heading">Chief complaints</p>
						<ul class="list-disc pl-4"><li v-for="s in c?.symptoms" :key="s">{{ s }}</li></ul>
					</div>
					<div>
						<p class="heading">Diagnosis</p>
						<ul class="list-disc pl-4"><li v-for="d in c?.diagnoses" :key="d">{{ d }}</li></ul>
					</div>
					<div v-if="data.patient.allergies">
						<p class="heading">Allergies</p>
						<p>{{ data.patient.allergies }}</p>
					</div>
					<div v-if="c?.lab_tests.length">
						<p class="heading">Investigations</p>
						<ul class="list-disc pl-4"><li v-for="t in c.lab_tests" :key="t.lab_test_code">{{ t.lab_test_name || t.lab_test_code }}</li></ul>
					</div>
				</aside>

				<!-- Right: Rx -->
				<section class="col-span-2">
					<p class="font-serif text-3xl font-bold text-brand-700">R<sub class="text-lg">x</sub></p>
					<p v-if="!c?.medicines.length" class="mt-3 text-gray-500">No medicines prescribed.</p>
					<ol class="mt-2 space-y-3">
						<li v-for="(m, i) in c?.medicines" :key="i">
							<p class="font-semibold">{{ i + 1 }}. {{ m.dosage_form }} {{ m.drug_name }}</p>
							<p class="pl-4 text-gray-700">{{ m.dosage }} &nbsp;·&nbsp; {{ m.period }}<span v-if="m.comment"> &nbsp;·&nbsp; {{ m.comment }}</span></p>
						</li>
					</ol>
					<div v-if="c?.notes" class="mt-6">
						<p class="heading">Advice</p>
						<p class="whitespace-pre-line">{{ c.notes }}</p>
					</div>
				</section>
			</div>

			<footer class="mt-10 flex items-end justify-between border-t pt-3 text-xs text-gray-500">
				<p>Printed {{ new Date().toLocaleString("en-GB") }} · {{ hospital.name }}</p>
				<div class="text-center">
					<div class="mb-1 w-48 border-b border-gray-400" />
					<p>Dr. {{ data.visit.practitioner_name }}</p>
				</div>
			</footer>
		</article>
	</div>
</template>

<script setup>
import { computed } from "vue"
import { Button, createResource, FeatherIcon, LoadingIndicator } from "frappe-ui"
import { session } from "@/data/session"

const props = defineProps({ appointment: { type: String, required: true } })
const visit = createResource({ url: "hospital_saas.api.opd.get_visit", makeParams: () => ({ appointment: props.appointment }), auto: true })
const data = computed(() => visit.data)
const c = computed(() => data.value?.consultation)
const vitals = computed(() => data.value?.vitals?.[0])
const hospital = computed(() => session.data?.hospital || {})

function print() {
	window.print()
}
</script>

<style scoped>
.heading {
	@apply mb-1 text-[11px] font-semibold uppercase tracking-wide text-brand-700;
}
@media print {
	@page {
		size: A4;
		margin: 10mm;
	}
}
</style>
