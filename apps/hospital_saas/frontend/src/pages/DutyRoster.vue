<template>
	<div class="mx-auto max-w-7xl space-y-4 p-4 sm:p-6">
		<div class="flex flex-wrap items-center gap-3">
			<div class="flex-1">
				<h1 class="text-xl font-semibold text-gray-900">Duty roster</h1>
				<p class="text-sm text-gray-600">Week of {{ roster.data?.days[0] }}</p>
			</div>
			<Button size="sm" @click="shift(-7)"><FeatherIcon name="chevron-left" class="h-4 w-4" /></Button>
			<Button size="sm" @click="shift(0, true)">This week</Button>
			<Button size="sm" @click="shift(7)"><FeatherIcon name="chevron-right" class="h-4 w-4" /></Button>
		</div>
		<div class="flex flex-wrap gap-3 text-xs">
			<span v-for="s in roster.data?.shifts || []" :key="s.name" class="flex items-center gap-1.5">
				<span class="h-3 w-3 rounded" :class="COLORS[s.color] || 'bg-gray-400'" />{{ s.name }} {{ s.time }}
			</span>
			<span class="flex items-center gap-2 text-gray-500">Drag-and-drop roster editing <SoonBadge /></span>
		</div>
		<div class="overflow-x-auto rounded-lg border bg-white">
			<table class="w-full text-sm">
				<thead class="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-500">
					<tr>
						<th class="px-4 py-2 font-medium">Staff</th>
						<th v-for="d in roster.data?.days || []" :key="d" class="px-2 py-2 text-center font-medium" :class="d === today ? 'text-brand-700' : ''">
							{{ new Date(d + "T00:00").toLocaleDateString("en-GB", { weekday: "short", day: "numeric" }) }}
						</th>
					</tr>
				</thead>
				<tbody>
					<tr v-if="!roster.data?.rows.length"><td colspan="8" class="px-4 py-8 text-center text-gray-500">No shifts assigned this week</td></tr>
					<tr v-for="r in roster.data?.rows || []" :key="r.employee" class="border-t">
						<td class="px-4 py-2">
							<p class="font-medium text-gray-900">{{ r.employee_name }}</p>
							<p class="text-xs text-gray-500">{{ r.department }}</p>
						</td>
						<td v-for="d in roster.data.days" :key="d" class="px-1 py-1.5 text-center">
							<span v-if="r.days[d]" class="inline-block w-full rounded px-1 py-1 text-xs font-medium text-white" :class="COLORS[shiftColor(r.days[d])] || 'bg-gray-400'">{{ r.days[d] }}</span>
							<span v-else class="text-xs text-gray-400">Off</span>
						</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue"
import { Button, createResource, FeatherIcon } from "frappe-ui"
import SoonBadge from "@/components/SoonBadge.vue"
import { todayISO } from "@/utils"

const today = todayISO()
const start = ref(today)
const COLORS = { Green: "bg-green-600", Blue: "bg-blue-500", Violet: "bg-violet-500", Orange: "bg-orange-500", Red: "bg-red-500" }
const roster = createResource({ url: "hospital_saas.api.hr.get_roster", makeParams: () => ({ start: start.value }), auto: true })
const shiftColor = (name) => roster.data.shifts.find((s) => s.name === name)?.color
function shift(days, reset = false) {
	const d = new Date((reset ? today : roster.data.days[0]) + "T00:00")
	d.setDate(d.getDate() + days)
	start.value = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
	roster.reload()
}
</script>
