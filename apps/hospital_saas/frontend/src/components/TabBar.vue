<template>
	<div class="-mb-px flex gap-1 overflow-x-auto border-b">
		<button
			v-for="tab in tabs"
			:key="tab.key"
			class="flex shrink-0 items-center gap-1.5 border-b-2 px-3 py-2.5 text-sm font-medium transition-colors"
			:class="
				modelValue === tab.key
					? 'border-brand-600 text-brand-700'
					: 'border-transparent text-gray-600 hover:border-gray-300 hover:text-gray-900'
			"
			@click="$emit('update:modelValue', tab.key)"
		>
			<FeatherIcon v-if="tab.icon" :name="tab.icon" class="h-4 w-4" />
			{{ tab.label }}
			<span v-if="tab.count != null" class="rounded-full bg-gray-100 px-1.5 text-xs text-gray-600">{{ tab.count }}</span>
			<SoonBadge v-if="tab.soon" />
		</button>
	</div>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"
import SoonBadge from "@/components/SoonBadge.vue"

defineProps({ tabs: { type: Array, required: true }, modelValue: String })
defineEmits(["update:modelValue"])
</script>
