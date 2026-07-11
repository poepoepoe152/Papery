# Papery

**AI-powered document verification platform.** Upload reference and target
business documents — Papery extracts the text (OCR when needed), detects the
document type, pulls out structured fields, compares them, highlights mismatches
with severity, and generates downloadable verification reports.

First vertical: **Freight Forwarding & Logistics**. Web application only.

## Status

🟢 **End-to-end working application.** Full flow runs locally with Docker:
register → activate license → upload documents → automatic
extract/classify/compare → results with severity → PDF/Excel/JSON reports →
history & search → admin panel.

Full system design: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Tech Stack

- **Frontend:** Next.js 15, React 19, TypeScript, TailwindCSS, next-themes
- **Backend:** Python, FastAPI, SQLAlchemy, background-task pipeline
- **Document understanding:** PyMuPDF (PDF text), Tesseract OCR (scans/images),
  python-docx, RapidFuzz (fuzzy matching), schema-driven extraction
- **Reports:** ReportLab (PDF), openpyxl (Excel), JSON
- **Database:** PostgreSQL · **Auth:** JWT + bcrypt · **Containers:** Docker

> **What is intentionally simplified (with clear seams in the code):**
> processing uses FastAPI background tasks instead of Celery/Redis; files are
> stored on a local volume instead of S3; OCR uses Tesseract (PaddleOCR is the
> production engine); the semantic LLM comparison step is a disabled-by-default
> hook (deterministic matching covers the core). The app runs fully **without
> any API keys**.

## Features

- Responsive landing page, dark / light mode
- JWT auth (register, login, refresh) + company license activation
- Roles: Admin, Manager, Staff (+ platform Super Admin) with RBAC
- Document upload (PDF, DOCX, PNG, JPG, JPEG, TIFF), reference vs target
- Automatic pipeline: text extraction → OCR fallback → classification →
  field extraction → comparison → severity (Critical / Major / Minor)
- Smart matching: number/date/whitespace normalization, OCR-confusion
  awareness (O/0, I/1, S/5, B/8), fuzzy similarity
- Results: split-screen field comparison + findings with explanations and
  suggested fixes; accept / dismiss actions
- Reports: download PDF, Excel, JSON
- History with search & filters; per-row drill-down
- Learning mode: dismissals/corrections captured as feedback for admin review
- Audit trail on key actions; usage quota & seat-limit enforcement
- Admin panel: companies, licenses (generate keys), plans, usage, MRR

---

## Run locally with Docker

**Prerequisites:** Docker + Docker Compose. From the repo root:

```bash
docker compose up --build
```

| Service  | URL                       | Notes                              |
|----------|---------------------------|------------------------------------|
| Frontend | http://localhost:3000     | Next.js web app                    |
| Backend  | http://localhost:8000     | FastAPI (interactive docs `/docs`) |
| Database | localhost:5432            | PostgreSQL (`papery`/`papery`)     |

### Full walkthrough

1. Open **http://localhost:3000** → **Sign up** (you become the company Admin).
2. Activate with a demo license key (clickable on the activation page):
   - `PAPERY-FREE-DEMO-2026` · `PAPERY-PRO-DEMO-2026` · `PAPERY-ENT-DEMO-2026`
3. Go to **New Verification**, give it a title, and upload:
   - **Reference** document(s) — the source of truth
   - **Target** document(s) — the document to verify
   (PDFs with a text layer work fully offline; scanned PDFs/images use OCR.)
4. Click **Verify** → watch the pipeline run → review the results: a
   split-screen field comparison and a findings list with severity and
   suggested fixes.
5. Download the **PDF / Excel / JSON** report.
6. Browse **History** to search past verifications; **Team** to manage roles.

> 💡 No sample documents handy? Any PDF/Word file works. For a meaningful demo,
> make two PDFs with lines like `Booking No: ABC123`, `Container No: TCLU1234567`,
> `Gross Weight: 26,557.68 KG` and change a value in the target.

### Platform super-admin (Admin Panel)

Seeded for the admin panel: `admin@papery.app` / `Admin123!`.
Log in to manage companies, generate license keys, and view usage/MRR.

> ⚠️ All default secrets in compose files are local-dev only — change them
> before any real deployment.

### Access from a phone (same Wi-Fi)

Set your computer's LAN IP once, then rebuild:

```bash
cp .env.example .env       # edit HOST_IP to your computer's IP (e.g. 192.168.1.45)
docker compose up --build
```

Open `http://<HOST_IP>:3000` on the phone. (Find your IP: macOS
`ipconfig getifaddr en0`, Windows `ipconfig`, Linux `hostname -I`.)

### Stop / reset

```bash
docker compose down            # stop
docker compose down -v         # stop and wipe database + uploaded files
```

---

## Production / pilot deployment

For a real pilot with automatic HTTPS (Caddy + Let's Encrypt), a domain, strong
secrets, and database backups, follow the step-by-step **[deployment guide](docs/DEPLOY.md)**:

```bash
# on a server with Docker + a domain pointed at it
docker compose -f docker-compose.tls.yml up --build -d   # auto-HTTPS via Caddy
```

A plain-HTTP variant behind your own load balancer is also provided
(`docker-compose.prod.yml`, Nginx on port 80). Database backup/restore scripts
are in `scripts/` (`backup.sh`, `restore.sh`).

---

## Run tests

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest
pytest -q
```

The suite covers the document-understanding engines: normalization,
classification, field extraction, and the comparison/severity logic.

---

## Project structure

```
Papery/
├── docker-compose.yml          # dev: db + backend + frontend
├── docker-compose.prod.yml     # prod: + nginx, built frontend
├── infra/nginx/nginx.conf      # reverse proxy
├── docs/ARCHITECTURE.md        # full system design
├── backend/                    # FastAPI app
│   ├── app/
│   │   ├── main.py             # app factory + startup
│   │   ├── models.py           # all ORM tables
│   │   ├── doctypes.py         # document types + field catalog (schema-driven)
│   │   ├── pipeline.py         # verification orchestration (background task)
│   │   ├── engines/            # text_extract, classify, extract_fields,
│   │   │                       #   normalize, compare, reports
│   │   └── routers/            # auth, license, team, files, verifications,
│   │                           #   findings, reports, admin
│   └── tests/                  # engine unit tests
└── frontend/                   # Next.js 15 (App Router)
    └── src/app/                # /, /login, /register, /activate,
                                #   /dashboard, /dashboard/verify[/[id]],
                                #   /dashboard/history, /team, /admin, /settings
```

## API overview

Auth & tenancy: `/auth/*`, `/license/*`, `/team/*`.
Verification: `POST /files/upload`, `POST /verifications`,
`GET /verifications` (search), `GET /verifications/{id}`,
`GET /verifications/{id}/status`, `GET /verifications/{id}/report?fmt=PDF`,
`PATCH /findings/{id}`. Admin: `/admin/*`. Full docs at
**http://localhost:8000/docs**.

## Roadmap

1. ✅ Architecture · 2. ✅ Auth & License · 3. ✅ Landing · 4. ✅ Dashboard ·
5. ✅ Upload · 6. ✅ OCR/text extraction · 7. ✅ Classification ·
8. ✅ Field extraction · 9. ✅ Comparison engine · 10. ✅ Results view ·
11. ✅ Reports · 12. ✅ History · 13. ✅ Learning mode · 14. ✅ Admin panel ·
15. ✅ Tests · 16. ✅ Deployment (Nginx)

**Next up (production hardening):** Celery/Redis queue, S3 storage, PaddleOCR,
pixel-level PDF highlight overlay, real email notifications, LLM semantic step.
