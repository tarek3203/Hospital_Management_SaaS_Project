# CityCare HMS: Plan

Goal: match the feature set of the CodeCanyon "Smart Hospital" product
(reference demo: https://demo.smart-hospital.in) on our Frappe v16 stack
(ERPNext + HRMS + Frappe Health + custom app `hospital_saas`), sold as a
**single-hospital install** with a public demo where every role can log in.

We copy **features and workflows only**. No code, UI assets, text or branding
from the CodeCanyon product (it is a licensed commercial item).

## Decisions (2026-10-10)

| Topic | Decision |
| --- | --- |
| Codebase | This repo, branch `feature/hybrid-parity` off `develop` |
| UI | **Hybrid**: custom Vue (frappe-ui) screens for daily work, Frappe Desk for setup, accounts, HR, reports |
| Delivery | Single-hospital install (one site per customer, branches inside it). SaaS layer dropped |
| Market / demo data | Bangladesh: BDT, Asia/Dhaka, bKash/Nagad, Bangladeshi names |
| Brand | CityCare HMS |
| Scope | **Every module and feature in the Smart Hospital demo**, nothing deferred (incl. chat, theme studio, multi-language, Zoom) |
| Licence key | Not needed now (we install directly). Design kept in section 10 in case we sell installs we don't control |

## Stage 0 (done 2026-10-09)

Docker stack, branding, demo hospital with 2 branches, doctors, beds,
patients, appointments, encounters, labs, invoices, inpatients, pharmacy,
staff and attendance. See `docs/FEATURES.md`.

## 1. Login check (2026-10-10)

All 10 demo accounts logged in successfully.

| Role | Login | Lands on | Result |
| --- | --- | --- | --- |
| Super Admin | superadmin@gmail.com | /admin/admin/dashboard | OK |
| Admin | jason@gmail.com | /admin/admin/dashboard | OK |
| Doctor | sonia@gmail.com | /admin/admin/dashboard | OK |
| Pharmacist | harry@gmail.com | /admin/admin/dashboard | OK |
| Pathologist | belinat@gmail.com | /admin/admin/dashboard | OK |
| Radiologist | johnhook@gmail.com | /admin/admin/dashboard | OK |
| Accountant | bradf@gmail.com | /admin/admin/dashboard | OK |
| Receptionist | maria@gmail.com | /admin/admin/dashboard | OK |
| Nurse | april@gmail.com | /admin/admin/dashboard | OK |
| Patient | pat1 (separate form at /site/userlogin) | /patient/dashboard | OK |

Staff share one login form; patients use a separate portal login.

## 2. Role menu matrix (from each role's sidebar)

| Module | SA | Adm | Doc | Pharm | Path | Rad | Acct | Rec | Nurse | Patient |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Dashboard | x | x | x | x | x | x | x | x | x | x |
| Patient | x | x | x | x | x | x | x | x | x | |
| Billing | x | x | x | x | x | x | x | x | | |
| Appointment | x | x | x | | | | x | x | | x |
| OPD | x | x | x | x | x | x | x | x | x | x |
| IPD | x | x | x | x | x | x | x | x | x | x |
| Pharmacy | x | x | | x | | | x | x | | x |
| Pathology | x | x | x | | x | | x | x | | x |
| Radiology | x | x | x | | | x | x | x | | x |
| Blood Bank | x | x | x | x | x | | x | x | | x |
| Ambulance | x | x | x | | | | x | x | | x |
| Front Office | x | x | | | | | | x | | |
| Birth & Death | x | x | x | | | | | x | | |
| Multi Branch | x | x | | | | | | | | |
| Human Resource | x | x | x | x | x | x | x | x | x | |
| QR Attendance / Duty Roster / Annual Calendar | x | x | partial | | | | | | | |
| Referral | x | x | | | | | x | | | |
| TPA Management | x | x | x | | | | x | x | | |
| Finance (Income, Expense) | x | x | | | | | x | | | |
| Survey Forms | x | x | | | | | | | | x |
| Messaging | x | x | x | x | x | x | x | x | x | |
| Inventory | x | x | | | | | x | x | | |
| Download Center | x | x | x | x | x | x | x | x | x | x |
| Certificate / ID Cards | x | x | x | | | | | | | |
| Front CMS (public site) | x | x | | | | | | | | |
| Live Consultation / Meeting | x | x | x | x | x | x | x | x | x | x |
| Reports (16 groups) | x | x | most | own | own | own | most | most | few | |
| Setup (charges, bed, masters) | x | x | some | own | own | own | some | some | bed | |
| Custom Fields | x | | | | | | | | | |
| Operations / OT setup | x | | | | | | | | | |

Topbar extras for staff: global search, quick-create menu, chat, calendar,
language switch (9 languages), notifications, survey prompts, theme studio.

Public front site: Home, About, Departments, Doctors, Events, Gallery,
Annual Calendar, FAQ, Testimonials, Contact, Survey Form, Book Appointment.

## 3. Gap analysis against our Frappe stack

Legend: **Have** = works today in Stage 0 · **Config** = exists in Frappe,
needs setup/tailoring · **Build** = new DocTypes/pages in `hospital_saas`.

| Smart Hospital module | Our status | How |
| --- | --- | --- |
| Patient registry, history | Have | Frappe Health Patient |
| Appointment (incl. online booking) | Have / Config | Patient Appointment + Web Form for public booking |
| OPD (visits, prescription, vitals, symptoms) | Have | Patient Encounter, Vital Signs |
| IPD (admission, bed, transfer, discharge) | Have / Config | Inpatient Record; add nurse notes, IPD charges, discharge summary |
| Bed status board | Build | Custom Desk page (visual ward grid) |
| Pathology | Have | Lab Test + templates |
| Radiology | Config / Build | Observation / Clinical Procedure + radiology report templates, image upload |
| Pharmacy billing | Config / Build | POS-style pharmacy bill page on Sales Invoice, batch/expiry |
| Billing (central, all modules) | Config / Build | Unified "bill dashboard" page pulling OPD/IPD/lab/pharmacy dues |
| Blood Bank | Build | Donor, Donation, Blood Bag stock by group/component, Issue, Blood Bank charges |
| Ambulance | Build | Vehicle, Ambulance Call, charges, driver |
| Front Office | Build | Visitor Book, Phone Call Log, Postal Receive/Dispatch, Complaint |
| Birth & Death records | Build | Birth Record, Death Record + certificate print formats |
| Multi Branch | Have / Build | Branch exists; add branch overview dashboard + cross-branch report |
| Human Resource | Have | HRMS Employee, leave, payroll |
| QR Code Attendance | Build | QR per employee + Employee Checkin endpoint |
| Duty Roster | Config | HRMS Shift Type + Shift Assignment, roster report |
| Annual Calendar | Config | Holiday List + calendar view |
| Referral commission | Build | Referral Person, Commission rules, payout |
| TPA / insurance | Build | TPA Organisation, TPA-specific charge rates, claims |
| Income / Expense | Have | ERPNext Journal Entry / Expense heads, simplified forms |
| Inventory (non-medical) | Have | ERPNext Stock |
| Survey Forms | Config / Build | Web Form + staff/patient assignment |
| Messaging (SMS/email/push) | Config / Build | Notification + SMS Settings; BD SMS gateway adapter |
| Download Center | Build | Content (file + type + audience) shared to roles/patients |
| Certificates, Patient/Staff ID cards | Build | Certificate templates + print formats with QR/barcode |
| Front CMS (public website) | Config | Frappe Website: Web Page, Blog, Web Form, Website Settings |
| Live Consultation / Meeting | Build | Jitsi or Zoom/Google Meet integration linked to appointments |
| Operation Theatre | Build | OT Booking, operation types, team, consent, notes |
| Symptoms / ICD-10 / Findings masters | Config / Build | Healthcare Complaint, Diagnosis; ICD-10 import via Code System |
| Hospital Charges (charge types, categories) | Config | Item + Price Lists by patient category / TPA |
| Print header/footer | Have | Letter Head per module |
| Custom Fields | Have | Customize Form |
| Chat | Build | Staff chat on `/hms` (1:1 and group, realtime via Frappe socket.io) |
| Multi-language | Config / Build | Language switcher in topbar; English, Bangla plus the demo's 9 languages (Frappe ships most; our own strings need translation files) |
| Patient portal (11 menus) | Build | Portal pages: appointments, OPD/IPD history, bills, reports, downloads, live consult, pay online |
| Role dashboards | Build | Workspace per role with number cards and charts |
| Reports (16 groups) | Config / Build | Script/Query Reports where built-in ones do not fit |
| Theme studio | Build | Theme settings page on `/hms` (colours, logo, light/dark, sidebar style) |

Roughly: 40% Have, 25% Config, 35% Build.

## 4. Roles

Ten Role Profiles in `apps/hospital_saas/hospital_saas/roles.py`, applied on
install and every `bench migrate`. Each bundles our marker role with the
standard roles that grant the permissions:

| Profile | Marker role | Main standard roles |
| --- | --- | --- |
| Super Admin | Super Admin | System Manager + everything |
| Admin | Hospital Admin | Everything except System Manager |
| Doctor | Physician | Physician |
| Pharmacist | Pharmacist | Stock, Item, Purchase, Sales, Accounts User |
| Pathologist | Pathologist | Laboratory User, LabTest Approver |
| Radiologist | Radiologist | Laboratory User (Radiology module in Phase 2) |
| Accountant | Accountant | Accounts Manager/User, Sales, Purchase |
| Receptionist | Receptionist | Nursing User, Accounts User, Sales User |
| Nurse | Nursing User | Nursing User |
| Patient | Patient | Portal only (`/patient-portal`), no Desk |

Fine-grained permissions are tuned per module as each phase lands. Branch
restriction (User Permission on Branch) comes with the multi-branch work.

## 5. Hybrid UI

```
           Browser
   +--------------+--------------+
   | Custom UI    | Frappe Desk  |
   | (/hms)       | (/desk)      |
   | daily work   | setup, HR,   |
   |              | accounts,    |
   |              | reports      |
   +------+-------+------+-------+
          +-- same API --+
        Frappe backend + MariaDB
```

- **Custom UI (`/hms`)**: Vue 3 + frappe-ui SPA inside `hospital_saas`, the
  same way Frappe CRM and Helpdesk are built. Covers Receptionist, Doctor
  OPD/IPD, Nurse, Pharmacy POS, Pathology/Radiology result entry, Billing
  dashboard, Ambulance, Blood Bank, Front Office, Birth/Death.
- **Desk (`/desk`)**: setup masters, hospital charges, accounts, HR and
  payroll, inventory/procurement, reports, users and permissions, custom
  fields, print formats. Admins reach it from an "Admin / Setup" link.
- Staff land on `/hms` after login; Super Admin, Admin and Accountant can
  switch to Desk. Patients land on the patient portal.

## 6. Public demo mode

So prospects can try every role, like the Smart Hospital demo:

- [x] Site flag `hms_demo_mode` (`bench --site <site> set-config hms_demo_mode 1`).
      Never set on customer installs, so nothing below runs there.
- [x] Login page lists one-click logins for all 10 roles with the shared password
- [x] Demo accounts are locked: password, email, enabled flag and roles cannot be
      changed, and they cannot be deleted
- [x] Scheduled reset: `infrastructure/demo/snapshot.sh` saves the clean
      state, the `demo-reset` compose service (profile `demo`) restores it every
      `RESET_INTERVAL_HOURS` (default 6, takes ~20 s)
- [x] Rolling dates: demo dates shift daily so "today's" queue, admissions and
      appointments always look current
- [ ] Demo data volume per module, added as each module lands (blood bank
      stock, ambulance calls, visitors, births, OT bookings, ...)

**Going live for a customer:** fresh site without `hms_demo_mode` and without
demo data, setup wizard creates their hospital and admin, they add real staff
and assign the same Role Profiles.

## 7. Build phases (hybrid)

Each phase ends with demo data for the new modules, a role login check and a
walkthrough update. Estimates assume one developer with AI assistance.

### Phase 1: Foundation (1.5 weeks)
- [x] 10 Role Profiles, custom roles, extra read permissions
- [x] Demo users for every role, patient portal login
- [x] Demo mode: login page role picker, locked demo accounts, scheduled reset
- [x] Login smoke test for all roles (`infrastructure/demo/smoke_test.py`)
- [x] `/hms` frontend: Vue 3 + frappe-ui + Vite in `apps/hospital_saas/frontend`,
      staff land on `/hms` after login, app shell with per-role sidebar matching
      the Smart Hospital menu counts, topbar search and quick "New" menu
- [x] Role dashboards on `/hms` (cards, charts and lists for all 9 staff jobs)
- [x] Patients (list, search, register) and Appointments (day view, status
      tabs, booking with doctor slots, fee and payment, check in / out / no
      show / cancel)
- [x] Menu items not yet on `/hms` open the matching Desk page, or a "being
      built" page naming the phase
- [x] Rolling demo dates (moved up from Phase 8): every night and after each
      reset, all hospital data dates shift forward so the seeded "today" is
      always today (`hospital_saas/demo/rolling_dates.py`)

### Phase 2: Clinical core (3 weeks)
- [x] OPD list (`/hms/opd`), OPD patient page (overview with medical history,
  allergies, symptoms, diagnoses, consultants; visits; lab investigation;
  treatment history; timeline with notes; vitals) and OPD visit page
  (overview with billing progress, medication, lab investigation, charges,
  payments with "Add payment", timeline, vitals)
- [x] Doctor consultation on the visit: symptoms, diagnosis (free text adds
  new masters), medicines with dose/duration/form/instruction, lab orders,
  advice; save draft or complete the visit
- [x] Record vitals (nurse, receptionist, doctor); patient numbers
  HLC-PAT-YYYY-#####; structured symptoms/diagnoses/allergies in demo data;
  today's queue billed
- [ ] Prescription print, ICD-10 codes and findings masters, radiology orders
- IPD patient page (nurse notes, medication chart, bed transfer, IPD charges,
  discharge summary), visual bed board
- Radiology module (orders, report templates, images)
- Operation Theatre (booking, team, notes)
- Central billing dashboard across OPD, IPD, lab, radiology, pharmacy

### Phase 3: Pharmacy, charges, TPA, referral (2.5 weeks)
- Pharmacy POS bill with batch/expiry and returns
- Hospital Charges: categories, price lists by patient type
- TPA organisations, rates, claims; referral persons and commission payouts

### Phase 4: Support modules (2.5 weeks)
- Blood Bank, Ambulance, Front Office, Birth and Death records
- Certificates, patient and staff ID cards (QR/barcode)

### Phase 5: HR extras and finance (1 week)
- QR attendance, duty roster, annual calendar, simplified income/expense,
  multi-branch overview

### Phase 6: Communication and content (2.5 weeks)
- SMS gateway (BD provider), email, in-app notifications
- Download Center, Survey Forms
- Live Consultation and Live Meeting with Zoom (as in the demo) and Jitsi as a free option
- Staff chat (1:1 and group), calendar with events and to-dos

### Phase 7: Patient portal and public website (2 weeks)
- Patient portal pages to match Smart Hospital's 11 patient menus, online
  payment (bKash/Nagad)
- Public site: departments, doctors, events, gallery, FAQ, contact, booking

### Phase 8: Reports, language, theme, demo polish (3 weeks)
- All 16 report groups
- Language switcher with English, Bangla and the demo's other languages
  (Hindi, Spanish, Indonesian, Portuguese, Arabic with right-to-left, French,
  Turkish, Russian)
- Theme studio
- Final demo data pass, role-by-role regression run

### Phase 9: Packaging for single-hospital install (1.5 weeks)
- One-command Docker install, first-run setup wizard
- Update path with pre-update backup, scheduled backups, admin manual
- Security hardening: no default credentials, strong admin password on
  install, closed DB/Redis ports

**Total: about 21.5 weeks** (full Smart Hospital scope, nothing deferred).

## 8. Verification

- Login script for every role (done in Phase 1), extended to assert each
  role's `/hms` sidebar against the matrix in section 2
- Per-module smoke flow (register, book, consult, bill, pay, ...)
- Demo seeder extended for every module; reset tested after each phase

## 9. Parity checklist

The demo is "done" when every item below exists, has demo data and is
reachable by the same roles as in Smart Hospital (section 2):

Dashboard, Patient, Billing, Appointment, OPD, IPD, Pharmacy, Pathology,
Radiology, Blood Bank, Ambulance, Front Office, Birth & Death Record,
Multi Branch, Human Resource, QR Code Attendance, Duty Roster, Annual
Calendar, Referral, TPA Management, Finance (Income, Expenses), Survey Forms,
Messaging, Inventory, Download Center, Certificate, Patient/Staff ID Card,
Front CMS, Live Consultation, Live Meeting, Reports (16 groups), Setup
(charges, bed, print header/footer, front office, operations, pharmacy,
pathology, radiology, blood bank, symptoms, ICD-10, findings, vitals, Zoom,
finance, HR, referral, appointment, inventory, custom fields), topbar search,
quick-create menu, chat, calendar, language switch, notifications, theme
studio, patient portal, public website with online booking.

## 10. Parked: licence key activation

Not built. Kept here so it can be added quickly if we start selling installs
we do not set up ourselves (resellers, self-install downloads).

**What it is:** CodeCanyon products ask for a purchase code on first run; the
app checks it with the seller before it unlocks. It stops one copy being
installed at many hospitals.

**How we would build it (about 2 to 3 days):**
1. **Licence server** (small separate service we host): stores customers and
   issues licences. Endpoint `POST /activate {key, site_url}` returns a
   licence file.
2. **Licence file**: JSON with hospital name, site URL, expiry date, max
   branches, enabled modules, signed with our private Ed25519 key. The
   public key ships inside `hospital_saas`, so the app verifies offline and
   the file cannot be edited without breaking the signature.
3. **In the app**: a "Licence" settings page (Super Admin only) to paste the
   key; activation stores the file in a Single DocType. A `before_request`
   hook (cached check) blocks `/hms` and `/desk` with a "licence required"
   page when the file is missing, invalid, expired or for another URL.
   14-day grace period after expiry; login, the licence page and backups
   always work.
4. **Demo and our own installs**: skipped when `hms_demo_mode` is on or
   site config has `hms_licence_exempt: 1`.
