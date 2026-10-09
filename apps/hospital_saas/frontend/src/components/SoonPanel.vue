<template>
	<div class="flex flex-col items-center rounded-lg border border-dashed border-amber-300 bg-amber-50/40 px-6 py-12 text-center">
		<SoonBadge />
		<p class="mt-3 text-sm font-semibold text-gray-900">{{ title }} is coming soon</p>
		<p v-if="description" class="mt-1 max-w-md text-sm text-gray-600">{{ description }}</p>
	</div>
</template>

<script setup>
import SoonBadge from "@/components/SoonBadge.vue"

defineProps({ title: { type: String, required: true }, description: String })
</script>
