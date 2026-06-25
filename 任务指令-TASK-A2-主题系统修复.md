# 任务指令：主题系统 warm/cool/dark 全量实现

## 元信息
- **任务编号：** TASK-A2
- **优先级：** P0（Must — 当前 Sprint 唯一 P0）
- **负责角色：** 前端技术负责人
- **预估工作量：** 1 人天
- **发出人：** 产品经理
- **发出日期：** 2025-07-15

---

## 问题描述

当前 4 套主题切换效果严重残缺：

| 主题 | 当前状态 |
|:----:|---------|
| ☀️ Light（默认） | ✅ 完整 — `@theme inline` 定义了全部 18 个 `--color-*` 变量 |
| 🌙 Dark | ❌ 残缺 — 仅编辑器 ProseMirror 区域有 3 行颜色覆盖，页面其他区域无暗色变量 |
| 🌅 Warm | ❌ **完全缺失** — class `theme-warm` 被添加但 CSS 中无任何 `.theme-warm` 定义 |
| ❄️ Cool | ❌ **完全缺失** — class `theme-cool` 被添加但 CSS 中无任何 `.theme-cool` 定义 |

切换 warm/cool 后页面视觉零变化，影响用户信任感。

---

## 允许修改的文件

| 文件 | 说明 |
|------|------|
| `src/app/globals.css` | 追加 `.dark`、`.theme-warm`、`.theme-cool` 的 CSS 变量块 |

---

## 不允许修改的文件

| 文件 | 理由 |
|------|------|
| `src/app/editor/[id]/page.tsx` | 主题切换逻辑（class 添加）已在，不需要改 |
| `src/lib/` 下的任何文件 | 不涉及数据层 |
| `src/app/api/` 下的任何文件 | 后端范围 |
| `src/components/` 下的任何文件 | 不涉及组件逻辑 |

---

## 实现要求

### 1. 完善 `.dark` 主题（当前仅 3 行，需补齐）

**位置：** `globals.css` 中 `@theme inline` 块之后

需要覆盖全部 18 个 `--color-*` 变量，参考 shadcn/ui 标准暗黑色板：

```css
.dark {
  --color-background: hsl(222.2 84% 4.9%);
  --color-foreground: hsl(210 40% 98%);
  --color-card: hsl(222.2 84% 4.9%);
  --color-card-foreground: hsl(210 40% 98%);
  --color-popover: hsl(222.2 84% 4.9%);
  --color-popover-foreground: hsl(210 40% 98%);
  --color-primary: hsl(210 40% 98%);
  --color-primary-foreground: hsl(222.2 47.4% 11.2%);
  --color-secondary: hsl(217.2 32.6% 17.5%);
  --color-secondary-foreground: hsl(210 40% 98%);
  --color-muted: hsl(217.2 32.6% 17.5%);
  --color-muted-foreground: hsl(215 20.2% 65.1%);
  --color-accent: hsl(217.2 32.6% 17.5%);
  --color-accent-foreground: hsl(210 40% 98%);
  --color-destructive: hsl(0 62.8% 30.6%);
  --color-destructive-foreground: hsl(210 40% 98%);
  --color-border: hsl(217.2 32.6% 17.5%);
  --color-input: hsl(217.2 32.6% 17.5%);
  --color-ring: hsl(212.7 26.8% 83.9%);
}
```

同时覆盖 ProseMirror 编辑器区域文字颜色（替代当前仅 3 行的残缺覆盖）。

### 2. 新建 `.theme-warm` 主题

暖色调色板，以暖黄/米白/琥珀为基础，适合长时间阅读：

**色调方向：** 背景暖白（hsl 40左右）、文字暖棕（hsl 30左右）、强调色琥珀（hsl 25-35）

```css
.theme-warm {
  --color-background: hsl(40 30% 96%);
  --color-foreground: hsl(30 40% 20%);
  --color-card: hsl(40 25% 94%);
  --color-card-foreground: hsl(30 40% 20%);
  --color-popover: hsl(40 25% 94%);
  --color-popover-foreground: hsl(30 40% 20%);
  --color-primary: hsl(25 50% 40%);
  --color-primary-foreground: hsl(40 30% 96%);
  --color-secondary: hsl(35 25% 88%);
  --color-secondary-foreground: hsl(30 40% 20%);
  --color-muted: hsl(40 20% 90%);
  --color-muted-foreground: hsl(30 20% 45%);
  --color-accent: hsl(30 40% 50%);
  --color-accent-foreground: hsl(40 30% 96%);
  --color-destructive: hsl(0 50% 50%);
  --color-destructive-foreground: hsl(40 30% 96%);
  --color-border: hsl(35 20% 85%);
  --color-input: hsl(35 20% 85%);
  --color-ring: hsl(25 50% 40%);
}
```

