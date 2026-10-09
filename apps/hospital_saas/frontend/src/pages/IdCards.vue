<template>
	<div class="min-h-screen bg-gray-100 py-6 print:bg-white print:py-0">
		<div class="mx-auto max-w-[210mm] space-y-3 px-2 print:hidden">
			<div class="flex items-center justify-between">
				<Button @click="$router.push('/')"><template #prefix><FeatherIcon name="arrow-left" class="h-4 w-4" /></template>Back</Button>
				<p class="text-lg font-semibold text-gray-900">{{ kind === "staff" ? "Staff ID cards" : "Patient ID cards" }}</p>
				<Button variant="solid" :disabled="!cards.data?.length" @click="print()"><template #prefix><FeatherIcon name="printer" class="h-4 w-4" /></template>Print</Button>
			</div>
			<div class="rounded-lg border bg-white p-3">
				<Autocomplete v-model="pick" :placeholder="kind === 'staff' ? 'Add staff member' : 'Add patient'" :options="options" @update:query="onQuery" />
				<div class="mt-2 flex flex-wrap gap-1.5">
					<span v-for="s in selected" :key="s.value" class="flex items-center gap-1 rounded bg-gray-100 px-2 py-0.5 text-sm">
						{{ s.label }} <button class="text-gray-400 hover:text-gray-700" @click="remove(s)"><FeatherIcon name="x" class="h-3 w-3" /></button>
					</span>
					<span v-if="!selected.length" class="text-sm text-gray-500">Pick one or more {{ kind === "staff" ? "staff members" : "patients" }}</span>
				</div>
			</div>
		</div>
		<div class="mx-auto mt-4 grid max-w-[210mm] grid-cols-2 gap-4 px-2 print:mt-0 print:gap-3">
			<div v-for="c in cards.data || []" :key="c.id" class="card flex flex-col overflow-hidden rounded-lg border bg-white shadow-sm print:shadow-none">
				<div class="flex items-center gap-2 bg-brand-600 px-3 py-1.5 text-white">
					<img :src="hospital.logo" class="h-5 w-5 rounded bg-white p-0.5" alt="" />
					<p class="flex-1 truncate text-[11px] font-semibold">{{ hospital.company }}</p>
					<p class="text-[9px] uppercase tracking-wide opacity-90">{{ kind === "staff" ? "Staff" : "Patient" }}</p>
				</div>
				<div class="flex flex-1 gap-2 px-3 py-2">
					<div class="min-w-0 flex-1">
						<p class="truncate text-[13px] font-bold text-gray-900">{{ c.name }}</p>
						<p class="font-mono text-[10px] text-gray-700">{{ c.id }}</p>
						<p class="mt-1 truncate text-[10px] text-gray-600">{{ c.line1 }}</p>
						<p class="truncate text-[10px] text-gray-600">{{ c.line2 }}</p>
						<p class="text-[9px] text-gray-500">Since {{ c.since }}</p>
					</div>
					<div class="qr h-16 w-16 shrink-0" v-html="c.qr" />
				</div>
				<div class="barcode h-6 px-3 pb-1" v-html="c.barcode" />
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { Autocomplete, Button, createResource, debounce, FeatherIcon } from "frappe-ui"
import { session } from "@/data/session"

const props = defineProps({ kind: { type: String, default: "patient" } })
const hospital = computed(() => session.data?.hospital || {})
const pick = ref(null)
const selected = ref([])
const search = createResource({
	url: props.kind === "staff" ? "hospital_saas.api.cards.search_employees" : "hospital_saas.api.patients.search_patients",
})
const onQuery = debounce((txt) => search.submit({ txt }), 250)
const options = computed(() =>
	(search.data || []).map((r) => (props.kind === "staff" ? r : { label: r.patient_name, value: r.name, description: r.name })),
)
const cards = createResource({
	url: props.kind === "staff" ? "hospital_saas.api.cards.staff_cards" : "hospital_saas.api.cards.patient_cards",
	makeParams: () => (props.kind === "staff" ? { employees: selected.value.map((s) => s.value) } : { patients: selected.value.map((s) => s.value) }),
})
watch(pick, (p) => {
	if (p && !selected.value.some((s) => s.value === p.value)) selected.value.push(p)
	pick.value = null
})
watch(selected, () => (selected.value.length ? cards.reload() : cards.reset()), { deep: true })
onQuery("")
function remove(s) {
	selected.value = selected.value.filter((x) => x.value !== s.value)
}
const print = () => window.print()
</script>

<style scoped>
.card {
	width: 85.6mm;
	height: 54mm;
	break-inside: avoid;
}
.qr :deep(svg),
.barcode :deep(svg) {
	width: 100%;
	height: 100%;
}
@media print {
	@page {
		size: A4;
		margin: 10mm;
	}
}
</style>
