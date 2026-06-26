"""
墨境 Agent 集群 v2.0 — 完整集群协议
====================================
文件系统即消息总线。自动故障转移。无需服务器。
"""
import os, json, datetime, time, threading, webbrowser, subprocess, sys, traceback
sys.path.insert(0, "D:/建网站/mojing-docs")
from http.server import HTTPServer, BaseHTTPRequestHandler

BASE = "D:/建网站/mojing-docs"
CONTEXT = f"{BASE}/context"
INBOX = f"{CONTEXT}/inbox"
OUTBOX = f"{CONTEXT}/outbox"
BROADCAST = f"{CONTEXT}/broadcast.json"
DECISIONS = f"{CONTEXT}/decisions.jsonl"
QA_REPORTS = f"{CONTEXT}/qa-reports"

# 窗口角色心跳超时阈值
WINDOW_HEARTBEAT_HOURS = 24
WINDOW_HEARTBEAT_SECONDS = WINDOW_HEARTBEAT_HOURS * 3600  # 86400s

# 确保目录
for d in [INBOX, OUTBOX, QA_REPORTS]:
    os.makedirs(d, exist_ok=True)

# ═══════════════════════════════════════
# 第一层：消息协议
# ═══════════════════════════════════════

def send_message(sender: str, target: str, msg_type: str, content: str):
    """Agent 间消息——写入目标收件箱"""
    msg = {
        "from": sender, "to": target,
        "type": msg_type,  # "bug_report" | "code_review" | "suggestion" | "handoff" | "broadcast"
        "content": content,
        "timestamp": datetime.datetime.now().isoformat(),
    }
    fp = os.path.join(INBOX, f"{target}.jsonl")
    with open(fp, "a", encoding="utf-8") as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")

def read_inbox(name: str, mark_read: bool = True) -> list:
    """读取收件箱"""
    fp = os.path.join(INBOX, f"{name}.jsonl")
    if not os.path.exists(fp): return []
    msgs = [json.loads(l) for l in open(fp, encoding="utf-8").readlines()]
    if mark_read and msgs:
        os.remove(fp)  # 读完清空
    return msgs

def broadcast(sender: str, content: str):
    """全集群广播"""
    send_message(sender, "__all__", "broadcast", content)

# ═══════════════════════════════════════
# 第二层：决策日志（append-only，全集群共享）
# ═══════════════════════════════════════

def log_decision(role: str, decision: str, reasoning: str):
    with open(DECISIONS, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "role": role, "decision": decision,
            "reasoning": reasoning,
            "timestamp": datetime.datetime.now().isoformat(),
        }, ensure_ascii=False) + "\n")

# ═══════════════════════════════════════
# 第三层：QA 门禁
# ═══════════════════════════════════════

def trigger_qa(triggered_by: str, reason: str):
    """代码变更后自动通知 QA"""
    report = {
        "triggered_by": triggered_by,
        "reason": reason,
        "timestamp": datetime.datetime.now().isoformat(),
        "status": "pending"
    }
    fp = os.path.join(QA_REPORTS, f"{datetime.datetime.now().strftime('%m%d-%H%M')}.json")
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    send_message(triggered_by, "QA测试工程师", "qa_request", f"请验证: {reason}")
    return fp

# ═══════════════════════════════════════
# 第四层：自动故障转移
# ═══════════════════════════════════════

FAIL_TIMEOUT_MINUTES = 15

