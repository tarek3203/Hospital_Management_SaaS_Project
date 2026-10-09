<template>
	<div class="min-h-screen bg-gray-100 py-6 print:bg-white print:py-0">
		<div class="mx-auto mb-4 flex max-w-[210mm] items-center justify-between px-2 print:hidden">
			<Button @click="$router.back()"><template #prefix><FeatherIcon name="arrow-left" class="h-4 w-4" /></template>Back</Button>
			<Button variant="solid" :disabled="!d" @click="print()"><template #prefix><FeatherIcon name="printer" class="h-4 w-4" /></template>Print</Button>
		</div>
		<div v-if="!d" class="py-20 text-center"><LoadingIndicator class="mx-auto h-6 w-6" /></div>
		<article v-else class="mx-auto max-w-[210mm] bg-white px-10 py-8 text-[13px] text-gray-900 shadow print:shadow-none">
			<header class="flex items-start justify-between border-b-2 border-brand-600 pb-4">
				<div class="flex items-center gap-3">
					<img :src="hospital.logo" class="h-12 w-12" alt="" />
					<div>
						<p class="text-lg font-bold text-brand-700">{{ hospital.company }}</p>
						<p class="text-xs text-gray-600">{{ hospital.address }}</p>
						<p class="text-xs text-gray-600">{{ [hospital.phone, hospital.email].filter(Boolean).join(" · ") }}</p>
					</div>
				</div>
				<p class="text-right text-sm font-semibold uppercase tracking-wide text-brand-700">{{ d.test.group === "Radiology" ? "Radiology report" : "Laboratory report" }}</p>
			</header>
			<section class="mt-4 grid grid-cols-3 gap-x-4 gap-y-1 rounded border px-3 py-2 text-xs">
				<p><span class="text-gray-500">Patient:</span> <b>{{ d.patient.patient_name }}</b></p>
				<p><span class="text-gray-500">ID:</span> {{ d.patient.name }}</p>
				<p><span class="text-gray-500">Age/Sex:</span> {{ d.patient.age ?? "-" }} y / {{ d.patient.sex }}</p>
				<p><span class="text-gray-500">Test No:</span> {{ d.test.name }}</p>
				<p><span class="text-gray-500">Referred by:</span> {{ d.test.practitioner_name || "-" }}</p>
				<p><span class="text-gray-500">Reported:</span> {{ d.test.result_date || d.test.date }}</p>
			</section>
			<h2 class="mt-5 text-center text-base font-semibold underline">{{ d.test.lab_test_name }}</h2>
			<div v-if="d.test.descriptive" class="mt-4 space-y-3">
				<div v-for="r in d.results" :key="r.name">
					<p class="text-xs font-semibold uppercase tracking-wide text-brand-700">{{ r.label }}</p>
					<p class="whitespace-pre-line">{{ r.value || "-" }}</p>
				</div>
			</div>
			<table v-else class="mt-4 w-full">
				<thead><tr class="border-b text-left text-xs uppercase text-gray-500"><th class="py-1.5">Test</th><th class="py-1.5">Result</th><th class="py-1.5">Unit</th><th class="py-1.5">Reference range</th></tr></thead>
				<tbody><tr v-for="r in d.results" :key="r.name" class="border-b border-dashed"><td class="py-1.5">{{ r.label }}</td><td class="py-1.5 font-semibold">{{ r.value }}</td><td class="py-1.5">{{ r.uom }}</td><td class="py-1.5 text-gray-600">{{ r.normal_range }}</td></tr></tbody>
			</table>
			<p v-if="d.test.comment" class="mt-4"><b>Comment:</b> {{ d.test.comment }}</p>
			<footer class="mt-16 flex items-end justify-between text-xs text-gray-600">
				<div class="text-center"><div class="mb-1 w-40 border-b border-gray-400" /><p>Prepared by {{ d.test.submitted_by }}</p></div>
				<div class="text-center"><div class="mb-1 w-40 border-b border-gray-400" /><p>{{ d.test.approved_by ? `Approved by ${d.test.approved_by}` : "Not yet approved" }}</p></div>
			</footer>
		</article>
	</div>
</template>

<script setup>
import { computed } from "vue"
import { Button, createResource, FeatherIcon, LoadingIndicator } from "frappe-ui"
import { session } from "@/data/session"

const props = defineProps({ name: { type: String, required: true } })
const test = createResource({ url: "hospital_saas.api.lab.get_test", makeParams: () => ({ name: props.name }), auto: true })
const d = computed(() => test.data)
const hospital = computed(() => session.data?.hospital || {})
const print = () => window.print()
</script>
