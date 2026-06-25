"""
墨境 Agent 集群 — 总管调度中心
用法：python dispatch.py <命令>
命令：
  progress  查看全部进度
  push      将任务文件推送到各角色
  status    检查各角色对话最后活跃时间
"""
import os, json, datetime, sys

BASE = "D:/建网站/mojing-docs"
TASKS = f"{BASE}/tasks"
OUTPUT = f"{BASE}/output"
CONTEXT = f"{BASE}/context"
SESSIONS = "C:/Users/nicou/AppData/Roaming/reasonix/projects/D--建网站/sessions"

ROLES = {
    "前端技术负责人":   {"task": "前端技术负责人.md",   "session": "20260621-202458.041590800-mimo-v2.5-pro.jsonl",     "mode": "task"},
    "后端技术负责人":   {"task": "后端技术负责人.md",   "session": "20260621-191522.542692500-deepseek-v4-flash.jsonl", "mode": "task"},
    "提示词系统专家":   {"task": "提示词系统专家.md",   "session": "20260621-193727.562644600-deepseek-v4-flash.jsonl", "mode": "task"},
    "产品经理":         {"task": "产品经理.md",         "session": "20260621-194638.192807500-deepseek-v4-flash.jsonl", "mode": "task"},
    "UI设计师":         {"task": "UI设计师.md",         "session": "20260621-194748.846743400-deepseek-v4-flash.jsonl", "mode": "window"},
    "UX体验员":         {"task": "UX体验员.md",         "session": "20260622-005205.499761900-deepseek-v4-pro.jsonl",   "mode": "window"},
    "QA测试工程师":     {"task": "QA测试工程师.md",     "session": "20260621-195417.277398500-deepseek-v4-flash.jsonl", "mode": "window"},
    "架构审查员":       {"task": "架构审查员.md",       "session": "20260621-175807.046140700-deepseek-v4-flash.jsonl", "mode": "window"},
}

def show_progress():
    """查看所有角色进度"""
    print("\n===== 墨境 Agent 集群 · 实时进度 =====\n")
    task_count = window_count = 0
    for name, cfg in ROLES.items():
        tf = os.path.join(TASKS, cfg["task"])
        sf = os.path.join(SESSIONS, cfg["session"])
        cf = os.path.join(CONTEXT, f"{name}.md")
        tsize = os.path.getsize(tf) if os.path.exists(tf) else 0
        ttime = datetime.datetime.fromtimestamp(os.path.getmtime(tf)).strftime("%H:%M") if os.path.exists(tf) else "缺"
        csize = os.path.getsize(cf) if os.path.exists(cf) else 0
        
        last_msg = "(无)"
        if os.path.exists(sf):
            lines = open(sf, encoding='utf-8').readlines()
            for i in range(len(lines)-1, -1, -1):
                msg = json.loads(lines[i])
                if msg['role'] == 'assistant' and msg.get('content', '').strip():
                    last_msg = msg['content'][:100].replace('\n', ' ')
                    break
            stime = datetime.datetime.fromtimestamp(os.path.getmtime(sf)).strftime("%H:%M")
        else:
            stime = "无"
        
        mode_icon = "🔧 task" if cfg.get("mode") == "task" else "🖥️ 窗口"
        if cfg.get("mode") == "task": task_count += 1
        else: window_count += 1
        
        print(f"  [{mode_icon}] {name}")
        print(f"    任务: {ttime} ({tsize}B) | 记忆: {csize}B | 对话: {stime}")
        print(f"    最后: {last_msg}\n")
    print(f"┌─────────────────────────────┐")
    print(f"│ 🔧 task 小弟: {task_count}人  │ 🖥️ 窗口: {window_count}人  │")
    print(f"│ Token 节省: ~{task_count * 90}%               │")
    print(f"└─────────────────────────────┘")

def context_append(name: str, content: str):
    """追加 task 小弟的记忆"""
    os.makedirs(CONTEXT, exist_ok=True)
    cf = os.path.join(CONTEXT, f"{name}.md")
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(cf, "a", encoding="utf-8") as f:
        f.write(f"\n--- {stamp} ---\n{content}\n")

def context_read(name: str, max_chars: int = 2000) -> str:
    """读取 task 小弟的最近记忆（用于注入 prompt）"""
    cf = os.path.join(CONTEXT, f"{name}.md")
    if not os.path.exists(cf):
        return ""
    content = open(cf, encoding="utf-8").read()
    if len(content) > max_chars:
        content = content[-max_chars:]
        content = content[content.find("\n--- "):]  # 从最近的完整条目开始
    return content.strip()

def build_prompt(name: str, instruction: str) -> str:
    """为 task 小弟构建含上下文记忆的完整 prompt"""
    cfg = ROLES[name]
    task_content = open(os.path.join(TASKS, cfg["task"]), encoding="utf-8").read()
    ctx = context_read(name)
    
    prompt = f"""你是墨境项目的{name}。
    
## 当前任务文件
{task_content[:3000]}

## 你的历史记忆（最近工作）
{ctx if ctx else "(新人，暂无记忆)"}

## 当前指令
{instruction}

请完成工作。"""
    return prompt

def show_files():
    """列出所有任务和产出文件"""
    print("\n--- 任务文件 ---")
    for f in sorted(os.listdir(TASKS)):
        fp = os.path.join(TASKS, f)
        print(f"  {f}  ({os.path.getsize(fp)}B)")
    print("\n--- 最近产出 ---")
    for f in sorted(os.listdir(OUTPUT), key=lambda x: os.path.getmtime(os.path.join(OUTPUT, x)), reverse=True)[:5]:
        fp = os.path.join(OUTPUT, f)
        print(f"  {f}  ({os.path.getsize(fp)}B)")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "progress"
    if cmd == "progress":
        show_progress()
        show_files()
    elif cmd == "files":
        show_files()
    else:
        show_progress()
        show_files()
