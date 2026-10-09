<template>
	<div>
		<label v-if="label" class="mb-1.5 block text-xs text-gray-600">{{ label }}</label>
		<div class="flex min-h-[2rem] flex-wrap items-center gap-1.5 rounded-md bg-gray-100 px-2 py-1 focus-within:ring-2 focus-within:ring-brand-500">
			<span v-for="tag in modelValue" :key="tag" class="flex items-center gap-1 rounded bg-white px-2 py-0.5 text-sm text-gray-800 shadow-sm">
				{{ tag }}
				<button type="button" class="text-gray-400 hover:text-gray-700" @click="remove(tag)">
					<FeatherIcon name="x" class="h-3 w-3" />
				</button>
			</span>
			<input
				v-model="text"
				:list="listId"
				:placeholder="modelValue.length ? '' : placeholder"
				class="min-w-[10rem] flex-1 border-0 bg-transparent p-0.5 text-sm focus:ring-0"
				@keydown.enter.prevent="add(text)"
				@keydown.backspace="!text && modelValue.length && remove(modelValue[modelValue.length - 1])"
				@change="onPick"
			/>
			<datalist :id="listId">
				<option v-for="o in available" :key="o" :value="o" />
			</datalist>
		</div>
		<p class="mt-1 text-xs text-gray-500">Pick from the list or type and press Enter</p>
	</div>
</template>

<script setup>
import { computed, ref } from "vue"
import { FeatherIcon } from "frappe-ui"

const props = defineProps({
	modelValue: { type: Array, default: () => [] },
	options: { type: Array, default: () => [] },
	label: String,
	placeholder: String,
})
const emit = defineEmits(["update:modelValue"])
const text = ref("")
const listId = `tags-${Math.random().toString(36).slice(2, 8)}`
const available = computed(() => props.options.filter((o) => !props.modelValue.includes(o)))

function add(value) {
	value = (value || "").trim()
	if (value && !props.modelValue.includes(value)) emit("update:modelValue", [...props.modelValue, value])
	text.value = ""
}
function remove(tag) {
	emit("update:modelValue", props.modelValue.filter((t) => t !== tag))
}
// Choosing a datalist suggestion fires "change" with the full value.
function onPick() {
	if (props.options.includes(text.value)) add(text.value)
}
</script>
