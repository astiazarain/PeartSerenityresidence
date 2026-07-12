# peart_serenity

Custom Odoo 19 module for **Peart Serenity Residence**. Odoo is the sole
backend for peartserenityresidence.com — this module is where every model
and every public API route the website depends on lives. There is no other
datastore.

## Models

- **`product.template`** (`data/product_data.xml`) — the five care plans
  from the business plan pricing table, loaded as Service products. Prices
  are seeded at the midpoint of each range and meant to be adjusted from
  **Sales > Products** — not hardcoded anywhere else. Loaded with
  `noupdate="1"` so a module upgrade never overwrites prices staff have
  changed.

- **`peart.admission`** (`models/peart_admission.py`) — mirrors the
  Admission Form sections A–G. On creation it finds-or-creates the
  applicant and resident as `res.partner` contacts (deduplicated by email),
  opens a `crm.lead` in the Care Admissions pipeline (stage **New**),
  computes an internal `care_level` (Low/Moderate/High/Specialized) used
  only for staff triage, and suggests a service product for the
  **Create Quotation** action (generates a standard `sale.order`, tagged
  with the Care Admissions team and the website quote template).

- **`peart.tour.booking`**, **`peart.waitlist`** — facility tour requests
  and waitlist sign-ups, each linked to a deduplicated `res.partner`.

- **`peart.testimonial`** (seeded in `data/testimonial_data.xml`) — family
  testimonials shown on the homepage. Only `approved` ones are returned to
  the site (featured first, max 20); manage them from the **Care
  Admissions > Testimonials** backend menu.

- **`res.partner`** is extended with `peart_find_or_create(name, email,
  phone)` — a shared find-or-dedupe helper used everywhere a contact needs
  to be created from a public form or from account sign-up, so the same
  family never ends up with duplicate contacts.

## Pipeline & sales

- **Care Admissions sales team** (`data/crm_team_data.xml`) — every
  lead/quotation originating from the website uses this team.
- **Pipeline stages** (`data/crm_stage_data.xml`) — `New → Assessed →
  Quoted → Admitted`, scoped to the Care Admissions team only.
- **Website Care Quote template** (`data/sale_order_template_data.xml`) —
  applied to quotations generated from the site.

## Public JSON API (`controllers/main.py`)

| Route | Auth | Purpose |
|---|---|---|
| `POST /api/care-quote` | public | Quote Request form → `peart.admission` |
| `POST /api/contact` | public | Contact form → `crm.lead` |
| `POST /api/tour-booking` | public | → `peart.tour.booking` |
| `POST /api/waitlist` | public | → `peart.waitlist` |
| `POST /api/testimonials` | public | Read-only, approved testimonials |
| `POST /api/auth/signup` | public | Creates a portal `res.users` + contact |
| `POST /api/my/admissions` | user | Caller's own admissions |
| `POST /api/my/tours` | user | Caller's own tour bookings |

`public` routes elevate to `sudo()` only after validating required fields
— visitors never get direct model access. `user` routes require a valid
Odoo session and always scope queries to `request.env.user.partner_id`,
never to client-supplied identifiers. Login/logout/session-check are not
custom routes — the website calls Odoo's own `/web/session/authenticate`,
`/web/session/get_session_info` and `/web/session/destroy`.

## Dependencies

`sale_management`, `crm`, `website`, `mail`, `portal` (all part of Odoo
Community).

## What's coming next

- Record rules restricting medical fields on `peart.admission` to internal
  staff roles (currently readable by any internal user via the backend UI).
- Backend UI polish (kanban view of the pipeline, activities/reminders).
- Odoo eCommerce for the future online store, reusing this same product
  catalog.
