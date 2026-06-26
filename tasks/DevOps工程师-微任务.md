【强制技能 — systematic-debugging】
────────────────────────

**微任务：本地 → 预览环境一键部署脚本**

1. 在 `D:\建网站\mojing-app` 根目录创建 `deploy-preview.sh`（或 `.ps1`）
2. 脚本逻辑：git push → pnpm build → 自动上传 dist 到预览服务器 → 健康检查（curl /api/health）
3. 健康检查失败时自动回滚到上一个版本 + 飞书/钉钉告警
4. 输出到 `output/DevOps-预览部署流水线.md`

验收标准：跑 `bash deploy-preview.sh` 后 3 分钟内预览站可用，失败后自动回滚。
