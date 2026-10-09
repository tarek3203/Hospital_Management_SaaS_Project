<template>
	<FrappeUIProvider>
		<router-view v-if="session.data && $route.meta.bare" />
		<div v-else-if="session.data" class="flex h-screen overflow-hidden">
			<AppSidebar :open="sidebarOpen" @close="sidebarOpen = false" />
			<div class="flex min-w-0 flex-1 flex-col">
				<AppTopbar @toggle-sidebar="sidebarOpen = !sidebarOpen" />
				<main class="flex-1 overflow-y-auto">
					<router-view />
				</main>
			</div>
		</div>
		<div v-else-if="session.error" class="flex h-screen items-center justify-center p-6">
			<div class="max-w-sm text-center">
				<p class="text-lg font-semibold text-gray-900">Cannot open CityCare HMS</p>
				<p class="mt-2 text-sm text-gray-600">{{ session.error.messages?.[0] || session.error.message }}</p>
				<Button class="mt-4" variant="solid" @click="logout">Log in again</Button>
			</div>
		</div>
		<div v-else class="flex h-screen items-center justify-center">
			<LoadingIndicator class="h-6 w-6 text-brand-600" />
		</div>
	</FrappeUIProvider>
</template>

<script setup>
import { ref } from "vue"
import { Button, FrappeUIProvider, LoadingIndicator } from "frappe-ui"
import AppSidebar from "@/components/AppSidebar.vue"
import AppTopbar from "@/components/AppTopbar.vue"
import { session } from "@/data/session"

const sidebarOpen = ref(false)

function logout() {
	window.location.href = "/login?redirect-to=/hms"
}
</script>
