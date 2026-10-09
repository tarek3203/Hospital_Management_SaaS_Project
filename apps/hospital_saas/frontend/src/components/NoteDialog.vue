<template>
	<Dialog v-model="show" :options="{ title }">
		<template #body-content>
			<FormControl v-model="text" type="textarea" :label="label" :rows="4" />
			<ErrorMessage class="mt-2" :message="save.error" />
		</template>
		<template #actions>
			<div class="flex justify-end gap-2">
				<Button @click="show = false">Cancel</Button>
				<Button variant="solid" :loading="save.loading" :disabled="!text.trim()" @click="save.submit({ ...params, [field]: text })">Save</Button>
			</div>
		</template>
	</Dialog>
</template>

<script setup>
import { ref, watch } from "vue"
import { Button, createResource, Dialog, ErrorMessage, FormControl, toast } from "frappe-ui"

const show = defineModel({ type: Boolean })
const props = defineProps({
	title: { type: String, default: "Add note" },
	label: { type: String, default: "Note" },
	url: { type: String, required: true },
	params: { type: Object, default: () => ({}) },
	field: { type: String, default: "note" },
	success: { type: String, default: "Saved" },
})
const emit = defineEmits(["saved"])
const text = ref("")
watch(show, (open) => open && (text.value = ""))

const save = createResource({
	url: props.url,
	onSuccess() {
		toast.success(props.success)
		show.value = false
		emit("saved")
	},
})
</script>
