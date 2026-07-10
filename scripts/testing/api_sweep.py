"""Papery API contract & security sweep — compact PASS/FAIL output."""
import io
import json
import subprocess
import time
import uuid

import requests

BASE = "http://127.0.0.1:8000/api/v1"
results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  <- {detail}" if not cond and detail else ""))


def api(method, path, token=None, expect=None, **kw):
    headers = kw.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.request(method, f"{BASE}{path}", headers=headers, timeout=30, **kw)
    return r


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


REF_ROWS = [("Booking No", "SITGUAYE12345"), ("Container No", "TCLU1234567"),
            ("Seal No", "ML-998877"), ("Gross Weight", "26,557.68 KG"),
            ("Consignee", "GLOBEX LOGISTICS")]
TGT_ROWS = [("Booking No", "SITGUAYE12345"), ("Container No", "TCLU1234561"),
            ("Seal No", "ML-998877"), ("Gross Weight", "26557.680 KG"),
            ("Consignee", "GLOBEX LOGISTICS")]

run_id = uuid.uuid4().hex[:6]
A_admin_email = f"a-admin-{run_id}@test.co"
B_admin_email = f"b-admin-{run_id}@test.co"
PW = "Password123"

# ---------- AUTH ----------
r = api("POST", "/auth/register", json={"company_name": f"CoA-{run_id}", "full_name": "A Admin",
                                        "email": A_admin_email, "password": PW})
check("register company A", r.status_code == 201, f"{r.status_code} {r.text[:80]}")
A = r.json()["access_token"] if r.ok else None

r = api("POST", "/auth/register", json={"company_name": "dup", "full_name": "x",
                                        "email": A_admin_email, "password": PW})
check("duplicate email -> 409", r.status_code == 409, str(r.status_code))

r = api("POST", "/auth/register", json={"company_name": "w", "full_name": "x",
                                        "email": f"w{run_id}@t.co", "password": "short"})
check("weak password -> 422", r.status_code == 422, str(r.status_code))

r = api("POST", "/auth/login", json={"email": A_admin_email, "password": "WrongPass1"})
check("wrong password -> 401", r.status_code == 401, str(r.status_code))

r = api("POST", "/auth/login", json={"email": A_admin_email, "password": PW})
check("login ok", r.status_code == 200, str(r.status_code))
A = r.json()["access_token"]
A_refresh = r.json()["refresh_token"]

check("me without token -> 401", api("GET", "/auth/me").status_code == 401)
check("me garbage token -> 401", api("GET", "/auth/me", token="garbage").status_code == 401)
check("me ok", api("GET", "/auth/me", token=A).status_code == 200)

r = api("POST", "/auth/refresh", json={"refresh_token": A_refresh})
check("refresh ok", r.status_code == 200, str(r.status_code))
r = api("POST", "/auth/refresh", json={"refresh_token": A})  # access token misused
check("refresh with access token -> 401", r.status_code == 401, str(r.status_code))

# ---------- LICENSE GATE ----------
pdf_ref = make_pdf(REF_ROWS)
r = api("POST", "/files/upload", token=A, files={"file": ("ref.pdf", pdf_ref, "application/pdf")})
check("upload before license -> 402", r.status_code == 402, str(r.status_code))

r = api("POST", "/license/activate", token=A, json={"license_key": "NOT-A-REAL-KEY"})
check("bad license key -> 404", r.status_code == 404, str(r.status_code))

# fresh keys per run (demo keys may be bound from earlier runs)
_sa = api("POST", "/auth/login", json={"email": "admin@papery.app", "password": "Admin123!"}).json()["access_token"]
_plans = api("GET", "/admin/plans", token=_sa).json()
_free = next(p for p in _plans if p["name"] == "Free")
_ent = next(p for p in _plans if p["name"] == "Enterprise")
KEY_A = api("POST", "/admin/licenses", token=_sa, json={"plan_id": _free["id"]}).json()["license_key"]
KEY_B = api("POST", "/admin/licenses", token=_sa, json={"plan_id": _ent["id"]}).json()["license_key"]

r = api("POST", "/license/activate", token=A, json={"license_key": KEY_A})
check("activate FREE key", r.status_code == 200, f"{r.status_code} {r.text[:80]}")

r = api("GET", "/license", token=A)
check("license ACTIVE", r.ok and r.json().get("status") == "ACTIVE", r.text[:80])

# ---------- COMPANY B (tenant isolation setup) ----------
r = api("POST", "/auth/register", json={"company_name": f"CoB-{run_id}", "full_name": "B Admin",
                                        "email": B_admin_email, "password": PW})
B = r.json()["access_token"]
r = api("POST", "/license/activate", token=B, json={"license_key": KEY_A})
check("B steal A's bound key -> 409", r.status_code == 409, str(r.status_code))
r = api("POST", "/license/activate", token=B, json={"license_key": KEY_B})
check("B activate ENT key", r.status_code == 200, f"{r.status_code} {r.text[:80]}")

