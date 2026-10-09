<template>
	<div class="overflow-hidden rounded-lg border bg-white">
		<div v-if="title" class="border-b bg-gray-50 px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-gray-600">
			{{ title }}
		</div>
		<dl class="grid grid-cols-2 lg:grid-cols-4">
			<div v-for="item in items" :key="item.label" class="border-b border-r px-4 py-3 last:border-r-0">
				<dt class="text-[11px] font-medium uppercase tracking-wide text-gray-500">{{ item.label }}</dt>
				<dd class="mt-0.5 break-words text-sm text-gray-900">{{ item.value || "-" }}</dd>
			</div>
		</dl>
	</div>
</template>

<script setup>
defineProps({ title: String, items: { type: Array, required: true } })
</script>
