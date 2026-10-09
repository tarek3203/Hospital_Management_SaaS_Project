<template>
	<span
		class="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-700 ring-1 ring-amber-200"
		:title="title || 'This feature is coming soon'"
	>
		<FeatherIcon name="clock" class="h-3 w-3" />
		Soon
	</span>
</template>

<script setup>
import { FeatherIcon } from "frappe-ui"

defineProps({ title: String })
</script>
