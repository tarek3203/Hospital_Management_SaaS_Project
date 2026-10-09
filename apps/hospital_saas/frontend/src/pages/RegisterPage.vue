<template>
	<div class="mx-auto max-w-7xl space-y-4 p-4 sm:p-6">
		<div class="flex flex-wrap items-center gap-3">
			<div class="flex-1">
				<p class="text-xs text-gray-500">{{ reg.data?.module }}</p>
				<h1 class="text-xl font-semibold text-gray-900">{{ reg.data?.title || "..." }}</h1>
				<p class="text-sm text-gray-600">{{ reg.data?.total ?? "-" }} records</p>
			</div>
			<Button v-if="reg.data?.can.create" variant="solid" @click="open(null)">
				<template #prefix><FeatherIcon name="plus" class="h-4 w-4" /></template>
				Add
			</Button>
		</div>

		<div v-if="reg.data?.stats.rows.length" class="rounded-lg border bg-white p-4">
			<p class="mb-2 text-xs font-medium uppercase tracking-wide text-gray-500">{{ reg.data.stats.label || `By ${labelOf(reg.data.stats.field).toLowerCase()}` }}</p>
			<div class="flex flex-wrap gap-2">
				<div v-for="s in reg.data.stats.rows" :key="s[reg.data.stats.field]" class="min-w-[7rem] rounded-md border px-3 py-2">
					<p class="text-lg font-semibold tabular-nums text-gray-900">{{ s.count }}</p>
					<p class="text-xs text-gray-500">{{ s[reg.data.stats.field] || "Not set" }}</p>
				</div>
			</div>
		</div>

		<div class="max-w-sm">
			<TextInput v-model="search" type="search" placeholder="Search" @update:modelValue="onSearch">
				<template #prefix><FeatherIcon name="search" class="h-4 w-4 text-gray-500" /></template>
			</TextInput>
		</div>

		<DataTable v-if="reg.data" :columns="columns" :rows="reg.data.rows" clickable empty-text="Nothing recorded yet" @row-click="open">
			<template v-if="reg.data.certificate" #actions="{ row }">
				<Button size="sm" variant="ghost" title="Certificate" @click="$router.push(`/r/${registerKey}/${encodeURIComponent(row.name)}/certificate`)">
					<FeatherIcon name="award" class="h-4 w-4" />
				</Button>
			</template>
		</DataTable>
		<div v-else-if="reg.loading" class="py-20 text-center"><LoadingIndicator class="mx-auto h-6 w-6" /></div>
		<ErrorMessage v-else :message="reg.error" />

		<RecordDialog v-if="reg.data" v-model="show" :register-key="registerKey" :title="reg.data.title" :fields="reg.data.fields" :record="current" :can="reg.data.can" @saved="reg.reload()" />
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { Button, createResource, debounce, ErrorMessage, FeatherIcon, LoadingIndicator, TextInput } from "frappe-ui"
import DataTable from "@/components/DataTable.vue"
import RecordDialog from "@/components/RecordDialog.vue"

const props = defineProps({ registerKey: { type: String, required: true } })
const search = ref("")
const show = ref(false)
const current = ref(null)
const reg = createResource({
	url: "hospital_saas.api.registers.get_register",
	makeParams: () => ({ key: props.registerKey, search: search.value }),
	auto: true,
})
watch(() => props.registerKey, () => {
	search.value = ""
	reg.reset()
	reg.reload()
})
const onSearch = debounce(() => reg.reload(), 300)
const labelOf = (fn) => reg.data?.fields.find((f) => f.fieldname === fn)?.label || fn
const BADGE_FIELDS = ["status"]
const columns = computed(() => [
	{ key: "name", label: "ID" },
	...reg.data.columns.map((fn) => {
		const f = reg.data.fields.find((x) => x.fieldname === fn)
		return { key: fn, label: f.label, badge: BADGE_FIELDS.includes(fn), format: f.fieldtype === "Currency" ? "currency" : undefined }
	}),
])
function open(row) {
	current.value = row ? { ...row } : null
	show.value = true
}
</script>