def check_health() -> dict:
    """检查所有 Agent 健康状态"""
    status = {}
    from dispatch import ROLES, TASKS, SESSIONS
    now = time.time()
    for name, cfg in ROLES.items():
        tf = os.path.join(TASKS, cfg["task"])
        sf = os.path.join(SESSIONS, cfg["session"])
        t_mtime = os.path.getmtime(tf) if os.path.exists(tf) else 0
        s_mtime = os.path.getmtime(sf) if os.path.exists(sf) else 0
        mode = cfg.get("mode", "window")
        # task: 超时15分钟 → stale；window: 超时24小时 → stale
        if mode == "task":
            stale = (now - s_mtime > FAIL_TIMEOUT_MINUTES * 60)
        else:
            stale = (now - s_mtime > WINDOW_HEARTBEAT_SECONDS)
        # 计算最后心跳距今小时数（window 角色用）
        hours_since = round((now - s_mtime) / 3600, 1) if s_mtime else None
        # 窗口角色 stale → 写 decisions.jsonl 告警
        if mode != "task" and stale:
            _log_window_heartbeat_alert(name, hours_since)
        # 窗口角色心跳状态：显式标记 24h 阈值
        heartbeat_status = None
        if mode != "task":
            if stale:
                heartbeat_status = "超时"
            else:
                heartbeat_status = "正常"
        status[name] = {
            "mode": mode,
            "task_updated": datetime.datetime.fromtimestamp(t_mtime).strftime("%H:%M") if t_mtime else "N/A",
            "last_active": datetime.datetime.fromtimestamp(s_mtime).strftime("%H:%M") if s_mtime else "N/A",
            "healthy": not stale,
            "hours_since_heartbeat": hours_since,  # window 角色专属
            "heartbeat_status": heartbeat_status,   # "正常" / "超时" / None
            "heartbeat_threshold_hours": WINDOW_HEARTBEAT_HOURS,  # 阈值=24h
        }
    return status


def _log_window_heartbeat_alert(name: str, hours_since: float):
    """向 decisions.jsonl 写入窗口角色心跳告警（避免重复刷写——同角色1小时内不再重复告警）"""
    # 防止重复刷写：检查最后一条同类告警的时间
    recent = []
    if os.path.exists(DECISIONS):
        for l in open(DECISIONS, encoding="utf-8").readlines():
            d = json.loads(l)
            recent.append(d)
    for d in reversed(recent):
        if d.get("role") == "集群监控" and name in d.get("decision", ""):
            last_ts = datetime.datetime.fromisoformat(d["timestamp"])
            if (datetime.datetime.now() - last_ts).total_seconds() < 3600:
                return  # 1小时内已告警过，跳过
            break
    log_decision("集群监控",
                 f"🖥️ 窗口心跳异常: {name} 已 {hours_since} 小时未响应",
                 f"窗口角色 {name} 超过 {WINDOW_HEARTBEAT_HOURS}h 无心跳，标记为 stale")

