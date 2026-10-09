import { createResource } from "frappe-ui"

// Logged-in user, their hospital job and the sidebar menu for that job.
export const session = createResource({
	url: "hospital_saas.api.session.get_session",
	auto: true,
})
