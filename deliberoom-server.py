"""圆桌会议室服务器 — 独立端口 8901"""
import http.server, json, os
from pathlib import Path

DELIB_DIR = Path("D:/建网站/mojing-docs/context/deliberations")
VIEWER_HTML = Path("D:/建网站/mojing-docs/deliberoom-viewer.html")
GAME_HTML = Path("D:/建网站/mojing-docs/圆桌会议-游戏界面.html")

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/deliberoom.json":
            sessions = []
            dp = str(DELIB_DIR)
            if os.path.isdir(dp):
                for f in sorted(os.listdir(dp), reverse=True):
                    if f.endswith(".json"):
                        s = json.load(open(os.path.join(dp, f), encoding="utf-8"))
                        sessions.append({
                            "id": s["id"], "topic": s["topic"], "status": s["status"],
                            "participants": s.get("participants", []),
                            "rounds": s.get("rounds", []),
                            "conclusion": s.get("conclusion", ""),
                        })
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(sessions, ensure_ascii=False).encode())
        if self.path == "/game":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(open(GAME_HTML, "rb").read())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(open(VIEWER_HTML, "rb").read())
    
    def log_message(self, *a): pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("127.0.0.1", 8901), Handler)
    print("🏛️ 圆桌会议室: http://localhost:8901")
    s.serve_forever()
