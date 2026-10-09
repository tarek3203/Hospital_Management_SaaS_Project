<template>
	<div class="flex items-start gap-3 rounded-lg border bg-white p-4">
		<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
			<FeatherIcon :name="icon || 'bar-chart-2'" class="h-5 w-5" />
		</div>
		<div class="min-w-0">
			<p class="truncate text-sm text-gray-600">{{ label }}</p>
			<p class="mt-0.5 text-xl font-semibold tabular-nums text-gray-900">{{ formatValue(value, format) }}</p>
			<p v-if="hint" class="mt-0.5 text-xs text-gray-500">{{ hint }}</p>
		</div>
	</div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"
import { formatValue } from "@/utils"

defineProps({ label: String, value: [Number, String], icon: String, format: String, hint: String })
</script>
