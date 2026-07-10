import io, sys, time, uuid
import requests
BASE = "http://127.0.0.1:8000/api/v1"
def api(m, p, token=None, **kw):
    h = kw.pop("headers", {})
    if token: h["Authorization"] = f"Bearer {token}"
    return requests.request(m, f"{BASE}{p}", headers=h, timeout=60, **kw)
def bigpdf(pages=250):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    b = io.BytesIO(); c = canvas.Canvas(b, pagesize=A4)
    for p in range(pages):
        c.setFont("Helvetica", 11)
        c.drawString(50, 800, "BOOKING CONFIRMATION" if p==0 else f"RIDER PAGE {p}")
        for i in range(35): c.drawString(50, 770-i*20, f"Cargo line {p}-{i} lorem cargo details continue here")
        c.showPage()
    c.save(); return b.getvalue()

mode = sys.argv[1]
if mode == "start":
    rid = uuid.uuid4().hex[:6]
    T = api("POST","/auth/register",json={"company_name":f"CrashCo-{rid}","full_name":"c","email":f"crash-{rid}@t.co","password":"Password123"}).json()["access_token"]
    sa = api("POST","/auth/login",json={"email":"admin@papery.app","password":"Admin123!"}).json()["access_token"]
    ent = next(p for p in api("GET","/admin/plans",token=sa).json() if p["name"]=="Enterprise")
    key = api("POST","/admin/licenses",token=sa,json={"plan_id":ent["id"]}).json()["license_key"]
    api("POST","/license/activate",token=T,json={"license_key":key})
    big = bigpdf()
    ref = api("POST","/files/upload",token=T,files={"file":("r.pdf",big,"application/pdf")}).json()["id"]
    tgt = api("POST","/files/upload",token=T,files={"file":("t.pdf",big,"application/pdf")}).json()["id"]
    v = api("POST","/verifications",token=T,json={"title":"crash-victim","reference_file_ids":[ref],"target_file_ids":[tgt]}).json()
    print(T); print(v["id"])
elif mode == "check":
    T, vid = sys.argv[2], sys.argv[3]
    st = api("GET", f"/verifications/{vid}/status", token=T).json()
    print("status:", st["status"], "| stage:", st.get("stage"))
    det = api("GET", f"/verifications/{vid}", token=T).json()
    print("error:", (det.get("error_message") or "")[:80])
