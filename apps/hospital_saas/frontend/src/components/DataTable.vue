<template>
	<div class="overflow-hidden rounded-lg border bg-white">
		<div v-if="title" class="flex items-center justify-between border-b px-4 py-3">
			<p class="text-sm font-semibold text-gray-900">{{ title }}</p>
			<router-link v-if="link" :to="link" class="text-xs font-medium text-brand-600 hover:underline">View all</router-link>
		</div>
		<div class="overflow-x-auto">
			<table class="w-full text-sm">
				<thead>
					<tr class="border-b bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-500">
						<th v-for="col in columns" :key="col.key" class="whitespace-nowrap px-4 py-2 font-medium">{{ col.label }}</th>
						<th v-if="$slots.actions" class="px-4 py-2" />
					</tr>
				</thead>
				<tbody>
					<tr v-if="!rows?.length">
						<td :colspan="columns.length + 1" class="px-4 py-8 text-center text-gray-500">{{ emptyText }}</td>
					</tr>
					<tr
						v-for="(row, i) in rows"
						:key="row.name || i"
						class="border-b last:border-0 hover:bg-gray-50"
						:class="{ 'cursor-pointer': clickable }"
						@click="clickable && $emit('row-click', row)"
					>
						<td v-for="col in columns" :key="col.key" class="whitespace-nowrap px-4 py-2.5 text-gray-800">
							<slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
								<Badge v-if="col.badge" :label="row[col.key]" :theme="STATUS_THEMES[row[col.key]] || 'gray'" variant="subtle" />
								<span v-else>{{ formatValue(row[col.key], col.format) }}</span>
							</slot>
						</td>
						<td v-if="$slots.actions" class="whitespace-nowrap px-4 py-2 text-right" @click.stop>
							<slot name="actions" :row="row" />
						</td>
					</tr>
				</tbody>
			</table>
		</div>
		<slot name="footer" />
	</div>
</template>

<script setup>
import { Badge } from "frappe-ui"
import { STATUS_THEMES, formatValue } from "@/utils"

defineProps({
	title: String,
	link: String,
	columns: { type: Array, required: true },
	rows: Array,
	clickable: Boolean,
	emptyText: { type: String, default: "Nothing here yet" },
})
defineEmits(["row-click"])
</script>
