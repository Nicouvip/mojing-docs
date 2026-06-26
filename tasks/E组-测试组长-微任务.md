【强制技能 — webapp-testing + systematic-debugging】
────────────────────────

**微任务：搭建自动化测试骨架 + 首个冒烟测试用例**

1. 在项目根目录创建 `tests/` 目录结构：
   ```
   tests/
   ├── conftest.py          # pytest 全局 fixture
   ├── unit/                # 单元测试
   ├── integration/         # 集成测试
   ├── e2e/                 # 端到端测试
   └── reports/             # 测试报告输出目录
   ```
2. 创建 `tests/conftest.py`，包含：
   - 一个 `pytest` 会话级 fixture，启动测试用临时 SQLite 内存数据库
   - 一个 `client` fixture，返回 HTTPX 的 `AsyncClient` 指向 `http://localhost:PORT`
3. 创建 `tests/unit/test_health.py` 冒烟测试：
   - 断言 `GET /health` 返回 200，且 JSON 中包含 `"status": "ok"`
4. 在 `pyproject.toml` 中添加 pytest 配置：
   ```toml
   [tool.pytest.ini_options]
   testpaths = ["tests"]
   asyncio_mode = "auto"
   ```
5. 运行 `pytest tests/unit/test_health.py -v` 确认通过
6. 输出到 `output/E组-测试骨架搭建报告.md`

验收标准：`pytest tests/` 能发现并运行测试；`test_health` 绿通过；测试报告目录可写。
