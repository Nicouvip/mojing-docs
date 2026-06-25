"""墨境团队监控面板 — 实时查看任务状态和成果"""
import http.server
import json
import os
import time
import webbrowser
from pathlib import Path
from datetime import datetime

PORT = 8899
TASKS_DIR = Path("D:/建网站/mojing-docs/tasks")
OUTPUT_DIR = Path("D:/建网站/mojing-docs/output")
SESSIONS_DIR = Path("C:/Users/nicou/AppData/Roaming/reasonix/projects/D--建网站/sessions")

ROLES = {
    "后端技术负责人": {"icon": "⚙️", "color": "#3b82f6", "session": "20260621-191522.542692500"},
    "前端技术负责人": {"icon": "🎨", "color": "#8b5cf6", "session": "20260621-182254.498497400"},
    "架构审查员":     {"icon": "🔍", "color": "#f59e0b", "session": "20260621-175807.046140700"},
    "提示词系统专家": {"icon": "🧠", "color": "#ec4899", "session": "20260621-193727.562644600"},
    "产品经理":       {"icon": "📊", "color": "#10b981", "session": "20260621-194638.192807500"},
    "UIUX设计师":     {"icon": "🎯", "color": "#f97316", "session": "20260621-194748.846743400"},
    "QA测试工程师":   {"icon": "🧪", "color": "#06b6d4", "session": "20260621-195417.277398500"},
}