# ---------- TEAM / ROLES ----------
r = api("POST", "/team/members", token=A,
        json={"full_name": "A Staff", "email": f"a-staff-{run_id}@t.co", "password": PW, "role": "STAFF"})
check("create staff member", r.status_code == 201, f"{r.status_code} {r.text[:80]}")
staff_id = r.json().get("id") if r.ok else None

r = api("POST", "/team/members", token=A,
        json={"full_name": "X", "email": f"x-{run_id}@t.co", "password": PW, "role": "ADMIN"})
check("create member as ADMIN -> 400", r.status_code == 400, str(r.status_code))

r = api("POST", "/auth/login", json={"email": f"a-staff-{run_id}@t.co", "password": PW})
S = r.json()["access_token"]
check("staff list members -> 403", api("GET", "/team/members", token=S).status_code == 403)
check("staff create member -> 403",
      api("POST", "/team/members", token=S,
          json={"full_name": "y", "email": f"y-{run_id}@t.co", "password": PW, "role": "STAFF"}).status_code == 403)

# seat limit: FREE max_users=3 (admin+staff=2, add 1 more ok, next -> 409)
r = api("POST", "/team/members", token=A,
        json={"full_name": "A M3", "email": f"a-m3-{run_id}@t.co", "password": PW, "role": "MANAGER"})
check("3rd seat ok", r.status_code == 201, str(r.status_code))
r = api("POST", "/team/members", token=A,
        json={"full_name": "A M4", "email": f"a-m4-{run_id}@t.co", "password": PW, "role": "STAFF"})
check("4th seat -> 409 (max_users=3)", r.status_code == 409, str(r.status_code))

r = api("PATCH", f"/team/members/{staff_id}", token=A, json={"status": "DISABLED"})
check("disable member", r.status_code == 200, str(r.status_code))
r = api("POST", "/auth/login", json={"email": f"a-staff-{run_id}@t.co", "password": PW})
check("disabled member login -> 403", r.status_code == 403, str(r.status_code))
api("PATCH", f"/team/members/{staff_id}", token=A, json={"status": "ACTIVE"})
r = api("POST", "/auth/login", json={"email": f"a-staff-{run_id}@t.co", "password": PW})
S = r.json()["access_token"]

me = api("GET", "/auth/me", token=A).json()
r = api("PATCH", f"/team/members/{me['id']}", token=A, json={"role": "STAFF"})
check("modify own account -> 400", r.status_code == 400, str(r.status_code))

# ---------- FILES ----------
r = api("POST", "/files/upload", token=A, files={"file": ("evil.exe", b"MZ....", "application/x-msdownload")})
check("upload .exe -> 400", r.status_code == 400, str(r.status_code))
r = api("POST", "/files/upload", token=A, files={"file": ("empty.pdf", b"", "application/pdf")})
check("upload empty -> 400", r.status_code == 400, str(r.status_code))

r = api("POST", "/files/upload", token=A, files={"file": ("ref.pdf", pdf_ref, "application/pdf")})
check("upload ref.pdf", r.status_code == 201, f"{r.status_code} {r.text[:80]}")
A_ref_id = r.json()["id"]
r = api("POST", "/files/upload", token=A, files={"file": ("tgt.pdf", make_pdf(TGT_ROWS, "DRAFT BILL OF LADING"), "application/pdf")})
A_tgt_id = r.json()["id"]

# ---------- VERIFICATION ----------
r = api("POST", "/verifications", token=A,
        json={"title": "missing files", "reference_file_ids": [str(uuid.uuid4())],
              "target_file_ids": [str(uuid.uuid4())]})
check("verification with unknown file ids -> 404", r.status_code == 404, str(r.status_code))

r = api("POST", "/verifications", token=A,
        json={"title": f"sweep-{run_id}", "reference_file_ids": [A_ref_id], "target_file_ids": [A_tgt_id]})
check("create verification", r.status_code == 201, f"{r.status_code} {r.text[:100]}")
vid = r.json()["id"]

deadline = time.time() + 60
status = None
while time.time() < deadline:
    st = api("GET", f"/verifications/{vid}/status", token=A).json()
    status = st["status"]
    if status in ("COMPLETED", "FAILED"):
        break
    time.sleep(1)
check("verification completes", status == "COMPLETED", f"status={status}")
det = api("GET", f"/verifications/{vid}", token=A).json()
check("result FAIL + 1 critical", det.get("overall_result") == "FAIL" and det.get("critical_count") == 1,
      f"{det.get('overall_result')} crit={det.get('critical_count')}")
check("weight not flagged critical",
      all(f["field_key"] != "gross_weight" or f["match_type"] == "NORMALIZED" for f in det.get("findings", [])))

