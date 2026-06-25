"""
墨境网站自动化截图测试
用法：python D:/建网站/mojing-docs/体验测试.py
"""
from playwright.sync_api import sync_playwright
from datetime import datetime

BASE = "http://localhost:3000"
OUTPUT = "D:/建网站/mojing-docs/output/screenshots"
TS = datetime.now().strftime("%Y%m%d-%H%M%S")
REPORT = []

def snap(page, name):
    path = f"{OUTPUT}/screenshot-{TS}-{name}.png"
    page.screenshot(path=path, full_page=True)
    REPORT.append(f"📸 {name}")
    print(f"  📸 {name}")

def ok(msg):
    REPORT.append(f"✅ {msg}")
    print(f"  ✅ {msg}")

def fail(msg):
    REPORT.append(f"❌ {msg}")
    print(f"  ❌ {msg}")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.set_default_timeout(15000)

    print("1. 首页")
    try:
        page.goto(BASE, timeout=10000)
        snap(page, "01-首页")
        ok("首页加载")
    except: fail("首页加载失败")

    print("2. 编辑器")
    try:
        page.goto(f"{BASE}/editor/demo-1", timeout=10000)
        snap(page, "02-编辑器")
        ok("编辑器加载")
    except: fail("编辑器加载失败")

    print("3. 合规检测")
    try:
        page.click("button[title='合规检测']")
        page.wait_for_timeout(500)
        snap(page, "03-合规检测")
        ok("合规检测面板")
    except: fail("合规检测")

    print("4. 角色面板")
    try:
        page.click("button[title='角色']")
        page.wait_for_timeout(300)
        snap(page, "04-角色面板")
        ok("角色面板")
    except: fail("角色面板")

    print("5. 灵感面板")
    try:
        page.click("button[title='灵感']")
        page.wait_for_timeout(300)
        snap(page, "05-灵感面板")
        ok("灵感面板")
    except: fail("灵感面板")

    print("6. 脑洞喷射弹窗")
    try:
        page.click("button:has-text('脑洞喷射')")
        page.wait_for_timeout(500)
        snap(page, "06-脑洞喷射")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        ok("脑洞喷射弹窗")
    except: fail("脑洞喷射")

    print("7. 章末自检")
    try:
        page.click("button:has-text('完成本章'), button:has-text('章末自检')")
        page.wait_for_timeout(500)
        snap(page, "07-章末自检")
        page.keyboard.press("Escape")
        ok("章末自检")
    except: fail("章末自检")

    print("8. Admin")
    try:
        page.goto(f"{BASE}/admin", timeout=10000)
        snap(page, "08-Admin后台")
        ok("Admin后台")
    except: fail("Admin后台")

    print("9. 系统设置")
    try:
        page.goto(f"{BASE}/admin/settings", timeout=10000)
        snap(page, "09-系统设置")
        ok("系统设置")
    except: fail("系统设置")

    browser.close()

# 写报告
report_path = f"D:/建网站/mojing-docs/output/自动化测试-{TS}.md"
with open(report_path, "w", encoding="utf-8") as f:
    f.write(f"# 墨境自动化截图测试\n> {TS}\n\n")
    for line in REPORT:
        f.write(f"- {line}\n")
print(f"\n✅ 完成，报告：{report_path}")
