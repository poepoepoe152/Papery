# Papery — Software Architecture Document (Phase 1)

> **Status:** Phase 1 — System Design Only. **No implementation code.**
> **Product:** Papery — AI-Powered Document Verification Platform
> **First vertical:** Freight Forwarding & Logistics
> **Document type:** Web application (no desktop, no mobile native app)
> **Author role:** Principal Architect / CTO design pass
> **Version:** 1.0
> **Last updated:** 2026-06-27

---

## Table of Contents

1. [Product Requirements Document (PRD)](#1-product-requirements-document-prd)
2. [Functional Requirements](#2-functional-requirements)
3. [Non-Functional Requirements](#3-non-functional-requirements)
4. [High-Level Architecture Diagram](#4-high-level-architecture-diagram)
5. [Low-Level Architecture](#5-low-level-architecture)
6. [Folder Structure](#6-folder-structure)
7. [Database Schema](#7-database-schema)
8. [API Endpoint Specification](#8-api-endpoint-specification)
9. [OCR Pipeline](#9-ocr-pipeline)
10. [Document Classification Flow](#10-document-classification-flow)
11. [Field Extraction Flow](#11-field-extraction-flow)
12. [AI Comparison Flow](#12-ai-comparison-flow)
13. [File Upload Flow](#13-file-upload-flow)
14. [Authentication Flow](#14-authentication-flow)
15. [License Activation Flow](#15-license-activation-flow)
16. [User Permission Matrix](#16-user-permission-matrix)
17. [Landing Page Structure](#17-landing-page-structure)
18. [Dashboard Structure](#18-dashboard-structure)
19. [Admin Dashboard Structure](#19-admin-dashboard-structure)
20. [UI Wireframes (ASCII)](#20-ui-wireframes-ascii)
21. [ER Diagram](#21-er-diagram)
22. [Security Architecture](#22-security-architecture)
23. [Deployment Architecture](#23-deployment-architecture)
24. [Infrastructure Diagram](#24-infrastructure-diagram)
25. [Scalability Plan](#25-scalability-plan)
26. [Cost Optimization Strategy](#26-cost-optimization-strategy)
27. [Risk Analysis](#27-risk-analysis)
28. [Testing Strategy](#28-testing-strategy)
29. [Open-Source Libraries](#29-open-source-libraries)
30. [Complete Development Roadmap](#30-complete-development-roadmap)

---

## 1. Product Requirements Document (PRD)

### 1.1 Vision

Papery eliminates manual, error-prone cross-checking of business documents. A
user uploads one or more **reference** documents (the source of truth) and one
or more **target** documents (the document to verify). Papery automatically
ingests, OCRs, classifies, extracts structured fields, compares them, flags
mismatches with severity, and produces an auditable verification report.

**One-sentence pitch:** *Upload your documents, and Papery tells you exactly
what's wrong — instantly, with proof.*

### 1.2 Problem Statement

In freight forwarding, a single shipment generates many documents (Booking
Confirmation, Shipping Instruction, Draft B/L, Final B/L, Commercial Invoice,
Packing List, Delivery Order). Operators manually cross-check fields like
Container Number, Seal Number, Weight, Consignee, and Ports. A single wrong
digit in a B/L can cause customs holds, demurrage charges, cargo
mis-delivery, and contractual penalties costing thousands of dollars per
incident. The work is repetitive, slow, and unreliable under volume.

### 1.3 Target Users

| Persona | Role | Goal |
|---|---|---|
| **Operations Staff** | Staff | Verify a draft B/L against booking + SI quickly |
| **Operations Manager** | Manager | Oversee team verifications, catch critical errors |
| **Company Admin** | Admin | Manage license, users, billing, audit |
| **Papery Platform Admin** | Super Admin | Manage all companies, licenses, plans, revenue |

### 1.4 Goals & Success Metrics

| Goal | Metric | Target |
|---|---|---|
| Reduce manual verification time | Median time per verification | < 60s for a 5-page doc |
| Catch critical errors | Critical-error recall | ≥ 98% |
| Minimize false alarms | False-positive rate on critical fields | ≤ 2% |
| Control AI cost | LLM cost per verification | ≤ $0.05 average |
| Reliability | Verification job success rate | ≥ 99.5% |
| Adoption | Weekly active verifying users / seats | ≥ 60% |

### 1.5 Scope (MVP — Freight vertical)

**In scope:** Web app; multi-tenant SaaS; auth + license; upload (PDF/DOCX/
PNG/JPG/JPEG/TIFF); OCR; classification; field extraction; comparison engine;
split-screen result view; PDF/Excel/JSON reports; history + search; audit
trail; notifications; admin panel; learning mode (feedback capture).

**Out of scope (MVP):** Native mobile apps; desktop apps; offline mode;
real-time collaborative editing; direct carrier EDI integrations (post-MVP);
e-signature; non-freight verticals (designed-for but not shipped in MVP).

### 1.6 Design Principles

1. **Extensible by document type** — adding a new document type or field must
   be config/schema work, not a rewrite. The freight vertical is the first
   plugin, not the whole product.
2. **Cost-aware AI** — deterministic matching first; LLM only when confidence
   < 90%.
3. **Auditable** — every action logged; every verdict explainable.
4. **Async by default** — heavy work runs in background workers; UI never
   blocks on OCR/LLM.
5. **Multi-tenant isolation** — strict company-scoped data access at every
   layer.

---

## 2. Functional Requirements

IDs are referenced by the roadmap and test plan.

### 2.1 Authentication & Accounts
- **FR-AUTH-1** Register with email + password (bcrypt-hashed).
- **FR-AUTH-2** Email verification before activation.
- **FR-AUTH-3** Login issuing short-lived access JWT + refresh token.
- **FR-AUTH-4** Forgot/reset password via signed, expiring token.
- **FR-AUTH-5** Logout / refresh-token revocation.
- **FR-AUTH-6** Optional TOTP 2FA (post-MVP toggle, schema-ready).

### 2.2 Company & License
- **FR-LIC-1** A company is created on first admin signup or via invite.
- **FR-LIC-2** Activate company with a License Key.
- **FR-LIC-3** License defines plan, expiry, monthly doc limit, max users.
- **FR-LIC-4** Dashboard access blocked unless license is `ACTIVE`.
- **FR-LIC-5** Enforce monthly document quota; block + notify on exceed.
- **FR-LIC-6** Enforce max-users on invite.

### 2.3 Team & Roles
- **FR-USER-1** Invite team members by email (role: Manager/Staff).
- **FR-USER-2** Roles: Admin, Manager, Staff (see permission matrix).
- **FR-USER-3** Deactivate/reactivate users.

### 2.4 Upload & Ingestion
- **FR-UP-1** Upload PDF, DOCX, PNG, JPG, JPEG, TIFF.
- **FR-UP-2** Designate documents as **Reference** or **Target**.
- **FR-UP-3** Support N reference docs + M target docs in one verification.
- **FR-UP-4** Support mixed formats in a single verification.
- **FR-UP-5** Validate file type (magic bytes), size, page count.
- **FR-UP-6** Virus scan before processing.
- **FR-UP-7** Direct-to-S3 presigned uploads (no large bodies through API).

### 2.5 OCR & Text Extraction
- **FR-OCR-1** Auto-detect digital-text PDFs → extract directly.
- **FR-OCR-2** Scanned PDF / image → OCR automatically (no user choice).
- **FR-OCR-3** Primary engine PaddleOCR; fallback Tesseract; DocTR optional.
- **FR-OCR-4** Auto-detect orientation/rotation and de-skew.
- **FR-OCR-5** Handle multi-page (300+ pages) via chunked processing.
- **FR-OCR-6** Table structure recognition.
- **FR-OCR-7** Automatic language detection.
- **FR-OCR-8** Persist OCR output with per-token bounding boxes + page index.

### 2.6 Classification
- **FR-CLS-1** Auto-classify each document into a supported type.
- **FR-CLS-2** Return confidence; if low, mark `UNKNOWN` and allow manual set.
- **FR-CLS-3** Allow manual reclassification (logged as feedback).

### 2.7 Field Extraction
- **FR-EXT-1** Extract structured fields per document-type schema.
- **FR-EXT-2** Store each field with value, normalized value, confidence, and
  source location (page + bbox).
- **FR-EXT-3** Store full extraction as structured JSON.
- **FR-EXT-4** Allow manual field correction (logged as feedback).

### 2.8 Comparison Engine
- **FR-CMP-1** Compare each target field against reference field(s).
- **FR-CMP-2** Detect: wrong value, missing field, extra field, formatting
  diff, OCR mistake, semantic difference.
- **FR-CMP-3** Smart normalization (numbers, dates, whitespace, casing).
- **FR-CMP-4** OCR-confusion-aware matching (O↔0, I↔1, S↔5, B↔8, etc.).
- **FR-CMP-5** Fuzzy matching with thresholds.
- **FR-CMP-6** LLM semantic check only when confidence < 90%.
- **FR-CMP-7** Assign severity (Critical / Major / Minor) per field rule.
- **FR-CMP-8** Produce explanation + suggested fix per finding.

### 2.9 Results & Reports
- **FR-RES-1** Split-screen reference vs target view.
- **FR-RES-2** Synchronized scrolling.
- **FR-RES-3** Highlight differences on the rendered document.
- **FR-RES-4** Click a finding → jump to its location in both docs.
- **FR-RES-5** Findings table: field, reference value, detected value,
  severity, explanation, suggested fix.
- **FR-RES-6** Export PDF, Excel, JSON reports.

### 2.10 History & Search
- **FR-HIS-1** Persist every verification.
- **FR-HIS-2** Re-open and re-download past reports.
- **FR-SRCH-1** Search/filter by company, date range, user, document type,
  status.

### 2.11 Learning Mode
- **FR-LRN-1** Capture manual corrections as feedback records.
- **FR-LRN-2** Admin approval queue for learning data.
- **FR-LRN-3** Approved feedback feeds normalization/matching rules &
  few-shot examples.

### 2.12 Audit & Notifications
- **FR-AUD-1** Log who uploaded/verified/edited/downloaded with timestamp+IP.
- **FR-NOT-1** Notify on: verification complete, critical errors detected,
  license expiring, quota exceeded.
- **FR-NOT-2** Channels: in-app + email (MVP); webhook (post-MVP).

### 2.13 Admin Panel
- **FR-ADM-1** Manage companies; generate/revoke license keys; suspend.
- **FR-ADM-2** Manage users across tenants.
- **FR-ADM-3** Manage subscription plans.
- **FR-ADM-4** View usage, analytics, revenue, system health.

---

## 3. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Performance** | Async pipeline; 300+ page docs supported via chunking; p95 API latency < 300ms for non-processing endpoints; status updates streamed/polled. |
| **Throughput** | Horizontal worker scaling; queue-backed; per-tenant fair scheduling. |
| **Availability** | 99.9% target for API/web; graceful degradation if LLM provider down (deterministic-only mode). |
| **Scalability** | Stateless API; workers scale by queue depth; DB read replicas; object storage for files. |
| **Security** | HTTPS everywhere, RBAC, encrypted storage (at rest + in transit), virus scan, OWASP Top-10 mitigations, audit logs. |
| **Privacy/Compliance** | Tenant data isolation; data retention policy; GDPR-style delete/export; PII handling for shipper/consignee data. |
| **Reliability** | Idempotent jobs; retries with backoff; dead-letter queue; exactly-once report generation. |
| **Observability** | Structured logs, metrics, traces; per-job timeline; error tracking. |
| **Maintainability** | Modular monolith → service-ready; typed contracts (TS + Pydantic); schema-driven doc types. |
| **Cost** | LLM gated behind confidence threshold; caching; spot/auto-scaled workers. |
| **Accessibility** | WCAG 2.1 AA on web app; keyboard navigation; dark/light mode. |
| **Internationalization** | Multi-language OCR; UTF-8 throughout; i18n-ready frontend. |
| **Portability** | Dockerized; cloud-agnostic core (S3-compatible storage). |

---

## 4. High-Level Architecture Diagram

```
                              ┌───────────────────────────┐
                              │          Users            │
                              │  (Browser — Web App only)  │
                              └─────────────┬─────────────┘
                                            │ HTTPS
                                  ┌─────────▼─────────┐
                                  │   CDN / WAF        │
                                  │  (CloudFront)      │
                                  └─────────┬─────────┘
                                            │
                                  ┌─────────▼─────────┐
                                  │      Nginx         │
                                  │  Reverse Proxy /   │
                                  │  TLS / Rate Limit  │
                                  └────┬──────────┬────┘
                                       │          │
                  ┌────────────────────▼──┐   ┌───▼───────────────────────┐
                  │  Next.js Frontend      │   │   FastAPI Backend (API)    │
                  │  (SSR/ISR, React, TS)  │   │   Auth, REST, RBAC,        │
                  │                        │   │   presigned URLs, status   │
                  └────────────────────────┘   └───┬───────────────┬───────┘
                                                    │               │
                                       enqueue jobs │               │ read/write
                                                    │               │
                                         ┌──────────▼─────┐   ┌─────▼──────────┐
                                         │   Redis         │   │  PostgreSQL    │
                                         │ Queue + Cache   │   │ (primary +     │
                                         │ (Celery broker) │   │  read replica) │
                                         └──────────┬─────┘   └─────┬──────────┘
                                                    │               │
                              ┌─────────────────────▼───────────────▼─────────────────┐
                              │              Worker Pool (Celery)                       │
                              │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐ │
                              │  │ Ingest/  │ │   OCR    │ │ Classify │ │ Extract / │ │
                              │  │ Virus    │ │ Pipeline │ │  Worker  │ │ Compare / │ │
                              │  │ Scan     │ │          │ │          │ │ Report    │ │
                              │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬─────┘ │
                              └───────┼────────────┼────────────┼─────────────┼───────┘
                                      │            │            │             │
                  ┌───────────────────▼───┐  ┌─────▼──────┐  ┌──▼───────────┐ │
                  │  Object Storage (S3)   │  │ OCR Engines│  │ LLM Provider │ │
                  │  raw files, renders,   │  │ Paddle /   │  │ GPT-5.5 API  │◄┘
                  │  reports               │  │ DocTR /    │  │ (gated)      │
                  │                        │  │ Tesseract  │  └──────────────┘
                  └────────────────────────┘  └────────────┘
```

---

## 5. Low-Level Architecture

### 5.1 Style
**Modular monolith** for backend (single deployable FastAPI app organized into
bounded modules) + **separate worker process** sharing the same codebase.
This keeps MVP velocity high while preserving clean seams to split into
microservices later (each module owns its tables and exposes an internal
service interface).

### 5.2 Backend Modules (bounded contexts)

| Module | Responsibility | Owns tables |
|---|---|---|
| `auth` | registration, login, JWT, password reset, 2FA | users, refresh_tokens |
| `tenancy` | companies, licenses, plans, quotas, invites | companies, licenses, plans, invites, usage_counters |
| `storage` | presigned URLs, file metadata, virus-scan status | files |
| `ingestion` | verification jobs, document grouping (ref/target) | verifications, documents |
| `ocr` | OCR orchestration + results | ocr_results, pages |
| `classification` | doc-type detection | (writes documents.doc_type) |
| `extraction` | field extraction + schemas | extracted_fields, field_schemas |
| `comparison` | matching engine, findings, severity | comparisons, findings |
| `reporting` | PDF/Excel/JSON generation | reports |
| `learning` | feedback capture + approval | feedback, learning_rules |
| `audit` | activity log | audit_logs |
| `notifications` | in-app + email | notifications |
| `admin` | platform-wide management & analytics | (cross-module reads) |

### 5.3 Internal Service Layering (per module)

```
Router (FastAPI)  →  Service (business logic)  →  Repository (SQLAlchemy)  →  DB
        │                     │
        │                     └→ Tasks (Celery)  →  Engines (OCR/LLM)  →  S3 / Provider
        └→ Schemas (Pydantic DTOs)  ←→  Domain models
```

### 5.4 Pipeline Orchestration

A verification runs as a **Celery chord/chain** with a state machine persisted
on the `verifications` row:

```
QUEUED → INGESTING → OCR → CLASSIFYING → EXTRACTING → COMPARING → REPORTING → COMPLETED
                                                                   └→ FAILED (any stage)
```

Each stage is idempotent and writes a `job_events` timeline row. Failures move
to a dead-letter queue with retry policy (3 retries, exponential backoff).

### 5.5 Configuration-Driven Document Types

Each document type is defined by a **field schema** (JSON/YAML):
field name, data type, normalizer, severity, required?, extraction hints,
synonyms/aliases (header labels). Adding a new vertical = adding schemas, not
code rewrites.

---

## 6. Folder Structure

```
papery/
├── docs/
│   ├── ARCHITECTURE.md            # this document
│   └── adr/                       # architecture decision records
├── docker-compose.yml
├── .github/workflows/             # CI/CD
│
├── frontend/                      # Next.js + React + TS + Tailwind
│   ├── public/
│   ├── src/
│   │   ├── app/                   # Next.js App Router
│   │   │   ├── (marketing)/       # landing, pricing, faq, contact
│   │   │   ├── (auth)/            # login, register, reset
│   │   │   ├── (dashboard)/       # app shell (license-gated)
│   │   │   │   ├── verify/        # upload + result split-screen
│   │   │   │   ├── history/
│   │   │   │   ├── search/
│   │   │   │   ├── team/
│   │   │   │   └── settings/
│   │   │   └── (admin)/           # platform admin
│   │   ├── components/            # ui primitives, viewer, tables
│   │   ├── features/              # feature-scoped logic
│   │   ├── lib/                   # api client, auth, hooks
│   │   ├── stores/                # client state (Zustand)
│   │   └── styles/
│   ├── package.json
│   └── tsconfig.json
│
├── backend/                       # FastAPI (API + workers, shared code)
│   ├── app/
│   │   ├── main.py                # FastAPI app factory
│   │   ├── core/                  # config, security, db, deps, logging
│   │   ├── modules/
│   │   │   ├── auth/              # router, service, repo, schemas, models
│   │   │   ├── tenancy/
│   │   │   ├── storage/
│   │   │   ├── ingestion/
│   │   │   ├── ocr/
│   │   │   ├── classification/
│   │   │   ├── extraction/
│   │   │   ├── comparison/
│   │   │   ├── reporting/
│   │   │   ├── learning/
│   │   │   ├── audit/
│   │   │   ├── notifications/
│   │   │   └── admin/
│   │   ├── workers/               # celery app, task routing, pipeline
│   │   ├── engines/               # ocr/, llm/, normalize/, matching/
│   │   └── schemas_doctypes/      # field schemas per document type (YAML)
│   ├── alembic/                   # DB migrations
│   ├── tests/                     # unit, integration, e2e
│   ├── pyproject.toml
│   └── Dockerfile
│
├── infra/                         # IaC (Terraform), nginx, k8s manifests
│   ├── terraform/
│   ├── nginx/
│   └── k8s/
└── scripts/                       # ops, seed, license-keygen
```

---

## 7. Database Schema

PostgreSQL. All tenant-owned tables carry `company_id` for isolation +
row-level scoping. UUID primary keys. `created_at`/`updated_at` everywhere.
JSONB used for flexible structured payloads.

```sql
-- ===== Tenancy =====
plans (
  id UUID PK,
  name TEXT,                       -- Free, Pro, Enterprise
  monthly_document_limit INT,
  max_users INT,
  price_cents INT,
  features JSONB,
  is_active BOOL,
  created_at, updated_at
)

companies (
  id UUID PK,
  name TEXT,
  status TEXT,                     -- ACTIVE | SUSPENDED | EXPIRED | PENDING
  created_at, updated_at
)

licenses (
  id UUID PK,
  company_id UUID FK -> companies,
  plan_id UUID FK -> plans,
  license_key TEXT UNIQUE,         -- hashed lookup + display prefix
  status TEXT,                     -- ACTIVE | SUSPENDED | EXPIRED | UNACTIVATED
  activated_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  created_at, updated_at
)

usage_counters (
  id UUID PK,
  company_id UUID FK,
  period_start DATE,               -- monthly bucket
  documents_used INT DEFAULT 0,
  UNIQUE (company_id, period_start)
)

-- ===== Users & Auth =====
users (
  id UUID PK,
  company_id UUID FK -> companies (nullable for platform super-admin),
  email CITEXT UNIQUE,
  password_hash TEXT,              -- bcrypt
  full_name TEXT,
  role TEXT,                       -- SUPER_ADMIN | ADMIN | MANAGER | STAFF
  status TEXT,                     -- ACTIVE | INVITED | DISABLED
  email_verified BOOL,
  totp_secret TEXT NULL,
  last_login_at TIMESTAMPTZ,
  created_at, updated_at
)

refresh_tokens (
  id UUID PK,
  user_id UUID FK,
  token_hash TEXT,
  expires_at TIMESTAMPTZ,
  revoked BOOL DEFAULT false,
  created_at
)

invites (
  id UUID PK,
  company_id UUID FK,
  email CITEXT,
  role TEXT,
  token_hash TEXT,
  status TEXT,                     -- PENDING | ACCEPTED | EXPIRED
  expires_at TIMESTAMPTZ,
  created_at
)

password_resets (
  id UUID PK, user_id UUID FK, token_hash TEXT,
  expires_at TIMESTAMPTZ, used BOOL, created_at
)

-- ===== Files & Verification =====
files (
  id UUID PK,
  company_id UUID FK,
  uploaded_by UUID FK -> users,
  s3_key TEXT,
  original_name TEXT,
  mime_type TEXT,
  size_bytes BIGINT,
  page_count INT,
  checksum TEXT,                   -- sha256
  virus_scan_status TEXT,          -- PENDING | CLEAN | INFECTED
  created_at
)

verifications (
  id UUID PK,
  company_id UUID FK,
  created_by UUID FK -> users,
  title TEXT,
  status TEXT,                     -- QUEUED | INGESTING | OCR | CLASSIFYING
                                   -- | EXTRACTING | COMPARING | REPORTING
                                   -- | COMPLETED | FAILED
  overall_result TEXT,            -- PASS | WARN | FAIL
  critical_count INT, major_count INT, minor_count INT,
  error_message TEXT NULL,
  created_at, updated_at, completed_at
)

documents (
  id UUID PK,
  verification_id UUID FK -> verifications,
  file_id UUID FK -> files,
  role TEXT,                       -- REFERENCE | TARGET
  doc_type TEXT,                   -- BOOKING | SI | DRAFT_BL | ... | UNKNOWN
  doc_type_confidence NUMERIC,
  language TEXT,
  created_at
)

pages (
  id UUID PK,
  document_id UUID FK,
  page_index INT,
  width INT, height INT,
  render_s3_key TEXT,              -- rasterized page image for viewer
  created_at
)

ocr_results (
  id UUID PK,
  document_id UUID FK,
  page_index INT,
  engine TEXT,                     -- PADDLE | TESSERACT | DOCTR | NATIVE_PDF
  text TEXT,
  tokens JSONB,                    -- [{text, bbox:[x,y,w,h], conf}]
  tables JSONB,
  rotation INT,
  confidence NUMERIC,
  created_at
)

-- ===== Extraction & Comparison =====
field_schemas (
  id UUID PK,
  doc_type TEXT,
  version INT,
  schema JSONB,                    -- field defs, normalizers, severity
  is_active BOOL,
  created_at
)

extracted_fields (
  id UUID PK,
  document_id UUID FK,
  field_key TEXT,                  -- booking_number, bl_number, ...
  raw_value TEXT,
  normalized_value TEXT,
  confidence NUMERIC,
  source_page INT,
  source_bbox JSONB,               -- [x,y,w,h]
  created_at
)

comparisons (
  id UUID PK,
  verification_id UUID FK,
  reference_document_id UUID FK -> documents,
  target_document_id UUID FK -> documents,
  status TEXT,
  created_at
)

findings (
  id UUID PK,
  comparison_id UUID FK,
  field_key TEXT,
  reference_value TEXT,
  detected_value TEXT,
  match_type TEXT,                 -- EXACT | NORMALIZED | FUZZY | SEMANTIC
                                   -- | MISMATCH | MISSING | EXTRA
  severity TEXT,                   -- CRITICAL | MAJOR | MINOR
  confidence NUMERIC,
  used_llm BOOL,
  explanation TEXT,
  suggested_fix TEXT,
  reference_location JSONB,        -- {page, bbox}
  target_location JSONB,
  status TEXT,                     -- OPEN | ACCEPTED | DISMISSED | CORRECTED
  created_at
)

-- ===== Reports, Learning, Audit, Notifications =====
reports (
  id UUID PK,
  verification_id UUID FK,
  format TEXT,                     -- PDF | XLSX | JSON
  s3_key TEXT,
  generated_by UUID FK,
  created_at
)

feedback (
  id UUID PK,
  company_id UUID FK,
  finding_id UUID FK NULL,
  field_key TEXT,
  original_value TEXT,
  corrected_value TEXT,
  correction_type TEXT,            -- RECLASSIFY | FIELD_FIX | VERDICT_OVERRIDE
  created_by UUID FK,
  approval_status TEXT,            -- PENDING | APPROVED | REJECTED
  approved_by UUID FK NULL,
  created_at
)

learning_rules (
  id UUID PK,
  company_id UUID FK NULL,         -- null = global
  scope TEXT,                      -- NORMALIZER | ALIAS | THRESHOLD
  rule JSONB,
  derived_from_feedback UUID FK NULL,
  is_active BOOL,
  created_at
)

audit_logs (
  id UUID PK,
  company_id UUID FK NULL,
  user_id UUID FK NULL,
  action TEXT,                     -- UPLOAD | VERIFY | EDIT | DOWNLOAD | LOGIN ...
  entity_type TEXT, entity_id UUID,
  metadata JSONB,
  ip_address INET,
  user_agent TEXT,
  created_at
)

notifications (
  id UUID PK,
  company_id UUID FK,
  user_id UUID FK,
  type TEXT,                       -- VERIFICATION_DONE | CRITICAL | LICENSE_EXP | QUOTA
  title TEXT, body TEXT,
  read BOOL DEFAULT false,
  created_at
)

job_events (                       -- pipeline timeline / observability
  id UUID PK,
  verification_id UUID FK,
  stage TEXT, status TEXT,
  detail JSONB, duration_ms INT,
  created_at
)
```

**Key indexes:** `verifications(company_id, created_at)`,
`documents(verification_id)`, `extracted_fields(document_id, field_key)`,
`findings(comparison_id, severity)`, `audit_logs(company_id, created_at)`,
`usage_counters(company_id, period_start)`, full-text/trigram on
`verifications.title` and `findings` values for search.

---

## 8. API Endpoint Specification

REST, JSON, versioned under `/api/v1`. Auth via `Authorization: Bearer
<access_jwt>`. All mutating endpoints are RBAC-checked and audit-logged.
Tenant scoping is implicit from the JWT's `company_id`.

### 8.1 Auth
| Method | Path | Role | Description |
|---|---|---|---|
| POST | `/auth/register` | public | Create user + company (admin), send verify email |
| POST | `/auth/verify-email` | public | Confirm email token |
| POST | `/auth/login` | public | Returns access + refresh token |
| POST | `/auth/refresh` | public | Rotate access token |
| POST | `/auth/logout` | auth | Revoke refresh token |
| POST | `/auth/forgot-password` | public | Send reset link |
| POST | `/auth/reset-password` | public | Set new password |
| GET  | `/auth/me` | auth | Current user + company + license summary |

### 8.2 Tenancy / License
| Method | Path | Role | Description |
|---|---|---|---|
| POST | `/license/activate` | Admin | Activate company with license key |
| GET  | `/license` | Admin/Manager | License status, plan, quota usage |
| GET  | `/company` | Admin | Company profile |
| PATCH| `/company` | Admin | Update company profile |

### 8.3 Team
| Method | Path | Role | Description |
|---|---|---|---|
| POST | `/team/invites` | Admin | Invite member |
| GET  | `/team/members` | Admin/Manager | List members |
| PATCH| `/team/members/{id}` | Admin | Change role/status |
| POST | `/team/invites/accept` | public | Accept invite + set password |

### 8.4 Files & Verification
| Method | Path | Role | Description |
|---|---|---|---|
| POST | `/files/presign` | Staff+ | Get presigned S3 upload URL |
| POST | `/files/confirm` | Staff+ | Register uploaded file metadata; trigger scan |
| POST | `/verifications` | Staff+ | Create verification (ref + target file ids) → enqueue |
| GET  | `/verifications` | Staff+ | List/search (filters: date,user,type,status) |
| GET  | `/verifications/{id}` | Staff+ | Detail incl. status + counts |
| GET  | `/verifications/{id}/status` | Staff+ | Lightweight poll / SSE stream |
| GET  | `/verifications/{id}/documents` | Staff+ | Documents + pages + render URLs |
| GET  | `/verifications/{id}/findings` | Staff+ | Findings list |
| PATCH| `/findings/{id}` | Staff+ | Accept/dismiss/correct (→ feedback) |
| DELETE | `/verifications/{id}` | Manager+ | Soft-delete |

### 8.5 Reports
| Method | Path | Role | Description |
|---|---|---|---|
| POST | `/verifications/{id}/reports` | Staff+ | Generate report (format) |
| GET  | `/verifications/{id}/reports` | Staff+ | List reports |
| GET  | `/reports/{id}/download` | Staff+ | Presigned download URL |

### 8.6 Learning / Feedback
| Method | Path | Role | Description |
|---|---|---|---|
| GET  | `/feedback` | Manager+ | List feedback |
| GET  | `/feedback/pending` | Admin | Approval queue |
| PATCH| `/feedback/{id}` | Admin | Approve/reject |

### 8.7 Notifications / Audit
| Method | Path | Role | Description |
|---|---|---|---|
| GET  | `/notifications` | auth | List |
| PATCH| `/notifications/{id}/read` | auth | Mark read |
| GET  | `/audit` | Admin/Manager | Audit log (scoped) |

### 8.8 Platform Admin (`/api/v1/admin`, SUPER_ADMIN)
| Method | Path | Description |
|---|---|---|
| GET/POST | `/admin/companies` | List/create companies |
| PATCH | `/admin/companies/{id}` | Suspend/activate |
| POST | `/admin/licenses` | Generate license key |
| PATCH | `/admin/licenses/{id}` | Revoke/extend |
| GET/POST/PATCH | `/admin/plans` | Manage plans |
| GET | `/admin/users` | Cross-tenant users |
| GET | `/admin/analytics` | Usage, revenue, KPIs |
| GET | `/admin/health` | System health |

**Conventions:** cursor pagination; `409` on quota exceeded with
`code=QUOTA_EXCEEDED`; `402` on inactive license; consistent error envelope
`{error:{code,message,details}}`; idempotency keys on POST `/verifications`.

---

## 9. OCR Pipeline

```
File (S3) ─► [1] Type sniff (magic bytes)
                 │
   ┌─────────────┼──────────────────────────────┐
   │ PDF                    DOCX            IMAGE │
   ▼                          ▼                 ▼
[2a] PDF text layer?     [2b] Convert      [2c] decode
   │  yes ──► extract        DOCX→PDF/text     image
   │  no ───► rasterize         │                │
   ▼          pages             ▼                ▼
[3] Pre-process each page image:
    de-skew → rotate-detect → denoise → binarize/contrast → upscale if low-DPI
                 │
                 ▼
[4] Language detection (per page)
                 │
                 ▼
[5] OCR engine selection:
    Primary: PaddleOCR (det+rec+cls, table mode)
    If avg confidence < threshold OR layout fails ─► DocTR
    If still low ─► Tesseract (lang packs)
                 │
                 ▼
[6] Table structure recognition (PP-Structure)
                 │
                 ▼
[7] Post-process: merge tokens→lines→blocks; keep bbox+conf; reading order
                 │
                 ▼
[8] Persist ocr_results (text, tokens, tables, bbox, rotation, confidence)
    + store page render images for the viewer
                 │
                 ▼
[9] Chunking for 300+ pages: process in page-batches across workers,
    stream partial results, aggregate per document
```

**Decisions:** Native PDF text is preferred (fast, free, exact). OCR is fully
automatic — the user never selects a mode. Confidence-driven fallback chain
balances accuracy and cost. Handwriting is best-effort via Paddle/DocTR and
flagged low-confidence.

---

## 10. Document Classification Flow

```
OCR text + layout features per document
        │
        ▼
[1] Fast heuristic pass (cheap, deterministic):
    - keyword/anchor matching ("BILL OF LADING", "BOOKING CONFIRMATION",
      "PACKING LIST", "COMMERCIAL INVOICE", carrier templates)
    - layout signature (logo zones, table patterns)
    → candidate type + heuristic confidence
        │
        ├─ confidence ≥ 0.90 ──► assign doc_type ──► done
        │
        ▼ (low confidence)
[2] ML/embedding classifier:
    - text embedding → nearest doc-type centroid / lightweight classifier
    → candidate + confidence
        │
        ├─ confidence ≥ threshold ──► assign
        │
        ▼ (still ambiguous)
[3] LLM classification (gated, cheap prompt with label set + snippets)
    → doc_type + confidence + rationale
        │
        ▼
[4] If all low ─► doc_type = UNKNOWN; surface manual selector to user
    (manual choice logged as feedback for learning)
        │
        ▼
[5] Persist documents.doc_type + confidence; select field_schema(doc_type)
```

Supported types map to enum: BOOKING, SI, DRAFT_BL, FINAL_BL, SEA_WAYBILL,
COMMERCIAL_INVOICE, INVOICE, PACKING_LIST, DELIVERY_ORDER, FREIGHT_REQUEST,
ERP_SCREENSHOT, PURCHASE_ORDER, CONTRACT, UNKNOWN.

---

## 11. Field Extraction Flow

```
doc_type → load field_schema (fields, aliases, normalizers, severity)
        │
        ▼
[1] Anchor/label extraction (deterministic):
    - find field labels & synonyms ("Booking No", "Bkg #", "B/L No")
    - take value by spatial relation (right-of / below label) using bbox
    - regex validators (container ISO 6346, dates, weights, CBM)
        │
        ▼
[2] Table extraction:
    - map recognized tables → line items (commodity, qty, weight, package)
        │
        ▼
[3] Confidence scoring per field (label match × OCR conf × regex valid)
        │
        ├─ field confidence ≥ 0.90 ──► accept
        │
        ▼ (low/missing critical fields)
[4] LLM structured extraction (gated):
    - prompt with doc text + JSON schema (function/structured output)
    - only for missing/low-confidence fields → cost control
        │
        ▼
[5] Normalize each value (normalized_value):
    numbers (26,557.680 → 26557.68), dates → ISO, whitespace, case,
    container/seal canonical form
        │
        ▼
[6] Persist extracted_fields (raw, normalized, confidence, page, bbox)
    + full structured JSON snapshot per document
```

---

## 12. AI Comparison Flow

```
For each TARGET document, pair with relevant REFERENCE document(s)
(by doc-type relationship rules, e.g. Draft B/L ↔ Booking + SI)
        │
        ▼
For each field_key in union(ref, target):
        │
  ┌─────┴──────────────────────────────────────────────┐
  │ MISSING in target & required ─► finding MISSING      │
  │ EXTRA in target only         ─► finding EXTRA(minor) │
  └─────┬──────────────────────────────────────────────┘
        ▼ (both present)
[1] EXACT compare normalized_value
        │ equal ─► EXACT match (no finding / PASS)
        ▼ not equal
[2] Smart normalization re-check:
    - numeric tolerance (trailing zeros, thousands sep)
    - date format equivalence
    - whitespace/case/punctuation
        │ equal ─► NORMALIZED match (PASS, maybe MINOR formatting note)
        ▼ not equal
[3] OCR-confusion-aware compare:
    - apply confusion map (O↔0,I↔1,S↔5,B↔8,Z↔2,...) within edit distance
        │ resolves ─► flag likely OCR (MINOR/MAJOR by field) + suggested fix
        ▼ not resolved
[4] Fuzzy match (token/char similarity, e.g. Jaro-Winkler/Levenshtein ratio)
        │ similarity ≥ field threshold ─► FUZZY (severity by field)
        ▼ confidence < 0.90
[5] LLM semantic check (GATED — only here):
    - "are these the same entity/value semantically?"
      (e.g. abbreviated company name, address reorder, synonym commodity)
    - returns verdict + explanation + suggested fix
        │
        ▼
[6] Severity assignment from field_schema:
    CRITICAL: booking_no, bl_no, container_no, seal_no, weight, consignee,
              shipper, port_*, eta, etd, vessel
    MAJOR:    invoice_no, commodity, quantity, address
    MINOR:    formatting, spacing, capitalization
        │
        ▼
[7] Persist findings (match_type, severity, confidence, used_llm,
    explanation, suggested_fix, ref/target locations)
        │
        ▼
[8] Roll up verification.overall_result:
    any CRITICAL open ─► FAIL ; only MAJOR ─► WARN ; else ─► PASS
```

**Cost control:** Stages 1–4 are deterministic and free; LLM (stage 5) runs
only when confidence < 90%. Identical field-pair comparisons are cached by a
hash of (field_key, ref_norm, target_norm).

---

## 13. File Upload Flow

```
User selects files & assigns ref/target
        │
[1] Frontend ─► POST /files/presign (per file: name, type, size)
        │       API validates plan/quota, returns presigned S3 PUT URL
        ▼
[2] Browser ─► PUT file directly to S3 (progress bar)
        │
[3] Frontend ─► POST /files/confirm (s3_key, checksum)
        │       API records files row (PENDING scan)
        ▼
[4] Async virus scan (ClamAV worker) ─► CLEAN | INFECTED
        │  INFECTED ─► quarantine + reject + notify
        ▼
[5] Frontend ─► POST /verifications (reference_file_ids[], target_file_ids[])
        │       API checks quota → increments usage_counter → enqueue pipeline
        ▼
[6] Verification status = QUEUED; UI subscribes to /status (SSE/poll)
```

**Validations:** magic-byte type check (not just extension), size limit per
plan, page-count cap, checksum dedupe.

---

## 14. Authentication Flow

```
Register:
  POST /auth/register → create company(PENDING)+user(ADMIN, email_verified=false)
       → email verification token (signed, expiring)
  POST /auth/verify-email → email_verified=true

Login:
  POST /auth/login (email,password)
       → bcrypt.verify → issue access JWT (15 min) + refresh token (7–30 d, hashed in DB)
       → [optional] TOTP challenge if 2FA enabled
  Access JWT claims: sub(user_id), company_id, role, exp

Authorized request:
  Authorization: Bearer <access JWT>
       → middleware verifies signature+exp → loads principal → RBAC check
       → license gate (must be ACTIVE for dashboard endpoints)

Refresh:
  POST /auth/refresh (refresh token) → validate+rotate → new access (+new refresh)

Logout:
  POST /auth/logout → revoke refresh token (revoked=true)

Reset:
  POST /auth/forgot-password → email signed token
  POST /auth/reset-password → verify token → bcrypt new password → revoke sessions
```

Security: short access tokens; refresh rotation + reuse detection; tokens
stored hashed; httpOnly secure cookies option for refresh; rate-limited auth
endpoints.

---

## 15. License Activation Flow

```
Platform admin generates key:
  POST /admin/licenses (company_id, plan_id, expires_at)
       → key = prefix + random; store hash; status=UNACTIVATED
       → deliver key to company admin

Company admin activates:
  POST /license/activate (license_key)
       → lookup by hash → validate not expired/revoked/already-bound
       → bind to company → license.status=ACTIVE, company.status=ACTIVE
       → set quota period; emit audit log

Runtime enforcement (every dashboard request / verification create):
  - license.status must be ACTIVE and now < expires_at
       else 402 PAYMENT_REQUIRED / dashboard blocked
  - monthly quota: usage_counters.documents_used < plan.monthly_document_limit
       else 409 QUOTA_EXCEEDED + notify
  - seats: active users < plan.max_users on invite

Lifecycle:
  expiry job → status=EXPIRED + notify (T-14, T-7, T-1 days)
  admin can SUSPEND (immediate block) or extend (new expires_at)
```

---

## 16. User Permission Matrix

Roles: **SUPER_ADMIN** (Papery platform), **ADMIN** (company), **MANAGER**,
**STAFF**.

| Capability | Staff | Manager | Admin | Super Admin |
|---|:--:|:--:|:--:|:--:|
| Upload & create verification | ✅ | ✅ | ✅ | ✅ |
| View own verifications | ✅ | ✅ | ✅ | ✅ |
| View all company verifications | ❌ | ✅ | ✅ | ✅ |
| Correct findings / fields | ✅ | ✅ | ✅ | ✅ |
| Generate/download reports | ✅ | ✅ | ✅ | ✅ |
| Delete verification | ❌ | ✅ | ✅ | ✅ |
| Search & history (company-wide) | ❌ | ✅ | ✅ | ✅ |
| View audit log | ❌ | ✅(scoped) | ✅ | ✅ |
| Approve learning feedback | ❌ | ❌ | ✅ | ✅ |
| Invite/manage team members | ❌ | ❌ | ✅ | ✅ |
| Manage company profile | ❌ | ❌ | ✅ | ✅ |
| Activate/view license | ❌ | view | ✅ | ✅ |
| Manage companies (cross-tenant) | ❌ | ❌ | ❌ | ✅ |
| Generate/revoke licenses | ❌ | ❌ | ❌ | ✅ |
| Manage subscription plans | ❌ | ❌ | ❌ | ✅ |
| View revenue/global analytics | ❌ | ❌ | ❌ | ✅ |
| System health | ❌ | ❌ | ❌ | ✅ |

---

## 17. Landing Page Structure

Marketing site (Next.js, SSR/ISR for SEO). Dark + light mode, responsive.

```
Navbar (logo, Features, Pricing, FAQ, Contact, Login, Sign up, theme toggle)
 ├─ Hero            : headline, subhead, primary CTA, product visual/demo
 ├─ Logos / Trust   : "trusted by freight forwarders" strip
 ├─ Features        : OCR, auto-classify, smart compare, severity, reports
 ├─ How It Works    : 1 Upload → 2 AI verifies → 3 Get report (3-step)
 ├─ Benefits        : time saved, error reduction, cost avoidance, audit
 ├─ Pricing         : Free / Pro / Enterprise (monthly doc limits, seats)
 ├─ Testimonials    : quotes, metrics
 ├─ FAQ             : security, file types, accuracy, pricing
 ├─ Contact / CTA   : demo request form, sign-up
 └─ Footer          : links, legal (Privacy, Terms), social
```

---

## 18. Dashboard Structure

License-gated app shell.

```
Top bar: company name, license/quota chip, notifications bell, user menu, theme
Sidebar:
  • Dashboard (overview)        – KPIs: verifications this month, critical
                                  errors found, quota usage, recent activity
  • New Verification            – upload ref + target, start
  • History                     – list with status, result, severity counts
  • Search                      – filters: date, user, doc type, status
  • Team (Admin)                – members, invites, roles
  • Settings                    – company, license, notifications, profile
Main:
  • Verification Result         – split-screen viewer + findings panel
```

---

## 19. Admin Dashboard Structure

Platform super-admin console (separate route group, SUPER_ADMIN only).

```
Sidebar:
  • Overview        – MRR, active companies, docs processed, system health
  • Companies       – list, status, suspend/activate, drill-down
  • Licenses        – generate, revoke, extend, bind status
  • Plans           – CRUD subscription plans (limits, price, features)
  • Users           – cross-tenant search, disable
  • Usage Analytics – per-company doc volume, OCR/LLM cost, trends
  • Revenue         – MRR/ARR, plan distribution, churn
  • System Health   – queue depth, worker status, error rates, OCR/LLM latency
  • Audit           – global activity log
```

---

## 20. UI Wireframes (ASCII)

### 20.1 Landing — Hero
```
┌───────────────────────────────────────────────────────────────┐
│ Papery    Features  Pricing  FAQ  Contact      [Login] [Sign up]│
├───────────────────────────────────────────────────────────────┤
│                                                                 │
│   Stop checking documents by hand.                              │
│   Papery verifies them in seconds.                              │
│                                                                 │
│   AI compares your shipping docs, finds every mismatch,         │
│   and proves it.            [ Start free ]  [ Watch demo ]      │
│                                                                 │
│        ┌───────────────┐        ┌───────────────┐              │
│        │  Booking.pdf  │  ───►   │  Draft BL.pdf │  ✓ 3 errors  │
│        └───────────────┘        └───────────────┘              │
└───────────────────────────────────────────────────────────────┘
```

### 20.2 New Verification (Upload)
```
┌──────────────────────────────────────────────────────────────┐
│  New Verification                          Quota: 142 / 500    │
├───────────────────────────────┬──────────────────────────────┤
│  REFERENCE DOCUMENTS          │  TARGET DOCUMENT(S)           │
│  ┌──────────────────────────┐ │  ┌─────────────────────────┐ │
│  │  ⬆ Drag & drop / browse  │ │  │  ⬆ Drag & drop / browse │ │
│  │  Booking.pdf      ✓ 4p   │ │  │  Draft BL.pdf    ⟳ scan │ │
│  │  SI.pdf           ✓ 2p   │ │  └─────────────────────────┘ │
│  │  Invoice.pdf      ✓ 1p   │ │                              │
│  └──────────────────────────┘ │  Detected: DRAFT_BL (0.97)   │
│  PDF DOCX PNG JPG TIFF        │                              │
├───────────────────────────────┴──────────────────────────────┤
│                                       [ Cancel ] [ Verify ▶ ]  │
└──────────────────────────────────────────────────────────────┘
```

### 20.3 Processing Status
```
┌──────────────────────────────────────────────────────────────┐
│  Verifying… "Booking vs Draft BL"                             │
│                                                                │
│  ✓ Ingest     ✓ OCR     ✓ Classify    ⟳ Extract    · Compare │
│  ████████████████████████░░░░░░░░░░  68%                       │
└──────────────────────────────────────────────────────────────┘
```

### 20.4 Result — Split Screen
```
┌──────────────────────────────────────────────────────────────────────┐
│ Result: FAIL  ● 2 Critical  ● 1 Major  ● 3 Minor   [PDF][XLSX][JSON]   │
├──────────────────────────────┬───────────────────────────────────────┤
│  REFERENCE (Booking.pdf)     │  TARGET (Draft BL.pdf)                  │
│  ┌─────────────────────────┐ │  ┌──────────────────────────────────┐  │
│  │ Booking: SITGUAYE12345  │ │  │ Booking: SITGUAYE12345           │  │
│  │ Container: TCLU1234567 ◄─┼─┼─►│ Container: TCLU1234561  ✖CRIT   │  │
│  │ Weight: 26,557.68 kg    │ │  │ Weight: 26557.680 kg    ~MINOR   │  │
│  └─────────────────────────┘ │  └──────────────────────────────────┘  │
│   (synchronized scroll ⇅)     │   (synchronized scroll ⇅)              │
├──────────────────────────────┴───────────────────────────────────────┤
│ FINDINGS                                                               │
│ ┌───────────┬───────────────┬──────────────┬──────────┬────────────┐ │
│ │ Field     │ Reference     │ Detected     │ Severity │ Action     │ │
│ ├───────────┼───────────────┼──────────────┼──────────┼────────────┤ │
│ │ Container │ TCLU1234567   │ TCLU1234561  │ CRITICAL │ [Fix][Dis] │ │
│ │ Seal No   │ ML-998877     │ (missing)    │ CRITICAL │ [Fix][Dis] │ │
│ │ Weight    │ 26,557.68     │ 26557.680    │ MINOR    │ identical  │ │
│ └───────────┴───────────────┴──────────────┴──────────┴────────────┘ │
│ ▸ Container: last digit 7→1 likely OCR/typo. Suggested fix: TCLU1234567│
└───────────────────────────────────────────────────────────────────────┘
```

### 20.5 History / Search
```
┌──────────────────────────────────────────────────────────────┐
│ History           [Date▼][User▼][Type▼][Status▼]  🔍 search… │
├──────┬───────────────────┬─────────┬────────┬────────┬───────┤
│ Date │ Title             │ Type    │ User   │ Result │       │
├──────┼───────────────────┼─────────┼────────┼────────┼───────┤
│ 6/27 │ Booking vs BL     │ DRAFT_BL│ A.Lee  │ ● FAIL │ ⬇ ↗  │
│ 6/26 │ SI vs BL          │ FINAL_BL│ M.Tan  │ ● PASS │ ⬇ ↗  │
└──────┴───────────────────┴─────────┴────────┴────────┴───────┘
```

### 20.6 Admin — Companies
```
┌──────────────────────────────────────────────────────────────┐
│ Admin ▸ Companies                         [ + New License ]    │
├───────────────┬────────┬──────────┬───────────┬──────────────┤
│ Company       │ Plan   │ Status   │ Docs (mo) │ Expires      │
├───────────────┼────────┼──────────┼───────────┼──────────────┤
│ Acme Freight  │ Pro    │ ● ACTIVE │ 142/500   │ 2026-12-01   │
│ Globex Logis. │ Ent.   │ ⏸ SUSPND │ 0/5000    │ 2026-09-15   │
└───────────────┴────────┴──────────┴───────────┴──────────────┘
```

---

## 21. ER Diagram

```
plans ──1:N── licenses ──N:1── companies ──1:N── users
                                   │                 │
                                   │ 1:N             │ 1:N (created_by)
                                   ▼                 ▼
                              usage_counters     verifications ──1:N── documents
                                                      │                   │
                                                      │ 1:N               │ 1:N
                                                      ▼                   ▼
                                                 comparisons         pages / ocr_results
                                                      │                   │
                                                      │ 1:N               │ 1:N
                                                      ▼                   ▼
                                                  findings          extracted_fields
                                                      │
                                   ┌──────────────────┼───────────────┐
                                   ▼                   ▼               ▼
                                feedback            reports        job_events
                                   │
                                   ▼
                             learning_rules

companies ──1:N── invites
users ──1:N── refresh_tokens / password_resets
companies ──1:N── files ──1:1── documents (via file_id)
companies/users ──1:N── audit_logs, notifications
field_schemas ──(doc_type)── documents / extraction
```

Cardinalities: company 1:N users/verifications/files/licenses(active 1);
verification 1:N documents/comparisons/findings/reports; document 1:N
pages/ocr_results/extracted_fields; comparison 1:N findings; finding 1:0..1
feedback.

---

## 22. Security Architecture

| Layer | Control |
|---|---|
| **Transport** | HTTPS/TLS everywhere; HSTS; TLS termination at Nginx/CDN. |
| **Edge** | WAF, DDoS protection, IP rate limiting, bot filtering. |
| **AuthN** | bcrypt password hashing; short-lived access JWT; rotating refresh tokens with reuse detection; optional TOTP 2FA; email verification. |
| **AuthZ** | RBAC enforced in API middleware; tenant scoping by `company_id` from JWT; row-level checks in repositories. |
| **Input** | Pydantic validation; magic-byte file-type checks; size/page caps; reject on schema violation. |
| **Uploads** | Presigned S3 (no large bodies via API); ClamAV virus scan + quarantine; checksum dedupe. |
| **Injection** | Parameterized queries / ORM (SQLi); output encoding + CSP (XSS); SameSite + CSRF tokens for cookie flows. |
| **Secrets** | Secrets manager (AWS Secrets Manager / SSM); no secrets in repo; rotated keys. |
| **Data at rest** | S3 SSE (KMS); RDS encryption; encrypted backups; field-level encryption option for PII. |
| **Tenant isolation** | All queries filtered by company_id; defense-in-depth tests; optional Postgres RLS. |
| **Audit** | Immutable audit_logs (who/what/when/IP/UA) on all sensitive actions. |
| **LLM safety** | Strip secrets before prompts; no training on customer data; prompt-injection guarding on extracted text; provider DPA. |
| **Rate limiting** | Per-IP + per-user + per-tenant quotas; stricter on auth endpoints. |
| **Compliance** | GDPR-style data export/delete; retention policy; access logging. |

OWASP Top-10 mapped: A01 (RBAC+tenant scope), A02 (TLS+KMS), A03 (ORM+CSP),
A05 (hardened config), A07 (auth controls), A08 (checksum/integrity),
A09 (logging/monitoring), A10 (SSRF guards on URL fetches).

---

## 23. Deployment Architecture

- **Containerization:** Docker images for frontend, API, worker, beat
  (scheduler). Multi-stage builds.
- **Orchestration:** Docker Compose for dev; Kubernetes (or ECS) for prod.
- **Reverse proxy:** Nginx (TLS, gzip, rate-limit, static) behind CDN/WAF.
- **CI/CD:** GitHub Actions — lint → type-check → test → build images → push
  to registry → deploy (staging → prod with approval gate). Alembic
  migrations run as a pre-deploy job.
- **Environments:** dev, staging, production with isolated DB/S3/secrets.
- **Zero-downtime:** rolling deploys; health/readiness probes; DB migrations
  backward-compatible (expand/contract).
- **Scaling:** API HPA on CPU/RPS; worker HPA on queue depth; separate worker
  pools for OCR (CPU/GPU) vs light tasks.

```
GitHub ─► Actions (test/build) ─► Registry ─► K8s/ECS
                                                │
                 ┌───────────┬──────────────────┼────────────────┐
                 ▼           ▼                   ▼                ▼
           frontend pods  api pods         worker pods       beat pod
                 └───────────┴──────────────────┴────────────────┘
                 managed: RDS Postgres (+replica), ElastiCache Redis,
                          S3, Secrets Manager, CloudWatch
```

---

## 24. Infrastructure Diagram

```
                         Internet
                            │
                    ┌───────▼────────┐
                    │ CloudFront CDN │  + AWS WAF
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │  Load Balancer │ (ALB, TLS)
                    └───┬────────┬───┘
                        │        │
                ┌───────▼──┐  ┌──▼─────────┐
                │ Frontend │  │  API pods  │
                │  pods    │  │ (FastAPI)  │
                └──────────┘  └──┬─────┬───┘
                                 │     │
                      ┌──────────▼┐  ┌─▼─────────────┐
                      │ ElastiCache│  │  RDS Postgres │
                      │  Redis     │  │  primary      │
                      │ broker+    │  │   └─ replica  │
                      │ cache      │  └───────────────┘
                      └─────┬──────┘
                            │ (queue)
                   ┌────────▼─────────────────────┐
                   │  Worker pods (Celery)         │
                   │  OCR pool (CPU/GPU) | general │
                   └───┬───────────────┬───────────┘
                       │               │
                ┌──────▼─────┐   ┌─────▼────────┐
                │  S3 buckets │   │ GPT-5.5 API  │
                │ files/      │   │ (egress)     │
                │ renders/    │   └──────────────┘
                │ reports     │
                └─────────────┘
        Cross-cutting: Secrets Manager, CloudWatch/Grafana, ClamAV
```

---

## 25. Scalability Plan

| Dimension | Strategy |
|---|---|
| **API tier** | Stateless pods behind LB; autoscale on RPS/CPU. |
| **Workers** | Queue-depth autoscaling; dedicated OCR pool (GPU-optional) separate from light tasks; per-tenant fair queueing to prevent noisy-neighbor. |
| **Large docs (300+ pages)** | Chunked page-batch processing across workers; partial result streaming; aggregate per document. |
| **Database** | Read replicas for history/search/analytics; connection pooling (PgBouncer); partition large tables (audit_logs, findings) by month; archive cold data. |
| **Caching** | Redis for sessions, status, field-pair comparison cache, classification embeddings; HTTP/CDN cache for marketing + static. |
| **Storage** | S3 scales infinitely; lifecycle policies move old files to cold tiers. |
| **Search** | Postgres FTS/trigram for MVP; promote to OpenSearch at scale. |
| **LLM** | Batch + concurrency limits + provider rate-limit handling + fallback to deterministic-only on outage. |
| **Service split** | Modular monolith → extract OCR and comparison into independent services when load demands. |

---

## 26. Cost Optimization Strategy

1. **LLM gating** — deterministic stages first; call GPT-5.5 only when
   confidence < 90%. Expected to cover 80–90% of comparisons without LLM.
2. **Caching** — hash-keyed cache for identical field-pair comparisons and
   repeated extractions; classification embedding cache.
3. **Native text first** — skip OCR entirely for digital PDFs (free + exact).
4. **Tiered OCR** — cheap PaddleOCR primary; escalate engines only on low
   confidence.
5. **Right-sized prompts** — send only low-confidence fields/snippets, not
   whole documents; structured outputs to reduce tokens; smaller model tier
   for classification.
6. **Compute** — spot/preemptible instances for stateless workers; scale to
   zero off-peak; GPU only for OCR pool when justified.
7. **Storage lifecycle** — transition raw files to infrequent-access/Glacier;
   keep only renders+reports hot.
8. **Batching** — batch LLM calls and OCR pages; concurrency caps to avoid
   overage tiers.
9. **Observability on cost** — per-tenant LLM/OCR cost metrics surfaced in
   admin analytics to detect runaway usage.

---

## 27. Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| OCR inaccuracy on poor scans | High | High | Engine fallback chain, pre-processing, confidence flagging, manual correction + learning loop. |
| False negatives on critical fields | Med | Critical | Conservative thresholds for critical fields, LLM check on low confidence, recall-focused tuning, human-in-loop. |
| LLM cost overrun | Med | High | Confidence gating, caching, prompt minimization, per-tenant cost alerts. |
| LLM provider outage/latency | Med | Med | Graceful degradation to deterministic-only; retries + circuit breaker. |
| Tenant data leakage | Low | Critical | Strict company_id scoping, RLS option, isolation tests, audits. |
| Malicious file upload | Med | High | Virus scan, magic-byte validation, sandboxed processing, size/page caps. |
| Prompt injection via doc text | Med | Med | Treat extracted text as untrusted; structured prompts; no tool exposure in extraction prompts. |
| Scaling bottleneck on big docs | Med | Med | Chunked processing, dedicated OCR pool, queue autoscaling. |
| Vendor lock-in (cloud/LLM) | Med | Med | S3-compatible abstraction, provider-agnostic LLM/OCR interfaces. |
| Compliance/PII mishandling | Low | High | Encryption, retention policy, DPA, export/delete tooling. |
| Document-type drift (new templates) | High | Med | Schema-driven config, learning mode, easy schema versioning. |

---

## 28. Testing Strategy

| Level | Scope | Tooling |
|---|---|---|
| **Unit** | normalizers, matchers, severity rules, schema parsing, RBAC, license logic | pytest, Vitest |
| **Integration** | API + DB + Redis + S3 (localstack), pipeline stages | pytest + testcontainers |
| **Engine accuracy** | OCR/extraction/comparison on a labeled fixture corpus (golden set per doc type); track precision/recall, esp. critical-field recall | custom eval harness, regression gates |
| **Contract** | OpenAPI schema validation; frontend/back type sync | schemathesis, OpenAPI types |
| **E2E** | full user journeys: register→activate→upload→verify→report | Playwright |
| **Performance/Load** | 300+ page docs, concurrent verifications, queue saturation | Locust/k6 |
| **Security** | authz/tenant-isolation tests, dependency scan, SAST, file-upload abuse, OWASP checks | Bandit, npm audit, Trivy, ZAP |
| **Accessibility** | WCAG AA on key pages | axe, Lighthouse |
| **Regression CI gates** | accuracy on golden set must not drop below thresholds before merge | GitHub Actions |

Test data: synthetic + anonymized freight documents covering each type,
languages, rotations, low-quality scans, and known-mismatch cases.

---

## 29. Open-Source Libraries

**Frontend:** Next.js, React, TypeScript, TailwindCSS, shadcn/ui + Radix UI,
TanStack Query, Zustand, React Hook Form + Zod, `react-pdf`/PDF.js (viewer +
highlight overlay), Recharts (admin charts), next-themes (dark/light).

**Backend:** FastAPI, Uvicorn/Gunicorn, Pydantic v2, SQLAlchemy 2.x, Alembic,
Celery, Redis (redis-py), psycopg, passlib/bcrypt, python-jose/PyJWT,
boto3 (S3), python-multipart, slowapi (rate limiting).

**OCR / Document:** PaddleOCR + PP-Structure (primary), DocTR (secondary),
Tesseract/pytesseract (fallback), pdfplumber/PyMuPDF (native PDF text +
rasterize), pdf2image, OpenCV + Pillow (pre-processing), python-docx /
LibreOffice-convert (DOCX), langdetect/fastText (language detection),
camelot (table fallback).

**Matching / NLP:** RapidFuzz (fuzzy/Jaro-Winkler/Levenshtein),
python-dateutil (date parsing), Babel (number/locale), sentence-transformers
(classification embeddings, optional), OpenAI SDK (GPT-5.5 gated calls).

**Reports:** ReportLab / WeasyPrint (PDF), openpyxl (Excel).

**Infra / Quality:** Docker, Nginx, ClamAV, pytest, Vitest, Playwright,
Locust/k6, Ruff, Black, mypy, ESLint, Prettier, Trivy, Bandit.

---

## 30. Complete Development Roadmap

| Phase | Name | Key deliverables | Exit criteria |
|---|---|---|---|
| **1** | **Architecture** *(current)* | This SAD; ADRs; schema/API/flows agreed | Approval to proceed |
| 2 | Auth & License | Register/login/JWT/reset; companies, plans, licenses; activation; quota enforcement; RBAC | A user can register, activate a license, and be gated by role/quota |
| 3 | Landing Page | Marketing site (all sections), dark/light, responsive, SEO | Public site live in staging |
| 4 | Dashboard | App shell, navigation, overview KPIs, settings, team mgmt | Authenticated, license-gated shell works |
| 5 | Upload | Presigned S3 upload, ref/target grouping, validation, virus scan, verification creation | Files upload + verification record created & enqueued |
| 6 | OCR | OCR pipeline (native PDF, Paddle→DocTR→Tesseract), pre-processing, chunking, bbox storage, language detection | Text+layout extracted for all supported formats incl. 300+ pages |
| 7 | Document Classification | Heuristic→ML→LLM classifier, UNKNOWN handling, manual override | Each doc auto-typed with confidence |
| 8 | Field Extraction | Schema-driven extraction, table parsing, normalization, gated LLM extraction, JSON storage | Structured fields with confidence + locations |
| 9 | Comparison Engine | Exact→normalized→OCR-aware→fuzzy→gated semantic; severity; findings; explanations | Findings produced with severity + suggested fixes |
| 10 | PDF Highlight | Split-screen viewer, sync scroll, highlight overlays, click-to-jump | Interactive result page works end-to-end |
| 11 | Reports | PDF / Excel / JSON generation + download | All three report formats downloadable |
| 12 | History | Persist + list + re-open + re-download; search & filters | Past verifications searchable & retrievable |
| 13 | Learning Mode | Feedback capture on corrections, approval queue, rule derivation | Corrections stored; admin approval improves rules |
| 14 | Admin Panel | Companies/licenses/plans/users mgmt; usage/revenue/health analytics | Platform admin can run the business |
| 15 | Testing | Unit/integration/E2E/accuracy/load/security suites + CI gates | Coverage + accuracy thresholds met in CI |
| 16 | Deployment | Dockerized prod, K8s/ECS, CI/CD, monitoring, zero-downtime deploys | Production launch ready |

**Post-MVP (future):** additional verticals (general business documents),
carrier EDI integrations, webhook notifications, e-signature, advanced
analytics, multi-language UI, fine-tuned extraction models.

---

*End of Phase 1 — System Design. Awaiting approval before Phase 2
(Authentication & License). No implementation code has been written.*