**对比度要求：** 文字色（`--color-foreground`: hsl(30 40% 20%)）与背景色（hsl(40 30% 96%)）对比度约 11:1，符合 WCAG AAA 标准。

### 3. 新建 `.theme-cool` 主题

冷色调色板，以冷灰/蓝灰为基础，适合专注写作：

**色调方向：** 背景冷灰（hsl 210左右）、文字深蓝灰（hsl 215左右）、强调色蓝（hsl 210-220）

```css
.theme-cool {
  --color-background: hsl(210 20% 94%);
  --color-foreground: hsl(215 30% 20%);
  --color-card: hsl(210 15% 92%);
  --color-card-foreground: hsl(215 30% 20%);
  --color-popover: hsl(210 15% 92%);
  --color-popover-foreground: hsl(215 30% 20%);
  --color-primary: hsl(210 50% 45%);
  --color-primary-foreground: hsl(210 20% 98%);
  --color-secondary: hsl(210 15% 85%);
  --color-secondary-foreground: hsl(215 30% 20%);
  --color-muted: hsl(210 12% 88%);
  --color-muted-foreground: hsl(215 15% 50%);
  --color-accent: hsl(215 40% 55%);
  --color-accent-foreground: hsl(210 20% 98%);
  --color-destructive: hsl(0 50% 50%);
  --color-destructive-foreground: hsl(210 20% 98%);
  --color-border: hsl(210 15% 82%);
  --color-input: hsl(210 15% 82%);
  --color-ring: hsl(210 50% 45%);
}
```

### 4. 各主题下的 ProseMirror 编辑器适配

为每个主题添加编辑器区域的文字颜色覆盖：
```css
.dark .ProseMirror { color: var(--color-foreground); }
.theme-warm .ProseMirror { color: var(--color-foreground); }
.theme-cool .ProseMirror { color: var(--color-foreground); }
```

同时覆盖选中文本高亮色（`::selection`）、光标色（`caret-color`）、占位符色。

### 5. 自定义滚动条颜色适配

当前 `globals.css` 中有自定义滚动条样式（约第 100-120 行），需要为每个主题覆盖：
```css
.dark ::-webkit-scrollbar-thumb { background: hsl(215 20% 30%); }
.theme-warm ::-webkit-scrollbar-thumb { background: hsl(30 20% 70%); }
.theme-cool ::-webkit-scrollbar-thumb { background: hsl(210 15% 70%); }
```

---

## 验收标准

1. ✅ 点击主题切换按钮 ☀️→🌅→🌙→❄️，页面整体颜色正确变化
2. ✅ **dark 主题**：背景深色(约 #0a0c10)、文字浅色(约 #f8fafc)、侧栏/卡片/弹窗均深色背景
3. ✅ **warm 主题**：背景暖米色(约 #f7f3ed)、文字暖棕色(约 #4a3d33)，不刺眼
4. ✅ **cool 主题**：背景冷灰色(约 #eef1f5)、文字深蓝灰(约 #2d3748)，干净清爽
5. ✅ 编辑器（ProseMirror）区域在 4 套主题下文字均清晰可读
6. ✅ 自定义滚动条颜色适配各主题
7. ✅ 切换主题时无闪烁或白屏
8. ✅ `tsc --noEmit` 编译通过

---

## 验收命令

```bash
# 编译检查
cd D:/建网站/mojing-app && npx tsc --noEmit

# 启动开发服务器
pnpm dev

# 手动验证：访问 http://localhost:3000
# 1. 新建或打开一个作品进入编辑器
# 2. 点击右上角主题切换按钮，依次切换所有 4 套主题
# 3. 观察页面整体颜色变化是否符合验收标准
```

---

## 边界条件

- **切换不闪烁**：主题切换通过 JS 添加/移除 class，不应有页面重载或闪烁
- **弹窗也必须适配**：打开弹窗/面板时，颜色应跟随当前主题而不是保持 light
- **编辑器占位符**：TipTap 编辑器的 placeholder 文字颜色也需适配
- **加载过渡**：首次加载时如果检测到 `prefers-color-scheme: dark`，考虑是否自动应用 dark（可选，本期可不做）
- **对比度检查**：warm 和 cool 的 `--color-foreground` 与 `--color-background` 对比度需 ≥ 7:1

---

## 对外影响

| 影响范围 | 说明 |
|---------|------|
| 无 | 本任务只改 `globals.css`，不涉及其他组件或数据层。主题切换逻辑在 page.tsx 中已实现，不需要修改 |

---

## 替代建议（可选）

如果 warm/cool 的色值不确定，可以先参考以下现成方案微调：
- **Warm**：参考 shadcn 的 "neutral" 或 "stone" 色板，将色相偏向暖色
- **Cool**：参考 shadcn 的 "slate" 或 "gray" 色板，将色相偏向蓝色
- **Dark**：直接使用 shadcn 官方 dark 色板，这是最成熟的选择
