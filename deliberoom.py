"""
墨境集团 · 圆桌会议室
====================
多轮辩论：Agent 可以读到别人的上轮发言，逐轮深化讨论。
"""
import json, datetime, os, time

BASE = "D:/建网站/mojing-docs"
DELIB_DIR = f"{BASE}/context/deliberations"
os.makedirs(DELIB_DIR, exist_ok=True)

def start_session(topic: str, participants: list) -> str:
    """开启一场会议室"""
    sid = datetime.datetime.now().strftime("%m%d-%H%M")
    session = {
        "id": sid,
        "topic": topic,
        "participants": participants,
        "rounds": [],
        "status": "open",
        "created": datetime.datetime.now().isoformat(),
    }
    fp = f"{DELIB_DIR}/{sid}.json"
    json.dump(session, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"🏛️ 会议室 #{sid} 已开启")
    print(f"   议题: {topic}")
    print(f"   参会: {', '.join(participants)}")
    print(f"   文件: {fp}")
    return sid

def add_statement(session_id: str, speaker: str, angle: str, content: str, responds_to: str = ""):
    """某位 Agent 发言"""
    fp = f"{DELIB_DIR}/{session_id}.json"
    s = json.load(open(fp, encoding="utf-8"))
    if not s.get("rounds"):
        s["rounds"] = [{"number": 1, "statements": []}]
    current_round = s["rounds"][-1]
    stmt = {
        "speaker": speaker,
        "angle": angle,
        "content": content,
        "responds_to": responds_to,
        "timestamp": datetime.datetime.now().isoformat(),
    }
    current_round["statements"].append(stmt)
    json.dump(s, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"  💬 [{speaker}] ({angle}): {content[:60]}...")
    return stmt

def next_round(session_id: str):
    """进入下一轮辩论"""
    fp = f"{DELIB_DIR}/{session_id}.json"
    s = json.load(open(fp, encoding="utf-8"))
    rn = len(s["rounds"]) + 1
    s["rounds"].append({"number": rn, "statements": []})
    json.dump(s, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"  🔄 进入第 {rn} 轮辩论")

def close_session(session_id: str, conclusion: str):
    """会议结束，记结论"""
    fp = f"{DELIB_DIR}/{session_id}.json"
    s = json.load(open(fp, encoding="utf-8"))
    s["status"] = "closed"
    s["conclusion"] = conclusion
    s["closed"] = datetime.datetime.now().isoformat()
    json.dump(s, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"🏁 会议室 #{session_id} 结束")
    print(f"   结论: {conclusion[:80]}")

def get_session(session_id: str) -> dict:
    fp = f"{DELIB_DIR}/{session_id}.json"
    return json.load(open(fp, encoding="utf-8")) if os.path.exists(fp) else None

def list_sessions() -> list:
    files = sorted(os.listdir(DELIB_DIR), reverse=True)
    return [f.replace(".json", "") for f in files if f.endswith(".json")]

def get_latest_round_context(session_id: str, max_chars: int = 1000) -> str:
    """获取上一轮内容供 Agent 阅读后参与下一轮"""
    s = get_session(session_id)
    if not s or not s.get("rounds"):
        return ""
    last_round = s["rounds"][-1]
    ctx = ""
    for stmt in last_round.get("statements", []):
        ctx += f"[{stmt['speaker']} - {stmt['angle']}]\n{stmt['content']}\n\n"
    if len(ctx) > max_chars:
        ctx = ctx[-max_chars:]
    return ctx.strip()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法:")
        print("  python deliberoom.py start <议题> <角色1> <角色2> ...")
        print("  python deliberoom.py speak <会议ID> <发言者> <角度> <内容>")
        print("  python deliberoom.py next <会议ID>")
        print("  python deliberoom.py close <会议ID> <结论>")
        print("  python deliberoom.py list")
        print("  python deliberoom.py view <会议ID>")
    elif sys.argv[1] == "start":
        start_session(sys.argv[2], sys.argv[3:])
    elif sys.argv[1] == "speak":
        add_statement(sys.argv[2], sys.argv[3], sys.argv[4], " ".join(sys.argv[5:]))
    elif sys.argv[1] == "next":
        next_round(sys.argv[2])
    elif sys.argv[1] == "close":
        close_session(sys.argv[2], " ".join(sys.argv[3:]))
    elif sys.argv[1] == "list":
        for s in list_sessions():
            sess = get_session(s)
            print(f"  #{s} | {sess['topic'][:50]} | {sess['status']} | {len(sess.get('rounds',[]))}轮")
    elif sys.argv[1] == "view":
        s = get_session(sys.argv[2])
        if s:
            print(f"\n{'='*60}")
            print(f"🏛️ 会议室 #{s['id']}")
            print(f"议题: {s['topic']}")
            print(f"参会: {', '.join(s['participants'])}")
            print(f"状态: {s['status']}")
            for r in s.get("rounds", []):
                print(f"\n--- 第 {r['number']} 轮 ---")
                for stmt in r.get("statements", []):
                    print(f"  💬 [{stmt['speaker']}] ({stmt['angle']})")
                    print(f"     {stmt['content'][:100]}")
            if s.get("conclusion"):
                print(f"\n📋 结论: {s['conclusion']}")
