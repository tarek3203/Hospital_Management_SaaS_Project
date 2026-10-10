<template>
	<div class="mx-auto max-w-4xl space-y-4 p-4 sm:p-6">
		<nav class="text-xs text-gray-500"><router-link to="/r/surveys" class="hover:text-gray-800">Survey Forms</router-link> / {{ name }}</nav>
		<div v-if="s.data" class="space-y-4">
			<div class="rounded-lg border bg-white p-5">
				<h1 class="text-xl font-semibold text-gray-900">{{ s.data.title }}</h1>
				<p class="text-sm text-gray-600">For {{ s.data.audience.toLowerCase() }} · {{ s.data.responses }} responses{{ s.data.average ? ` · average ${s.data.average} / 5` : "" }}</p>
				<p v-if="s.data.description" class="mt-2 text-sm text-gray-700">{{ s.data.description }}</p>
				<p class="mt-2 flex items-center gap-2 text-xs text-gray-500">Sending to patients by SMS link <SoonBadge /></p>
			</div>
			<div class="rounded-lg border bg-white">
				<div class="flex border-b px-4"><TabBar v-model="tab" :tabs="[{ key: 'fill', label: 'Fill in' }, { key: 'results', label: 'Results' }]" /></div>
				<div v-if="tab === 'fill'" class="space-y-4 p-4">
					<FormControl v-model="respondent" label="Respondent (patient or staff name)" />
					<div v-for="(q, i) in s.data.questions" :key="i">
						<p class="mb-1.5 text-sm text-gray-800">{{ i + 1 }}. {{ q.text }}</p>
						<div class="flex gap-1">
							<button v-for="n in 5" :key="n" type="button" class="h-9 w-9 rounded-md border text-sm font-medium" :class="answers[i] === n ? 'border-brand-600 bg-brand-600 text-white' : 'bg-white text-gray-700 hover:border-brand-500'" @click="answers[i] = n">{{ n }}</button>
						</div>
					</div>
					<FormControl v-model="comment" type="textarea" label="Comment" />
					<ErrorMessage :message="submit.error" />
					<div class="flex justify-end"><Button variant="solid" :disabled="answers.filter(Boolean).length < s.data.questions.length" :loading="submit.loading" @click="send">Submit response</Button></div>
				</div>
				<div v-else class="space-y-3 p-4">
					<div v-for="(q, i) in s.data.questions" :key="i">
						<p class="flex justify-between text-sm"><span class="text-gray-800">{{ q.text }}</span><span class="tabular-nums text-gray-600">{{ q.average ?? "-" }} / 5</span></p>
						<div class="mt-1 h-2 overflow-hidden rounded-full bg-gray-100"><div class="h-full rounded-full bg-brand-500" :style="{ width: `${((q.average || 0) / 5) * 100}%` }" /></div>
					</div>
					<div v-if="s.data.comments.length" class="pt-2">
						<p class="mb-1 text-xs font-medium uppercase tracking-wide text-gray-500">Recent comments</p>
						<p v-for="(c, i) in s.data.comments" :key="i" class="border-b py-1.5 text-sm text-gray-700 last:border-0">"{{ c.comment }}" <span class="text-xs text-gray-500">{{ c.respondent }}, {{ c.response_date }}</span></p>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue"
import { Button, createResource, ErrorMessage, FormControl, toast } from "frappe-ui"
import SoonBadge from "@/components/SoonBadge.vue"
import TabBar from "@/components/TabBar.vue"

const props = defineProps({ name: { type: String, required: true } })
const tab = ref("fill")
const answers = ref([])
const respondent = ref("")
const comment = ref("")
const s = createResource({ url: "hospital_saas.api.registers.get_survey", makeParams: () => ({ name: props.name }), auto: true })
const submit = createResource({
	url: "hospital_saas.api.registers.submit_survey",
	onSuccess() {
		toast.success("Thank you, response saved")
		answers.value = []
		comment.value = ""
		respondent.value = ""
		tab.value = "results"
		s.reload()
	},
})
function send() {
	submit.submit({ name: props.name, answers: answers.value, respondent: respondent.value || null, comment: comment.value || null })
}
</script>
