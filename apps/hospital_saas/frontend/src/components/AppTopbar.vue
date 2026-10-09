<template>
	<header class="flex h-14 shrink-0 items-center gap-3 border-b bg-white px-4">
		<button class="rounded p-1.5 text-gray-600 hover:bg-gray-100 lg:hidden" @click="$emit('toggle-sidebar')">
			<FeatherIcon name="menu" class="h-5 w-5" />
		</button>

		<div class="relative hidden max-w-md flex-1 sm:block">
			<FeatherIcon name="search" class="pointer-events-none absolute left-2.5 top-2 h-4 w-4 text-gray-400" />
			<input
				v-model="search"
				type="search"
				placeholder="Search patients by name, ID or mobile"
				class="h-8 w-full rounded-md border-0 bg-gray-100 pl-8 pr-3 text-sm placeholder:text-gray-500 focus:bg-white focus:ring-2 focus:ring-brand-500"
				@keydown.enter="searchPatients"
			/>
		</div>
		<div class="flex-1 sm:hidden" />

		<Dropdown v-if="quickActions.length" :options="quickActions" placement="right">
			<Button variant="solid" class="!bg-brand-600 hover:!bg-brand-700">
				<template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
				New
			</Button>
		</Dropdown>

		<Dropdown :options="userMenu" placement="right">
			<button class="flex items-center gap-2 rounded-md p-1 hover:bg-gray-100">
				<Avatar :label="session.data.full_name" :image="session.data.user_image" size="md" />
				<div class="hidden text-left md:block">
					<p class="text-sm font-medium leading-tight text-gray-900">{{ session.data.full_name }}</p>
					<p class="text-xs leading-tight text-gray-500">{{ session.data.job }}</p>
				</div>
			</button>
		</Dropdown>
	</header>
</template>

<script setup>
import { computed, ref } from "vue"
import { useRouter } from "vue-router"
import { Avatar, Button, Dropdown, FeatherIcon } from "frappe-ui"
import { session } from "@/data/session"

defineEmits(["toggle-sidebar"])
const router = useRouter()
const search = ref("")

function hasMenu(key) {
	return session.data.menu.some((m) => m.key === key)
}

const quickActions = computed(() => {
	const actions = []
	if (["Super Admin", "Admin", "Receptionist"].includes(session.data.job))
		actions.push({ label: "Patient", icon: "user-plus", onClick: () => router.push({ path: "/patients", query: { new: 1 } }) })
	if (hasMenu("appointments"))
		actions.push({ label: "Appointment", icon: "calendar", onClick: () => router.push({ path: "/appointments", query: { new: 1 } }) })
	return actions
})

const userMenu = [
	{ label: "Admin and setup (Desk)", icon: "settings", onClick: () => (window.location.href = "/desk") },
	{ label: "Log out", icon: "log-out", onClick: logout },
]

function searchPatients() {
	router.push({ path: "/patients", query: { q: search.value } })
}

async function logout() {
	await fetch("/api/method/logout", { headers: { "X-Frappe-CSRF-Token": window.csrf_token } })
	sessionStorage.clear()
	window.location.href = "/login"
}
</script>
