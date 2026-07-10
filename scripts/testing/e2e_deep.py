"""Deep browser E2E: full user journey through the real UI."""
import time
import uuid

import requests
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000/api/v1"
SAMP = "/tmp/claude-0/-home-user-Papery/a80de5a6-b20b-5af7-a7d3-2e3218a540f2/scratchpad/samples"
SHOTS = "/tmp/claude-0/-home-user-Papery/a80de5a6-b20b-5af7-a7d3-2e3218a540f2/scratchpad/shots"
results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  <- {detail}" if not cond else ""))


# fresh Pro license for this run
sa = requests.post(f"{BASE}/auth/login", json={"email": "admin@papery.app", "password": "Admin123!"}).json()["access_token"]
plans = requests.get(f"{BASE}/admin/plans", headers={"Authorization": f"Bearer {sa}"}).json()
pro = next(p for p in plans if p["name"] == "Pro")
KEY = requests.post(f"{BASE}/admin/licenses", headers={"Authorization": f"Bearer {sa}"},
                    json={"plan_id": pro["id"]}).json()["license_key"]

rid = uuid.uuid4().hex[:6]
EMAIL = f"e2e-{rid}@acme.co"

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
                          args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.set_default_timeout(20000)

    # 1) register
    pg.goto("http://localhost:3000/register", wait_until="networkidle")
    pg.fill("#company", f"E2E Freight {rid}")
    pg.fill("#name", "E2E Admin")
    pg.fill("#email", EMAIL)
    pg.fill("#password", "Password123")
    pg.click("button[type=submit]")
    pg.wait_for_url("**/activate")
    check("register -> activate page", True)

    # 2) activate with generated key
    pg.fill("#key", KEY)
    pg.click("button:has-text('Activate')")
    pg.wait_for_url("**/dashboard")
    check("license activation -> dashboard", True)

    # 3) team: add member + change role
    pg.goto("http://localhost:3000/dashboard/team", wait_until="networkidle")
    pg.click("button:has-text('Add member')")
    pg.fill("form input >> nth=0", "Team Mate")
    pg.fill("form input[type=email]", f"mate-{rid}@acme.co")
    pg.fill("form input[placeholder='At least 8 characters']", "Password123")
    pg.select_option("form select", "MANAGER")
    pg.click("form button[type=submit]")
    pg.wait_for_selector(f"text=mate-{rid}@acme.co")
    check("team: member added", True)
    rows = pg.locator("tbody tr")
    check("team: 2 rows", rows.count() == 2, f"n={rows.count()}")

    # 4) verification flow
    pg.goto("http://localhost:3000/dashboard/verify", wait_until="networkidle")
    pg.fill("#title", "E2E Booking vs BL")
    inputs = pg.locator("input[type=file]")
    inputs.nth(0).set_input_files(f"{SAMP}/Booking_Reference.pdf")
    inputs.nth(1).set_input_files(f"{SAMP}/DraftBL_Target.pdf")
    pg.wait_for_selector("text=ready")
    time.sleep(1)
    pg.click("button:has-text('Verify')")
    pg.wait_for_url("**/dashboard/verify/**")
    # wait for result
    ok = False
    for _ in range(40):
        body = pg.inner_text("body")
        if "Findings" in body:
            ok = True
            break
        time.sleep(1)
    check("verification result renders", ok)
    body = pg.inner_text("body")
    check("result shows FAIL", "FAIL" in body)
    check("container error visible", "TCLU1234561" in body)

    # 5) dismiss a finding -> status updates
    before = pg.locator("button:has-text('Dismiss')").count()
    pg.locator("button:has-text('Dismiss')").first.click()
    time.sleep(1.5)
    after = pg.locator("button:has-text('Dismiss')").count()
    check("dismiss finding removes actions", after == before - 1, f"{before}->{after}")
    check("DISMISSED label shown", "DISMISSED" in pg.inner_text("body"))

    # 6) report downloads (PDF)
    with pg.expect_download() as dl:
        pg.click("button:has-text('PDF')")
    download = dl.value
    check("PDF report downloads", download.suggested_filename.endswith(".pdf"),
          download.suggested_filename)
    with pg.expect_download() as dl:
        pg.click("button:has-text('XLSX')")
    check("XLSX report downloads", dl.value.suggested_filename.endswith(".xlsx"))

    # 7) history search
    pg.goto("http://localhost:3000/dashboard/history", wait_until="networkidle")
    pg.wait_for_selector("text=E2E Booking vs BL")
    check("history lists verification", True)
    pg.fill("input[placeholder*='Search']", "no-such-title-xyz")
    time.sleep(1)
    check("search filters out", "E2E Booking vs BL" not in pg.inner_text("tbody") if pg.locator("tbody").count() else True)
    pg.fill("input[placeholder*='Search']", "E2E Booking")
    time.sleep(1)
    check("search finds by title", "E2E Booking vs BL" in pg.inner_text("body"))

    # 8) settings shows license
    pg.goto("http://localhost:3000/dashboard/settings", wait_until="networkidle")
    body = pg.inner_text("body")
    check("settings shows Pro plan + ACTIVE", "Pro" in body and "ACTIVE" in body)

    # 9) dark mode toggle
    pg.click("button[aria-label='Toggle dark mode']")
    time.sleep(0.5)
    is_dark = pg.evaluate("document.documentElement.classList.contains('dark')")
    check("dark mode toggles", is_dark)
    pg.screenshot(path=f"{SHOTS}/e2e_settings_dark.png")

    # 10) mobile drawer
    pg.set_viewport_size({"width": 390, "height": 800})
    pg.goto("http://localhost:3000/dashboard", wait_until="networkidle")
    sidebar_hidden = pg.locator("aside").evaluate("el => el.classList.contains('-translate-x-full')")
    pg.click("button[aria-label='Open menu']")
    time.sleep(0.5)
    sidebar_shown = pg.locator("aside").evaluate("el => el.classList.contains('translate-x-0')")
    check("mobile drawer opens", sidebar_hidden and sidebar_shown)
    pg.screenshot(path=f"{SHOTS}/e2e_mobile_drawer.png")
    pg.set_viewport_size({"width": 1440, "height": 900})

    # 11) logout -> login as super admin -> admin panel
    pg.goto("http://localhost:3000/dashboard", wait_until="networkidle")
    pg.evaluate("localStorage.clear()")
    pg.goto("http://localhost:3000/login", wait_until="networkidle")
    pg.fill("#email", "admin@papery.app")
    pg.fill("#password", "Admin123!")
    pg.click("button[type=submit]")
    pg.wait_for_url("**/dashboard")
    pg.goto("http://localhost:3000/dashboard/admin", wait_until="networkidle")
    body = pg.inner_text("body")
    check("admin panel loads with stats", "Companies" in body and "MRR" in body)
    check("admin sees new company", f"E2E Freight {rid}" in body)
    pg.screenshot(path=f"{SHOTS}/e2e_admin.png", full_page=True)

    # generate a license from the UI
    before_keys = pg.locator("td.font-mono").count()
    pg.click("button:has-text('Generate key')")
    time.sleep(1.5)
    after_keys = pg.locator("td.font-mono").count()
    check("admin generates license via UI", after_keys == before_keys + 1, f"{before_keys}->{after_keys}")

    b.close()

fails = [n for n, ok in results if not ok]
print(f"\n===== {len(results)} checks | PASS {len(results)-len(fails)} | FAIL {len(fails)} =====")
for n in fails:
    print("  FAILED:", n)
