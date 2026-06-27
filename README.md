# Papery

**AI-powered document verification platform.** Upload reference and target
business documents — Papery detects document types, extracts structured fields,
compares them, highlights mismatches with severity, and generates auditable
verification reports.

First vertical: **Freight Forwarding & Logistics**. Web application only.

## Status

🟡 **Phase 1 — System Design.** No implementation code yet.

See the full Software Architecture Document: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Planned Tech Stack

- **Frontend:** Next.js, React, TypeScript, TailwindCSS
- **Backend:** Python, FastAPI, Celery
- **OCR:** PaddleOCR (primary), DocTR, Tesseract (fallback)
- **AI:** GPT-5.5 API (gated by confidence)
- **Data:** PostgreSQL, Redis, AWS S3
- **Auth:** JWT, bcrypt
- **Deploy:** Docker, Nginx, GitHub Actions

## Roadmap (summary)

1. Architecture *(current)* → 2. Auth & License → 3. Landing Page →
4. Dashboard → 5. Upload → 6. OCR → 7. Classification → 8. Field Extraction →
9. Comparison Engine → 10. PDF Highlight → 11. Reports → 12. History →
13. Learning Mode → 14. Admin Panel → 15. Testing → 16. Deployment

Full roadmap with exit criteria is in the architecture document.
