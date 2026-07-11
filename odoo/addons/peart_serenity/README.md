# peart_serenity

Custom Odoo 19 module for **Peart Serenity Residence**. This module is the
integration point between the public website and Odoo: it is where the
care service catalog, the admissions pipeline, and (in later releases) the
website API and family portal live.

## What this module installs today

- **Care service catalog** (`data/product_data.xml`) — the five care plans
  from the business plan pricing table, loaded as `product.template`
  records of type Service:
  - Adult Day Care (per day)
  - Respite Stay (per week)
  - Shared Residence (monthly)
  - Private Premium Suite (monthly)
  - Post-Surgical Recovery Care (per day)

  Prices are seeded at the midpoint of each range and are meant to be
  adjusted from **Sales > Products** as the business needs — they are not
  hardcoded anywhere else in this module. Loaded with `noupdate="1"` so a
  module upgrade never overwrites prices staff have changed.

- **Care Admissions sales team** (`data/crm_team_data.xml`) — a dedicated
  `crm.team` used for every lead/quotation originating from the website's
  care request flow, so it's filterable and reportable on its own.

- **Website Care Quote template** (`data/sale_order_template_data.xml`) —
  a `sale.order.template` applied to quotations generated from the site,
  so they're immediately recognizable inside the standard Sales pipeline.

## What's coming next

- `models/` — the care intake/assessment model (mirrors the Admission Form
  sections A–H) with care-level scoring logic, linked to `res.partner` and
  to the generated `sale.order`.
- `controllers/` — a JSON API consumed by the website's Quote Request form
  and, later, by the family portal (`Dashboard.tsx`) to read back status.
- `security/` — access rights and record rules (portal users only see
  their own admission/quote records; medical data restricted by role).
- `views/` — backend UI for staff to review assessments and manage the
  `New → Assessed → Quoted → Admitted` pipeline stages.

## Dependencies

`sale_management`, `crm`, `website` (all part of Odoo Community).
