"""
墨境任务自动派发器
用法: python 任务派发器.py [角色名]
不带参数: 派发所有待执行任务
带参数: 派发指定角色的任务
"""
import json
import sys
import os
import time
from pathlib import Path

SESSIONS_DIR = Path("C:/Users/nicou/AppData/Roaming/reasonix/projects/D--建网站/sessions")
TASKS_DIR = Path("D:/建网站/mojing-docs/tasks")

# 角色名 → 会话文件名映射
ROLE_SESSION_MAP = {
    "后端技术负责人": "20260621-191522.542692500-deepseek-v4-flash.jsonl",
    "架构审查员": "20260621-175807.046140700-deepseek-v4-flash.jsonl",
    "提示词系统专家": "20260621-193727.562644600-deepseek-v4-flash.jsonl",
    "产品经理": "20260621-194638.192807500-deepseek-v4-flash.jsonl",
    "前端技术负责人": None,  # 需要新开会话
    "UIUX设计师": "20260621-194748.846743400-deepseek-v4-flash.jsonl",
    "QA测试工程师": "20260621-195417.277398500-deepseek-v4-flash.jsonl",
}


def dispatch_task(role_name: str) -> bool:
    """把任务文件内容注入到对应角色的会话中"""
    task_file = TASKS_DIR / f"{role_name}.md"
    if not task_file.exists():
        print(f"  ❌ 任务文件不存在: {task_file}")
        return False

    content = task_file.read_text(encoding="utf-8").strip()
    if not content or content == "暂无任务":
        print(f"  ⏭️  {role_name}: 暂无任务")
        return False

    session_file = ROLE_SESSION_MAP.get(role_name)
    if not session_file:
        print(f"  ⚠️  {role_name}: 需要新开会话（前端技术负责人旧会话有报错）")
        print(f"     请新开一个对话框，贴入角色设定后手动输入: 查收任务")
        return False

    session_path = SESSIONS_DIR / session_file
    if not session_path.exists():
        print(f"  ❌ 会话文件不存在: {session_path}")
        return False

    # 读取现有会话
    with open(session_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 检查最后一条是否已经是相同的任务（避免重复派发）
    if lines:
        try:
            last_msg = json.loads(lines[-1])
            if last_msg.get("role") == "user" and content in last_msg.get("content", ""):
                print(f"  ⏭️  {role_name}: 任务已派发（未重复）")
                return False
        except:
            pass

    # 构造用户消息
    task_message = f"【自动派发任务】\n\n{content}"
    new_line = json.dumps({"role": "user", "content": task_message}, ensure_ascii=False) + "\n"

    # 追加到会话文件
    with open(session_path, "a", encoding="utf-8") as f:
        f.write(new_line)

    print(f"  ✅ {role_name}: 任务已注入会话 {session_file}")
    return True


def update_display_json():
    """更新 .display.json 以触发桌面端刷新"""
    display_path = SESSIONS_DIR / ".display.json"
    if display_path.exists():
        with open(display_path, "r", encoding="utf-8") as f:
            display = json.load(f)
        # 更新时间戳触发刷新
        display["_last_dispatch"] = time.time()
        with open(display_path, "w", encoding="utf-8") as f:
            json.dump(display, f, ensure_ascii=False)


def main():
    if len(sys.argv) > 1:
        # 派发指定角色
        role = sys.argv[1]
        print(f"🎯 派发任务给: {role}")
        dispatch_task(role)
    else:
        # 派发所有待执行任务
        print("📋 扫描所有待执行任务...\n")
        dispatched = 0
        for task_file in sorted(TASKS_DIR.glob("*.md")):
            role_name = task_file.stem
            if dispatch_task(role_name):
                dispatched += 1

        update_display_json()
        print(f"\n📊 共派发 {dispatched} 个任务")

        if dispatched > 0:
            print("\n💡 提示: 打开对应角色的对话框，任务消息应该已出现。")
            print("   如果消息没有自动触发 AI 回复，请按 Enter 键发送。")


if __name__ == "__main__":
    main()
