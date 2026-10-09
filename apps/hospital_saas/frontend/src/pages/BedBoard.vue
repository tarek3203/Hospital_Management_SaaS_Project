<template>
	<div class="mx-auto max-w-7xl space-y-4 p-4 sm:p-6">
		<div class="flex flex-wrap items-center gap-3">
			<div class="flex-1">
				<h1 class="text-xl font-semibold text-gray-900">Bed status</h1>
				<p class="text-sm text-gray-600">{{ occupied }} of {{ total }} beds occupied · {{ total - occupied }} vacant</p>
			</div>
			<div class="flex items-center gap-3 text-xs text-gray-600">
				<span class="flex items-center gap-1.5"><span class="h-3 w-3 rounded bg-brand-600" /> Occupied</span>
				<span class="flex items-center gap-1.5"><span class="h-3 w-3 rounded border border-gray-300 bg-white" /> Vacant</span>
			</div>
			<FormControl v-model="branch" type="select" :options="branchOptions" class="w-48" />
		</div>
		<div v-if="board.loading && !board.data" class="py-20 text-center"><LoadingIndicator class="mx-auto h-6 w-6" /></div>
		<div v-for="ward in wards" :key="ward.branch + ward.ward" class="rounded-lg border bg-white p-4">
			<div class="mb-3 flex flex-wrap items-baseline gap-2">
				<p class="text-sm font-semibold text-gray-900">{{ ward.ward }}</p>
				<p class="text-xs text-gray-500">{{ ward.branch }} · {{ ward.floor }}</p>
				<p class="ml-auto text-xs text-gray-500">{{ ward.beds.filter((b) => b.status === "Occupied").length }}/{{ ward.beds.length }} occupied</p>
			</div>
			<div class="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-6">
				<button
					v-for="bed in ward.beds"
					:key="bed.name"
					class="flex min-h-[4.5rem] flex-col items-start rounded-md border p-2.5 text-left transition-colors"
					:class="bed.status === 'Occupied' ? 'border-brand-600 bg-brand-600 text-white hover:bg-brand-700' : 'bg-white text-gray-700 hover:border-brand-500'"
					:disabled="!bed.record"
					@click="bed.record && $router.push(`/ipd/${encodeURIComponent(bed.record)}`)"
				>
					<span class="flex w-full items-center gap-1.5 text-xs font-semibold">
						<FeatherIcon name="square" class="h-3.5 w-3.5" />
						{{ bed.label }}
					</span>
					<span class="mt-1 truncate text-xs" :class="bed.status === 'Occupied' ? 'text-white/90' : 'text-gray-400'">
						{{ bed.patient_name || "Vacant" }}
					</span>
					<span v-if="bed.los" class="text-[11px] text-white/70">Day {{ bed.los }}</span>
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue"
import { createResource, FeatherIcon, FormControl, LoadingIndicator } from "frappe-ui"

const board = createResource({ url: "hospital_saas.api.ipd.get_bed_board", auto: true })
const branch = ref("")
const branchOptions = computed(() => [
	{ label: "All branches", value: "" },
	...[...new Set((board.data || []).map((w) => w.branch))].map((b) => ({ label: b, value: b })),
])
const wards = computed(() => (board.data || []).filter((w) => !branch.value || w.branch === branch.value))
const total = computed(() => wards.value.reduce((n, w) => n + w.beds.length, 0))
const occupied = computed(() => wards.value.reduce((n, w) => n + w.beds.filter((b) => b.status === "Occupied").length, 0))
</script>
