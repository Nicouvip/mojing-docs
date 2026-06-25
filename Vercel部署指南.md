# Vercel 部署指南

1. 打开 [vercel.com](https://vercel.com)，使用 GitHub 登录 → 点击 **Add New → Project** → 选择 `mojing-app` 仓库 → **Import** → 保持默认配置 → **Deploy**。

2. 部署前在 **Environment Variables** 中设置 `DEEPSEEK_API_KEY`（你的 DeepSeek API 密钥），否则应用无法正常调用 AI 接口。

3. 部署完成后 Vercel 会自动分配域名 `xxx.vercel.app`，每次推送 `main` 分支都会自动重新部署。
