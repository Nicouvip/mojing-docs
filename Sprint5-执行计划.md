# 墨境 Sprint 5 — 详细执行计划

> 2025-07-16 | using brainstorming → writing-plans → dispatching-parallel-agents

---

## 📊 当前状态

| 角色 | 任务 | 状态 |
|------|------|:---:|
| 前端 | GrapesJS 编辑器集成 | 🔄 进行中 |
| 后端 | PageRenderer 升级完成 | ⏸ 空闲 |
| UI设计师 | 文档检查（误读） | ⏸ 空闲 |
| QA | 页面编辑器验收完成 | ⏸ 空闲 |
| 架构 | /desk 审查完成 | ⏸ 空闲 |
| 提示词 | API审计（重复3次） | ⏸ 空闲 |
| 产品 | /desk定位评估完成 | ⏸ 空闲 |
| UX | GrapesJS报告完成 | ⏸ 空闲 |

---

## 🔴 Phase 1：立刻执行（零冲突，可并行）

### T1 — 前端：GrapesJS 编辑器收尾
- **做什么**：画布显示首页内容 + 开启全部组件 + 保存/加载
- **技能**：`frontend-design` + `ui-ux-pro-max`
- **验收**：打开编辑器看到完整首页 → 点元素可编辑 → 保存后刷新仍在
- **风险**：GrapesJS 格式兼容性 | **缓解**：用 HTML import 替代 JSON
- **时间**：1h

### T2 — 后端：安装 Supabase + NextAuth 基础设施
- **做什么**：`pnpm add @supabase/supabase-js next-auth@beta` + 创建 `src/lib/supabase.ts` + `src/auth.ts`
- **技能**：`executing-plans` + `test-driven-development`
- **验收**：`tsc --noEmit` 零错误，Supabase 客户端可连接
- **风险**：Supabase 需要注册账号 | **缓解**：先用本地 Docker Supabase
- **时间**：1h

### T3 — 提示词专家：清理虚假 API + 包装未调用函数
- **做什么**：删除 3 个不存在的 API 端点引用 + 为 19 个零调用函数写 API 包装
- **技能**：`writing-skills` + `systematic-debugging`
- **验收**：所有 API 端点 curl 返回 200
- **风险**：API 包装可能与现有 route.ts 冲突 | **缓解**：新建独立 api 路由
- **时间**：1h

### T4 — 产品经理：更新完整需求文档
- **做什么**：整理所有已确认的设计决策 + 页面清单 + 功能列表
- **技能**：`brainstorming` + `chinese-documentation`
- **验收**：一份完整产品需求文档
- **时间**：30min

---

## 🟡 Phase 2：串联执行（Phase 1完成后）

### T5 — 前端：接入 Supabase 替换 store.ts
- **前提**：T2 完成（Supabase 客户端就位）
- **技能**：`frontend-design` + `test-driven-development`
- **时间**：2h

### T6 — 前端+后端：NextAuth 替换 mock 登录
- **前提**：T2 完成
- **技能**：前端 `frontend-design` | 后端 `executing-plans`
- **时间**：1h

### T7 — UI设计师：GrapesJS 编辑器视觉审查
- **前提**：T1 完成
- **技能**：`ui-ux-pro-max` + `frontend-design` + `brand-guidelines`
- **时间**：30min

### T8 — QA：全流程回归测试
- **前提**：T1+T5+T6 完成
- **技能**：`webapp-testing` + `systematic-debugging`
- **时间**：1h

### T9 — UX体验员：全站交互走查
- **前提**：T1+T5+T6 完成
- **技能**：`gstack` + `webapp-testing`
- **时间**：1h

---

## 🟢 Phase 3：体验升级（Phase 2完成后）

### T10 — 前端：一行安装包
- `reading-time` + `Sonner` + `Sharp` + `use-debounce`
- **时间**：30min

### T11 — 后端：PromptLayer 接入
- 替换 feedback.ts / ab-test.ts / registry.ts
- **时间**：2h

### T12 — 架构审查员：代码质量终审
- **前提**：Phase 2 全部完成
- **技能**：`chinese-code-review` + `flow-review`
- **时间**：1h

---

## ⚠️ 遗留未完成项（嵌入 Phase 1-3）

| 遗留 | 嵌入哪步 | 谁 |
|------|------|------|
| BUG-04 字数统计 | T10 reading-time | 前端 |
| 新手引导验证 | T8 QA测试 | QA |
| /desk 全功能验收 | T9 UX走查 | UX |
| 提示词19个零调用函数 | T3 API包装 | 提示词 |

---

## 📋 分配

| Phase | 角色 | 任务 | 技能 |
|:---:|------|------|------|
| 1 | 前端 | T1 GrapesJS收尾 | frontend-design+ui-ux-pro-max |
| 1 | 后端 | T2 Supabase+NextAuth | executing-plans+TDD |
| 1 | 提示词 | T3 API清理+包装 | writing-skills+debugging |
| 1 | 产品 | T4 需求文档 | brainstorming+chinese-doc |
| 2 | 前端 | T5 Supabase接入 | frontend-design+TDD |
| 2 | 前端+后端 | T6 NextAuth接入 | frontend-design+executing-plans |
| 2 | UI设计师 | T7 视觉审查 | ui-ux-pro-max+frontend-design |
| 2 | QA | T8 回归测试 | webapp-testing+debugging |
| 2 | UX体验员 | T9 全站走查 | gstack+webapp-testing |
| 2 | 架构 | T12 终审 | chinese-code-review+flow-review |
| 3 | 前端 | T10 一行包 | frontend-design |
| 3 | 后端 | T11 PromptLayer | executing-plans |

---

## 💾 备份计划

- Phase 1 完成后备份
- Phase 2 每完成一个串联步骤备份
- 每日收工全量备份