# tenant isolation
r = api("POST", "/verifications", token=B,
        json={"title": "steal", "reference_file_ids": [A_ref_id], "target_file_ids": [A_tgt_id]})
check("B uses A's files -> 404", r.status_code == 404, str(r.status_code))
check("B reads A's verification -> 404", api("GET", f"/verifications/{vid}", token=B).status_code == 404)
finding_id = det["findings"][0]["id"] if det.get("findings") else None
check("B patches A's finding -> 404",
      api("PATCH", f"/findings/{finding_id}", token=B, json={"status": "DISMISSED"}).status_code == 404)

# staff scope: staff sees only own
r = api("GET", "/verifications", token=S)
check("staff sees 0 verifications (none own)", r.ok and len(r.json()) == 0, f"n={len(r.json()) if r.ok else '?'}")
r = api("GET", f"/verifications/{vid}", token=S)
check("staff open admin's verification -> 403", r.status_code == 403, str(r.status_code))

# findings + learning
r = api("PATCH", f"/findings/{finding_id}", token=A, json={"status": "BOGUS"})
check("finding invalid status -> 400", r.status_code == 400, str(r.status_code))
r = api("PATCH", f"/findings/{finding_id}", token=A, json={"status": "DISMISSED"})
check("dismiss finding", r.status_code == 200, str(r.status_code))
r = api("GET", "/feedback/pending", token=A)
check("feedback captured", r.ok and len(r.json()) >= 1, f"n={len(r.json()) if r.ok else r.status_code}")
if r.ok and r.json():
    fb_id = r.json()[0]["id"]
    r2 = api("PATCH", f"/feedback/{fb_id}?approve=true", token=A)
    check("approve feedback", r2.status_code == 200, str(r2.status_code))

# reports
for fmt, sniff in [("PDF", b"%PDF"), ("XLSX", b"PK"), ("JSON", b"{")]:
    r = api("GET", f"/verifications/{vid}/report?fmt={fmt}", token=A)
    ok = r.status_code == 200 and r.content[:4].startswith(sniff[:4] if len(sniff) >= 4 else sniff)
    if fmt == "JSON" and r.ok:
        ok = ok and "findings" in json.loads(r.content)
    check(f"report {fmt}", ok, f"{r.status_code} head={r.content[:8]!r}")

# ---------- QUOTA (force near-limit via DB) ----------
subprocess.run(
    ["/usr/lib/postgresql/16/bin/psql", "-h", "127.0.0.1", "-p", "5432", "-U", "papery", "-d", "papery", "-c",
     f"UPDATE usage_counters SET documents_used = 49 WHERE company_id = (SELECT company_id FROM users WHERE email = '{A_admin_email}');"],
    capture_output=True)
r = api("POST", "/verifications", token=A,
        json={"title": "quota-buster", "reference_file_ids": [A_ref_id], "target_file_ids": [A_tgt_id]})
check("over quota -> 409", r.status_code == 409, f"{r.status_code} {r.text[:60]}")

# ---------- ADMIN ----------
check("company admin hits /admin -> 403", api("GET", "/admin/stats", token=A).status_code == 403)
r = api("POST", "/auth/login", json={"email": "admin@papery.app", "password": "Admin123!"})
SA = r.json()["access_token"]
r = api("GET", "/admin/stats", token=SA)
check("super admin stats", r.ok and r.json()["companies"] >= 2, r.text[:80])

plans = api("GET", "/admin/plans", token=SA).json()
pro = next(p for p in plans if p["name"] == "Pro")
r = api("POST", "/admin/licenses", token=SA, json={"plan_id": pro["id"]})
check("generate license key", r.status_code == 201 and r.json()["license_key"].startswith("PAPERY-"),
      r.text[:80])

companies = api("GET", "/admin/companies", token=SA).json()
coA = next(c for c in companies if c["name"] == f"CoA-{run_id}")
r = api("PATCH", f"/admin/companies/{coA['id']}?status=SUSPENDED", token=SA)
check("suspend company A", r.status_code == 200, str(r.status_code))
r = api("POST", "/files/upload", token=A, files={"file": ("x.pdf", pdf_ref, "application/pdf")})
check("suspended company gated -> 402", r.status_code == 402, str(r.status_code))
r = api("PATCH", f"/admin/companies/{coA['id']}?status=ACTIVE", token=SA)
r = api("POST", "/files/upload", token=A, files={"file": ("x.pdf", pdf_ref, "application/pdf")})
check("reactivated company works again", r.status_code == 201, str(r.status_code))

# ---------- summary ----------
fails = [n for n, ok, _ in results if not ok]
print(f"\n===== {len(results)} checks | PASS {len(results)-len(fails)} | FAIL {len(fails)} =====")
for n in fails:
    print("  FAILED:", n)
