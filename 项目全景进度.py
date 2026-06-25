"""墨境项目全景进度面板 v2 — 实时监控版"""
import http.server, json, webbrowser, time
from pathlib import Path
from datetime import datetime

PORT = 8899
ROOT = Path("D:/建网站/mojing-docs")
OUTPUT_DIR = ROOT / "output"
TASKS_DIR = ROOT / "tasks"
CONTEXT_DIR = ROOT / "context"
DELIB_DIR = ROOT / "context" / "deliberations"
SESSIONS_DIR = Path("C:/Users/nicou/AppData/Roaming/reasonix/projects/D--建网站/sessions")
PROJECT_DIR = Path("D:/建网站/mojing-app")

ROLES = {
    # 原8人
    "后端技术负责人": {"icon": "⚙️", "color": "#3b82f6", "session": "20260621-191522.542692500", "mode": "task"},
    "前端技术负责人": {"icon": "🎨", "color": "#8b5cf6", "session": "20260621-202458.041590800", "mode": "task"},
    "架构审查员":     {"icon": "🔍", "color": "#f59e0b", "session": "20260621-175807.046140700", "mode": "window"},
    "提示词系统专家": {"icon": "🧠", "color": "#ec4899", "session": "20260621-193727.562644600", "mode": "task"},
    "产品经理":       {"icon": "📊", "color": "#10b981", "session": "20260621-194638.192807500", "mode": "task"},
    "UI设计师":     {"icon": "🎯", "color": "#f97316", "session": "20260621-194748.846743400", "mode": "window"},
    "QA测试工程师":   {"icon": "🧪", "color": "#06b6d4", "session": "20260621-195417.277398500", "mode": "window"},
    "UX体验员":   {"icon": "👁️", "color": "#ec4899", "session": "20260622-005205.499761900", "mode": "window"},
    # 🆕 新10人
    "协议执行官":   {"icon": "🛡️", "color": "#dc2626", "mode": "window"},
    "组织发展官":   {"icon": "🌱", "color": "#84cc16", "mode": "task"},
    "DevOps工程师": {"icon": "🔧", "color": "#6366f1", "mode": "task"},
    "编辑器专责":   {"icon": "✂️", "color": "#a855f7", "mode": "task"},
    "增长分析师":   {"icon": "📈", "color": "#14b8a6", "mode": "task"},
    "AI模型评测员": {"icon": "🤖", "color": "#f43f5e", "mode": "task"},
    "API逻辑工程师": {"icon": "🔌", "color": "#0ea5e9", "mode": "task"},
    "页面组件工程师": {"icon": "📄", "color": "#8b5cf6", "mode": "task"},
    "动效交互设计师": {"icon": "✨", "color": "#f59e0b", "mode": "window"},
    "品牌插画师":   {"icon": "🖌️", "color": "#ec4899", "mode": "window"},
}

def get_session_info(name):
    """获取角色会话状态"""
    cfg = ROLES.get(name, {})
    prefix = cfg.get("session", "")
    if not prefix:
        return {"active": False, "last_activity": "🆕", "msg_count": 0}
    for f in SESSIONS_DIR.glob(f"{prefix}*.jsonl"):
        stat = f.stat()
        age = time.time() - stat.st_mtime
        return {
            "active": age < 120,
            "last_activity": datetime.fromtimestamp(stat.st_mtime).strftime("%H:%M"),
            "msg_count": sum(1 for _ in open(f, 'r', encoding='utf-8')) if f.exists() else 0,
        }
    return {"active": False, "last_activity": "无", "msg_count": 0}

def get_task_info(name):
    """获取角色任务"""
    task_file = TASKS_DIR / f"{name}.md"
    if task_file.exists():
        try:
            content = task_file.read_text(encoding="utf-8").strip()
        except UnicodeDecodeError:
            content = task_file.read_text(encoding="gbk", errors="ignore").strip()
        if content and content != "暂无任务":
            return content[:300]
    return None

