# Peart Serenity Residence — Platform

**Where Care Feels Like Home.**

Fullstack platform for **Peart Serenity Residence**, a premium elder-care residence in Montego Bay, Jamaica. This repository contains the public website and the Odoo 19 backend that powers it — **Odoo is the sole backend**: CRM pipeline for care inquiries, service catalog and quotations, contacts, portal accounts, and — in a later phase — the online store.

> This is a private, proprietary repository for an active business. Do not fork, mirror, or redistribute.

---

## 1. Architecture

```
┌─────────────────────────┐        JSON-RPC API         ┌──────────────────────────────┐
│   project/ (Website)     │ ───────────────────────────▶ │   odoo/ (Odoo 19 backend)     │
│   React + Vite + TS      │ ◀─────────────────────────── │   CRM · Sales · Website       │
│   built with bolt.new    │   session cookie (login)     │   custom module: peart_serenity│
└─────────────────────────┘                              └──────────────────────────────┘
```

- The **website** (`project/`) is the public-facing marketing site, the multi-step Care Quote Request form, and the account/family portal. It keeps its existing bolt.new design and UX.
- **Odoo 19 is the single source of truth for everything the site reads and writes** — there is no other datastore. Contacts, the care admissions pipeline (`New → Assessed → Quoted → Admitted`), tour bookings, the waitlist, testimonials, the service/pricing catalog, quotations, and portal accounts (login/sign-up) all live in Odoo.
- The website talks to Odoo exclusively through `project/src/lib/odoo.ts`, which calls:
  - a public JSON API in `peart_serenity` for forms (quote requests, contact, tour bookings, waitlist, testimonials, sign-up) — see the table below;
  - Odoo's own built-in session endpoints (`/web/session/authenticate`, `/web/session/get_session_info`, `/web/session/destroy`) for login/logout, since accounts are real Odoo portal users;
  - a small `auth='user'` API (`/api/my/*`) for the family portal, always scoped server-side to the logged-in user's own partner — never to client-supplied IDs.
- Every quotation submitted by a family lands as a **standard Odoo quotation** (`sale.order`), flagged with the *Care Admissions* sales team and the *Peart Serenity — Care Quote (Website)* template, so staff work entirely inside Odoo's native Sales pipeline — no parallel system to maintain.

## 2. Repository structure

```
.
├── project/                          Public website (React + Vite + TypeScript)
│   ├── src/pages/                    Home, Services, About, Facility, Contact, Quote Request, Auth, Dashboard
│   └── src/lib/odoo.ts               The only backend client — talks to Odoo exclusively
├── odoo/
│   ├── addons/
│   │   └── peart_serenity/           Custom, installable Odoo module (see its own README)
│   └── config/
│       └── odoo.conf                 Local Odoo configuration
└── infra/
    ├── docker-compose.yml            Local dev environment: Odoo 19 + PostgreSQL 16 + reverse proxy
    └── nginx/default.conf            Single local entry point (see below)
```

Confidential business documentation (business plan, contracts, financials — the `Business Package/` folder) is kept **local only** and is excluded via `.gitignore`. It is intentionally not part of this repository.

## 3. Tech stack

| Layer | Technology |
|---|---|
| Website | React 18, TypeScript, Vite, Tailwind CSS, React Router |
| Backend / ERP | Odoo 19 (Community), PostgreSQL 16 |
| Local dev environment | Docker Compose |

## 4. Getting started

There is a **single local entry point** for the whole platform, so you never have to juggle two URLs: **http://localhost:8080**

- `http://localhost:8080/` → the website (proxied to the Vite dev server)
- `http://localhost:8080/odoo`, `/web`, `/website`, `/api`, `/report`, `/mail` → the Odoo backend (proxied to the `peartserenity` container)

This is handled by an Nginx reverse proxy (`infra/nginx/default.conf`) that ships with the Docker Compose stack. In production the same split happens at the domain/edge level instead (main domain → website, admin subdomain → Odoo).

### 1. Start Odoo + Postgres + the proxy

```bash
cd infra
docker compose up -d
```

On first run, open **http://localhost:8080/odoo**, create a database (must be named `peartserenity` — see `ODOO_DB` in `project/src/lib/odoo.ts` — or update that constant to match) and install the **Peart Serenity - Care Services** module (`peart_serenity`) from *Apps*.

The database manager master password is set in `odoo/config/odoo.conf` — it is a local-dev-only placeholder and **must** be changed before any non-local deployment. Odoo itself is still reachable directly on `http://localhost:8169` if you need to bypass the proxy for debugging.

### 2. Start the website

```bash
cd project
npm install
npm run dev -- --host 0.0.0.0
```

`--host 0.0.0.0` is required so the Nginx container (running in Docker) can reach the Vite dev server on the host — otherwise it only binds to `localhost` and the proxy gets a 502. No `.env` file is needed — the site talks to Odoo via relative paths (`/api`, `/web`) through whatever host it's served from.

Once both are running, use **http://localhost:8080** for everything.

## 5. Public API (`peart_serenity` module)

| Route | Auth | Purpose |
|---|---|---|
| `POST /api/care-quote` | public | Submits the multi-step Quote Request form. Creates/dedupes contacts, a `peart.admission` record, and a `crm.lead` in the Care Admissions pipeline (stage **New**). |
| `POST /api/contact` | public | General contact form → `crm.lead`. |
| `POST /api/tour-booking` | public | Facility tour requests → `peart.tour.booking`. |
| `POST /api/waitlist` | public | Waitlist sign-ups → `peart.waitlist`. |
| `POST /api/testimonials` | public | Returns approved testimonials (featured first, max 20) for the homepage. |
| `POST /api/auth/signup` | public | Creates a portal `res.users` + `res.partner` for account registration. |
| `POST /api/my/admissions` | user | The logged-in family's own admission/quote records. |
| `POST /api/my/tours` | user | The logged-in family's own tour bookings. |

All routes are JSON-RPC (`{jsonrpc: "2.0", method: "call", params: {...}}`). `public` routes elevate to `sudo()` only after validating required fields; `user` routes require a valid Odoo session (see login below) and always scope queries server-side to `request.env.user.partner_id` — never to client-supplied IDs. Login/logout/session-check reuse Odoo's own built-in endpoints (`/web/session/*`) rather than a custom one.

## 6. Roadmap

1. ✅ Repository, Docker dev environment, and `peart_serenity` module scaffold with the default care service catalog
2. ✅ Care intake/assessment model (`peart.admission`) + public JSON API — the Quote Request form and account sign-up write directly to Odoo (contacts, CRM lead, admissions pipeline)
3. ✅ Full Supabase decommission: contact form, tour bookings, waitlist and testimonials now read/write Odoo; accounts are real Odoo portal users (session-cookie login) and the family portal (`Dashboard.tsx`) reads the logged-in user's own records from Odoo
4. Production deployment (VPS + Docker + domain + professional email)
5. Odoo eCommerce for the future online store

## 7. Data privacy

This platform handles sensitive personal and medical information submitted through the Care Quote Request form. Access is restricted by role inside Odoo, and handling follows Jamaica's **Data Protection Act (2020)**. The public form only collects what's needed for a care assessment; pricing and care-level scoring are internal-only, never exposed on the public site.

## 8. License

Proprietary — © Peart Serenity Residence. All rights reserved. Internal use only.
