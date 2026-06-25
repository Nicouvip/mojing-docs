# 需求文档：主题系统修复（Dark / Warm / Cool）

## 元信息
- **需求编号：** REQ-A2
- **优先级：** P0 (Must)
- **RICE 评分：** 24/100
- **涉及角色：** 前端技术负责人
- **预估工作量：** 1 人天
- **依赖：** 无

---

## 用户故事

> **As a** 使用墨境的作者
> **I want** 切换主题时界面颜色真正改变，而不是点了没反应
> **So that** 我能在不同光照环境下舒适写作，选择自己偏好的视觉风格

**现状问题：** 当前 4 套主题图标已展示、切换逻辑已实现（通过添加 `.dark` / `.theme-warm` / `.theme-cool` 类名），但 warm 和 cool 主题在 CSS 中**没有任何变量定义**，dark 主题也只有编辑器区域的 3 条颜色覆盖，切换后页面基本不变。

---

## 功能拆解

### 2.1 设计主题色板
参考 shadcn/ui 暗黑主题标准色板，定义 3 套主题的完整 `--color-*` CSS 变量：

**🌙 Dark 主题（`.dark`）：**
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

**🌅 Warm 主题（`.theme-warm`）：**
暖色调色板，基调为暖黄/米白/琥珀色，适合长时间阅读：
```css
.theme-warm {
  --color-background: hsl(40 30% 96%);
  --color-foreground: hsl(30 40% 20%);
  --color-primary: hsl(25 50% 40%);
  --color-primary-foreground: hsl(40 30% 96%);
  --color-secondary: hsl(35 25% 88%);
  --color-secondary-foreground: hsl(30 40% 20%);
  --color-muted: hsl(40 20% 90%);
  --color-muted-foreground: hsl(30 20% 45%);
  /* 其他变量类推，保持暖色调统一 */
}
```

**❄️ Cool 主题（`.theme-cool`）：**
冷色调色板，基调为冷灰/蓝灰/冰蓝，适合专注写作：
```css
.theme-cool {
  --color-background: hsl(210 20% 92%);
  --color-foreground: hsl(215 30% 20%);
  --color-primary: hsl(210 50% 45%);
  --color-primary-foreground: hsl(210 20% 98%);
  --color-secondary: hsl(210 15% 85%);
  --color-secondary-foreground: hsl(215 30% 20%);
  /* 其他变量类推，保持冷色调统一 */
}
```

### 2.2 在 `globals.css` 中追加主题变量块
- 在 `globals.css` 中追加 3 个 CSS 块：`.dark`, `.theme-warm`, `.theme-cool`
- 每个块覆盖所有 18 个 `--color-*` 变量
- 同时定义自定义变量（`--gradient`, `--shadow`, 编辑器相关变量）

### 2.3 定义编辑器（ProseMirror）主题适配
- TipTap 编辑器的 `.ProseMirror` 区域需要各主题下的文字颜色、背景色、选中色覆盖
- 目前 dark 仅有 3 条覆盖，需补齐到完整

### 2.4 验证切换逻辑
当前切换逻辑在 `page.tsx` 第 287 行：
```tsx
const root = document.documentElement;
root.className = root.className.replace(/theme-\w+|dark/g,'').trim();
if (k === 'dark') root.classList.add('dark');
else if (k !== 'light') root.classList.add('theme-' + k);
```
确认 class 添加正确，无冲突。

---

## 验收标准

1. ✅ 点击主题切换按钮（☀️→🌅→🌙→❄️），页面整体色调正确变化
2. ✅ dark 主题下：背景深色、文字浅色、卡片/弹窗/侧栏均为深色背景，不刺眼
3. ✅ warm 主题下：整体暖黄基调，文字不刺眼，长时间阅读舒适
4. ✅ cool 主题下：整体冷灰基调，清晰干净
5. ✅ 编辑器区域在 4 套主题下均正常可读，选中文本高亮颜色适配主题
6. ✅ 主题切换不产生视觉闪烁或白屏
7. ✅ 所有 `--color-*` 变量都有值，无继承到浏览器默认值的变量

---

## 边界条件

- 切换主题时，已打开的弹窗/面板应同步改变颜色（不能出现弹窗深色、背景浅色的不协调）
- 如果用户使用操作系统偏好（`prefers-color-scheme: dark`），需考虑初始加载是否应该自动应用 dark 主题（当前未实现，可不做，留到后期）
- 自定义滚动条颜色也需适配各主题
- warm/cool 主题的对比度需满足 WCAG AA 标准（文字与背景对比度 ≥ 4.5:1）

---

## 团队备注

- 不需要新增 UI 切换组件，当前 theme 切换按钮逻辑已在 page.tsx 中
- 注意 `@theme inline` 中定义的变量是 light 主题默认值，`.dark` / `.theme-warm` / `.theme-cool` 的块级覆盖需在 `@theme inline` 块之后定义
- 参考 Tailwind CSS v4 的 `@custom-variant` 和 CSS 层叠规则
