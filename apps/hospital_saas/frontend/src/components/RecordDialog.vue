<template>
	<Dialog v-model="show" :options="{ title: record?.name ? `${title} ${record.name}` : `New ${title.toLowerCase()}`, size: '3xl' }">
		<template #body-content>
			<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
				<template v-for="f in fields" :key="f.fieldname">
					<LinkInput v-if="f.fieldtype === 'Link' && !f.read_only" v-model="form[f.fieldname]" :doctype="f.options" :label="label(f)" />
					<FormControl
						v-else-if="f.fieldtype === 'Select'"
						v-model="form[f.fieldname]"
						type="select"
						:label="label(f)"
						:options="(f.options || '').split('\n').filter(Boolean)"
						:disabled="!!f.read_only"
					/>
					<FormControl
						v-else-if="['Small Text', 'Text', 'Long Text'].includes(f.fieldtype)"
						v-model="form[f.fieldname]"
						type="textarea"
						:label="label(f)"
						class="sm:col-span-2"
						:disabled="!!f.read_only"
					/>
					<div v-else-if="f.fieldtype === 'Attach'">
						<p class="mb-1.5 text-xs text-gray-600">{{ f.label }}</p>
						<div class="flex items-center gap-2">
							<FileUploader :upload-args="{ private: false }" @success="(file) => (form[f.fieldname] = file.file_url)">
								<template #default="{ openFileSelector, uploading, progress }">
									<Button size="sm" :loading="uploading" @click="openFileSelector()">{{ uploading ? `${progress}%` : "Upload file" }}</Button>
								</template>
							</FileUploader>
							<a v-if="form[f.fieldname]" :href="form[f.fieldname]" target="_blank" rel="noopener" class="truncate text-sm text-brand-600 hover:underline">{{ form[f.fieldname].split("/").pop() }}</a>
						</div>
					</div>
					<FormControl v-else-if="f.fieldtype === 'Check'" v-model="form[f.fieldname]" type="checkbox" :label="f.label" />
					<FormControl
						v-else
						v-model="form[f.fieldname]"
						:type="INPUT_TYPES[f.fieldtype] || 'text'"
						:label="label(f)"
						:disabled="!!f.read_only"
					/>
				</template>
			</div>
			<ErrorMessage class="mt-3" :message="save.error" />
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button @click="show = false">Close</Button>
				<Button v-if="canSave" variant="solid" :loading="save.loading" @click="save.submit({ key: registerKey, data: { ...form } })">Save</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { computed, reactive, watch } from "vue"
import { Button, createResource, Dialog, ErrorMessage, FileUploader, FormControl, toast } from "frappe-ui"
import LinkInput from "@/components/LinkInput.vue"
import { todayISO } from "@/utils"

const show = defineModel({ type: Boolean })
const props = defineProps({ registerKey: String, title: String, fields: Array, record: Object, can: Object })
const emit = defineEmits(["saved"])
const form = reactive({})
const INPUT_TYPES = { Date: "date", Time: "time", Int: "number", Float: "number", Currency: "number", Percent: "number" }
const label = (f) => (f.reqd ? `${f.label} *` : f.label)
const canSave = computed(() => (props.record?.name ? props.can?.write : props.can?.create))

watch(show, (open) => {
	if (!open) return
	Object.keys(form).forEach((k) => delete form[k])
	if (props.record) Object.assign(form, props.record)
	else
		for (const f of props.fields) {
			if (f.default === "Today") form[f.fieldname] = todayISO()
			else if (f.default) form[f.fieldname] = f.fieldtype === "Int" ? Number(f.default) : f.default
			else if (f.fieldtype === "Select") form[f.fieldname] = (f.options || "").split("\n").filter(Boolean)[0]
		}
	save.reset()
})

const save = createResource({
	url: "hospital_saas.api.registers.save_record",
	onSuccess(name) {
		toast.success(`${name} saved`)
		show.value = false
		emit("saved")
	},
})
</script>
