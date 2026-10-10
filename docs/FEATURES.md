# CityCare HMS - Features

What the system does today, module by module, following the Smart Hospital
menu. Built on Frappe v16 (ERPNext, HRMS, Frappe Health) with our app
`hospital_saas`: daily work happens in the `/hms` staff app, setup, accounts
and HR administration in Frappe Desk.

Legend: **Live** works today · **Soon** visible in the product with a Soon
label, planned next.

## Access and roles

- Live: ten role profiles (Super Admin, Admin, Doctor, Pharmacist,
  Pathologist, Radiologist, Accountant, Receptionist, Nurse, Patient), each
  with the Smart Hospital sidebar for that role
- Live: patient portal inside `/hms` for the Patient role
- Live: public demo mode with one-click role logins, locked demo accounts,
  scheduled reset and dates that stay current
- Soon: language switch (Bangla and 8 more), theme studio

## Clinical

| Module | Live | Soon |
| --- | --- | --- |
| Dashboard | Role dashboards (cards, charts, lists) and notice board | |
| Patient | Register, search, profile with history | |
| Appointment | Day view, slot booking with fee and payment, check in/out | |
| OPD | Patient page (6 tabs), visit page, consultation (symptoms, diagnosis, medicines, lab orders, advice), vitals, payments, prescription print | ICD-10 codes, findings |
| IPD | Admission with advance, bed board, ward rounds, nurse notes, vitals, transfer, discharge with final bill | Printable discharge summary |
| Operations | OT bookings with team, anaesthesia, notes, outcome | Consent upload, OT billing |
| Pathology / Radiology | Worklists, result entry, complete, approve, printable report | Sample tracking, image viewer |
| Pharmacy | Prescription-to-bill with stock issue, stock by store, reorder alerts | Batch/expiry, returns, in-app purchase |
| Blood Bank | Stock by group, donors, issue (bag locking), expiry | Component setup, blood billing |
| Ambulance | Vehicles, calls, charges | Ambulance billing |
| Birth & Death | Records and certificates | |

## Administration

| Module | Live | Soon |
| --- | --- | --- |
| Billing | Collections, dues, bills by module, new bill with discount, money receipt | |
| Front Office | Visitors, calls, postal, complaints, website enquiries | |
| Multi Branch | Overview and report per branch | Branch P&L, transfers |
| Human Resource | Attendance with QR kiosk, duty roster, annual calendar, staff ID cards | Camera scanning, roster editing |
| Referral / TPA | Referral persons and commissions, TPA organisations | Per-service TPA rates, claims |
| Finance | Income and expenses posted to the books | |
| Messaging | Notices to staff and patients, notice board | SMS and email gateway |
| Download Center | Shared documents and links | |
| Certificate | Birth/death certificates, patient and staff ID cards | Custom certificate templates |
| Live Consultation | Jitsi meetings with join links | Zoom/Google Meet API |
| Survey Forms | Ratings surveys, results | Sending by SMS |
| Front CMS | Public website, events, gallery, FAQ, testimonials | Maps, instant online booking |
| Reports | 17 reports with date range, CSV, print | Report builder in /hms |
| Setup | Setup hub linking every master | ICD-10, findings, OT types, Zoom/SMS settings |

## Delivery

- One-command install (`infrastructure/install.sh`), upgrade script, daily
  backups, no default passwords. See [INSTALL.md](INSTALL.md).
