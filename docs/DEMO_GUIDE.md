# Client Demo Guide — CityCare HMS

URL (local): http://localhost:8080

All demo accounts use the password `Demo@2026`. With demo mode on (see below)
the login page shows a button per role, so visitors never need to type them.

| Login | Role | Person in the story |
| --- | --- | --- |
| `superadmin@citycare.test` | Super Admin | Shafiqul Islam, Managing Director (everything, incl. system settings) |
| `admin@citycare.test` | Admin | Masud Rana, hospital admin |
| `doctor@citycare.test` | Doctor | Prof. Dr. Mahbubul Alam (Cardiology) |
| `pharmacist@citycare.test` | Pharmacist | Anwar Hossain |
| `pathologist@citycare.test` | Pathologist | Hasib Uddin |
| `radiologist@citycare.test` | Radiologist | Tanjila Ahmed |
| `accountant@citycare.test` | Accountant | Selina Parvin |
| `reception@citycare.test` | Receptionist | Rasel Mia |
| `nurse@citycare.test` | Nurse | Rupa Akter |
| `patient@citycare.test` | Patient | A patient with visits, labs and bills (patient portal) |

`Administrator` is the system super user; its password is in `infrastructure/.env`
and is never shown on the demo.

## Public demo mode

1. Load demo data (see `infrastructure/README.md`), then turn demo mode on:

   ```bash
   docker exec hms-backend-1 bench --site hms.localhost set-config hms_demo_mode 1
   ```

2. Save the clean state that resets go back to:

   ```bash
   docker exec hms-backend-1 bash /home/frappe/demo/snapshot.sh
   ```

3. Enable the reset timer: in `infrastructure/.env` set `COMPOSE_PROFILES=demo`
   (and optionally `RESET_INTERVAL_HOURS`), then `up -d` again.

Check every role after a change or a reset:

```bash
python3 infrastructure/demo/smoke_test.py
```

Reset by hand at any time:

```bash
docker exec -e DB_ROOT_PASSWORD=<db root password> hms-backend-1 bash /home/frappe/demo/reset.sh
```

The demo data never goes stale: just after midnight (and after every reset)
all dates in the hospital data move forward so the day the data was generated
for is always today. The seeder records that day as the `hms_demo_anchor`
default. Calendar setup (fiscal years, holiday lists, leave and payroll
periods) is not moved. Weekdays do drift, so a seeded booking can land on a
Friday.

While demo mode is on, demo accounts cannot change their password, email,
roles, role profiles or enabled flag, cannot be renamed or deleted, and
password reset links are refused. Each reset also deletes visitor uploads and
logs everyone out.

Demo Super Admin and Admin use "Demo ..." role profiles without System
Manager, Website Manager, Workspace Manager and Script Manager, because those
roles let a visitor run script in other visitors' browsers (Client Script,
Website Script, custom HTML). Customer installs get the full profiles. Customer installs never set
`hms_demo_mode`, so none of this applies there.

## What's in the data

- One hospital (CityCare General Hospital, BDT, Asia/Dhaka) with two branches: Dhanmondi (Main) and Uttara
- 10 doctors across 10 departments with weekly chambers (Sat–Thu)
- Ward → floor → ward → bed tree per branch, 40 beds/cabins/ICU, ~65% occupied
- 90 patients; 45 days of OPD history, a live queue today and a week of bookings
- Encounters with prescriptions, vitals, 150+ lab tests with results
- Invoices paid by Cash / bKash / Nagad / Card, with some outstanding dues
- Pharmacy stock in two branch stores, reorder levels, supplier purchase orders
- 22 employees with two weeks of attendance

## Suggested 15-minute walkthrough

1. **Dashboard** (admin) — Healthcare home: department-wise appointments,
   patients, admissions, appointments to bill.
2. **Front desk** (reception) — *Patient* → *+ Add* to register a walk-in, then
   *Patient Appointment* → book with a doctor; show the slot picker and today's queue.
3. **Consultation** (doctor) — open a checked-in appointment → *Create Patient
   Encounter*; record vitals, prescribe medicines and order a CBC; submit.
4. **Lab** (lab) — *Lab Test* list → open a draft test, enter results, submit;
   print the report.
5. **Billing** (reception/accounts) — *Sales Invoice* for the patient, take a
   bKash payment; show *Accounts Receivable* for outstanding dues.
6. **Inpatient** — *Healthcare Service Unit* tree for bed occupancy; *Inpatient
   Record* → admit a patient to a vacant bed; transfer/discharge.
7. **Pharmacy & stock** — *Stock Balance* report by branch store; items below
   reorder level; open purchase orders from suppliers.
8. **HR** — employee directory by branch/department; attendance.
9. **Configurability** (the main selling point) — live in front of the client:
   - *Customize Form* on Patient: add a field (e.g. "NID Number"), make it mandatory
   - *Workflow*: an approval rule for discounts or purchase orders
   - *Role Permission Manager*: restrict a role to its branch
   - *Report Builder*: build and save a report in a few clicks

## Resetting the demo

Recreate the site and reload data (wipes everything):

```bash
docker compose -f infrastructure/compose.yaml --env-file infrastructure/.env exec backend bench drop-site hms.localhost --db-root-password admin --force
```

```bash
docker compose -f infrastructure/compose.yaml --env-file infrastructure/.env up -d create-site
```

```bash
docker exec hms-backend-1 bench --site hms.localhost execute hospital_saas.demo.setup.run
```
