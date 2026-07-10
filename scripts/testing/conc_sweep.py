"""Concurrency benchmark: parallel verifications + usage-counter race check."""
import io
import statistics
import subprocess
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import requests

BASE = "http://127.0.0.1:8000/api/v1"


def api(method, path, token=None, **kw):
    headers = kw.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(method, f"{BASE}{path}", headers=headers, timeout=120, **kw)


def pdf_bytes(rows, title):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 15); c.drawString(50, 800, title)
    c.setFont("Helvetica", 11); y = 760
    for k, v in rows:
        c.drawString(50, y, f"{k}: {v}"); y -= 24
    c.save(); return buf.getvalue()


ROWS_REF = [("Booking No", "SITGUAYE12345"), ("Container No", "TCLU1234567"),
            ("Gross Weight", "26,557.68 KG"), ("Consignee", "GLOBEX LOGISTICS")]
ROWS_TGT = [("Booking No", "SITGUAYE12345"), ("Container No", "TCLU1234561"),
            ("Gross Weight", "26557.680 KG"), ("Consignee", "GLOBEX LOGISTICS")]

rid = uuid.uuid4().hex[:6]
r = api("POST", "/auth/register", json={"company_name": f"ConcCo-{rid}", "full_name": "C",
                                        "email": f"conc-{rid}@t.co", "password": "Password123"})
T = r.json()["access_token"]
sa = api("POST", "/auth/login", json={"email": "admin@papery.app", "password": "Admin123!"}).json()["access_token"]
plans = api("GET", "/admin/plans", token=sa).json()
ent = next(p for p in plans if p["name"] == "Enterprise")
key = api("POST", "/admin/licenses", token=sa, json={"plan_id": ent["id"]}).json()["license_key"]
api("POST", "/license/activate", token=T, json={"license_key": key})
print("setup ok:", key)

ref_id = api("POST", "/files/upload", token=T,
             files={"file": ("ref.pdf", pdf_bytes(ROWS_REF, "BOOKING CONFIRMATION"), "application/pdf")}).json()["id"]
tgt_id = api("POST", "/files/upload", token=T,
             files={"file": ("tgt.pdf", pdf_bytes(ROWS_TGT, "DRAFT BILL OF LADING"), "application/pdf")}).json()["id"]

N = 12


def one(i):
    t0 = time.time()
    r = api("POST", "/verifications", token=T,
            json={"title": f"conc-{i}", "reference_file_ids": [ref_id], "target_file_ids": [tgt_id]})
    if r.status_code != 201:
        return (i, "CREATE_FAIL", r.status_code, 0)
    vid = r.json()["id"]
    while time.time() - t0 < 120:
        st = api("GET", f"/verifications/{vid}/status", token=T).json()
        if st["status"] in ("COMPLETED", "FAILED"):
            return (i, st["status"], st.get("overall_result"), round(time.time() - t0, 2))
        time.sleep(0.5)
    return (i, "TIMEOUT", None, 120)


wall0 = time.time()
with ThreadPoolExecutor(max_workers=N) as ex:
    out = list(ex.map(one, range(N)))
wall = round(time.time() - wall0, 2)

times = [o[3] for o in out if o[1] == "COMPLETED"]
ok = sum(1 for o in out if o[1] == "COMPLETED" and o[2] == "FAIL")
print(f"\n{N} concurrent verifications: wall={wall}s | completed-correct={ok}/{N}")
if times:
    print(f"per-job: min={min(times)}s median={statistics.median(times)}s max={max(times)}s")
for o in out:
    if o[1] != "COMPLETED" or o[2] != "FAIL":
        print("  anomaly:", o)

# usage counter race check: expected = N*2 docs + 2... counter counts files per verification (2 each)
q = subprocess.run(
    ["/usr/lib/postgresql/16/bin/psql", "-h", "127.0.0.1", "-p", "5432", "-U", "papery", "-d", "papery", "-tAc",
     f"SELECT documents_used FROM usage_counters WHERE company_id=(SELECT company_id FROM users WHERE email='conc-{rid}@t.co');"],
    capture_output=True, text=True)
used = q.stdout.strip()
expected = N * 2
print(f"usage counter: {used} (expected {expected})", "OK" if used == str(expected) else "**RACE DETECTED**")
