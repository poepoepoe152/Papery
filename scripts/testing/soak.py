"""Soak: 100 sequential verifications + memory watch + hostile strings."""
import io, os, subprocess, time, uuid
import requests
BASE = "http://127.0.0.1:8000/api/v1"
def api(m, p, token=None, **kw):
    h = kw.pop("headers", {})
    if token: h["Authorization"] = f"Bearer {token}"
    return requests.request(m, f"{BASE}{p}", headers=h, timeout=60, **kw)
def pdf(rows, title):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    b = io.BytesIO(); c = canvas.Canvas(b, pagesize=A4)
    c.setFont("Helvetica-Bold", 14); c.drawString(50, 800, title)
    c.setFont("Helvetica", 11); y = 760
    for k, v in rows: c.drawString(50, y, f"{k}: {v}"); y -= 24
    c.save(); return b.getvalue()

def backend_rss_mb():
    out = subprocess.run(["bash","-c","ps -o rss= -p $(pgrep -f 'app.main:app' | head -1) 2>/dev/null"],
                         capture_output=True, text=True).stdout.strip()
    return int(out)//1024 if out else -1

rid = uuid.uuid4().hex[:6]
T = api("POST","/auth/register",json={"company_name":f"SoakCo-{rid}","full_name":"s","email":f"soak-{rid}@t.co","password":"Password123"}).json()["access_token"]
sa = api("POST","/auth/login",json={"email":"admin@papery.app","password":"Admin123!"}).json()["access_token"]
ent = next(p for p in api("GET","/admin/plans",token=sa).json() if p["name"]=="Enterprise")
key = api("POST","/admin/licenses",token=sa,json={"plan_id":ent["id"]}).json()["license_key"]
api("POST","/license/activate",token=T,json={"license_key":key})

REF=[("Booking No","SITGUAYE12345"),("Container No","TCLU1234567"),("Gross Weight","26,557.68 KG")]
TGT=[("Booking No","SITGUAYE12345"),("Container No","TCLU1234561"),("Gross Weight","26557.680 KG")]
ref = api("POST","/files/upload",token=T,files={"file":("r.pdf",pdf(REF,"BOOKING CONFIRMATION"),"application/pdf")}).json()["id"]
tgt = api("POST","/files/upload",token=T,files={"file":("t.pdf",pdf(TGT,"DRAFT BILL OF LADING"),"application/pdf")}).json()["id"]

rss0 = backend_rss_mb()
t0 = time.time(); done=0; wrong=0; times=[]
N=100
for i in range(N):
    ta=time.time()
    r = api("POST","/verifications",token=T,json={"title":f"soak-{i}","reference_file_ids":[ref],"target_file_ids":[tgt]})
    vid = r.json()["id"]
    while True:
        st = api("GET",f"/verifications/{vid}/status",token=T).json()
        if st["status"] in ("COMPLETED","FAILED"): break
        time.sleep(0.3)
    times.append(time.time()-ta)
    if st["status"]=="COMPLETED" and st["overall_result"]=="FAIL" and st["critical_count"]==1: done+=1
    else: wrong+=1
rss1 = backend_rss_mb()
import statistics
print(f"soak {N} runs in {round(time.time()-t0,1)}s | correct={done} wrong={wrong}")
print(f"latency: median={round(statistics.median(times),2)}s p95={round(sorted(times)[int(N*0.95)],2)}s max={round(max(times),2)}s")
print(f"backend RSS: {rss0}MB -> {rss1}MB (delta {rss1-rss0:+d}MB)")

# hostile strings
inj = "'; DROP TABLE users; --"
xss = "<script>alert(1)</script>"
r1 = api("POST","/verifications",token=T,json={"title":inj,"reference_file_ids":[ref],"target_file_ids":[tgt]})
r2 = api("POST","/verifications",token=T,json={"title":xss,"reference_file_ids":[ref],"target_file_ids":[tgt]})
r3 = api("GET",f"/verifications?q={requests.utils.quote(inj)}",token=T)
users_alive = api("POST","/auth/login",json={"email":f"soak-{rid}@t.co","password":"Password123"}).status_code==200
print(f"sqli title={r1.status_code} xss title={r2.status_code} sqli search={r3.status_code} users table intact={users_alive}")
r4 = api("GET","/verifications?q="+requests.utils.quote(xss),token=T)
found = any(v["title"]==xss for v in r4.json())
print(f"xss title stored+returned verbatim (React escapes on render): {found}")
# path traversal filename
r5 = api("POST","/files/upload",token=T,files={"file":("../../../etc/passwd.pdf",pdf(REF,"X"),"application/pdf")})
print(f"path traversal filename accepted as plain name: {r5.status_code}")
if r5.ok:
    esc = os.path.exists("/tmp/etc/passwd.pdf") or os.path.exists("/etc/passwd.pdf")
    print(f"escaped storage dir: {esc} (must be False)")
