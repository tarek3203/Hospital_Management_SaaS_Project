<template>
	<Autocomplete
		:model-value="selected"
		:label="label"
		:placeholder="`Search ${doctype.toLowerCase()}`"
		:options="options"
		@update:query="onQuery"
		@update:model-value="(o) => $emit('update:modelValue', o?.value || null)"
	/>
</template>

<script setup>
import { computed, onMounted } from "vue"
import { Autocomplete, createResource, debounce } from "frappe-ui"

const props = defineProps({ modelValue: String, doctype: { type: String, required: true }, label: String })
defineEmits(["update:modelValue"])
const search = createResource({ url: "hospital_saas.api.registers.search_link" })
const onQuery = debounce((txt) => search.submit({ doctype: props.doctype, txt }), 250)
onMounted(() => search.submit({ doctype: props.doctype, txt: "" }))
const options = computed(() => {
	const list = search.data || []
	if (props.modelValue && !list.some((o) => o.value === props.modelValue)) return [{ label: props.modelValue, value: props.modelValue }, ...list]
	return list
})
const selected = computed(() => options.value.find((o) => o.value === props.modelValue) || null)
</script>
