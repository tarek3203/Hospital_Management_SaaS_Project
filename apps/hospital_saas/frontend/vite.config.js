import path from "path"
import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import frappeui from "frappe-ui/vite"

// Builds into hospital_saas/public/frontend and writes www/hms.html.
// Day to day: `npm run watch`, then open the real site at /hms.
export default defineConfig({
	plugins: [
		frappeui({
			frappeProxy: false,
			lucideIcons: true,
			jinjaBootData: true,
			buildConfig: {
				indexHtmlPath: "../hospital_saas/www/hms.html",
				outDir: path.resolve(__dirname, "../hospital_saas/public/frontend"),
				baseUrl: "/assets/hospital_saas/frontend/",
				sourcemap: false,
			},
		}),
		vue(),
	],
	resolve: {
		alias: { "@": path.resolve(__dirname, "src") },
	},
	optimizeDeps: {
		include: ["feather-icons", "tailwind.config.js"],
	},
})
