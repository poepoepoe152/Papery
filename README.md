# Papery

**AI-powered document verification platform.** Upload reference and target
business documents — Papery detects document types, extracts structured fields,
compares them, highlights mismatches with severity, and generates auditable
verification reports.

First vertical: **Freight Forwarding & Logistics**. Web application only.

## Status

🟢 **Phase 2 — Project foundation complete.** Authentication, company license
activation, user roles, landing page, and the dashboard shell are implemented
and runnable via Docker. OCR and AI are intentionally **not** implemented yet
(Phases 5–11).

Full system design: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Tech Stack

- **Frontend:** Next.js 15, React 19, TypeScript, TailwindCSS, next-themes
- **Backend:** Python, FastAPI, SQLAlchemy
- **Database:** PostgreSQL
- **Auth:** JWT (access + refresh), bcrypt
- **Containers:** Docker + Docker Compose

## What's implemented in Phase 2

- Landing page (hero, features, how-it-works, pricing, FAQ) — responsive
- Login & Register pages
- Dashboard layout with sidebar + top navigation (responsive, mobile drawer)
- Dark / Light mode (system-aware, toggle persists)
- JWT authentication (register, login, refresh, me, logout)
- Company license activation with seeded demo keys
- Role-based access control (Admin, Manager, Staff, + platform Super Admin)
- Team management (add members, change roles, enable/disable) with seat limits

---

## Run locally with Docker (recommended)

**Prerequisites:** Docker + Docker Compose.

```bash
# from the repository root
docker compose up --build
```

This starts three containers:

| Service  | URL                            | Notes                          |
|----------|--------------------------------|--------------------------------|
| Frontend | http://localhost:3000          | Next.js web app                |
| Backend  | http://localhost:8000          | FastAPI (docs at `/docs`)      |
| Database | localhost:5432                 | PostgreSQL (`papery`/`papery`) |

The backend waits for PostgreSQL, creates tables, and seeds plans + demo
license keys on first startup.

### Try it out

1. Open **http://localhost:3000**.
2. Click **Sign up** and create an account (this makes you the company **Admin**).
3. You'll be sent to the **license activation** page. Use a demo key:
   - `PAPERY-FREE-DEMO-2026` (Free — 50 docs / 3 users)
   - `PAPERY-PRO-DEMO-2026` (Pro — 500 docs / 10 users)
   - `PAPERY-ENT-DEMO-2026` (Enterprise — 5000 docs / 100 users)
4. After activation you reach the **Dashboard**. Visit **Team** to add Manager
   or Staff members and manage their roles.
5. Toggle **dark / light mode** from the top bar.

### Seeded platform super-admin

A platform super-admin is seeded for later admin-panel work (Phase 14):

- Email: `admin@papery.app`
- Password: `Admin123!`

> ⚠️ All default secrets/passwords in `docker-compose.yml` are for local
> development only. Change them before any non-local deployment.

### Stop / reset

```bash
docker compose down          # stop containers
docker compose down -v       # stop and wipe the database volume (fresh start)
```

---

## Run locally without Docker (manual)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# point at a running PostgreSQL instance
export DATABASE_URL="postgresql+psycopg2://papery:papery@localhost:5432/papery"
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
export NEXT_PUBLIC_API_URL="http://localhost:8000"
npm run dev
```

Open http://localhost:3000.

---

## Project structure

```
Papery/
├── docker-compose.yml      # db + backend + frontend
├── docs/ARCHITECTURE.md    # full system design (Phase 1)
├── backend/                # FastAPI app
│   ├── app/
│   │   ├── main.py         # app factory + startup (init + seed)
│   │   ├── config.py       # env-driven settings
│   │   ├── database.py     # engine/session + init
│   │   ├── models.py       # plans, companies, licenses, users
│   │   ├── security.py     # bcrypt + JWT
│   │   ├── deps.py         # auth + RBAC dependencies
│   │   ├── schemas.py      # Pydantic DTOs
│   │   ├── services.py     # shared helpers
│   │   ├── seed.py         # plans + demo licenses + super-admin
│   │   └── routers/        # auth, license, team
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/               # Next.js 15 app (App Router)
    ├── src/app/            # routes: /, /login, /register, /activate, /dashboard/*
    ├── src/components/     # theme, header, dashboard sidebar/topbar
    ├── src/lib/            # api client, auth context, types
    └── Dockerfile
```

## API overview (Phase 2)

| Method | Path                          | Role          |
|--------|-------------------------------|---------------|
| POST   | `/api/v1/auth/register`       | public        |
| POST   | `/api/v1/auth/login`          | public        |
| POST   | `/api/v1/auth/refresh`        | public        |
| GET    | `/api/v1/auth/me`             | authenticated |
| POST   | `/api/v1/auth/logout`         | authenticated |
| GET    | `/api/v1/license`             | authenticated |
| POST   | `/api/v1/license/activate`    | Admin         |
| GET    | `/api/v1/team/members`        | Admin/Manager |
| POST   | `/api/v1/team/members`        | Admin         |
| PATCH  | `/api/v1/team/members/{id}`   | Admin         |

Interactive API docs: **http://localhost:8000/docs**.

## Roadmap

1. ✅ Architecture · 2. ✅ Auth & License (+ landing, dashboard shell) →
3. Landing Page polish → 4. Dashboard → 5. Upload → 6. OCR →
7. Classification → 8. Field Extraction → 9. Comparison Engine →
10. PDF Highlight → 11. Reports → 12. History → 13. Learning Mode →
14. Admin Panel → 15. Testing → 16. Deployment

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full roadmap.
