<template>
	<div class="mx-auto max-w-5xl space-y-4 p-4 sm:p-6">
		<div>
			<h1 class="text-xl font-semibold text-gray-900">Annual calendar</h1>
			<p class="text-sm text-gray-600">{{ cal.data?.name }} · weekly off: {{ cal.data?.weekly_off }}</p>
		</div>
		<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
			<div v-for="h in cal.data?.holidays || []" :key="h.holiday_date" class="flex items-center gap-3 rounded-lg border bg-white p-3" :class="h.holiday_date < today ? 'opacity-60' : ''">
				<div class="flex h-12 w-12 shrink-0 flex-col items-center justify-center rounded-lg bg-brand-50 text-brand-700">
					<span class="text-[10px] font-semibold uppercase">{{ month(h.holiday_date) }}</span>
					<span class="text-lg font-bold leading-none">{{ h.holiday_date.slice(8) }}</span>
				</div>
				<div>
					<p class="font-medium text-gray-900">{{ h.description }}</p>
					<p class="text-xs text-gray-500">{{ weekday(h.holiday_date) }}{{ h.holiday_date < today ? " · passed" : "" }}</p>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { createResource } from "frappe-ui"
import { todayISO } from "@/utils"

const today = todayISO()
const cal = createResource({ url: "hospital_saas.api.hr.get_calendar", auto: true })
const month = (d) => new Date(d + "T00:00").toLocaleDateString("en-GB", { month: "short" })
const weekday = (d) => new Date(d + "T00:00").toLocaleDateString("en-GB", { weekday: "long", year: "numeric" })
</script>
