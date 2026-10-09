import frappeUIPreset from "frappe-ui/tailwind"

export default {
	presets: [frappeUIPreset],
	content: [
		"./index.html",
		"./src/**/*.{vue,js,ts}",
		"./node_modules/frappe-ui/src/components/**/*.{vue,js,ts}",
	],
	theme: {
		extend: {
			colors: {
				brand: {
					50: "#effaf7",
					100: "#d6f2ea",
					500: "#12927e",
					600: "#0e7c6b",
					700: "#0b6356",
					900: "#0a2f2a",
				},
			},
		},
	},
}
