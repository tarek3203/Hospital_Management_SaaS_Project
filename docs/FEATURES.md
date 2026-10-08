# CityCare HMS — Current Features

What the system can do **today** (Stage 0 — client demo). It is built on
Frappe v16 with ERPNext, Frappe HR and Frappe Health, plus our custom app
`hospital_saas`.

Legend: ✅ available now · 🟡 available but basic / needs tailoring · ⏳ planned

---

## 1. Hospital & Branches

- ✅ Hospital profile (company, currency **BDT**, timezone **Asia/Dhaka**,
  Bangladesh fiscal year July–June)
- ✅ Multiple branches (demo: **Dhanmondi (Main)** and **Uttara**)
- ✅ Branch-wise bed trees, pharmacy stores and doctor chambers
- ✅ Medical departments (25: Cardiology, Gynaecology, Paediatrics, ENT, …)
- ✅ Product branding: name, logo and colours on login and desk
- ⏳ Separate site per hospital (multi-tenant SaaS onboarding)

## 2. Users, Roles & Security

- ✅ User accounts with login, password policy and session management
- ✅ Role-based access control (each screen and action is permission-controlled)
- ✅ Ready roles: Hospital Admin, Physician, Nursing, Laboratory, Lab Approver,
  Accounts, HR, Stock
- ✅ Restrict users by branch or department (User Permissions)
- ✅ Full audit trail: who changed what and when, with before/after values
- ✅ Two-factor authentication (can be enabled in System Settings)
- 🟡 Dedicated Receptionist role (front desk currently uses combined roles)

## 3. Patient Management

- ✅ Patient registration with auto ID, demographics, blood group, contacts
- ✅ Patient linked to a billing customer automatically
- ✅ Patient history timeline (appointments, encounters, vitals, labs, admissions)
- ✅ Document attachments on any patient record
- 🟡 NID / passport fields (add with Customize Form, no code)

## 4. Appointments & OPD

- ✅ Doctor schedules and time slots (Sat–Thu, morning/evening chambers)
- ✅ Book by doctor, department or service unit; slot availability check
- ✅ Statuses: Scheduled → Open → Checked In → Checked Out / Closed,
  plus Cancelled and No Show
- ✅ Today's queue with position, reschedule and cancel
- ✅ Consultation (Patient Encounter): complaints, diagnosis notes,
  **prescriptions** (dose, duration, form), **lab orders**
- ✅ Vital signs: temperature, pulse, BP, respiratory rate, height, weight, BMI
- ✅ Free follow-up visits within a set number of days
- 🟡 Appointment reminders (SMS/email — needs gateway setup)

## 5. Inpatient (IPD) & Beds

- ✅ Floor → Ward → Room/Bed hierarchy per branch
- ✅ Bed types: General Ward, Private Cabin, ICU (with daily rates)
- ✅ Live bed status: Vacant / Occupied
- ✅ Admission orders, admit to a bed, transfer, discharge
- ✅ Inpatient records with primary doctor, department and expected stay
- 🟡 Bed charges and IPD billing (configured, not yet shown in demo data)
- ⏳ Visual bed-occupancy board

## 6. Laboratory

- ✅ Test catalogue with prices (CBC, FBS, HbA1c, Lipid Profile, Creatinine,
  Dengue NS1, SGPT, TSH)
- ✅ Single and multi-parameter tests with units and normal ranges
- ✅ Lab orders from the doctor's consultation
- ✅ Result entry, completion and approval
- ✅ Printable lab reports
- 🟡 Sample collection tracking (available, not used in demo)
- ⏳ Radiology report templates and critical-value alerts

## 7. Billing & Payments

- ✅ Service catalogue with prices (consultation, lab tests, bed charges)
- ✅ Patient invoices with printing
- ✅ Payments by **Cash, bKash, Nagad, Card** with transaction reference
- ✅ Partial payments and outstanding dues tracking
- ✅ Doctor-wise consultation fees (OPD and IPD visit)
- ✅ Discounts and taxes on invoices
- ⏳ Packages, corporate / patient-category price lists, discount approvals

## 8. Pharmacy & Inventory

- ✅ Medicine master (item, dosage form, price)
- ✅ Multiple stores (one pharmacy per branch)
- ✅ Stock receipt, issue, transfer, stock balance and ledger
- ✅ Reorder levels with low-stock alerts
- ✅ Batch and expiry tracking (can be enabled per item)
- ✅ Stock valuation reports

## 9. Procurement & Suppliers

- ✅ Supplier profiles (demo: Square, Beximco, Incepta)
- ✅ Material request → Purchase order → Goods receipt → Supplier invoice
- ✅ Supplier payables and purchase analytics
- 🟡 Multi-level purchase approval (configure with Workflow)

## 10. HR & Staff

- ✅ Employee records (doctors, nurses, front desk, lab, pharmacy, accounts)
- ✅ Department, designation and branch per employee
- ✅ Daily attendance
- ✅ Leave, shifts, holidays and overtime (available, not seeded)
- 🟡 Payroll (available; Bangladesh salary structure not configured yet)

## 11. Accounting & Finance

- ✅ Chart of accounts, journal entries, general ledger
- ✅ Cash and bank accounts, including bKash / Nagad settlement accounts
- ✅ Accounts receivable and payable
- ✅ Profit & loss, balance sheet, cash flow
- ✅ Expense recording
- ⏳ Branch / department / doctor profitability views, investment tracking

## 12. Dashboards & Reports

- ✅ Healthcare dashboard: department-wise appointments, total patients,
  admissions, open appointments, appointments to bill
- ✅ Hundreds of built-in reports (sales, receivables, stock, HR, accounts)
- ✅ Export to PDF, Excel and CSV
- ✅ Report Builder: create and save custom reports without code
- ⏳ Role-specific dashboards (owner, branch manager, doctor, …)

## 13. Configurability (no code needed)

The proposal's key selling point — these work today from the browser:

- ✅ **Customize Form** — add, rename, reorder, hide or make fields mandatory
- ✅ **Custom Fields** — any type, with conditional show/require logic
- ✅ **Workflow** — multi-level approvals (e.g. discount → manager → finance)
- ✅ **Role Permission Manager** — who can view, create, submit, cancel
- ✅ **Print Format Builder** — design invoice and report layouts
- ✅ **Notifications** — email / system alerts on any event or condition
- ✅ **Naming series** — custom document numbering
- ✅ **Dashboard charts and number cards** — build new widgets

## 14. Demo Data Included

One command loads a realistic hospital:

| Data | Amount |
| --- | --- |
| Branches | 2 |
| Doctors with schedules | 10 |
| Beds / cabins / ICU | 40 (~65% occupied) |
| Patients | 90 |
| Appointments (45 days past, today, next week) | ~290 |
| Consultations with vitals and prescriptions | ~200 |
| Lab tests with results | ~155 |
| Invoices / payments | ~200 / ~180 |
| Pharmacy items with stock | 10 |
| Purchase orders | 3 |
| Staff with attendance | 22 |
| Demo logins (one per role) | 6 |

---

## Not Yet Built (next stages)

See [PLAN.md](../PLAN.md) for the full roadmap.

- ⏳ SaaS layer: self-service hospital onboarding, subscription plans, usage limits
- ⏳ Bangla interface and Bangladesh invoice formats
- ⏳ SMS gateway and online payment (bKash/Nagad API) integration
- ⏳ Packages, price lists by patient category, discount approval rules
- ⏳ Branch-wise profitability and investment management
- ⏳ Mobile apps (doctor, nurse, patient) and AI features
