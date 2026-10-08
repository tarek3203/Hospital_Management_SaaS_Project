# Client Demo Guide — CityCare HMS

URL (local): http://localhost:8080

All demo accounts use the password `Demo@2026` (local demo only).

| Login | Role in the story |
| --- | --- |
| `admin.demo@citycare.test` | Hospital admin / owner — sees everything |
| `reception@citycare.test` | Front desk — registration, appointments, billing |
| `doctor@citycare.test` | Prof. Dr. Mahbubul Alam (Cardiology) — encounters, prescriptions |
| `nurse@citycare.test` | Nursing — vitals, inpatient care |
| `lab@citycare.test` | Lab technologist — results and approval |
| `accounts@citycare.test` | Accounts — invoices, payments, receivables |

`Administrator` / `admin` is the system super user; don't use it in front of clients.

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
