export function formatCurrency(value, currency = "BDT") {
	const amount = Number(value || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })
	return currency === "BDT" ? `Tk ${amount}` : `${currency} ${amount}`
}

export function formatValue(value, format, currency) {
	if (value === null || value === undefined || value === "") return "-"
	if (format === "currency") return formatCurrency(value, currency)
	if (format === "number") return Number(value).toLocaleString("en-IN")
	if (format === "datetime") return String(value).slice(0, 16).replace("T", " ")
	return value
}

export const STATUS_THEMES = {
	Scheduled: "blue",
	Open: "blue",
	Confirmed: "blue",
	"Checked In": "orange",
	"Checked Out": "green",
	Closed: "green",
	Completed: "green",
	Approved: "green",
	Admitted: "orange",
	Draft: "gray",
	Cancelled: "red",
	"No Show": "red",
	Rejected: "red",
}

export function todayISO() {
	const d = new Date()
	return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

export function deskUrl(path) {
	return path.startsWith("/desk") ? path : `/desk${path}`
}