def get_role_status(name):
    """获取角色当前状态"""
    info = ROLES[name]
    status = {"name": name, "icon": info["icon"], "color": info["color"], "task": None, "output": None, "session_active": False, "last_activity": None}

    # 检查任务文件
    task_file = TASKS_DIR / f"{name}.md"
    if task_file.exists():
        content = task_file.read_text(encoding="utf-8").strip()
        if content and content != "暂无任务":
            status["task"] = content

    # 检查输出文件（找最新的）
    outputs = sorted(OUTPUT_DIR.glob(f"{name.replace('UIUX设计师','设计')}*"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not outputs:
        # 尝试其他命名
        for pattern in [name[:2] + "*", name[:4] + "*"]:
            outputs = sorted(OUTPUT_DIR.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
            if outputs:
                break
    if outputs:
        latest = outputs[0]
        status["output"] = {
            "file": latest.name,
            "content": latest.read_text(encoding="utf-8")[:2000],
            "time": datetime.fromtimestamp(latest.stat().st_mtime).strftime("%m-%d %H:%M"),
            "full_path": str(latest),
        }

    # 检查会话活跃度
    session_prefix = info["session"]
    for f in SESSIONS_DIR.glob(f"{session_prefix}*.jsonl"):
        if f.stat().st_size > 100:
            status["session_active"] = True
            status["last_activity"] = datetime.fromtimestamp(f.stat().st_mtime).strftime("%m-%d %H:%M")

    return status


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode("utf-8"))
        elif self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            statuses = []
            for name in ROLES:
                statuses.append(get_role_status(name))
            self.wfile.write(json.dumps(statuses, ensure_ascii=False).encode("utf-8"))
        elif self.path.startswith("/api/output/"):
            filename = self.path[12:]
            filepath = OUTPUT_DIR / filename
            if filepath.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(filepath.read_text(encoding="utf-8").encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>墨境 · 团队监控面板</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}
.header{padding:20px 28px;border-bottom:1px solid rgba(255,255,255,.08);display:flex;align-items:center;justify-content:space-between}
.header h1{font-size:20px;font-weight:600}
.header .time{color:#64748b;font-size:12px}
.main{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:20px 28px;max-width:1400px}
@media(max-width:900px){.main{grid-template-columns:1fr}}
.card{background:#1e293b;border-radius:12px;border:1px solid rgba(255,255,255,.06);overflow:hidden;transition:all .2s}
.card:hover{border-color:rgba(255,255,255,.12)}
.card-head{padding:16px 20px;display:flex;align-items:center;gap:12px;border-bottom:1px solid rgba(255,255,255,.06)}
.card-icon{font-size:24px}
.card-name{font-size:15px;font-weight:600;flex:1}
.card-badge{font-size:11px;padding:3px 10px;border-radius:20px;font-weight:500}
.badge-idle{background:#1e3a5f;color:#60a5fa}
.badge-busy{background:#3b1f0b;color:#fbbf24}
.badge-done{background:#0f3a2a;color:#34d399}
.card-body{padding:16px 20px;font-size:13px;line-height:1.7;color:#94a3b8}
.card-body .label{color:#64748b;font-size:11px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}
.card-body .task-text{color:#e2e8f0;margin-bottom:12px;max-height:60px;overflow:hidden}
.card-body .output-link{color:#60a5fa;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:4px}
.card-body .output-link:hover{text-decoration:underline}
.card-body .meta{color:#475569;font-size:11px;margin-top:8px}
.empty{color:#334155;font-style:italic}
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.6);backdrop-filter:blur(4px);display:none;z-index:100;align-items:center;justify-content:center}
.modal-overlay.show{display:flex}
.modal{background:#1e293b;border-radius:16px;padding:28px;max-width:700px;width:90%;max-height:80vh;overflow-y:auto;border:1px solid rgba(255,255,255,.1)}
.modal h2{font-size:17px;margin-bottom:12px;color:#f1f5f9}
.modal pre{background:#0f172a;padding:16px;border-radius:8px;font-size:12px;line-height:1.7;white-space:pre-wrap;color:#cbd5e1;max-height:50vh;overflow-y:auto;font-family:Consolas,Menlo,monospace}
.modal-btns{display:flex;gap:8px;margin-top:14px}
.modal-btn{padding:8px 16px;border:none;border-radius:8px;font-size:13px;cursor:pointer;font-weight:500}
.modal-btn.primary{background:#3b82f6;color:#fff}
.modal-btn.secondary{background:#334155;color:#e2e8f0}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#1e293b;color:#e2e8f0;padding:10px 20px;border-radius:8px;font-size:13px;opacity:0;transition:opacity .3s;pointer-events:none;z-index:200;border:1px solid rgba(255,255,255,.1)}
.toast.show{opacity:1}
.refresh-bar{display:flex;align-items:center;gap:12px;padding:0 28px 0}
.refresh-bar .dot{width:6px;height:6px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.refresh-bar span{color:#64748b;font-size:12px}
.summary{display:flex;gap:24px;padding:16px 28px}
.summary-item{font-size:13px;color:#94a3b8}
.summary-item strong{color:#e2e8f0}
</style>
</head>
<body>
<div class="header">
  <h1>📋 墨境 · 团队监控面板</h1>
  <span class="time" id="clock"></span>
</div>
<div class="refresh-bar">
  <div class="dot"></div>
  <span>每 5 秒自动刷新</span>
</div>
<div class="summary" id="summary"></div>
<div class="main" id="grid"></div>

<div class="modal-overlay" id="overlay" onclick="closeModal()">
  <div class="modal" onclick="event.stopPropagation()">
    <h2 id="mTitle"></h2>
    <pre id="mContent"></pre>
    <div class="modal-btns">
      <button class="modal-btn primary" onclick="copyContent()">📋 复制内容</button>
      <button class="modal-btn secondary" onclick="closeModal()">关闭</button>
    </div>
  </div>
</div>
<div class="toast" id="toast"></div>
<script>
let data=[];
function toast(m){const t=document.getElementById('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2000)}
function closeModal(){document.getElementById('overlay').classList.remove('show')}
function copyContent(){navigator.clipboard.writeText(document.getElementById('mContent').textContent).then(()=>toast('✅ 已复制'))}

async function refresh(){
  try{
    const r=await fetch('/api/status');data=await r.json();
    render();
  }catch(e){console.error(e)}
}

function render(){
  const grid=document.getElementById('grid');grid.innerHTML='';
  let idle=0,busy=0,done=0;
  data.forEach(r=>{
    if(r.output)done++;else if(r.task)busy++;else idle++;
    const status=r.output?'done':r.task?'busy':'idle';
    const badgeText=r.output?'✅ 已完成':r.task?'⏳ 执行中':'💤 空闲';
    const badgeClass=r.output?'badge-done':r.task?'badge-busy':'badge-idle';
    let bodyHTML='';
    if(r.task){
      bodyHTML+=`<div class="label">当前任务</div><div class="task-text">${r.task.substring(0,150)}${r.task.length>150?'...':''}</div>`;
    }
    if(r.output){
      bodyHTML+=`<div class="label">最新成果</div>`;
      bodyHTML+=`<a class="output-link" onclick="viewOutput('${r.output.file}','${r.icon} ${r.name}')">📄 ${r.output.file} <span style="color:#475569">${r.output.time}</span></a>`;
    }
    if(!r.task&&!r.output){
      bodyHTML+=`<div class="empty">暂无任务</div>`;
    }
    if(r.last_activity){
      bodyHTML+=`<div class="meta">最后活跃: ${r.last_activity}</div>`;
    }
    const card=document.createElement('div');card.className='card';
    card.innerHTML=`<div class="card-head"><span class="card-icon">${r.icon}</span><span class="card-name">${r.name}</span><span class="card-badge ${badgeClass}">${badgeText}</span></div><div class="card-body">${bodyHTML}</div>`;
    grid.appendChild(card);
  });
  document.getElementById('summary').innerHTML=`<div class="summary-item">💤 空闲: <strong>${idle}</strong></div><div class="summary-item">⏳ 执行中: <strong>${busy}</strong></div><div class="summary-item">✅ 已完成: <strong>${done}</strong></div>`;
}

async function viewOutput(file,title){
  const r=await fetch('/api/output/'+encodeURIComponent(file));
  const content=await r.text();
  document.getElementById('mTitle').textContent='📄 '+title+' — '+file;
  document.getElementById('mContent').textContent=content;
  document.getElementById('overlay').classList.add('show');
}

function updateClock(){document.getElementById('clock').textContent=new Date().toLocaleString('zh-CN')}
updateClock();setInterval(updateClock,1000);
refresh();setInterval(refresh,5000);
</script>
</body>
</html>'''

if __name__ == "__main__":
    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"📋 墨境团队监控面板已启动: http://localhost:{PORT}")
    webbrowser.open(f"http://localhost:{PORT}")
    server.serve_forever()
