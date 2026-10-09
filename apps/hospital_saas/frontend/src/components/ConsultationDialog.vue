<template>
	<Dialog v-model="show" :options="{ title: 'Consultation', size: '4xl' }">
		<template #body-content>
			<div v-if="!opts.data" class="py-10 text-center"><LoadingIndicator class="mx-auto h-5 w-5" /></div>
			<div v-else class="space-y-5">
				<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
					<TagInput v-model="form.symptoms" label="Symptoms" placeholder="e.g. Fever" :options="opts.data.complaints" />
					<TagInput v-model="form.diagnoses" label="Diagnosis" placeholder="e.g. Dengue Fever" :options="opts.data.diagnoses" />
				</div>

				<div>
					<div class="mb-1.5 flex items-center justify-between">
						<p class="text-xs text-gray-600">Medicines</p>
						<Button size="sm" variant="ghost" @click="addMedicine">
							<template #prefix><FeatherIcon name="plus" class="h-3.5 w-3.5" /></template>
							Add medicine
						</Button>
					</div>
					<div class="overflow-x-auto rounded-md border">
						<table class="w-full text-sm">
							<thead class="bg-gray-50 text-left text-xs text-gray-500">
								<tr>
									<th class="px-2 py-1.5 font-medium">Medicine</th>
									<th class="px-2 py-1.5 font-medium">Dose</th>
									<th class="px-2 py-1.5 font-medium">Duration</th>
									<th class="px-2 py-1.5 font-medium">Form</th>
									<th class="px-2 py-1.5 font-medium">Instruction</th>
									<th />
								</tr>
							</thead>
							<tbody>
								<tr v-if="!form.medicines.length">
									<td colspan="6" class="px-2 py-3 text-center text-gray-500">No medicines prescribed</td>
								</tr>
								<tr v-for="(m, i) in form.medicines" :key="i" class="border-t">
									<td class="p-1.5"><select v-model="m.drug_code" class="cell"><option value="">Select</option><option v-for="o in opts.data.medicines" :key="o.value" :value="o.value">{{ o.label }}</option></select></td>
									<td class="p-1.5"><select v-model="m.dosage" class="cell"><option v-for="o in opts.data.dosages" :key="o" :value="o">{{ o }}</option></select></td>
									<td class="p-1.5"><select v-model="m.period" class="cell"><option v-for="o in opts.data.periods" :key="o" :value="o">{{ o }}</option></select></td>
									<td class="p-1.5"><select v-model="m.dosage_form" class="cell"><option v-for="o in opts.data.dosage_forms" :key="o" :value="o">{{ o }}</option></select></td>
									<td class="p-1.5"><input v-model="m.comment" class="cell" placeholder="After meals" /></td>
									<td class="p-1.5 text-right">
										<button class="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-red-600" @click="form.medicines.splice(i, 1)">
											<FeatherIcon name="trash-2" class="h-4 w-4" />
										</button>
									</td>
								</tr>
							</tbody>
						</table>
					</div>
				</div>

				<div>
					<p class="mb-1.5 text-xs text-gray-600">Lab investigations</p>
					<div class="flex flex-wrap gap-1.5">
						<button
							v-for="t in opts.data.lab_tests"
							:key="t.value"
							type="button"
							class="rounded-full px-3 py-1 text-xs font-medium ring-1 transition-colors"
							:class="hasLab(t.value) ? 'bg-brand-600 text-white ring-brand-600' : 'bg-white text-gray-700 ring-gray-200 hover:bg-gray-50'"
							@click="toggleLab(t.value)"
						>
							{{ t.label }}
						</button>
					</div>
				</div>

				<FormControl v-model="form.notes" type="textarea" label="Advice and notes" :rows="3" />
				<ErrorMessage :message="save.error" />
			</div>
		</template>
		<template #actions>
			<div class="flex flex-wrap justify-end gap-2">
				<Button @click="show = false">Cancel</Button>
				<Button :loading="save.loading && !finishing" @click="submit(0)">Save draft</Button>
				<Button variant="solid" :loading="save.loading && finishing" @click="submit(1)">Save and complete visit</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { reactive, ref, watch } from "vue"
import { Button, createResource, Dialog, ErrorMessage, FeatherIcon, FormControl, LoadingIndicator, toast } from "frappe-ui"
import TagInput from "@/components/TagInput.vue"

const show = defineModel({ type: Boolean })
const props = defineProps({ appointment: String, consultation: Object })
const emit = defineEmits(["saved"])

const opts = createResource({ url: "hospital_saas.api.opd.get_consultation_options", cache: "hms-consultation-options" })
const form = reactive({ symptoms: [], diagnoses: [], medicines: [], lab_tests: [], notes: "" })
const finishing = ref(false)

watch(
	show,
	(open) => {
		if (!open) return
		opts.fetch()
		const c = props.consultation || {}
		form.symptoms = [...(c.symptoms || [])]
		form.diagnoses = [...(c.diagnoses || [])]
		form.medicines = (c.medicines || []).map((m) => ({ ...m }))
		form.lab_tests = (c.lab_tests || []).map((t) => ({ ...t }))
		form.notes = c.notes || ""
		save.reset()
	},
	{ immediate: true },
)

function addMedicine() {
	form.medicines.push({ drug_code: "", dosage: "1-0-1", period: "5 Day", dosage_form: "Tablet", comment: "" })
}
const hasLab = (code) => form.lab_tests.some((t) => t.lab_test_code === code)
function toggleLab(code) {
	form.lab_tests = hasLab(code) ? form.lab_tests.filter((t) => t.lab_test_code !== code) : [...form.lab_tests, { lab_test_code: code }]
}

const save = createResource({
	url: "hospital_saas.api.opd.save_consultation",
	onSuccess() {
		toast.success(finishing.value ? "Consultation completed" : "Draft saved")
		show.value = false
		emit("saved")
	},
})

function submit(complete) {
	finishing.value = !!complete
	save.submit({ appointment: props.appointment, data: { ...form }, submit: complete })
}
</script>

<style scoped>
.cell {
	@apply h-8 w-full min-w-[7rem] rounded border-gray-200 bg-white px-2 text-sm focus:border-brand-500 focus:ring-brand-500;
}
</style>
