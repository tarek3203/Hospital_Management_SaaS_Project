// Imported first in main.js: resources created at import time (data/session.js)
// must already use frappeRequest.
import { setConfig, frappeRequest } from "frappe-ui"

setConfig("resourceFetcher", frappeRequest)
