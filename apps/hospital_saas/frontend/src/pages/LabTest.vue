<template>
	<div class="mx-auto max-w-5xl space-y-4 p-4 sm:p-6">
		<nav class="text-xs text-gray-500">
			<router-link :to="back" class="hover:text-gray-800">{{ d?.test.group === "Radiology" ? "Radiology" : "Pathology" }}</router-link>
			<span class="mx-1">/</span><span>{{ name }}</span>
		</nav>
		<div v-if="!d && test.loading" class="py-20 text-center"><LoadingIndicator class="mx-auto h-6 w-6" /></div>
		<ErrorMessage v-else-if="test.error" :message="test.error" />
		<template v-else-if="d">
			<div class="rounded-lg border bg-white p-4 sm:p-5">
				<PatientHeader :patient="d.patient" :extra="[d.test.lab_test_name, `${d.test.date} ${d.test.time || ''}`]">
					<template #actions>
						<div class="flex flex-wrap items-center gap-2">
							<Badge :label="d.test.status" :theme="{ Pending: 'orange', 'Report ready': 'blue', Approved: 'green' }[d.test.status] || 'gray'" variant="subtle" size="lg" />
							<Button v-if="d.test.docstatus === 1" @click="$router.push(`/lab/${encodeURIComponent(name)}/report`)">
								<template #prefix><FeatherIcon name="printer" class="h-4 w-4" /></template>
								Report
							</Button>
							<Button v-if="d.can.approve" variant="solid" :loading="approve.loading" @click="approve.submit({ name })">
								<template #prefix><FeatherIcon name="check" class="h-4 w-4" /></template>
								Approve
							</Button>
						</div>
					</template>
				</PatientHeader>
			</div>

			<div class="rounded-lg border bg-white">
				<div class="flex items-center justify-between border-b px-4 py-3">
					<p class="text-sm font-semibold text-gray-900">{{ d.test.descriptive ? "Report" : "Results" }}</p>
					<p class="text-xs text-gray-500">Referred by {{ d.test.practitioner_name || "-" }}</p>
				</div>
				<div v-if="d.test.descriptive" class="space-y-3 p-4">
					<div v-for="r in results" :key="r.name">
						<p class="mb-1 text-xs font-medium uppercase tracking-wide text-gray-500">{{ r.label }}</p>
						<textarea v-if="d.can.edit" v-model="r.value" rows="3" class="w-full rounded-md border-gray-200 text-sm focus:border-brand-500 focus:ring-brand-500" />
						<p v-else class="whitespace-pre-line text-sm text-gray-900">{{ r.value || "-" }}</p>
					</div>
				</div>
				<table v-else class="w-full text-sm">
					<thead class="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-500">
						<tr><th class="px-4 py-2 font-medium">Test</th><th class="px-4 py-2 font-medium">Result</th><th class="px-4 py-2 font-medium">Unit</th><th class="px-4 py-2 font-medium">Normal range</th></tr>
					</thead>
					<tbody>
						<tr v-for="r in results" :key="r.name" class="border-t">
							<td class="px-4 py-2 text-gray-900">{{ r.label }}</td>
							<td class="px-4 py-2">
								<input v-if="d.can.edit" v-model="r.value" class="h-8 w-32 rounded border-gray-200 text-sm focus:border-brand-500 focus:ring-brand-500" />
								<span v-else class="font-medium">{{ r.value || "-" }}</span>
							</td>
							<td class="px-4 py-2 text-gray-600">{{ r.uom || "" }}</td>
							<td class="px-4 py-2 text-gray-600">{{ r.normal_range || "" }}</td>
						</tr>
					</tbody>
				</table>
				<div class="border-t p-4">
					<FormControl v-if="d.can.edit" v-model="comment" type="textarea" label="Comment" :rows="2" />
					<p v-else-if="d.test.comment" class="text-sm text-gray-700"><b>Comment:</b> {{ d.test.comment }}</p>
					<ErrorMessage class="mt-2" :message="save.error || approve.error" />
				</div>
				<div v-if="d.can.edit" class="flex justify-end gap-2 border-t px-4 py-3">
					<Button :loading="save.loading && !finishing" @click="submit(0)">Save</Button>
					<Button variant="solid" :loading="save.loading && finishing" @click="submit(1)">Save and complete report</Button>
				</div>
			</div>
		</template>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue"
import { Badge, Button, createResource, ErrorMessage, FeatherIcon, FormControl, LoadingIndicator, toast } from "frappe-ui"
import PatientHeader from "@/components/PatientHeader.vue"

const props = defineProps({ name: { type: String, required: true } })
const results = ref([])
const comment = ref("")
const finishing = ref(false)
const test = createResource({
	url: "hospital_saas.api.lab.get_test",
	makeParams: () => ({ name: props.name }),
	auto: true,
	onSuccess(data) {
		results.value = data.results.map((r) => ({ ...r }))
		comment.value = data.test.comment || ""
	},
})
const d = computed(() => test.data)
const back = computed(() => (d.value?.test.group === "Radiology" ? "/radiology" : "/pathology"))
watch(() => props.name, () => test.reload())

const save = createResource({
	url: "hospital_saas.api.lab.save_results",
	onSuccess() {
		toast.success(finishing.value ? "Report completed" : "Saved")
		test.reload()
	},
})
const approve = createResource({
	url: "hospital_saas.api.lab.approve",
	onSuccess() {
		toast.success("Report approved")
		test.reload()
	},
})
function submit(done) {
	finishing.value = !!done
	save.submit({ name: props.name, results: results.value, comment: comment.value, submit: done })
}
</script>
