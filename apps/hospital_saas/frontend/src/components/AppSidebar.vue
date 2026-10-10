<template>
	<div v-if="open" class="fixed inset-0 z-30 bg-black/40 lg:hidden" @click="$emit('close')" />
	<aside
		class="fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-brand-900 text-gray-200 transition-transform lg:static lg:translate-x-0"
		:class="open ? 'translate-x-0' : '-translate-x-full'"
	>
		<div class="flex h-14 items-center gap-2.5 border-b border-white/10 px-4">
			<img :src="hospital.logo" class="h-8 w-8 rounded-md bg-white p-1" alt="" />
			<div class="min-w-0">
				<p class="truncate text-sm font-semibold text-white">{{ hospital.name }}</p>
				<p class="truncate text-xs text-gray-400">{{ session.data.job }}</p>
			</div>
		</div>

		<nav class="flex-1 overflow-y-auto px-2 py-3">
			<template v-for="item in menu" :key="item.key">
				<button
					class="group flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm transition-colors"
					:class="isActive(item) ? 'bg-white/10 text-white' : 'text-gray-300 hover:bg-white/5 hover:text-white'"
					@click="onItem(item)"
				>
					<FeatherIcon :name="item.icon" class="h-4 w-4 shrink-0" />
					<span class="flex-1 truncate">{{ item.label }}</span>
					<span
						v-if="!item.children && !item.route && !item.desk"
						class="rounded bg-amber-400/15 px-1.5 text-[10px] font-semibold uppercase tracking-wide text-amber-300"
						>soon</span
					>
					<FeatherIcon
						v-if="item.children"
						name="chevron-down"
						class="h-3.5 w-3.5 shrink-0 transition-transform"
						:class="expanded[item.key] ? '' : '-rotate-90'"
					/>
				</button>
				<div v-if="item.children && expanded[item.key]" class="mb-1 ml-7 border-l border-white/10 pl-2">
					<button
						v-for="child in item.children"
						:key="child.key"
						class="flex w-full items-center gap-2 rounded-md px-3 py-1.5 text-left text-[13px] text-gray-400 hover:bg-white/5 hover:text-white"
						@click="go(child)"
					>
						<span class="flex-1 truncate">{{ child.label }}</span>
						<span
							v-if="!child.route && !child.desk"
							class="rounded bg-amber-400/15 px-1.5 text-[10px] font-semibold uppercase tracking-wide text-amber-300"
							>soon</span
						>
					</button>
				</div>
			</template>
		</nav>

		<a
			v-if="session.data.job !== 'Patient'"
			href="/desk"
			class="flex items-center gap-2 border-t border-white/10 px-5 py-3 text-xs text-gray-400 hover:text-white"
		>
			<FeatherIcon name="settings" class="h-3.5 w-3.5" />
			Admin and setup (Desk)
		</a>
	</aside>
</template>

<script setup>
import { computed, reactive } from "vue"
import { useRoute, useRouter } from "vue-router"
import { FeatherIcon } from "frappe-ui"
import { session } from "@/data/session"

defineProps({ open: Boolean })
const emit = defineEmits(["close"])

const route = useRoute()
const router = useRouter()
const menu = computed(() => session.data.menu)
const hospital = computed(() => session.data.hospital)
const expanded = reactive({})

function isActive(item) {
	if (item.route) return item.route === "/" ? route.path === "/" : route.path.startsWith(item.route)
	if (item.children) return item.children.some((c) => c.route && route.path.startsWith(c.route))
	return route.name === "ComingSoon" && route.params.moduleKey === item.key
}

function onItem(item) {
	if (item.children) {
		expanded[item.key] = !expanded[item.key]
		return
	}
	go(item)
}

// /hms page if built, else the Desk page that covers it, else "being built".
function go(item) {
	emit("close")
	if (item.route) router.push(item.route)
	else if (item.desk) window.location.href = item.desk
	else router.push({ name: "ComingSoon", params: { moduleKey: item.key } })
}
</script>
