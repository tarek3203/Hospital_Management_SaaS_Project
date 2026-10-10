"""Log in as every demo role and check what each one gets.

Run from the host against a running demo site (standard library only):
    python3 infrastructure/demo/smoke_test.py [http://localhost:8080]

Checks per staff role: login lands on /hms, the session reports the right
job, the sidebar has the Smart Hospital item count for that role, and the
dashboard loads. The patient must land on the /hms patient portal.
"""

import http.cookiejar
import json
import sys
import urllib.parse
import urllib.request

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8080"
PASSWORD = "Demo@2026"

# login prefix -> (job, sidebar items in the Smart Hospital demo for that role)
STAFF = {
	"superadmin": ("Super Admin", 27),
	"admin": ("Admin", 27),
	"doctor": ("Doctor", 19),
	"pharmacist": ("Pharmacist", 13),
	"pathologist": ("Pathologist", 13),
	"radiologist": ("Radiologist", 12),
	"accountant": ("Accountant", 21),
	"reception": ("Receptionist", 21),
	"nurse": ("Nurse", 10),
}


def login(user):
	opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
	data = urllib.parse.urlencode({"usr": f"{user}@citycare.test", "pwd": PASSWORD}).encode()
	response = json.load(opener.open(f"{BASE}/api/method/login", data))
	return opener, "/" + (response.get("home_page") or "").strip("/")


def call(opener, method):
	return json.load(opener.open(f"{BASE}/api/method/{method}"))["message"]


def main():
	failures = []
	for user, (job, menu_count) in STAFF.items():
		try:
			opener, home = login(user)
			session = call(opener, "hospital_saas.api.session.get_session")
			dashboard = call(opener, "hospital_saas.api.dashboard.get_dashboard")
			problems = []
			if home != "/hms":
				problems.append(f"home {home}")
			if session["job"] != job:
				problems.append(f"job {session['job']}")
			if len(session["menu"]) != menu_count:
				problems.append(f"menu {len(session['menu'])} != {menu_count}")
			if not dashboard["cards"]:
				problems.append("empty dashboard")
		except Exception as e:  # report every role, do not stop at the first
			problems = [repr(e)]
		print(f"{'FAIL' if problems else 'ok  '} {user:<12} {', '.join(problems)}")
		if problems:
			failures.append(user)

	opener, home = login("patient")
	session = call(opener, "hospital_saas.api.session.get_session")
	portal = call(opener, "hospital_saas.api.portal.get_dashboard")
	ok = home == "/hms" and session["job"] == "Patient" and len(session["menu"]) == 12 and bool(portal["patient"]["name"])
	print(f"{'ok  ' if ok else 'FAIL'} {'patient':<12} home {home}, menu {len(session['menu'])}")
	if not ok:
		failures.append("patient")

	sys.exit(1 if failures else 0)


if __name__ == "__main__":
	main()
