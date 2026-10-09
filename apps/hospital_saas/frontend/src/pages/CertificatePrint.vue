<template>
	<div class="min-h-screen bg-gray-100 py-6 print:bg-white print:py-0">
		<div class="mx-auto mb-4 flex max-w-[210mm] items-center justify-between px-2 print:hidden">
			<Button @click="$router.back()"><template #prefix><FeatherIcon name="arrow-left" class="h-4 w-4" /></template>Back</Button>
			<Button variant="solid" :disabled="!r" @click="print()"><template #prefix><FeatherIcon name="printer" class="h-4 w-4" /></template>Print</Button>
		</div>
		<div v-if="!r" class="py-20 text-center"><LoadingIndicator class="mx-auto h-6 w-6" /></div>
		<article v-else class="mx-auto max-w-[210mm] border-[6px] border-double border-brand-600 bg-white px-14 py-12 text-gray-900 shadow print:shadow-none">
			<div class="text-center">
				<img :src="hospital.logo" class="mx-auto h-14 w-14" alt="" />
				<p class="mt-2 text-xl font-bold text-brand-700">{{ hospital.company }}</p>
				<p class="text-xs text-gray-600">{{ hospital.address }} · {{ hospital.phone }}</p>
				<h1 class="mt-8 font-serif text-3xl font-bold tracking-wide">{{ isBirth ? "Birth Certificate" : "Death Certificate" }}</h1>
				<p class="mt-1 text-xs text-gray-500">Certificate No: {{ r.name }}</p>
			</div>
			<div v-if="isBirth" class="mt-10 space-y-3 text-[15px] leading-relaxed">
				<p>This is to certify that <b>{{ r.child_name }}</b> ({{ r.gender }}) was born at {{ hospital.company }}
					on <b>{{ r.birth_date }}</b>{{ r.birth_time ? ` at ${String(r.birth_time).slice(0, 5)}` : "" }}.</p>
				<p>Mother: <b>{{ r.mother_name }}</b> · Father: <b>{{ r.father_name || "-" }}</b></p>
				<p>Birth weight: {{ r.weight ? `${r.weight} kg` : "-" }} · Delivery: {{ r.delivery_type || "-" }}</p>
				<p v-if="r.address">Address: {{ r.address }}</p>
			</div>
			<div v-else class="mt-10 space-y-3 text-[15px] leading-relaxed">
				<p>This is to certify that <b>{{ r.patient_name }}</b> ({{ r.patient }}) died at {{ hospital.company }}
					on <b>{{ r.death_date }}</b>{{ r.death_time ? ` at ${String(r.death_time).slice(0, 5)}` : "" }}.</p>
				<p>Cause of death: <b>{{ r.cause }}</b></p>
				<p>Guardian: {{ r.guardian_name || "-" }}</p>
			</div>
			<div class="mt-20 flex justify-between text-sm">
				<div class="text-center"><div class="mb-1 w-48 border-b border-gray-400" /><p>Issued on {{ new Date().toLocaleDateString("en-GB") }}</p></div>
				<div class="text-center"><div class="mb-1 w-48 border-b border-gray-400" /><p>Authorised signature</p></div>
			</div>
		</article>
	</div>
</template>

<script setup>
import { computed } from "vue"
import { Button, createResource, FeatherIcon, LoadingIndicator } from "frappe-ui"
import { session } from "@/data/session"

const props = defineProps({ registerKey: String, name: String })
const rec = createResource({ url: "hospital_saas.api.registers.get_record", makeParams: () => ({ key: props.registerKey, name: props.name }), auto: true })
const r = computed(() => rec.data)
const isBirth = computed(() => props.registerKey === "births")
const hospital = computed(() => session.data?.hospital || {})
const print = () => window.print()
</script>
