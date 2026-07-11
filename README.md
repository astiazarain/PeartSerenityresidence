# Peart Serenity Residence — Platform

Fullstack platform for Peart Serenity Residence (Montego Bay, Jamaica): public
website + Odoo 19 as the backend (CRM, sales/quotations, and eventually
eCommerce).

## Structure

```
.
├── project/        # Public website (React + Vite + TypeScript, built with bolt.new)
├── odoo/
│   ├── addons/
│   │   └── peart_serenity/   # Custom Odoo module (installable)
│   └── config/
│       └── odoo.conf
└── infra/
    └── docker-compose.yml    # Local dev environment: Odoo 19 + PostgreSQL 16
```

Business/legal documentation (`Business Package/`) is kept local only and is
excluded from git via `.gitignore` — it is not part of this repository.

## Local development — Odoo backend

```bash
cd infra
docker compose up -d
```

Odoo will be available at http://localhost:8069. On first run, create a
database and install the **Peart Serenity - Care Services** module
(`peart_serenity`) from Apps.

Default admin master password (for the database manager) is set in
`odoo/config/odoo.conf` — change it before any non-local deployment.

## Local development — Website

```bash
cd project
npm install
npm run dev
```

See `project/.env` for required environment variables (not committed).

## Roadmap

1. ~~Repo, Docker dev environment and `peart_serenity` module scaffold with default service catalog~~
2. Care intake/assessment model + website API (replaces Supabase calls in `project/src/lib`)
3. Family portal (Odoo portal users) powering `project/src/pages/Dashboard.tsx`
4. Data migration off Supabase
5. Deployment (VPS + Docker + domain + email)
6. Odoo eCommerce for the future online store
