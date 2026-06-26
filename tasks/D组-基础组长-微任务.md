【强制技能 — executing-plans】
────────────────────────

**微任务：Supabase 项目初始化 + Drizzle Schema 首表落地**

1. 在项目根目录创建 `supabase/` 配置骨架：
   - `supabase/config.toml`（项目名称 `mojing-novel`，端口 54321）
   - 初始化本地 Supabase 实例：`supabase init`
2. 安装 Drizzle ORM 依赖：
   ```
   npm install drizzle-orm postgres
   npm install -D drizzle-kit
   ```
3. 创建 `db/schema.ts`，定义首张表 `users`：
   ```ts
   import { pgTable, serial, text, timestamp } from "drizzle-orm/pg-core";

   export const users = pgTable("users", {
     id: serial("id").primaryKey(),
     email: text("email").notNull().unique(),
     nickname: text("nickname").notNull(),
     created_at: timestamp("created_at").defaultNow(),
   });
   ```
4. 创建 `db/index.ts`，导出 Drizzle 客户端实例（连接 `DATABASE_URL` 环境变量）
5. 创建 `drizzle.config.ts`，指向 `db/schema.ts`，输出到 `supabase/migrations/`
6. 运行 `npx drizzle-kit push:pg` 将 users 表推送到本地 Supabase
7. 输出到 `output/D组-Supabase初始化与首表落地.md`

验收标准：本地 Supabase 实例运行中；`npx drizzle-kit studio` 能看到 `users` 表结构；数据库连接字符串可被后端服务读取。
