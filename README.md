# Peart Serenity Residence — Platform

**Where Care Feels Like Home.**

Fullstack platform for **Peart Serenity Residence**, a premium elder-care residence in Montego Bay, Jamaica. This repository contains the public website and the Odoo 19 backend that powers it: CRM pipeline for care inquiries, service catalog and quotations, and — in a later phase — the online store.

> This is a private, proprietary repository for an active business. Do not fork, mirror, or redistribute.

---

## 1. Architecture

```
┌─────────────────────────┐        JSON/REST API        ┌──────────────────────────────┐
│   project/ (Website)     │ ───────────────────────────▶ │   odoo/ (Odoo 19 backend)     │
│   React + Vite + TS      │ ◀─────────────────────────── │   CRM · Sales · Website       │
│   built with bolt.new    │                              │   custom module: peart_serenity│
└─────────────────────────┘                              └──────────────────────────────┘
```

- The **website** (`project/`) is the public-facing marketing site and the multi-step Care Quote Request form families use to apply. It keeps its existing design and UX.
- **Odoo 19** is the single source of truth: contacts, the care admissions pipeline (`New → Assessed → Quoted → Admitted`), the service/pricing catalog, quotations, and — later — the eCommerce store.
- Every quotation submitted by a family lands as a **standard Odoo quotation** (`sale.order`), flagged with the *Care Admissions* sales team and the *Peart Serenity — Care Quote (Website)* template, so staff work entirely inside Odoo's native Sales pipeline — no parallel system to maintain.

Frontend integration with the Odoo API (replacing the current Supabase calls) and the family portal are being built next — see [Roadmap](#5-roadmap).

## 2. Repository structure

```
.
├── project/                          Public website (React + Vite + TypeScript)
│   ├── src/pages/                    Home, Services, About, Facility, Contact, Quote Request, Dashboard
│   └── src/lib/supabase.ts           Current data client (being migrated to the Odoo API)
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
| Current data layer (being replaced) | Supabase (Postgres + Auth) |
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

On first run, open **http://localhost:8080/odoo**, create a database and install the **Peart Serenity - Care Services** module (`peart_serenity`) from *Apps*.

The database manager master password is set in `odoo/config/odoo.conf` — it is a local-dev-only placeholder and **must** be changed before any non-local deployment. Odoo itself is still reachable directly on `http://localhost:8169` if you need to bypass the proxy for debugging.

### 2. Start the website

```bash
cd project
npm install
npm run dev -- --host 0.0.0.0
```

`--host 0.0.0.0` is required so the Nginx container (running in Docker) can reach the Vite dev server on the host — otherwise it only binds to `localhost` and the proxy gets a 502. Requires a local `project/.env` (not committed — see `project/.env.example` conventions once the Odoo API client lands).

Once both are running, use **http://localhost:8080** for everything.

## 5. Roadmap

1. ✅ Repository, Docker dev environment, and `peart_serenity` module scaffold with the default care service catalog
2. Care intake/assessment model + website API (replaces the Supabase calls in `project/src/lib`)
3. Family portal (Odoo portal users) powering `project/src/pages/Dashboard.tsx`
4. Data migration off Supabase
5. Production deployment (VPS + Docker + domain + professional email)
6. Odoo eCommerce for the future online store

## 6. Data privacy

This platform handles sensitive personal and medical information submitted through the Care Quote Request form. Access is restricted by role inside Odoo, and handling follows Jamaica's **Data Protection Act (2020)**. The public form only collects what's needed for a care assessment; pricing and care-level scoring are internal-only, never exposed on the public site.

## 7. License

Proprietary — © Peart Serenity Residence. All rights reserved. Internal use only.
