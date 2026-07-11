"""Integration API-contract & security tests against a running stack.

Skipped automatically unless a live server is reachable. Point at one with:

    PAPERY_API_BASE=http://localhost:8000/api/v1 pytest tests/integration -q

(Requires the backend + PostgreSQL running, e.g. via `docker compose up`.)
"""
import io
import os
import uuid

import pytest
import requests

BASE = os.environ.get("PAPERY_API_BASE", "http://127.0.0.1:8000/api/v1")


def _server_up() -> bool:
    try:
        root = BASE.rsplit("/api", 1)[0]
        return requests.get(f"{root}/health", timeout=2).ok
    except requests.RequestException:
        return False


pytestmark = pytest.mark.skipif(
    not _server_up(), reason=f"no live Papery server at {BASE}"
)


def api(method, path, token=None, **kw):
    headers = kw.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(method, f"{BASE}{path}", headers=headers, timeout=30, **kw)


def make_pdf(rows, title="BOOKING CONFIRMATION"):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(50, 800, title)
    c.setFont("Helvetica", 11)
    y = 760
    for k, v in rows:
        c.drawString(50, y, f"{k}: {v}")
        y -= 24
    c.save()
    return buf.getvalue()


def super_admin_token():
    r = api("POST", "/auth/login", json={"email": "admin@papery.app", "password": "Admin123!"})
    assert r.ok, "seeded super admin login failed"
    return r.json()["access_token"]


def fresh_license(plan_name="Free"):
    sa = super_admin_token()
    plans = api("GET", "/admin/plans", token=sa).json()
    plan = next(p for p in plans if p["name"] == plan_name)
    return api("POST", "/admin/licenses", token=sa, json={"plan_id": plan["id"]}).json()["license_key"]


@pytest.fixture
def rid():
    return uuid.uuid4().hex[:8]


def register(rid, name="Admin"):
    email = f"{name.lower()}-{rid}@t.co"
    r = api("POST", "/auth/register",
            json={"company_name": f"Co-{name}-{rid}", "full_name": name,
                  "email": email, "password": "Password123"})
    assert r.status_code == 201
    return email, r.json()["access_token"]


# ---------------- auth ----------------
def test_auth_rejections(rid):
    email, _ = register(rid)
    assert api("POST", "/auth/register",
               json={"company_name": "d", "full_name": "x", "email": email, "password": "Password123"}
               ).status_code == 409
    assert api("POST", "/auth/register",
               json={"company_name": "w", "full_name": "x", "email": f"w{rid}@t.co", "password": "short"}
               ).status_code == 422
    assert api("POST", "/auth/login", json={"email": email, "password": "nope"}).status_code == 401
    assert api("GET", "/auth/me").status_code == 401
    assert api("GET", "/auth/me", token="garbage").status_code == 401


def test_refresh_type_confusion(rid):
    _, tok = register(rid)
    # an access token must not work as a refresh token
    assert api("POST", "/auth/refresh", json={"refresh_token": tok}).status_code == 401


# ---------------- license & tenancy ----------------
def test_license_gate_and_isolation(rid):
    email_a, A = register(rid, "AA")
    # gated before activation
    assert api("POST", "/files/upload", token=A,
               files={"file": ("r.pdf", make_pdf([("Booking No", "X1")]), "application/pdf")}
               ).status_code == 402
    key = fresh_license("Free")
    assert api("POST", "/license/activate", token=A, json={"license_key": key}).status_code == 200
    # a second company cannot claim A's bound key
    _, B = register(rid, "BB")
    assert api("POST", "/license/activate", token=B, json={"license_key": key}).status_code == 409


# ---------------- roles ----------------
def test_role_permissions(rid):
    _, A = register(rid, "RA")
    api("POST", "/license/activate", token=A, json={"license_key": fresh_license("Pro")})
    r = api("POST", "/team/members", token=A,
            json={"full_name": "S", "email": f"s-{rid}@t.co", "password": "Password123", "role": "STAFF"})
    assert r.status_code == 201
    # admins can't create another admin via team endpoint
    assert api("POST", "/team/members", token=A,
               json={"full_name": "x", "email": f"x-{rid}@t.co", "password": "Password123", "role": "ADMIN"}
               ).status_code == 400
    S = api("POST", "/auth/login", json={"email": f"s-{rid}@t.co", "password": "Password123"}).json()["access_token"]
    assert api("GET", "/team/members", token=S).status_code == 403


# ---------------- verification + reports ----------------
def test_verification_and_reports(rid):
    import time

    _, A = register(rid, "VA")
    api("POST", "/license/activate", token=A, json={"license_key": fresh_license("Pro")})
    fr = api("POST", "/files/upload", token=A,
             files={"file": ("r.pdf", make_pdf([("Container No", "TCLU1234567")]), "application/pdf")}).json()["id"]
    ft = api("POST", "/files/upload", token=A,
             files={"file": ("t.pdf", make_pdf([("Container No", "TCLU1234561")], "DRAFT BILL OF LADING"),
                             "application/pdf")}).json()["id"]
    vid = api("POST", "/verifications", token=A,
              json={"title": f"v-{rid}", "reference_file_ids": [fr], "target_file_ids": [ft]}).json()["id"]
    for _ in range(60):
        st = api("GET", f"/verifications/{vid}/status", token=A).json()
        if st["status"] in ("COMPLETED", "FAILED"):
            break
        time.sleep(1)
    assert st["status"] == "COMPLETED"
    assert st["overall_result"] == "FAIL" and st["critical_count"] == 1

    import json as _json

    data = _json.loads(api("GET", f"/verifications/{vid}/report?fmt=JSON", token=A).content)
    assert "TCLU1234561" in _json.dumps(data["findings"])
    assert api("GET", f"/verifications/{vid}/report?fmt=PDF", token=A).content[:4] == b"%PDF"
    assert api("GET", f"/verifications/{vid}/report?fmt=XLSX", token=A).content[:2] == b"PK"


# ---------------- password reset ----------------
def test_password_reset_no_user_enumeration(rid):
    email, _ = register(rid, "PW")
    # same generic response whether or not the email exists
    r_known = api("POST", "/auth/forgot-password", json={"email": email})
    r_unknown = api("POST", "/auth/forgot-password", json={"email": f"nobody-{rid}@t.co"})
    assert r_known.status_code == 200 and r_unknown.status_code == 200
    assert r_known.json()["message"] == r_unknown.json()["message"]
    # an invalid/garbage token is rejected
    assert api("POST", "/auth/reset-password",
               json={"token": "not-a-real-token", "new_password": "NewPass123"}
               ).status_code == 400
    # weak new password is rejected by validation
    assert api("POST", "/auth/reset-password",
               json={"token": "x" * 40, "new_password": "short"}
               ).status_code == 422


# ---------------- admin ----------------
def test_admin_requires_super_admin(rid):
    _, A = register(rid, "NA")
    assert api("GET", "/admin/stats", token=A).status_code == 403
    sa = super_admin_token()
    assert api("GET", "/admin/stats", token=sa).ok
