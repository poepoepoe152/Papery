import io, subprocess, time, uuid
from concurrent.futures import ThreadPoolExecutor
import requests
BASE = "http://127.0.0.1:8000/api/v1"
def api(m, p, token=None, **kw):
    h = kw.pop("headers", {})
    if token: h["Authorization"] = f"Bearer {token}"
    return requests.request(m, f"{BASE}{p}", headers=h, timeout=60, **kw)
def pdf():
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    b = io.BytesIO(); c = canvas.Canvas(b, pagesize=A4)
    c.drawString(50, 800, "BOOKING CONFIRMATION"); c.drawString(50, 760, "Booking No: X1"); c.save()
    return b.getvalue()
rid = uuid.uuid4().hex[:6]
T = api("POST","/auth/register",json={"company_name":f"QR-{rid}","full_name":"q","email":f"qr-{rid}@t.co","password":"Password123"}).json()["access_token"]
sa = api("POST","/auth/login",json={"email":"admin@papery.app","password":"Admin123!"}).json()["access_token"]
plans = api("GET","/admin/plans",token=sa).json()
free = next(p for p in plans if p["name"]=="Free")   # limit 50
key = api("POST","/admin/licenses",token=sa,json={"plan_id":free["id"]}).json()["license_key"]
api("POST","/license/activate",token=T,json={"license_key":key})
ref = api("POST","/files/upload",token=T,files={"file":("r.pdf",pdf(),"application/pdf")}).json()["id"]
tgt = api("POST","/files/upload",token=T,files={"file":("t.pdf",pdf(),"application/pdf")}).json()["id"]
subprocess.run(["/usr/lib/postgresql/16/bin/psql","-h","127.0.0.1","-p","5432","-U","papery","-d","papery","-c",
  f"INSERT INTO usage_counters (id, company_id, period_start, documents_used) VALUES (gen_random_uuid(), (SELECT company_id FROM users WHERE email='qr-{rid}@t.co'), date_trunc('month', now())::date, 40);"],capture_output=True)
def one(i):
    r = api("POST","/verifications",token=T,json={"title":f"q{i}","reference_file_ids":[ref],"target_file_ids":[tgt]})
    return r.status_code
with ThreadPoolExecutor(max_workers=12) as ex:
    codes = list(ex.map(one, range(12)))
ok = codes.count(201); rej = codes.count(409)
q = subprocess.run(["/usr/lib/postgresql/16/bin/psql","-h","127.0.0.1","-p","5432","-U","papery","-d","papery","-tAc",
  f"SELECT documents_used FROM usage_counters WHERE company_id=(SELECT company_id FROM users WHERE email='qr-{rid}@t.co');"],capture_output=True,text=True)
used = q.stdout.strip()
print(f"created={ok} rejected={rej} counter={used}")
print("QUOTA RACE:", "SEALED (never exceeds 50)" if used=="50" and ok==5 and rej==7 else "**LEAK**")
