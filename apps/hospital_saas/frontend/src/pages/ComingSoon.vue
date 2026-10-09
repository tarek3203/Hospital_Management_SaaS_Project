<template>
	<div class="flex h-full items-center justify-center p-6">
		<div class="max-w-md text-center">
			<div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-600">
				<FeatherIcon :name="item?.icon || 'tool'" class="h-6 w-6" />
			</div>
			<h1 class="mt-4 text-lg font-semibold text-gray-900">{{ item?.label || "This module" }} is being built</h1>
			<p class="mt-2 text-sm text-gray-600">
				It is planned for phase {{ item?.phase || "-" }} of the build. See PLAN.md for what it will include.
			</p>
			<Button class="mt-5" @click="$router.push('/')">Back to dashboard</Button>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue"
import { Button, FeatherIcon } from "frappe-ui"
import { session } from "@/data/session"

const props = defineProps({ moduleKey: String })

const item = computed(() => {
	for (const entry of session.data.menu) {
		if (entry.key === props.moduleKey) return entry
		const child = entry.children?.find((c) => c.key === props.moduleKey)
		if (child) return { ...child, icon: entry.icon }
	}
	return null
})
</script>
