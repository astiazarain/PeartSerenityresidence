# peart_serenity

Custom Odoo 19 module for **Peart Serenity Residence**. This module is the
integration point between the public website and Odoo: it is where the
care service catalog, the admissions pipeline, and the website API live.

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

- **Pipeline stages** (`data/crm_stage_data.xml`) — `New → Assessed →
  Quoted → Admitted`, scoped to the Care Admissions team only.

- **Website Care Quote template** (`data/sale_order_template_data.xml`) —
  a `sale.order.template` applied to quotations generated from the site,
  so they're immediately recognizable inside the standard Sales pipeline.

- **Care Admission Request model** (`models/peart_admission.py`) — mirrors
  the Admission Form sections A–G. On creation it:
  - finds-or-creates the applicant and resident as `res.partner` contacts
    (deduplicated by email via the `res.partner.peart_find_or_create`
    helper in `models/res_partner.py`, shared with account sign-up);
  - creates a `crm.lead` in the Care Admissions pipeline, stage **New**;
  - computes an internal `care_level` (Low/Moderate/High/Specialized)
    from mobility and specialized-care answers — never shown publicly,
    used only to guide staff triage;
  - suggests a service product from the requested care type, used to
    prefill the quotation staff generate with **Create Quotation** (a
    standard `sale.order`, tagged with the Care Admissions team and the
    website quote template — see root README).

- **Public JSON API** (`controllers/main.py`):
  - `POST /api/care-quote` — submits the website's Quote Request form.
  - `POST /api/register-contact` — called on account sign-up so every
    registered user also exists as an Odoo contact.

  Both run `auth='public'` and only elevate to `sudo()` after validating
  required fields — visitors never get direct model access.

## What's coming next

- Portal access so families can log in and see their own admission/quote
  status (powers `project/src/pages/Dashboard.tsx`).
- Record rules restricting medical fields to internal staff roles.
- Backend UI polish (kanban view of the pipeline, activities/reminders).

## Dependencies

`sale_management`, `crm`, `website`, `mail` (all part of Odoo Community).
