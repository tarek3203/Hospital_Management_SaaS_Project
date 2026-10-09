<template>
	<div class="rounded-lg border bg-white p-4">
		<div class="mb-3 flex items-center justify-between">
			<p class="text-sm font-semibold text-gray-900">Timeline</p>
			<Button v-if="canAdd" size="sm" @click="showAdd = true">
				<template #prefix><FeatherIcon name="plus" class="h-3.5 w-3.5" /></template>
				Add note
			</Button>
		</div>
		<p v-if="!entries?.length" class="py-6 text-center text-sm text-gray-500">No timeline entries yet</p>
		<ol v-else class="relative ml-2 border-l border-gray-200">
			<li v-for="entry in entries" :key="entry.name" class="mb-5 ml-5">
				<span class="absolute -left-[9px] flex h-[18px] w-[18px] items-center justify-center rounded-full bg-white ring-2" :class="ring(entry.kind)">
					<FeatherIcon :name="icon(entry.kind)" class="h-2.5 w-2.5" />
				</span>
				<p class="text-xs text-gray-500">{{ entry.date }}</p>
				<p class="text-sm font-medium text-gray-900">{{ entry.title }}</p>
				<p v-if="entry.detail" class="text-sm text-gray-600">{{ entry.detail }}</p>
			</li>
		</ol>

		<Dialog v-model="showAdd" :options="{ title: 'Add timeline note' }">
			<template #body-content>
				<FormControl v-model="note" type="textarea" label="Note" :rows="4" />
				<ErrorMessage class="mt-2" :message="addNote.error" />
			</template>
			<template #actions>
				<div class="flex justify-end gap-2">
					<Button @click="showAdd = false">Cancel</Button>
					<Button variant="solid" :loading="addNote.loading" :disabled="!note.trim()" @click="addNote.submit({ patient, note })">Save</Button>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { ref } from "vue"
import { Button, createResource, Dialog, ErrorMessage, FeatherIcon, FormControl, toast } from "frappe-ui"

const props = defineProps({ patient: String, entries: Array, canAdd: Boolean })
const emit = defineEmits(["added"])
const showAdd = ref(false)
const note = ref("")

const addNote = createResource({
	url: "hospital_saas.api.opd.add_timeline_note",
	onSuccess() {
		toast.success("Note added")
		showAdd.value = false
		note.value = ""
		emit("added")
	},
})

const ICONS = { Consultation: "activity", Lab: "droplet", Vitals: "heart", Note: "edit-3" }
const RINGS = { Consultation: "ring-brand-500 text-brand-600", Lab: "ring-purple-400 text-purple-600", Vitals: "ring-red-400 text-red-500", Note: "ring-amber-400 text-amber-600" }
const icon = (k) => ICONS[k] || "file-text"
const ring = (k) => RINGS[k] || "ring-gray-300 text-gray-500"
</script>
