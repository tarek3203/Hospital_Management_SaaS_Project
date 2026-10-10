<template>
	<div class="flex h-full items-center justify-center p-6">
		<div class="max-w-md text-center">
			<div class="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-600">
				<FeatherIcon :name="item?.icon || 'tool'" class="h-6 w-6" />
			</div>
			<div class="mt-4"><SoonBadge /></div>
			<h1 class="mt-2 text-lg font-semibold text-gray-900">{{ item?.label || "This module" }} is coming soon</h1>
			<p class="mt-2 text-sm text-gray-600">
				{{ item?.text || `It is planned for phase ${item?.phase || "-"} of the build.` }}
			</p>
			<Button class="mt-5" @click="$router.push('/')">Back to dashboard</Button>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue"
import { Button, FeatherIcon } from "frappe-ui"
import SoonBadge from "@/components/SoonBadge.vue"
import { session } from "@/data/session"

const props = defineProps({ moduleKey: String })

// Topbar tools that are not menu items.
const EXTRA = {
	chat: { label: "Staff chat", icon: "message-circle", phase: 6, text: "One-to-one and group chat between staff, with live updates." },
	calendar: { label: "Calendar", icon: "calendar", phase: 6, text: "Appointments, operations, meetings and holidays on one calendar, with personal to-dos." },
}
const item = computed(() => {
	if (EXTRA[props.moduleKey]) return EXTRA[props.moduleKey]
	for (const entry of session.data.menu) {
		if (entry.key === props.moduleKey) return entry
		const child = entry.children?.find((c) => c.key === props.moduleKey)
		if (child) return { ...child, icon: entry.icon }
	}
	return null
})
</script>
