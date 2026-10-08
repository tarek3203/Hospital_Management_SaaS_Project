# Hospital Management SaaS — Plan

Source: `Hospital_Management_SaaS_Project_Proposal.pdf`. Built on Frappe v16 with
ERPNext, HRMS and Frappe Health (Marley) plus our app `hospital_saas`.

## Architecture decisions

- **Tenancy:** one Frappe site per hospital (database-level isolation).
- **Branches:** ERPNext `Branch` + per-branch service-unit trees, warehouses and
  practitioner schedules. A Company per branch is possible later if separate
  books are required.
- **Configurability:** Customize Form / Custom Fields, Workflow, Report Builder,
  Dashboards, Notifications and Role Permission Manager cover the proposal's
  form builder, approval engine, report builder and RBAC requirements.
- **Custom code** lives only in `apps/hospital_saas`; upstream apps are not forked.

## Stage 0 — Client demo ✅

- [x] Docker stack (Frappe v16, ERPNext, HRMS, Healthcare, our app)
- [x] Branding (name, logo, colours)
- [x] Demo data: company, branches, departments, doctors and schedules
- [x] Wards, rooms and beds with live occupancy
- [x] Patients, appointments (past, today, upcoming), encounters, vitals
- [x] Lab tests with results, invoices and payments (Cash/bKash/Nagad/Card)
- [x] Inpatient admissions
- [x] Pharmacy stock, suppliers and purchase orders
- [x] Staff, attendance and role-based demo logins
- [x] Demo walkthrough script (`docs/DEMO_GUIDE.md`)

## Later stages (from the proposal roadmap)

- [ ] 1. SaaS core: site provisioning per hospital, subscription plans, usage limits
- [ ] 2. Clinical hardening: OPD queue/token display, IPD nursing workflows
- [ ] 3. Billing: packages, price lists by patient category/corporate, discount approvals
- [ ] 4. Inventory & procurement approval workflows
- [ ] 5. HR & payroll (BD salary structure)
- [ ] 6. Accounting: branch P&L, investment tracking
- [ ] 7. Lab & radiology report formats, critical-value alerts
- [ ] 8. Custom dashboards per role, report builder templates
- [ ] 9. Integrations: SMS gateway, bKash/Nagad, Bangla localisation
- [ ] 10. Mobile apps and AI features