def get_output_info(name):
    """获取角色最近的 output"""
    outputs = []
    for f in sorted(OUTPUT_DIR.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
        if name[:2] in f.name or name[:4] in f.name:
            try:
                out_content = f.read_text(encoding="utf-8")[:3000]
            except UnicodeDecodeError:
                out_content = f.read_text(encoding="gbk", errors="ignore")[:3000]
            outputs.append({
                "file": f.name,
                "content": out_content,
                "time": datetime.fromtimestamp(f.stat().st_mtime).strftime("%m-%d %H:%M"),
            })
            break
    return outputs[0] if outputs else None

def get_decision_log():
    """获取最近决策"""
    log_file = OUTPUT_DIR / "决策日志.md"
    if log_file.exists():
        try:
            content = log_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = log_file.read_text(encoding="gbk", errors="ignore")
        # 提取最近3条决策
        decisions = []
        for part in content.split("### 决策")[1:6]:
            lines = part.strip().split("\n")
            title = lines[0].strip() if lines else ""
            decisions.append({"title": f"决策 {title}", "lines": part[:500]})
        return decisions[-3:]
    return []

def get_git_info():
    """获取 Git 状态"""
    import subprocess
    try:
        import os
        os.chdir(PROJECT_DIR)
        log = subprocess.run(["git", "log", "--oneline", "-3"], capture_output=True, text=True)
        return log.stdout.strip() if log.returncode == 0 else "N/A"
    except:
        return "N/A"

def get_server_status():
    """检查开发服务器状态 — 增强版"""
    import subprocess, socket, urllib.request, time as _time
    status = {
        "running": False,
        "port_3000": False,
        "port_3001": False,
        "mode": "未运行",
        "response_ms": 0,
        "node_count": 0,
        "next_version": "",
        "page_count": 0,
    }
    # 检测 node 进程
    try:
        out = subprocess.run(["tasklist", "/fi", "IMAGENAME eq node.exe"], capture_output=True, text=True)
        status["node_count"] = out.stdout.count("node.exe")
        # 尝试从 node 进程命令行识别 Next.js 版本
        try:
            out2 = subprocess.run(["wmic", "process", "where", "name='node.exe'", "get", "commandline"], capture_output=True, text=True, timeout=3)
            if "next" in out2.stdout.lower():
                import re
                m = re.search(r'next@(\d+\.\d+\.\d+)', out2.stdout)
                if m: status["next_version"] = m.group(1)
        except: pass
    except: pass

    # 检测端口 3000
    for port in [3000, 3001]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        ok = sock.connect_ex(('127.0.0.1', port)) == 0
        sock.close()
        status[f"port_{port}"] = ok
        if ok and not status["running"]:
            status["running"] = True
            status["port_3000"] = True
            # 测响应时间 + 判断模式
            try:
                t0 = _time.time()
                req = urllib.request.Request(f"http://localhost:{port}", headers={"User-Agent":"MojingDashboard/1.0"})
                resp = urllib.request.urlopen(req, timeout=3)
                status["response_ms"] = round((_time.time()-t0)*1000)
                html = resp.read(20000).decode('utf-8', errors='ignore')
                # 判断 dev 还是 prod
                if '__next_devtools' in html or 'Turbopack' in html or 'hmr-client' in html:
                    status["mode"] = "🔧 开发模式 (dev)"
                elif '_next/static' in html:
                    status["mode"] = "🚀 生产模式 (prod)"
                else:
                    status["mode"] = "运行中"
                # 粗略统计页面数
                status["page_count"] = html.count('script src="/_next/static/chunks/pages/') + html.count('script src="/_next/static/chunks/src_app_')
                if status["page_count"] == 0: status["page_count"] = html.count('/_next/static/')
            except Exception as e:
                status["mode"] = f"端口占用({port})"
    
    return status

def get_openclaw_status():
    """检查 OpenClaw Gateway 状态"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    ok = s.connect_ex(('127.0.0.1', 18789)) == 0
    s.close()
    return {"running": ok, "port": 18789, "url": "http://127.0.0.1:18789"}

def cluster_data():
    """集群健康数据"""
    import datetime as dt, time as t
    now = t.time()
    agents = {}
    for name, cfg in ROLES.items():
        tf = TASKS_DIR / f"{name}.md"
        sf = None
        if "session" in cfg:
            found = list(SESSIONS_DIR.glob(f"{cfg['session']}*.jsonl"))
            sf = found[0] if found else None
        cf = CONTEXT_DIR / f"{name}.md"
        s_mtime = sf.stat().st_mtime if sf else 0
        hours_since = int((now - s_mtime)//3600) if s_mtime else -1
        t_mtime = tf.stat().st_mtime if tf.exists() else 0
        mode = cfg.get("mode", "task")
        stale = (now - s_mtime > 900) and mode == "task" and t_mtime > s_mtime
        agents[name] = {
            "icon": cfg["icon"], "mode": mode,
            "task_updated": dt.datetime.fromtimestamp(t_mtime).strftime("%H:%M") if t_mtime else "N/A",
            "last_active": dt.datetime.fromtimestamp(s_mtime).strftime("%H:%M") if s_mtime else "N/A",
            "healthy": not stale,
            "heartbeat": "🆕 未创建" if hours_since == -1 else ("⚠️ 超时{}h".format(hours_since) if hours_since > 24 else "正常"),
            "context_size": cf.stat().st_size if cf.exists() else 0,
        }
    decisions_list = []
    df = CONTEXT_DIR / "decisions.jsonl"
    if df.exists():
        for l in open(df, encoding="utf-8").readlines()[-8:]:
            d = json.loads(l)
            decisions_list.append({"role": d["role"], "decision": d["decision"][:80], "time": d["timestamp"][11:16]})
    return {"agents": agents, "decisions": list(reversed(decisions_list)), "updated": dt.datetime.now().strftime("%H:%M:%S")}

def get_data():
    """组装全部数据"""
    roles = []
    for name, info in ROLES.items():
        session = get_session_info(name)
        roles.append({
            "name": name,
            "icon": info["icon"],
            "color": info["color"],
            "active": session["active"],
            "last_activity": session["last_activity"],
            "msg_count": session["msg_count"],
            "task": get_task_info(name),
            "output": get_output_info(name),
        })
    
    return {
        "roles": roles,
        "decisions": get_decision_log(),
        "git": get_git_info(),
        "server": get_server_status(),
        "openclaw": get_openclaw_status(),
        "roadmap": [
            {"phase": "Sprint 1", "status": "done", "items": ["Turbopack修复", "API Key迁移", "角色/灵感面板", "代码质量清理"]},
            {"phase": "Sprint 2", "status": "done", "items": ["提示词P0+P1+P2(30项)", "Admin 4页面", "品牌色苔绿", "emoji→Lucide", "编辑器视觉升级", "UX修复验证"]},
            {"phase": "Sprint 3", "status": "active", "items": ["引擎接UI(进行中)", "数据持久化", "Admin提示词管理", "主题全局Context", "用户中心/account"]},
            {"phase": "Sprint 4", "status": "pending", "items": ["全本TXT导出", "Admin补完6页", "创作流水线", "新手引导", "移动端适配"]},
        ],
        "updated": datetime.now().strftime("%H:%M:%S"),
    }

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # JSON helper
        if self.path == "/deliberoom.json":
            sessions = []
            dp = str(DELIB_DIR)
            if os.path.isdir(dp):
                for f in sorted(os.listdir(dp), reverse=True):
                    if f.endswith(".json"):
                        s = json.load(open(os.path.join(dp, f), encoding="utf-8"))
                        sessions.append({"id":s["id"],"topic":s["topic"],"status":s["status"],"participants":s.get("participants",[]),"rounds":s.get("rounds",[]),"conclusion":s.get("conclusion","")})
            self.send_response(200);self.send_header("Content-Type","application/json");self.send_header("Access-Control-Allow-Origin","*");self.end_headers()
            self.wfile.write(json.dumps(sessions,ensure_ascii=False).encode())
            return
        if self.path == "/deliberation":
            self.send_response(200);self.send_header("Content-Type","text/html;charset=utf-8");self.end_headers()
            self.wfile.write(open("D:/建网站/mojing-docs/deliberoom-viewer.html","rb").read())
            return
        if self.path == "/api/data":
            import json as _json
            try:
                data = get_data()
                resp = _json.dumps(data, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(resp)
            except Exception as _e:
                err = _json.dumps({"error": str(_e)})
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(err.encode("utf-8"))
            return
        elif self.path.startswith("/api/output/"):
            import urllib.parse
            filename = urllib.parse.unquote(self.path[12:])
            fp = OUTPUT_DIR / filename
            if fp.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(fp.read_text(encoding="utf-8").encode())
            else:
                self.send_response(404)
                self.end_headers()
        elif self.path == "/api/start-dev":
            import os
            os.startfile(r"D:\建网站\mojing-docs\Dev启动.vbs")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
        elif self.path == "/api/start-openclaw":
            import subprocess
            subprocess.Popen(
                'cmd /c start "" "C:\\Users\\nicou\\AppData\\Roaming\\npm\\openclaw.cmd" gateway run',
                shell=True
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
        elif self.path == "/uipm-data.json":
            with open("D:/建网站/mojing-docs/uipm-data.json", "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(data)
        elif self.path == "/skills-viz":
            with open("D:/建网站/mojing-docs/skills-viewer.html", "rb") as f:
                html = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html)
        elif self.path == "/design-db":
            try:
                with open("D:/建网站/mojing-docs/uipm-viewer.html", "rb") as f:
                    html_bytes = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html_bytes)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Error: {e}".encode())
        elif self.path == "/api/cluster":
            data = cluster_data()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
        elif self.path == "/cluster":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(CLUSTER_HTML.encode())
        elif self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode())
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, *a): pass

def DELIBERATION_HTML(sessions):
    cards = ""
    for s in sessions:
        color = "#22c55e" if s["status"] == "closed" else "#f59e0b"
        cards += '<div class="card" style="border-left:3px solid ' + color + '"><div style="flex:1"><div class="name">🏛️ ' + s["topic"][:60] + '</div><div class="meta">' + ', '.join(s["participants"]) + ' · ' + str(s["rounds"]) + '轮 · ' + s["status"] + '</div>'
        if s.get("conclusion"):
            cards += '<div class="meta" style="color:#6b8c6e">📋 ' + s["conclusion"] + '</div>'
        cards += '</div></div>'
    import html as h
    return '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>圆桌会议室 · 墨境</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:"PingFang SC","Microsoft YaHei",sans-serif;background:#faf9f6;color:#111}.container{max-width:800px;margin:0 auto;padding:24px}h1{font-size:20px;margin-bottom:4px}.sub{color:#888;font-size:12px;margin-bottom:20px}.card{background:#fff;border-radius:12px;padding:16px;margin-bottom:10px;border:1px solid #ebe5dd;display:flex;align-items:center;gap:12px}.name{font-weight:600;font-size:14px}.meta{font-size:11px;color:#888;margin-top:2px}a{color:#6b8c6e;text-decoration:none}.empty{text-align:center;color:#aaa;padding:40px;font-size:14px}.refresh{font-size:10px;color:#aaa;text-align:right;margin-top:8px}</style></head><body><div class="container"><h1>🏛️ 圆桌会议室</h1><div class="sub">Agent 多轮辩论 —— 每一轮都能看到别人说了什么</div>' + (cards if cards else '<div class="empty">暂无会议记录<br><span style="font-size:12px">会议自动出现——每轮发言实时可见</span></div>') + '<div class="refresh">每5秒刷新 · <a href="/">← 项目全景</a> · <a href="/cluster">集群</a></div></div><script>setTimeout(function(){location.reload()},5000)</script></body></html>'

CLUSTER_HTML = r'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>集群 · 墨境</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:"PingFang SC","Microsoft YaHei",sans-serif;background:#faf9f6;color:#111}.container{max-width:800px;margin:0 auto;padding:24px}h1{font-size:20px;margin-bottom:4px}.sub{color:#888;font-size:12px;margin-bottom:20px}.card{background:#fff;border-radius:12px;padding:16px;margin-bottom:10px;border:1px solid #ebe5dd;display:flex;align-items:center;gap:12px}.card.task{border-left:3px solid #8b5cf6}.card.window{border-left:3px solid #6b8c6e}.card.stale{border-left:3px solid #ef4444;background:#fef2f2}.icon{font-size:22px;width:36px;text-align:center}.name{font-weight:600;font-size:14px}.meta{font-size:11px;color:#888;margin-top:2px}.status{font-size:11px;margin-left:auto;min-width:55px;text-align:right}.healthy{color:#6b8c6e}.stale-tag{color:#ef4444}.bar{display:flex;gap:10px;margin-bottom:16px}.stat{background:#fff;border-radius:10px;padding:14px;flex:1;text-align:center;border:1px solid #ebe5dd}.stat-val{font-size:26px;font-weight:700}.stat-lbl{font-size:10px;color:#888;margin-top:2px}.feed{background:#fff;border-radius:12px;padding:14px;border:1px solid #ebe5dd;margin-top:14px}.feed-item{padding:6px 0;font-size:12px;border-bottom:1px solid #f5f5f5;display:flex;gap:8px}.feed-time{color:#aaa;flex-shrink:0;width:42px}.feed-from{color:#8b5cf6;flex-shrink:0;font-weight:600}.refresh{font-size:10px;color:#aaa;text-align:right;margin-top:8px}a{color:#6b8c6e;text-decoration:none}</style></head><body><div class="container">
<h1>🌙 墨境 · Agent 集群</h1><div class="sub" id="time">加载中...</div>
<div class="bar" id="stats"></div><div id="agents"></div>
<div class="feed" id="feed"><b>📨 集群决策流</b></div>
<div class="refresh">每5秒刷新 · <a href="/">← 项目全景</a></div></div>
<script>function fmt(t){return t==='N/A'?'--':t.split(':').slice(0,2).join(':')}
function render(d){document.getElementById('time').textContent='更新: '+d.updated;var total=0,ok=0,task=0,win=0,html='';
for(var k in d.agents){var a=d.agents[k];total++;a.healthy?ok++:0;a.mode==='task'?task++:win++;
var stale=a.mode==='task'&&!a.healthy?' stale':'';
var hc=a.healthy?'healthy':'stale-tag';var hl=a.healthy?'正常':'⚠️ 超时';
html+='<div class=\"card '+a.mode+stale+'\"><div class=\"icon\">'+a.icon+'</div><div><div class=\"name\">'+k+'</div><div class=\"meta\">任务:'+fmt(a.task_updated)+' · 活跃:'+fmt(a.last_active)+' · 记忆:'+(a.context_size||0)+'B</div></div><div class=\"status '+hc+'\">'+hl+'</div></div>';}
document.getElementById('agents').innerHTML=html;
document.getElementById('stats').innerHTML='<div class=\"stat\"><div class=\"stat-val\">'+total+'</div><div class=\"stat-lbl\">Agent</div></div><div class=\"stat\"><div class=\"stat-val\" style=\"color:#6b8c6e\">'+ok+'</div><div class=\"stat-lbl\">健康</div></div><div class=\"stat\"><div class=\"stat-val\" style=\"color:#8b5cf6\">'+task+'</div><div class=\"stat-lbl\">🔧 task</div></div><div class=\"stat\"><div class=\"stat-val\" style=\"color:#6b8c6e\">'+win+'</div><div class=\"stat-lbl\">🖥 窗口</div></div>';
if(d.decisions&&d.decisions.length){var feed='<b>📨 最近决策</b>';d.decisions.forEach(function(dd){feed+='<div class=\"feed-item\"><span class=\"feed-time\">'+dd.time+'</span><span class=\"feed-from\">'+dd.role+'</span><span>'+dd.decision+'</span></div>';});document.getElementById('feed').innerHTML=feed;}}
fetch('/api/cluster').then(r=>r.json()).then(render);setInterval(function(){fetch('/api/cluster').then(r=>r.json()).then(render)},5000);</script></body></html>'''

HTML = r'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>墨境 · 项目全景</title>
<style>
:root{
  --bg:#030712;--surface:#0a0f1d;--card:#111827;--border:rgba(255,255,255,.05);--border2:rgba(255,255,255,.08);
  --text:#f1f5f9;--text2:#94a3b8;--text3:#475569;
  --blue:#3b82f6;--green:#10b981;--amber:#f59e0b;--red:#ef4444;--purple:#8b5cf6;--cyan:#06b6d4;--pink:#ec4899;
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;overflow-x:hidden}
/* ====== AMBIENT BACKGROUND ====== */
body::before{
  content:'';position:fixed;inset:0;z-index:0;
  background:radial-gradient(ellipse 80% 50% at 20% 10%,rgba(59,130,246,.06) 0%,transparent 60%),
             radial-gradient(ellipse 60% 40% at 80% 80%,rgba(139,92,246,.04) 0%,transparent 60%);
  pointer-events:none
}
/* ====== TOP BAR ====== */
.topbar{
  position:sticky;top:0;z-index:50;padding:14px 32px;
  background:rgba(3,7,18,.85);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between
}
.brand{display:flex;align-items:center;gap:12px}
.brand .moon{font-size:24px;filter:drop-shadow(0 0 12px rgba(96,165,250,.4))}
.brand h1{font-size:17px;font-weight:700;letter-spacing:-.3px;background:linear-gradient(135deg,#e2e8f0 0%,#94a3b8 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.top-stats{display:flex;gap:28px;align-items:center}
.tstat{text-align:center}
.tstat .v{font-size:22px;font-weight:700;letter-spacing:-.5px}
.tstat .l{font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:.8px;margin-top:1px}
.server-chip{
  display:flex;align-items:center;gap:8px;padding:6px 14px;
  border-radius:20px;font-size:12px;font-weight:500;
  border:1px solid var(--border2);background:rgba(255,255,255,.03)
}
.server-chip .sc-dot{width:8px;height:8px;border-radius:50%}
.sc-on{background:var(--green);box-shadow:0 0 8px rgba(16,185,129,.6);animation:pulse 2s infinite}
.sc-off{background:var(--red)}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.4;transform:scale(.85)}}
/* ====== MAIN ====== */
.main{position:relative;z-index:1;padding:24px 32px;max-width:1440px;margin:0 auto}
/* ====== SUMMARY ROW ====== */
.summary-row{
  display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:28px
}
@media(max-width:1000px){.summary-row{grid-template-columns:repeat(2,1fr)}}
/* ====== ROADMAP ====== */
.roadmap{display:flex;gap:16px;margin-bottom:28px;overflow-x:auto;padding-bottom:8px}
.roadmap::-webkit-scrollbar{height:4px}
.roadmap::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
.rm-phase{flex:1;min-width:200px;background:var(--card);border:1px solid var(--border);border-radius:14px;padding:18px;position:relative}
.rm-phase .rm-badge{font-size:10px;padding:2px 10px;border-radius:10px;display:inline-block;margin-bottom:10px;font-weight:600}
.rm-done .rm-badge{background:rgba(16,185,129,.12);color:var(--green)}
.rm-active .rm-badge{background:rgba(59,130,246,.12);color:var(--blue);animation:pulse 2s infinite}
.rm-pending .rm-badge{background:rgba(100,116,139,.1);color:var(--text3)}
.rm-phase h4{font-size:14px;font-weight:600;margin-bottom:10px}
.rm-items{list-style:none;font-size:11px;line-height:1.8}
.rm-items li{color:var(--text2);padding:1px 0;display:flex;align-items:center;gap:6px}
.rm-done .rm-items li::before{content:'✅';font-size:10px}
.rm-active .rm-items li::before{content:'⏳'}
.rm-pending .rm-items li::before{content:'⬜';font-size:10px}
.rm-done{border-top:3px solid var(--green)}
.rm-active{border-top:3px solid var(--blue);box-shadow:0 0 20px rgba(59,130,246,.08)}
.rm-pending{border-top:3px solid var(--border)}
.server-hero{
  background:var(--card);border:1px solid var(--border);border-radius:18px;
  padding:24px 28px;margin-bottom:28px;
  display:flex;align-items:center;justify-content:space-between;gap:20px
}
@media(max-width:750px){.server-hero{flex-direction:column;align-items:flex-start}}
.server-row-hero{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:28px}
@media(max-width:900px){.server-row-hero{grid-template-columns:1fr}}
.sh-left{display:flex;align-items:center;gap:16px}
.sh-indicator{
  width:56px;height:56px;border-radius:50%;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;font-size:28px;
  transition:all .4s ease
}
.sh-on{background:rgba(16,185,129,.1);box-shadow:0 0 24px rgba(16,185,129,.15)}
.sh-off{background:rgba(239,68,68,.08);box-shadow:0 0 20px rgba(239,68,68,.1)}
.sh-mode{font-size:18px;font-weight:700;letter-spacing:-.3px}
.sh-url{font-size:11px;color:var(--text3);margin-top:2px}
.sh-metrics{display:flex;gap:20px}
@media(max-width:750px){.sh-metrics{flex-wrap:wrap;gap:14px}}
.sh-metric{text-align:center;min-width:60px}
.sh-metric .sh-val{font-size:18px;font-weight:700;letter-spacing:-.3px;font-family:'JetBrains Mono',Consolas,monospace}
.sh-metric .sh-lbl{font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:.5px;margin-top:2px}
.sh-fast{color:var(--green)}.sh-ok{color:var(--amber)}.sh-slow{color:var(--red)}
/* ====== PULSE BAR ====== */
.pulse-bar{display:flex;align-items:center;gap:10px;padding:10px 18px;background:var(--card);border:1px solid var(--border);border-radius:12px;margin-bottom:20px;font-size:12px;color:var(--text2)}
.pulse-sep{color:var(--border)}
.summary-card{
  background:var(--card);border:1px solid var(--border);border-radius:16px;
  padding:20px;position:relative;overflow:hidden
}
.summary-card .sc-icon{font-size:28px;margin-bottom:8px}
.summary-card .sc-val{font-size:28px;font-weight:700;letter-spacing:-.5px}
.summary-card .sc-lbl{font-size:11px;color:var(--text3);margin-top:2px}
.summary-card .sc-bar{
  margin-top:12px;height:4px;border-radius:2px;background:rgba(255,255,255,.05);overflow:hidden
}
.summary-card .sc-bar-fill{height:100%;border-radius:2px;transition:width .6s ease}
/* ====== SECTION HEADER ====== */
.sec-hd{
  display:flex;align-items:center;gap:10px;margin:28px 0 14px
}
.sec-hd span{font-size:12px;font-weight:600;color:var(--text3);text-transform:uppercase;letter-spacing:1px}
.sec-hd::after{content:'';flex:1;height:1px;background:var(--border)}
/* ====== ROLE CARDS ====== */
.role-grid{display:grid;grid-template-columns:repeat(8,1fr);gap:8px;overflow-x:auto}
@media(max-width:1200px){.role-grid{grid-template-columns:repeat(4,1fr)}}
.role-card{
  background:var(--card);border:1px solid var(--border);border-radius:12px;
  padding:12px;cursor:pointer;transition:all .25s;position:relative
}
.role-card:hover{border-color:var(--border2);transform:translateY(-2px);box-shadow:0 12px 40px rgba(0,0,0,.4)}
.role-card .r-hd{display:flex;align-items:center;gap:10px;margin-bottom:12px}
.role-card .r-icon{font-size:20px}
.role-card .r-name{font-size:12px;font-weight:600;flex:1}
.role-card .r-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0;transition:all .3s}
.r-active{background:var(--green);box-shadow:0 0 10px rgba(16,185,129,.5)}
.r-idle{background:#1e293b}
/* ====== CIRCULAR PROGRESS ====== */
.r-ring{display:flex;align-items:center;gap:10px;margin-bottom:8px}
.r-ring svg{flex-shrink:0}
.r-ring .r-pct{font-size:16px;font-weight:700;letter-spacing:-.5px}
.r-ring .r-pct-sub{font-size:10px;color:var(--text3);display:block}
.role-card .r-badge{
  font-size:10px;padding:3px 10px;border-radius:12px;display:inline-block;font-weight:500
}
.b-busy{background:rgba(245,158,11,.12);color:var(--amber)}
.b-done{background:rgba(16,185,129,.12);color:var(--green)}
.b-idle{background:rgba(100,116,139,.08);color:var(--text3)}
.role-card .r-info{font-size:10px;color:var(--text3);margin-top:8px;line-height:1.5}
.role-card .r-pv{font-size:11px;color:var(--text2);margin-top:4px;line-height:1.3;max-height:26px;overflow:hidden;opacity:.8}
/* ====== BOTTOM PANELS ====== */
.panel-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:28px}
@media(max-width:900px){.panel-row{grid-template-columns:1fr}}
.panel{
  background:var(--card);border:1px solid var(--border);border-radius:16px;padding:18px
}
.panel h3{font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px;display:flex;align-items:center;gap:6px}
.sv-row{display:flex;justify-content:space-between;align-items:center;padding:5px 0;font-size:12px;border-bottom:1px solid rgba(255,255,255,.03)}
.sv-row:last-child{border:none}
.sv-v{font-weight:600;font-family:'JetBrains Mono',Consolas,monospace;font-size:11px}
.sv-fast{color:var(--green)}.sv-ok{color:var(--amber)}.sv-slow{color:var(--red)}
.git-line{font-family:'JetBrains Mono',Consolas,monospace;font-size:11px;color:var(--text2);padding:4px 0;line-height:1.7}
.dec-line{padding:5px 0;font-size:11px;border-bottom:1px solid rgba(255,255,255,.03);line-height:1.5}
.dec-line:last-child{border:none}
.dec-h{color:var(--blue);font-weight:600;margin-right:4px}
/* ====== TIMELINE ====== */
.timeline{position:relative;padding-left:20px}
.timeline::before{content:'';position:absolute;left:5px;top:4px;bottom:4px;width:1px;background:var(--border2)}
.tl-item{position:relative;padding:8px 0;padding-left:24px;font-size:12px}
.tl-item::before{
  content:'';position:absolute;left:-18px;top:12px;
  width:8px;height:8px;border-radius:50%;border:2px solid var(--border2);background:var(--bg)
}
.tl-item.tl-active::before{border-color:var(--green);background:var(--green);box-shadow:0 0 6px rgba(16,185,129,.4)}
.tl-item.tl-busy::before{border-color:var(--amber);background:var(--amber)}
.tl-role{font-weight:600}
.tl-act{color:var(--text2);margin-left:4px}
.tl-time{font-size:10px;color:var(--text3);float:right}
/* ====== MODAL ====== */
.modal-overlay{
  position:fixed;inset:0;background:rgba(0,0,0,.8);backdrop-filter:blur(8px);
  display:none;z-index:100;align-items:center;justify-content:center
}
.modal-overlay.show{display:flex}
.modal-box{
  background:var(--surface);border:1px solid var(--border2);border-radius:20px;
  padding:28px;max-width:750px;width:92%;max-height:82vh;overflow-y:auto
}
.modal-box h2{font-size:16px;margin-bottom:16px;display:flex;align-items:center;gap:8px}
.modal-box pre{
  background:var(--bg);padding:18px;border-radius:12px;font-size:12px;line-height:1.7;
  white-space:pre-wrap;color:var(--text);font-family:'JetBrains Mono',Consolas,monospace;
  max-height:52vh;overflow-y:auto
}
.modal-actions{margin-top:16px;display:flex;gap:8px}
.btn{padding:8px 18px;border:none;border-radius:10px;font-size:12px;cursor:pointer;font-weight:500;transition:all .15s}
.btn-p{background:var(--blue);color:#fff}.btn-p:hover{background:#2563eb}
.btn-g{background:rgba(255,255,255,.04);color:var(--text2)}.btn-g:hover{background:rgba(255,255,255,.08)}
.foot{text-align:center;padding:20px;color:#0f172a;font-size:10px}
/* ====== NOTIFICATION ====== */
.notify-badge{
  display:none;background:var(--red);color:#fff;font-size:11px;font-weight:700;
  padding:3px 10px;border-radius:12px;margin-left:8px;
  animation:badge-pop .4s ease
}
.r-update-dot{font-size:10px;margin-left:4px;cursor:pointer;animation:badge-pop .4s ease}
.sec-badge{font-size:10px;padding:1px 8px;border-radius:8px;background:rgba(239,68,68,.12);color:var(--red);margin-left:8px;animation:badge-pop .4s ease}
@keyframes badge-pop{0%{transform:scale(.5);opacity:0}60%{transform:scale(1.15)}100%{transform:scale(1);opacity:1}}
.notify-badge.show{display:inline-block}
.topbar.flash-alert{border-bottom-color:var(--red);box-shadow:0 1px 20px rgba(239,68,68,.15);transition:all .3s}
.topbar.flash-alert .moon{animation:moon-shake .5s ease}
@keyframes moon-shake{0%,100%{transform:rotate(0)}25%{transform:rotate(-8deg)}75%{transform:rotate(8deg)}}
</style></head><body>
<div class="topbar">
  <div class="brand"><span class="moon">🌙</span><h1>墨境 · 项目全景</h1>
    <select id="refreshSelect" onchange="changeInterval()" style="background:var(--card);color:var(--text2);border:1px solid var(--border);border-radius:6px;padding:1px 6px;font-size:10px;cursor:pointer;margin-left:10px">
      <option value="5">5秒</option><option value="10">10秒</option><option value="30">30秒</option><option value="60">60秒</option><option value="0">手动</option>
    </select>
    <button onclick="refresh()" title="立即刷新" style="background:var(--card);color:var(--text2);border:1px solid var(--border);border-radius:6px;padding:1px 8px;font-size:12px;cursor:pointer;margin-left:4px">🔄</button>
    <a href="/design-db" target="_blank" style="background:var(--card);color:var(--blue);border:1px solid var(--border);border-radius:6px;padding:1px 10px;font-size:11px;text-decoration:none;margin-left:8px">🎨 设计库</a>
    <a href="/skills-viz" target="_blank" style="background:var(--card);color:var(--blue);border:1px solid var(--border);border-radius:6px;padding:1px 10px;font-size:11px;text-decoration:none;margin-left:4px">📦 技能包</a>
    <span class="notify-badge" id="notifyBadge">🆕 新成果</span></div>
  <div class="top-stats">
    <div class="tstat" id="tsRoles"><div class="v">-</div><div class="l">团队</div></div>
    <div class="tstat" id="tsActive"><div class="v">-</div><div class="l">活跃</div></div>
    <div class="tstat" id="tsDone"><div class="v">-</div><div class="l">完成</div></div>
    <div class="server-chip" id="serverChip"><span class="sc-dot sc-off"></span><span id="serverLabel">检测中</span></div>
  </div>
</div>

<div class="main">
  <!-- ====== SUMMARY CARDS ====== -->
  <div class="summary-row">
    <div class="summary-card">
      <div class="sc-icon">📋</div>
      <div class="sc-val" id="sumTotal">0</div>
      <div class="sc-lbl">总任务</div>
      <div class="sc-bar"><div class="sc-bar-fill" id="sumBar" style="width:0%;background:var(--blue)"></div></div>
    </div>
    <div class="summary-card">
      <div class="sc-icon">⏳</div>
      <div class="sc-val" id="sumBusy">0</div>
      <div class="sc-lbl">执行中</div>
      <div class="sc-bar"><div class="sc-bar-fill" id="busyBar" style="width:0%;background:var(--amber)"></div></div>
    </div>
    <div class="summary-card">
      <div class="sc-icon">✅</div>
      <div class="sc-val" id="sumDone">0</div>
      <div class="sc-lbl">已完成</div>
      <div class="sc-bar"><div class="sc-bar-fill" id="doneBar" style="width:0%;background:var(--green)"></div></div>
    </div>
    <div class="summary-card">
      <div class="sc-icon">💤</div>
      <div class="sc-val" id="sumIdle">0</div>
      <div class="sc-lbl">空闲</div>
      <div class="sc-bar"><div class="sc-bar-fill" id="idleBar" style="width:0%;background:var(--text3)"></div></div>
    </div>
  </div>

  <!-- ====== SERVER HERO ====== -->
  <div class="server-row-hero">
  <div class="server-hero" id="serverHero">
    <div class="sh-left">
      <div class="sh-indicator" id="shDot"></div>
      <div>
        <div class="sh-mode" id="shMode">检测中...</div>
        <div class="sh-url">localhost:3000</div>
      </div>
    </div>
    <div class="sh-metrics" id="shMetrics"></div>
  </div>
  <div class="server-hero" id="openclawHero">
    <div class="sh-left">
      <div class="sh-indicator" id="ocDot">🔴</div>
      <div>
        <div class="sh-mode" id="ocMode">检测中...</div>
        <div class="sh-url">OpenClaw Gateway</div>
      </div>
    </div>
    <div class="sh-metrics" id="ocMetrics"></div>
  </div>
  </div>

  <!-- ====== PULSE ====== -->
  <div class="pulse-bar" id="pulseBar">
    <span>🟢 全部正常</span><span class="pulse-sep">·</span>
    <span id="pulseActive">0人活跃</span><span class="pulse-sep">·</span>
    <span id="pulseIssues">0项待处理</span><span class="pulse-sep">·</span>
    <span id="pulseTime">刚刚</span>
  </div>

  <!-- ====== TEAM ====== -->
  <div class="sec-hd"><span>👥 团队</span></div>
  <div class="role-grid" id="roleGrid"></div>

  <!-- ====== ROADMAP ====== -->
  <div class="sec-hd"><span>🗺️ 开发路线图</span></div>
  <div class="roadmap" id="roadmap"></div>

  <!-- ====== PANELS ====== -->
  <div class="sec-hd"><span>📊 系统</span><span class="sec-badge" id="gitBadge" style="display:none">📦 更新</span><span class="sec-badge" id="decBadge" style="display:none">📋 更新</span></div>
  <div class="panel-row">
    <div class="panel"><h3>📋 决策日志</h3><div id="decPanel"></div></div>
    <div class="panel"><h3>📦 Git</h3><div id="gitPanel"></div></div>
  </div>

  <!-- ====== TIMELINE ====== -->
  <div class="sec-hd"><span>⏱️ 动态</span></div>
  <div class="panel" style="margin-bottom:28px">
    <div class="timeline" id="timeline"></div>
  </div>
</div>

<div class="modal-overlay" id="modal" onclick="closeModal()">
  <div class="modal-box" onclick="event.stopPropagation()">
    <h2 id="modalTitle"></h2><pre id="modalContent"></pre>
    <div class="modal-actions">
      <button class="btn btn-p" onclick="navigator.clipboard.writeText(document.getElementById('modalContent').textContent);this.textContent='✅ 已复制';setTimeout(()=>this.textContent='📋 复制',1500)">📋 复制</button>
      <button class="btn btn-g" onclick="closeModal()">关闭</button>
    </div>
  </div>
</div>
<div class="foot">墨境项目全景</div>

<script>
const ROLE_COLORS={
  "后端技术负责人":"#3b82f6","前端技术负责人":"#8b5cf6",
  "架构审查员":"#f59e0b","提示词系统专家":"#ec4899",
  "产品经理":"#10b981","UIUX设计师":"#f97316","QA测试工程师":"#06b6d4"
};
function esc(s){return s.replace(/\\/g,'\\\\').replace(/'/g,"\\'").replace(/"/g,'&quot;').replace(/\n/g,'\\n')}
function closeModal(){document.getElementById('modal').classList.remove('show')}
function showModal(title,content){
  document.getElementById('modalTitle').textContent=title;
  document.getElementById('modalContent').textContent=content;
  document.getElementById('modal').classList.add('show')
}
// SVG ring: radius=22, circumference=138.23
function ringSVG(pct,color){
  const c=138.23,offset=c*(1-pct/100);
  return `<svg width="52" height="52" viewBox="0 0 52 52"><circle cx="26" cy="26" r="22" fill="none" stroke="rgba(255,255,255,.06)" stroke-width="3"/><circle cx="26" cy="26" r="22" fill="none" stroke="${color}" stroke-width="3" stroke-dasharray="${c}" stroke-dashoffset="${offset}" stroke-linecap="round" transform="rotate(-90 26 26)" style="transition:stroke-dashoffset .8s ease"/></svg>`;
}

async function refresh(){
  try{
    const r=await fetch('/api/data');const d=await r.json();
    // ====== TOP STATS ======
    let act=0,out=0,busy=0,idle=0;
    d.roles.forEach(x=>{if(x.active)act++;if(x.output)out++;if(x.task&&!x.output)busy++;if(!x.task&&!x.output)idle++});
    document.querySelector('#tsRoles .v').textContent=d.roles.length;
    document.querySelector('#tsActive .v').textContent=act;
    document.querySelector('#tsDone .v').textContent=out;
    const sl=document.getElementById('serverLabel'),sc=document.getElementById('serverChip').querySelector('.sc-dot');
    if(d.server.port_3000){sl.textContent='3000 运行中';sc.className='sc-dot sc-on'}
    else{sl.textContent='3000 未运行';sc.className='sc-dot sc-off'}

    // ====== SUMMARY CARDS ======
    const total=d.roles.length, totalPct=total?100:0;
    document.getElementById('sumTotal').textContent=total;
    document.getElementById('sumBar').style.width=totalPct+'%';
    document.getElementById('sumBusy').textContent=busy;
    document.getElementById('busyBar').style.width=(total?(busy/total*100):0)+'%';
    document.getElementById('sumDone').textContent=out;
    document.getElementById('doneBar').style.width=(total?(out/total*100):0)+'%';
    document.getElementById('sumIdle').textContent=idle;
    document.getElementById('idleBar').style.width=(total?(idle/total*100):0)+'%';

    // ====== PULSE BAR ======
    let issues=0; d.roles.forEach(r=>{if(!r.task&&!r.output)issues++});
    document.getElementById('pulseActive').textContent=act+'人活跃';
    document.getElementById('pulseIssues').textContent=issues+'人空闲';
    document.getElementById('pulseTime').textContent='更新 '+d.updated;
    const pb=document.getElementById('pulseBar');
    pb.innerHTML=pb.innerHTML.replace(/🟢|🟡|🔴/, issues>3?'🟡 注意':issues>5?'🔴 异常':'🟢 正常');

    // ====== ROLE CARDS ======
    const g=document.getElementById('roleGrid');g.innerHTML='';
    d.roles.forEach(r=>{
      const hasOut=!!r.output,hasTask=!!r.task;
      const color=ROLE_COLORS[r.name]||'#3b82f6';
      // Progress: 100=has output, 50=has task, 20=active, 0=idle
      let pct=0;
      if(hasOut)pct=100;else if(hasTask)pct=50;else if(r.active)pct=20;
      const c=document.createElement('div');c.className='role-card';
      let pv='';
      if(hasOut)pv=`<div class="r-pv" style="color:var(--green);cursor:pointer">📄 ${r.output.file}</div>`;
      else if(hasTask)pv=`<div class="r-pv" style="cursor:pointer">📝 ${r.task.substring(0,60)}...</div>`;
      c.innerHTML=`<div class="r-hd">
        <span class="r-icon">${r.icon}</span><span class="r-name">${r.name}</span>
        <span class="r-dot ${r.active?'r-active':'r-idle'}" title="${r.active?'活跃(2分钟)':'空闲'}"></span>
      </div>
      <div class="r-ring">
        ${ringSVG(pct,color)}
        <div><span class="r-pct">${pct}%</span><span class="r-pct-sub">进度</span></div>
      </div>
      <span class="r-badge ${hasOut?'b-done':hasTask?'b-busy':'b-idle'}">${hasOut?'✅ 已完成':hasTask?'⏳ 执行中':'💤 空闲'}</span>
      ${roleUpdates[r.name]?`<span class="r-update-dot" title="新产出: ${roleUpdates[r.name]}" onclick="event.stopPropagation();showModal('${r.icon} ${r.name} — 新产出','${roleUpdates[r.name]}')">🆕</span>`:''}
      <div class="r-info">${r.last_activity||'--'} · ${r.msg_count}条消息</div>${pv}`;
      c.onclick=()=>{
        if(hasOut)showModal(r.icon+' '+r.name+' — '+r.output.file,r.output.content);
        else if(hasTask)showModal(r.icon+' '+r.name+' — 任务',r.task);
      };
      g.appendChild(c);
    });

    // ====== SERVER HERO ======
    const s=d.server;
    const respClass=s.response_ms<100?'sh-fast':s.response_ms<500?'sh-ok':'sh-slow';
    const modeColor=s.running?(s.mode.includes('dev')?'var(--blue)':'var(--green)'):'var(--red)';
    document.getElementById('shDot').className='sh-indicator '+(s.running?'sh-on':'sh-off');
    document.getElementById('shDot').textContent=s.running?'🟢':'🔴';
    document.getElementById('shMode').innerHTML=`<span style="color:${modeColor}">${s.mode}</span>`;
    document.getElementById('shMetrics').innerHTML=`
      <div class="sh-metric"><div class="sh-val ${respClass}">${s.response_ms||'--'}</div><div class="sh-lbl">ms 响应</div></div>
      <div class="sh-metric"><div class="sh-val">${s.port_3000?'✅':'❌'} ${s.port_3001?'✅':''}</div><div class="sh-lbl">端口 3000/3001</div></div>
      <div class="sh-metric"><div class="sh-val">${s.node_count||0}</div><div class="sh-lbl">Node 进程</div></div>
      ${s.next_version?`<div class="sh-metric"><div class="sh-val">v${s.next_version}</div><div class="sh-lbl">Next.js</div></div>`:''}
      ${s.running
        ? `<div class="sh-metric"><a href="http://localhost:3000" target="_blank" style="color:var(--blue);text-decoration:none;font-weight:600">↗</a><div class="sh-lbl">打开网站</div></div>`
        : `<div class="sh-metric" style="cursor:pointer" onclick="fetch('/api/start-dev');this.innerHTML='<div class=sh-val>⏳</div><div class=sh-lbl>启动中</div>';setTimeout(()=>location.reload(),12000)"><div class="sh-val" style="color:var(--green)">▶</div><div class="sh-lbl">启动</div></div>`
      }
    `;

    // ====== OPENCLAW PANEL ======
    const oc = d.openclaw;
    document.getElementById('ocDot').className = 'sh-indicator '+(oc.running?'sh-on':'sh-off');
    document.getElementById('ocDot').textContent = oc.running?'🦞':'🔴';
    document.getElementById('ocMode').innerHTML = `<span style="color:${oc.running?'var(--green)':'var(--red)'}">${oc.running?'🟢 运行中':'❌ 未运行'}</span>`;
    document.getElementById('ocMetrics').innerHTML = `
      <div class="sh-metric"><div class="sh-val">:18789</div><div class="sh-lbl">端口</div></div>
      ${oc.running
        ? `<div class="sh-metric"><a href="http://127.0.0.1:18789" target="_blank" style="color:var(--blue);text-decoration:none;font-weight:600">↗</a><div class="sh-lbl">打开</div></div>`
        : `<div class="sh-metric" style="cursor:pointer" onclick="fetch('/api/start-openclaw');this.innerHTML='<div class=sh-val>⏳</div><div class=sh-lbl>启动中</div>';setTimeout(()=>location.reload(),10000)"><div class="sh-val" style="color:var(--green)">▶</div><div class="sh-lbl">启动</div></div>`
      }
    `;

    // ====== ROADMAP ======
    const rm = document.getElementById('roadmap');
    rm.innerHTML = d.roadmap.map(p => `
      <div class="rm-phase rm-${p.status}">
        <span class="rm-badge">${p.status==='done'?'✅ 已完成':p.status==='active'?'🔄 进行中':'⬜ 待开始'}</span>
        <h4>${p.phase}</h4>
        <ul class="rm-items">${p.items.map(i=>`<li>${i}</li>`).join('')}</ul>
      </div>
    `).join('');

    // ====== DECISIONS ======
    const dd=document.getElementById('decPanel');
    if(d.decisions.length>0){
      dd.innerHTML=d.decisions.map(x=>`<div class="dec-line"><span class="dec-h">${x.title}</span></div>`).join('');
    }else{dd.innerHTML='<div class="dec-line" style="color:var(--text3)">暂无</div>'}

    // ====== GIT ======
    document.getElementById('gitPanel').innerHTML=(d.git||'N/A').split('\n').map(l=>`<div class="git-line">${l||'&nbsp;'}</div>`).join('');
    if(gitUpdated){document.getElementById('gitBadge').style.display='inline-block';}

    // Toggle update badges
    if(decUpdated){document.getElementById('decBadge').style.display='inline-block';}
    // Clear role updates after showing
    setTimeout(()=>{roleUpdates={};gitUpdated=false;decUpdated=false;},8000);

    // ====== TIMELINE ======
    const tl=document.getElementById('timeline');
    let items=[];
    d.roles.forEach(r=>{
      if(r.output)items.push({icon:r.icon,name:r.name,action:'输出成果: '+r.output.file,time:r.output.time,cls:'tl-active'});
      else if(r.task)items.push({icon:r.icon,name:r.name,action:'执行任务中...',time:r.last_activity||'',cls:'tl-busy'});
      else if(r.active)items.push({icon:r.icon,name:r.name,action:'在线',time:r.last_activity||'',cls:'tl-active'});
      else items.push({icon:r.icon,name:r.name,action:'空闲',time:r.last_activity||'',cls:''});
    });
    if(items.length===0){tl.innerHTML='<div style="color:var(--text3);font-size:12px;padding:4px 0">暂无动态</div>'}
    else{tl.innerHTML=items.map(i=>`<div class="tl-item ${i.cls}"><span class="tl-role">${i.icon} ${i.name}</span><span class="tl-act">${i.action}</span><span class="tl-time">${i.time}</span></div>`).join('');}
    checkNotifications(d.roles,d.git,d.decisions,d.server);
  }catch(e){console.error(e)}
}
let refreshTimer=setInterval(refresh,5000);
let knownOutputs=new Set();
let prevGit='',prevDecCount=0,prevActive=0,prevServerRunning=null;
let roleUpdates={},gitUpdated=false,decUpdated=false;

function checkNotifications(roles,git,decisions,server){
  const current=new Set();
  roles.forEach(r=>{if(r.output)current.add(r.output.file)});
  let alerts=[];
  // 新产出 - 标记具体角色
  if(knownOutputs.size>0){
    current.forEach(f=>{
      if(!knownOutputs.has(f)){
        const role = roles.find(r=>r.output&&r.output.file===f);
        if(role) roleUpdates[role.name]=f;
        alerts.push('📄 '+f);
      }
    });
  }
  knownOutputs=current;
  // Git
  if(prevGit && prevGit!==git){alerts.push('📦 Git更新');gitUpdated=true;}
  prevGit=git;
  // 决策
  if(prevDecCount && decisions.length!==prevDecCount){alerts.push('📋 新决策');decUpdated=true;}
  prevDecCount=decisions.length;
  // 活跃变化
  let act=0;roles.forEach(r=>{if(r.active)act++});
  if(prevActive && act!==prevActive) alerts.push('🟢 活跃变化');
  prevActive=act;
  // 服务器
  if(prevServerRunning!==null && prevServerRunning!==server.running) alerts.push('🖥️ 服务器变更');
  prevServerRunning=server.running;

  if(alerts.length>0){
    const badge=document.getElementById('notifyBadge');
    badge.textContent='🆕 '+alerts.join(' · ');
    badge.classList.add('show');
    document.querySelector('.topbar').classList.add('flash-alert');
    setTimeout(()=>{badge.classList.remove('show');document.querySelector('.topbar').classList.remove('flash-alert')},8000);
  }
}
function changeInterval(){
  const v=parseInt(document.getElementById('refreshSelect').value);
  clearInterval(refreshTimer);
  if(v>0)refreshTimer=setInterval(refresh,v*1000);
}
refresh();refreshTimer;
</script></body></html>'''

if __name__ == "__main__":
    # Kill any existing process on port 8899
    import os
    os.system('netstat -ano | findstr ":8899" | findstr "LISTENING" | awk "{print $5}" | sort -u | while read p; do taskkill //F //PID $p 2>nul; done')
    time.sleep(0.5)
    s = http.server.HTTPServer(("127.0.0.1", PORT), H)
    print(f"http://localhost:{PORT}")
    webbrowser.open(f"http://localhost:{PORT}")
    s.serve_forever()
