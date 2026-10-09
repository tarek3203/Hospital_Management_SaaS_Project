<template>
	<div class="flex flex-wrap items-center gap-4">
		<div
			class="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-brand-600 text-lg font-semibold text-white ring-4 ring-brand-100"
		>
			{{ initials }}
		</div>
		<div class="min-w-0 flex-1">
			<div class="flex flex-wrap items-center gap-2">
				<h1 class="truncate text-xl font-semibold text-gray-900">{{ patient.patient_name }}</h1>
				<Badge :label="badge" :theme="patient.inpatient_status === 'Admitted' ? 'orange' : 'blue'" variant="subtle" />
			</div>
			<div class="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-600">
				<span class="font-mono text-gray-700">{{ patient.name }}</span>
				<span v-for="item in facts" :key="item" class="flex items-center gap-1">{{ item }}</span>
			</div>
		</div>
		<slot name="actions" />
	</div>
</template>

<script setup>
import { computed } from "vue"
import { Badge } from "frappe-ui"

const props = defineProps({ patient: { type: Object, required: true }, extra: { type: Array, default: () => [] } })

const initials = computed(() =>
	props.patient.patient_name
		.split(" ")
		.filter(Boolean)
		.slice(0, 2)
		.map((w) => w[0])
		.join("")
		.toUpperCase(),
)
const badge = computed(() => (props.patient.inpatient_status === "Admitted" ? "IPD" : "OPD"))
const facts = computed(() =>
	[
		[props.patient.sex, props.patient.age != null ? `${props.patient.age} years` : null].filter(Boolean).join(" · "),
		props.patient.mobile,
		...props.extra,
	].filter(Boolean),
)
</script>
