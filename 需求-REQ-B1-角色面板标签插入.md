# 需求文档：角色面板标签插入

## 元信息
- **需求编号：** REQ-B1
- **优先级：** P1 (Should)
- **RICE 评分：** 18/100
- **涉及角色：** 前端技术负责人
- **预估工作量：** 0.5 人天
- **依赖：** 无

---

## 用户故事

> **As a** 在墨境中写小说的作者
> **I want** 点击"主角""反派""配角"按钮时，能在光标位置插入对应的角色标签
> **So that** 我可以在写作过程中快速标记角色出场，辅助后续人设管理和编辑

**现状问题：** 三个按钮要么没有绑定任何 onClick，要么绑了一个空的 InputEvent dispatch，完全不起作用。面板自述"完整人物卡功能待添加"，但这三个标签按钮应该先有基本功能。

---

## 功能拆解

### 1.1 角色标签文本定义
| 按钮 | 插入的标签文本 |
|------|---------------|
| 👤 主角 | `【主角:${name}】`（默认 name 为空，即显示`【主角】`） |
| 👤 反派 | `【反派】` |
| 👤 配角 | `【配角】` |

### 1.2 在光标位置插入文本
在 page.tsx 的角色面板按钮中，实现以下逻辑：

```typescript
// 插入标签到编辑器光标位置
const insertTag = (tag: string) => {
  // 需要通过 editorRef 获取 TipTap 编辑器实例
  if (editorRef.current) {
    editorRef.current.chain().focus().insertContent(tag).run();
  }
};
```

### 1.3 更新 3 个按钮的 onClick
```tsx
<button onClick={() => insertTag('【主角】')}>👤 主角</button>
<button onClick={() => insertTag('【反派】')}>👤 反派</button>
<button onClick={() => insertTag('【配角】')}>👤 配角</button>
```

### 1.4 暴露编辑器实例引用
当前 page.tsx 通过 `<WritingEditor key={activeChapterId} ... />` 使用编辑器，需要通过 ref 或回调方式获取编辑器实例。

方案一（推荐）：在 WritingEditor 中暴露 `editor` 实例，通过 `useImperativeHandle` + `forwardRef`
方案二：在 page.tsx 层面提供 `insertAtCursor` 回调，由 WritingEditor 内部调用

### 1.5 面板文字更新
将当前提示文字"完整人物卡功能待添加"改为"点击插入角色标签"或移除。

---

## 验收标准

1. ✅ 点击"👤 主角"，编辑器光标位置插入文本 `【主角】`
2. ✅ 点击"👤 反派"，编辑器光标位置插入文本 `【反派】`
3. ✅ 点击"👤 配角"，编辑器光标位置插入文本 `【配角】`
4. ✅ 插入位置为当前光标位置（不是追加到末尾）
5. ✅ 插入后，标签文本保留格式（可加粗、可选中、可删除）
6. ✅ 插入操作支持撤销（Ctrl+Z 可撤销插入）

---

## 边界条件

- 编辑器不存在（未初始化）：点击按钮不做任何操作，也不报错
- 编辑器内容为空：在光标位置（即文档开头）插入标签
- 连续点击：每次点击在当前光标位置插入，不会覆盖上一次插入
- 标签文本只做纯文本插入，不需要特殊样式

---

## 团队备注

- 需要让 page.tsx 能调用 WritingEditor 的编辑器实例，建议通过 `editorRef` 或 Context 共享
- 如果 WritingEditor 已经使用 `forwardRef`，可以直接通过 ref 调用
- 标签文本暂时为固定文字，未来可扩展为可输入角色名的弹窗
