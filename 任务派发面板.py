"""墨境任务派发面板 — 双击运行即可打开"""
import http.server
import json
import os
import webbrowser
from pathlib import Path

PORT = 8899
TASKS_DIR = Path("D:/建网站/mojing-docs/tasks")

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode("utf-8"))
        elif self.path.startswith("/tasks/"):
            filename = self.path[7:]
            filepath = TASKS_DIR / filename
            if filepath.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(filepath.read_text(encoding="utf-8").encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"")
        elif self.path == "/api/roles":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            roles = []
            for f in sorted(TASKS_DIR.glob("*.md")):
                content = f.read_text(encoding="utf-8").strip()
                roles.append({"file": f.name, "content": content, "has_task": content != "暂无任务"})
            self.wfile.write(json.dumps(roles, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>墨境 · 任务派发面板</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;background:#f0f2f5;color:#1f2329;min-height:100vh;padding:24px}
h1{font-size:22px;font-weight:600;margin-bottom:4px}
.subtitle{color:#8e929b;font-size:13px;margin-bottom:24px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;margin-bottom:32px}
.card{background:#fff;border-radius:12px;padding:20px;border:1px solid rgba(0,0,0,.06);transition:all .2s;cursor:pointer;position:relative}
.card:hover{box-shadow:0 4px 16px rgba(0,0,0,.08);transform:translateY(-2px)}
.card-icon{font-size:28px;margin-bottom:8px}
.card-name{font-size:15px;font-weight:600;margin-bottom:4px}
.card-status{font-size:12px;padding:2px 8px;border-radius:10px;display:inline-block;margin-bottom:8px}
.status-waiting{background:#e8f2ff;color:#0071e3}
.status-done{background:#e8f8f2;color:#27c997}
.card-task{font-size:13px;color:#646a73;line-height:1.6;max-height:60px;overflow:hidden}
.card-btn{display:block;width:100%;margin-top:12px;padding:8px;border:none;border-radius:8px;font-size:13px;font-weight:500;cursor:pointer;transition:all .15s}
.btn-send{background:#0071e3;color:#fff}
.btn-send:hover{background:#0066cc}
.btn-copy{background:#f0f2f5;color:#1f2329}
.btn-copy:hover{background:#e5e7eb}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#1f2329;color:#fff;padding:10px 20px;border-radius:8px;font-size:13px;opacity:0;transition:opacity .3s;pointer-events:none;z-index:999}
.toast.show{opacity:1}
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.4);backdrop-filter:blur(4px);display:none;z-index:100;align-items:center;justify-content:center}
.modal-overlay.show{display:flex}
.modal{background:#fff;border-radius:16px;padding:28px;max-width:640px;width:90%;max-height:80vh;overflow-y:auto}
.modal h2{font-size:18px;margin-bottom:12px}
.modal pre{background:#f7f8fa;padding:16px;border-radius:8px;font-size:13px;line-height:1.7;white-space:pre-wrap;word-break:break-all;font-family:Consolas,Menlo,monospace}
.modal-btns{display:flex;gap:8px;margin-top:16px}
.header-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:24px}
.badge{background:#ff3b30;color:#fff;font-size:11px;padding:2px 8px;border-radius:10px}
.help{background:#fff;border-radius:12px;padding:20px;border:1px solid rgba(0,0,0,.06)}
.help h3{font-size:15px;margin-bottom:8px}
.help ol{padding-left:20px;font-size:13px;color:#646a73;line-height:2}
.help code{background:#f0f2f5;padding:2px 6px;border-radius:4px;font-size:12px}
</style>
</head>
<body>
<h1>📋 墨境 · 任务派发面板</h1>
<p class="subtitle">点击角色卡片查看任务，一键复制指令</p>
<div class="header-row">
  <div style="display:flex;gap:8px;align-items:center">
    <button class="card-btn btn-send" style="width:auto;padding:8px 16px" onclick="refresh()">🔄 刷新</button>
  </div>
  <span id="taskCount" class="badge">0 个待办</span>
</div>
<div class="grid" id="grid"></div>
<div class="help">
  <h3>💡 使用流程</h3>
  <ol>
    <li>我（总管）写好任务文件 → 自动出现在面板上</li>
    <li>点击角色卡片 → 查看任务详情</li>
    <li>点击<strong>"复制全部"</strong> → 粘贴给对应角色</li>
    <li>或者只点击<strong>"复制查收任务"</strong> → 角色自动读取任务文件</li>
    <li>简短指令 <code>查收任务</code> 也可以（角色设定里已配置自动读取）</li>
  </ol>
</div>
<div class="modal-overlay" id="overlay" onclick="closeModal()">
  <div class="modal" onclick="event.stopPropagation()">
    <h2 id="mTitle"></h2>
    <pre id="mContent"></pre>
    <div class="modal-btns">
      <button class="card-btn btn-send" style="flex:1" onclick="copyFull()">📋 复制全部</button>
      <button class="card-btn btn-copy" style="flex:1" onclick="copyShort()">💬 复制"查收任务"</button>
    </div>
  </div>
</div>
<div class="toast" id="toast"></div>
<script>
const ICONS={'后端技术负责人.md':'⚙️','前端技术负责人.md':'🎨','架构审查员.md':'🔍','提示词系统专家.md':'🧠','产品经理.md':'📊','UIUX设计师.md':'🎯','QA测试工程师.md':'🧪'};
let roles=[],currentFile='';
function toast(m){const t=document.getElementById('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2000)}
function closeModal(){document.getElementById('overlay').classList.remove('show')}
async function refresh(){
  const r=await fetch('/api/roles');roles=await r.json();
  const g=document.getElementById('grid');g.innerHTML='';let pending=0;
  roles.forEach(r=>{
    if(r.has_task)pending++;
    const d=document.createElement('div');d.className='card';
    const preview=r.has_task?r.content.substring(0,100)+(r.content.length>100?'...':''):'暂无任务';
    d.innerHTML=`<div class="card-icon">${ICONS[r.file]||'📌'}</div><div class="card-name">${r.file.replace('.md','')}</div><span class="card-status ${r.has_task?'status-waiting':'status-done'}">${r.has_task?'⏳ 待执行':'✅ 无任务'}</span><div class="card-task">${preview}</div><button class="card-btn ${r.has_task?'btn-send':'btn-copy'}" onclick="event.stopPropagation();view('${r.file}')">${r.has_task?'📋 查看任务':'查看'}</button>`;
    g.appendChild(d);
  });
  document.getElementById('taskCount').textContent=pending+' 个待办';
}
async function view(f){currentFile=f;const r=roles.find(x=>x.file===f);document.getElementById('mTitle').textContent=(ICONS[f]||'')+' '+f.replace('.md','');document.getElementById('mContent').textContent=r?r.content:'暂无任务';document.getElementById('overlay').classList.add('show')}
function copyFull(){const r=roles.find(x=>x.file===currentFile);if(r)navigator.clipboard.writeText(r.content).then(()=>toast('✅ 任务已复制'))}
function copyShort(){navigator.clipboard.writeText('查收任务').then(()=>toast('✅ 已复制"查收任务"'))}
refresh();setInterval(refresh,5000);
</script>
</body>
</html>'''

if __name__ == "__main__":
    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"📋 任务派发面板已启动: http://localhost:{PORT}")
    webbrowser.open(f"http://localhost:{PORT}")
    server.serve_forever()
