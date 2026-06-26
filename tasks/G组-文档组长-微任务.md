【强制技能 — chinese-documentation】
────────────────────────

**微任务：文档站点骨架搭建 + 首个 API 文档页**

1. 在项目根目录创建 `docs/` 目录结构：
   ```
   docs/
   ├── index.md              # 文档首页
   ├── guide/                # 用户指南
   │   └── quickstart.md     # 快速开始
   ├── api/                  # API 文档
   │   └── health.md         # 健康检查 API
   ├── dev/                  # 开发者指南
   │   └── setup.md          # 本地开发环境搭建
   └── changelog.md          # 变更日志
   ```
2. 安装文档工具（推荐 VitePress）：
   ```
   npm install -D vitepress
   ```
3. 创建 `docs/.vitepress/config.ts`，配置站点标题、导航栏、侧边栏
4. 编写 `docs/index.md` 首页（项目简介 + 文档导航）
5. 编写 `docs/api/health.md`，记录 `GET /health` 端点：
   - 请求示例 · 响应格式 · 状态码说明 · 使用场景
6. 在 `package.json` 中添加脚本：
   ```json
   "docs:dev": "vitepress dev docs",
   "docs:build": "vitepress build docs"
   ```
7. 运行 `npm run docs:dev` 确认文档站点可访问
8. 输出到 `output/G组-文档站点骨架搭建报告.md`

验收标准：`npm run docs:dev` 启动后浏览器可访问本地文档站点；导航栏含"指南""API""开发者"三项；`/api/health` 页面内容完整。
