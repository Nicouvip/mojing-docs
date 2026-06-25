"""
墨境项目全景 — 桌面悬浮窗
双击桌面图标启动，系统托盘显示 🌙 图标
左键点击 → 打开/关闭面板  右键 → 退出
"""
import pystray
from PIL import Image, ImageDraw
import webbrowser
import threading
import time
import socket
import os
import subprocess
import sys

# 确保面板在运行
def ensure_panel():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    if s.connect_ex(('127.0.0.1', 8899)) != 0:
        subprocess.Popen(
            [sys.executable, r"D:\建网站\mojing-docs\项目全景进度.py"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(2)
    s.close()

def toggle_panel(icon, item):
    webbrowser.open("http://localhost:8899")

def on_quit(icon, item):
    icon.stop()

# 创建 64x64 月亮图标
img = Image.new('RGBA', (64, 64), (0,0,0,0))
draw = ImageDraw.Draw(img)
draw.ellipse([12, 4, 52, 44], fill='#60a5fa')  # 蓝色月亮
draw.ellipse([8, 8, 48, 40], fill='#030712')   # 暗色背景挖掉月牙
draw.ellipse([28, 42, 56, 56], fill='#a78bfa')  # 紫色小点

ensure_panel()

icon = pystray.Icon(
    "mojing",
    img,
    "墨境 · 项目全景",
    menu=pystray.Menu(
        pystray.MenuItem("📊 打开面板", toggle_panel, default=True),
        pystray.MenuItem("🖥️ 打开网站", lambda: webbrowser.open("http://localhost:3000")),
        pystray.MenuItem("🦞 打开 OpenClaw", lambda: webbrowser.open("http://127.0.0.1:18789")),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("❌ 退出", on_quit),
    )
)
icon.run()
