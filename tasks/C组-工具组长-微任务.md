【强制技能 — frontend-design】
────────────────────────

**微任务：tools/server.py 启动日志结构化 + 健康检查端点**

1. 在 `tools/server.py` 中将现有 `print()` 日志全部替换为 Python `logging` 模块：
   - 日志格式：`[2025-06-19 10:30:00] [INFO] [模块名] 消息内容`
   - 级别区分：连接/启动用 INFO，错误用 ERROR，调试用 DEBUG（默认级别 INFO）
   - 日志输出到 stdout + 可选文件 `logs/server.log`（自动轮转，最大 10MB，保留 3 份）
2. 新增 `GET /health` 端点，返回 JSON：
   ```json
   { "status": "ok", "uptime": 12345, "conns": 5, "version": "1.0.0" }
   ```
3. 将当前 WebSocket 连接计数暴露在健康检查中（`active_connections` 全局变量）
4. 输出到 `output/C组-Server日志与健康检查.md`

验收标准：启动 server.py 后看到结构化日志输出；`curl http://localhost:PORT/health` 返回正确 JSON；每次 WebSocket 连接/断开 `active_connections` 实时更新。
