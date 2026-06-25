# 墨境 UI 设计系统规范 — 设计师专用提示词

> 每次设计页面时，必须遵循以下规范。这不是建议，是强制标准。

---

## 设计哲学

墨境是一个**沉浸式写作工具**，设计必须传达：
- **安静感** — 界面退到背景，文字走到前台
- **精良感** — 每个像素都有意图，没有随意的间距和颜色
- **呼吸感** — 大量留白，信息密度适中，不压迫眼睛

参考标杆（按优先级）：
1. **Linear** — 极简、克制、信息层次清晰
2. **Notion** — 排版舒适、留白充足、内容优先
3. **Arc 浏览器** — 现代感、微动效、细节精致
4. **Apple HIG** — 圆角、阴影、过渡的一致性标准

---

## 色彩系统

### 主色板（浅色主题）
```
背景主色      #f8f9fb    极浅灰白，不是纯白
卡片背景      #ffffff    纯白
主色          #2563eb    纯净蓝（非苹果蓝，更沉稳）
主色浅底      #eff6ff    极淡蓝
主色悬停      #1d4ed8    深蓝
文字主色      #0f172a    近黑
文字次级      #64748b    中灰
文字辅助      #94a3b8    浅灰
边框          #e2e8f0    极浅灰线
成功          #10b981    翡翠绿
警告          #f59e0b    琥珀
错误          #ef4444    纯红
强调          #8b5cf6    紫色（AI 相关功能）
```

### 暗色主题
```
背景主色      #0f172a    深蓝黑
卡片背景      #1e293b    深灰蓝
主色          #3b82f6    亮蓝
文字主色      #f1f5f9    近白
文字次级      #94a3b8    中灰
边框          rgba(255,255,255,.06)
```

### 绝对禁止
- 不使用纯黑 `#000000` 作为背景或文字
- 不使用饱和度超过 80% 的大面积色块
- 不使用渐变色作为大面积背景（只用于按钮 hover、进度条等小元素）
- 不使用超过 3 种强调色在同一页面

---

## 字体系统

```css
/* 中文正文 */
font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;

/* 英文/数字 */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

/* 代码 */
font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
```

### 字号层级（严格遵守，不随意取值）
```
页面大标题    24px / 32px    font-weight: 700
区块标题      18px / 28px    font-weight: 600
卡片标题      15px / 24px    font-weight: 600
正文          14px / 22px    font-weight: 400
辅助文字      13px / 20px    font-weight: 400
标签/徽章     12px / 16px    font-weight: 500
极小文字      11px / 16px    font-weight: 400（仅用于时间戳等）
```

### 字重使用
- **700 (Bold)** — 仅用于页面标题
- **600 (Semibold)** — 区块标题、按钮文字、卡片标题
- **500 (Medium)** — 标签、徽章、导航项
- **400 (Regular)** — 正文、辅助文字

**不使用 300 (Light)**，在屏幕上太细看不清。

---

## 间距系统

基于 **4px 网格**，所有间距必须是 4 的倍数：

```
紧凑间距      4px      元素内部微调
基础间距      8px      图标与文字之间
标准间距      12px     列表项之间、卡片内边距
舒适间距      16px     区块内边距、组件间距
宽松间距      24px     区块之间
大间距        32px     页面区域之间
超大间距      48px     首屏区域分隔
```

---

## 圆角系统

```
小圆角        6px      按钮、标签、输入框
中圆角        10px     卡片、下拉菜单
大圆角        14px     弹窗、大卡片
全圆          9999px   徽章、头像
```

### 一致性原则
同一层级的元素必须使用相同的圆角值。页面内不允许出现超过 3 种圆角值。

---

## 阴影系统

```
无阴影        大部分元素（用边框代替阴影）
卡片阴影      0 1px 3px rgba(0,0,0,.04)
悬停阴影      0 4px 12px rgba(0,0,0,.06)
弹窗阴影      0 8px 24px rgba(0,0,0,.08)
```

### 原则
- 浅色主题优先用边框 `1px solid rgba(0,0,0,.06)` 而非阴影
- 暗色主题用 `rgba(255,255,255,.04)` 边框 + 微弱背景差异
- 阴影只在元素浮起时使用（hover、弹窗、下拉）

---

## 布局原则

### 全屏页面
```css
min-height: 100vh;
background: var(--background);
```

### 三栏布局（墨境核心布局）
```
左侧栏      220px    可折叠（48px 图标模式）
编辑区      flex:1   自适应
右面板      280px    可折叠
```

### 内容区最大宽度
```
文字阅读    720px    居中，两侧留白
表单/设置   640px    居中
全宽工具    100%     左右各留 24px
```

---

## 组件规范

### 按钮
```
主要按钮    bg-primary text-white rounded-md px-4 py-2 text-sm font-medium
次要按钮    bg-secondary text-foreground border rounded-md px-4 py-2 text-sm
幽灵按钮    bg-transparent text-muted-foreground hover:bg-secondary rounded-md px-3 py-1.5 text-sm
图标按钮    bg-transparent text-muted-foreground hover:bg-secondary rounded-md p-2
危险按钮    bg-destructive text-white rounded-md px-4 py-2 text-sm

hover 过渡    all 0.15s ease
active 缩放    transform: scale(0.98)
```

### 输入框
```
bg-white border border-border rounded-md px-3 py-2 text-sm
focus: border-primary ring-2 ring-primary/20 outline-none
placeholder: text-muted-foreground
```

### 卡片
```
bg-card border border-border rounded-[10px] p-4
hover: border-border/50 shadow-card
```

### 弹窗
```
fixed inset-0 bg-black/30 backdrop-blur-sm z-50
居中容器: bg-card rounded-2xl p-6 max-w-lg shadow-modal
```

---

## 动效规范

### 过渡时间
```
微交互      0.15s    按钮 hover、颜色变化
状态切换    0.2s     面板展开/折叠
页面过渡    0.3s     路由切换、弹窗出现
复杂动画    0.5s     骨架屏→内容
```

### 缓动函数
```
默认        ease
进入        cubic-bezier(0.16, 1, 0.3, 1)    弹性进入
退出        cubic-bezier(0.7, 0, 0.3, 1)    平滑退出
```

### 禁止
- 不使用 bounce 效果（太幼稚）
- 不使用超过 0.5s 的过渡（太慢）
- 不使用闪烁/脉冲作为常态（仅 loading 状态可用）

---

## 图标规范

使用 **Lucide React** 图标库（项目已安装）。
```
工具栏图标    18px    stroke-width: 1.5
导航图标      20px    stroke-width: 1.5
状态图标      16px    stroke-width: 2
装饰图标      24px    stroke-width: 1.5
```

---

## 输出要求

每次设计页面时，必须输出：
1. **完整的 Tailwind 类名** — 可直接复制到代码中
2. **HTML 结构** — 用 JSX 语法（className 而非 class）
3. **响应式断点** — 至少考虑 md（768px）和 lg（1024px）
4. **暗色模式** — 用 dark: 前缀适配
5. **交互状态** — hover、focus、active、disabled 都要定义
6. **动画/过渡** — 所有状态变化必须有过渡

### 禁止的写法
- `style={{}}` 内联样式 — 必须用 Tailwind 类名
- `#hex` 色值 — 必须用 CSS 变量
- 随意的 padding/margin 值 — 必须遵循 4px 网格
- `!important` — 说明选择器优先级有问题