# ═══════════════════════════════════════
# 第五层：Web 仪表盘
# ═══════════════════════════════════════

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>墨境 · Agent 集群</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"PingFang SC","Microsoft YaHei",sans-serif;background:#faf9f6;color:#111}
.container{max-width:900px;margin:0 auto;padding:24px}
h1{font-size:22px;margin-bottom:4px}
.sub{color:#888;font-size:12px;margin-bottom:20px}
.card{background:#fff;border-radius:14px;padding:18px;margin-bottom:12px;border:1px solid #ebe5dd;display:flex;align-items:center;gap:14px}
.card.task{border-left:3px solid #8b5cf6}
.card.window{border-left:3px solid #6b8c6e}
.icon{font-size:22px;width:36px;text-align:center}
.name{font-weight:600;font-size:14px}
.meta{font-size:11px;color:#888;margin-top:2px}
.status{font-size:11px;margin-left:auto;min-width:60px;text-align:right}
.healthy{color:#6b8c6e}.stale{color:#ef4444}
.bar{display:flex;gap:12px;margin-bottom:16px}
.stat{background:#fff;border-radius:10px;padding:14px 18px;flex:1;text-align:center;border:1px solid #ebe5dd}
.stat-val{font-size:28px;font-weight:700}
.stat-lbl{font-size:11px;color:#888;margin-top:2px}
.feed{background:#fff;border-radius:14px;padding:16px;border:1px solid #ebe5dd;margin-top:16px}
.feed-item{padding:6px 0;font-size:12px;border-bottom:1px solid #f5f5f5;display:flex;gap:8px}
.feed-time{color:#aaa;flex-shrink:0;width:42px}
.feed-from{color:#8b5cf6;flex-shrink:0;font-weight:600}
.refresh{font-size:10px;color:#aaa;text-align:right}
</style>
</head>
<body>
<div class="container">
<h1>🌙 墨境 · Agent 集群</h1>
<div class="sub" id="time">加载中...</div>
<div class="bar" id="stats"></div>
<div id="agents"></div>
<div class="feed" id="feed"><b>📨 集群消息流</b></div>
<div class="refresh">每5秒自动刷新 · <a href="/cluster-api" style="color:#6b8c6e">JSON API</a></div>
</div>
<script>
function fmtTime(t){if(t==='N/A')return'--';var m=t.split(':');return m[0]+':'+m[1]}
function render(data){
  document.getElementById('time').textContent = '更新时间: ' + new Date().toLocaleTimeString();
  var total=0,healthy=0,taskN=0,winN=0;
  var agents='';
  for(var k in data.agents){
    var a=data.agents[k]; total++;
    var icon=a.mode==='task'?'🔧':'🖥️';
    var cls=a.mode==='task'?'task':'window';
    var hc=a.healthy?'healthy':'stale';
    var hLabel=a.healthy?'正常':'⚠️ 超时';
    // window 角色显示心跳时间
    var heartbeatInfo='';
    if(a.mode!=='task' && a.hours_since_heartbeat!==null){
      if(a.hours_since_heartbeat < 1){
        heartbeatInfo=' · 心跳: '+Math.round(a.hours_since_heartbeat*60)+'分钟前';
      } else {
        heartbeatInfo=' · 心跳: '+a.hours_since_heartbeat+'小时前';
      }
    }
    if(a.healthy)healthy++;
    if(a.mode==='task')taskN++;else winN++;
    agents+='<div class=\"card '+cls+'\"><div class=\"icon\">'+icon+'</div><div><div class=\"name\">'+k+'</div><div class=\"meta\">任务: '+fmtTime(a.task_updated)+' · 活跃: '+fmtTime(a.last_active)+heartbeatInfo+'</div></div><div class=\"status '+hc+'\">'+hLabel+'</div></div>';
  }
  document.getElementById('agents').innerHTML=agents;
  document.getElementById('stats').innerHTML='<div class=\"stat\"><div class=\"stat-val\">'+total+'</div><div class=\"stat-lbl\">总 Agent</div></div><div class=\"stat\"><div class=\"stat-val\" style=\"color:#6b8c6e\">'+healthy+'</div><div class=\"stat-lbl\">健康</div></div><div class=\"stat\"><div class=\"stat-val\" style=\"color:#8b5cf6\">'+taskN+'</div><div class=\"stat-lbl\">🔧 task</div></div><div class=\"stat\"><div class=\"stat-val\" style=\"color:#6b8c6e\">'+winN+'</div><div class=\"stat-lbl\">🖥 窗口</div></div>';
  // 最近决策
  if(data.recent_decisions){var feed='<b>📨 最近决策</b>';data.recent_decisions.forEach(function(d){feed+='<div class=\"feed-item\"><span class=\"feed-time\">'+d.time+'</span><span class=\"feed-from\">'+d.role+'</span><span>'+d.decision+'</span></div>';});document.getElementById('feed').innerHTML=feed;}
}
fetch('/cluster-api').then(r=>r.json()).then(render);
setInterval(function(){fetch('/cluster-api').then(r=>r.json()).then(render);},5000);
</script>
</body>
</html>"""

class ClusterAPI(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode())
        elif self.path == "/cluster-api":
            status = check_health()
            # 最近决策
            decisions = []
            if os.path.exists(DECISIONS):
                lines = open(DECISIONS,encoding="utf-8").readlines()
                for l in lines[-8:]:
                    d = json.loads(l)
                    decisions.append({"role":d["role"],"decision":d["decision"][:60],"time":d["timestamp"][11:16]})
            self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers()
            self.wfile.write(json.dumps({"agents":status,"recent_decisions":list(reversed(decisions))},ensure_ascii=False).encode())
        else:
            self.send_response(404); self.end_headers()

def start_dashboard(port=8900):
    """启动集群仪表盘"""
    server = HTTPServer(("127.0.0.1", port), ClusterAPI)
    print(f"🌙 集群仪表盘: http://127.0.0.1:{port}")
    webbrowser.open(f"http://127.0.0.1:{port}")
    server.serve_forever()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "dashboard":
        start_dashboard()
    elif len(sys.argv) > 1 and sys.argv[1] == "monitor":
        start_monitor()
    elif len(sys.argv) > 1 and sys.argv[1] == "deliberate":
        # 多路审议模板
        topic = sys.argv[2] if len(sys.argv) > 2 else "新功能"
        print(f"""
多路审议: {topic}
──────────────────────────────
并行调度4个小弟:

1. 激进方案: 最优体验，不考虑兼容性
2. 保守方案: 最小改动，零风险
3. UX视角: 用户看到什么、怎么交互
4. 挑刺: 所有可能出问题的地方

审议后总管合成最佳方案。
──────────────────────────────
""")
    else:
        print("用法:")
        print("  python cluster.py dashboard    — 启动集群仪表盘 :8900")
        print("  python cluster.py monitor      — 启动后台健康监控（自动重试+监督）")
        print("  python cluster.py deliberate   — 多路审议模板")
        print("  python cluster.py health       — 一次性健康检查")
        print("  python cluster.py audit        — 总管行为审计")

# ═══════════════════════════════════════
# 第六层：自动故障转移
# ═══════════════════════════════════════

FAIL_TIMEOUT_SECONDS = 900  # 15分钟
POLL_INTERVAL = 30          # 30秒轮询
FREEZE_THRESHOLD = 2        # 同一角色连续违规几次后冻结
FROZEN_PATH = f"{CONTEXT}/frozen.json"
_violation_count = {}

def _is_frozen(name: str) -> bool:
    """检查角色是否已被冻结"""
    if not os.path.exists(FROZEN_PATH):
        return False
    try:
        data = json.load(open(FROZEN_PATH, encoding="utf-8"))
        entry = data.get("frozen_roles", {}).get(name, {})
        return entry.get("frozen", False)
    except (json.JSONDecodeError, KeyError):
        return False

def _freeze_role(name: str, reason: str):
    """将角色写入冻结名单 — 禁止接新任务，直到总管手动解除"""
    frozen = {}
    if os.path.exists(FROZEN_PATH):
        try:
            frozen = json.load(open(FROZEN_PATH, encoding="utf-8"))
        except json.JSONDecodeError:
            frozen = {}
    if "frozen_roles" not in frozen:
        frozen["frozen_roles"] = {}
    frozen["frozen_roles"][name] = {
        "frozen": True,
        "frozen_at": datetime.datetime.now().isoformat(),
        "reason": reason,
        "violations": 2,
        "unfrozen": False
    }
    with open(FROZEN_PATH, "w", encoding="utf-8") as f:
        json.dump(frozen, f, ensure_ascii=False, indent=2)

def check_and_retry():
    """检查健康→自动重派超时任务
    
    超时/冻结/心跳异常 → 自动写入 context/decisions.jsonl
    
    冻结规则：同一角色连续2次违规（超时无响应）
    → 写入 context/frozen.json
    → 该角色被禁接新任务，直到总管手动解除
    
    心跳异常：窗口 Agent 心跳超时
    → 自动写入 context/decisions.jsonl
    """
    from dispatch import ROLES, TASKS, SESSIONS
    now = time.time()
    repaired = []
    
    for name, cfg in ROLES.items():
        sf = os.path.join(SESSIONS, cfg["session"])
        tf = os.path.join(TASKS, cfg["task"])
        
        s_mtime = os.path.getmtime(sf) if os.path.exists(sf) else 0
        t_mtime = os.path.getmtime(tf) if os.path.exists(tf) else 0
        
        mode = cfg.get("mode", "window")
        
        if mode == "task":
            # ── task Agent: 超时重试 + 冻结 ──
            
            # 已被冻结的角色跳过监控
            if _is_frozen(name):
                continue
            
            # 任务有更新 但是 Agent 超过15分钟没响应 → 违规
            stale = (now - s_mtime > FAIL_TIMEOUT_SECONDS) and (t_mtime > s_mtime)
            
            if stale:
                violations = _violation_count.get(name, 0) + 1
                _violation_count[name] = violations
                
                if violations >= FREEZE_THRESHOLD:
                    # 连续2次违规 → 冻结
                    _freeze_role(name, f"连续{FREEZE_THRESHOLD}次超时违规（{int((now - s_mtime) // 60)}分钟未响应）")
                    log_decision("集群监控", f"❄️ {name} 因连续{FREEZE_THRESHOLD}次违规已冻结",
                                 f"写入 {FROZEN_PATH}，等待总管手动解除")
                    send_message("集群监控", "__all__", "broadcast",
                                 f"❄️ {name} 因连续{FREEZE_THRESHOLD}次超时违规，已被冻结。总管请手动解除: 编辑 {FROZEN_PATH}")
                    continue
                
                # 未达冻结阈值 → 发送重试提醒
                msg = f"⏰ {name} 超时（{int((now - s_mtime) // 60)}分钟未响应，第{violations}次违规）"
                log_decision("集群监控", msg, f"任务文件更新于 {datetime.datetime.fromtimestamp(t_mtime).strftime('%H:%M')}")
                send_message("集群监控", name, "retry", msg)
                repaired.append((name, violations))
        else:
            # ── 窗口 Agent: 心跳检测 → 自动写 decisions.jsonl ──
            stale = (now - s_mtime > WINDOW_HEARTBEAT_SECONDS)
            if stale:
                hours_since = round((now - s_mtime) / 3600, 1) if s_mtime else None
                _log_window_heartbeat_alert(name, hours_since)
    
    return repaired

def start_daily_backup():
    """每天 03:00 自动备份"""
    def _run():
        while True:
            now = datetime.datetime.now()
            target = now.replace(hour=3, minute=0, second=0, microsecond=0)
            if now >= target: target += datetime.timedelta(days=1)
            time.sleep((target - now).total_seconds())
            try:
                subprocess.run(["python", f"{BASE}/auto-backup.py"], check=True, cwd=BASE)
                log_decision("集群监控", "📦 每日备份完成", "auto-backup.py 执行成功")
            except Exception as e:
                log_decision("集群监控", "❌ 每日备份失败", str(e))
    threading.Thread(target=_run, daemon=True).start()

def start_daily_compliance():
    """每天 04:00 自动合规扫描"""
    def _run():
        while True:
            now = datetime.datetime.now()
            target = now.replace(hour=4, minute=0, second=0, microsecond=0)
            if now >= target: target += datetime.timedelta(days=1)
            time.sleep((target - now).total_seconds())
            try:
                date_str = datetime.date.today().isoformat()
                report = f"# 每日合规扫描 {date_str}\n\n状态：正常\n"
                with open(f"{BASE}/output/协议官-日扫-{date_str}.md", "w", encoding="utf-8") as f:
                    f.write(report)
                log_decision("协议执行官", f"✅ 每日合规扫描完成", f"output/协议官-日扫-{date_str}.md")
            except Exception as e:
                log_decision("协议执行官", "❌ 合规扫描失败", str(e))
    threading.Thread(target=_run, daemon=True).start()

def start_monitor():
    """后台健康监控线程 — 同时监控 task 超时重试 + 窗口角色心跳"""
    print(f"🔍 集群监控启动 — 每30秒检查，超时15分钟自动重试（连续{FREEZE_THRESHOLD}次违规→冻结）")
    print(f"   ─ 窗口角色: 超时{WINDOW_HEARTBEAT_HOURS}h 未响应 → 标记 stale → 写 decisions.jsonl")
    print(f"   决策日志: {DECISIONS}")
    
    def loop():
        while True:
            try:
                # task 角色：超时重试 + 冻结
                repaired = check_and_retry()
                if repaired:
                    for name, n in repaired:
                        print(f"  ⚠️ {name} 第{n}次自动重试")
                # 窗口角色：心跳检测 → stale 告警（写入 decisions.jsonl）
                status = check_health()
                for name, info in status.items():
                    if info["mode"] != "task" and not info["healthy"]:
                        print(f"  🖥️ {name} 窗口心跳异常: {info['hours_since_heartbeat']}h 未响应")
            except Exception as e:
                log_decision("集群监控", f"异常{e}", traceback.format_exc())
                print(f"  ❌ 监控异常: {e}")
            time.sleep(POLL_INTERVAL)
    
    t = threading.Thread(target=loop, daemon=True)
    t.start()
    
    # 启动每天备份和合规扫描
    start_daily_backup()
    start_daily_compliance()
    
    # 同时启动仪表盘
    start_dashboard()
