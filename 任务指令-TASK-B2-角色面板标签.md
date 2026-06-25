# 任务指令：角色面板标签插入

## 元信息
- **任务编号：** TASK-B2
- **优先级：** P1（Should）
- **负责角色：** 前端技术负责人
- **预估工作量：** 0.5 人天
- **发出人：** 产品经理
- **发出日期：** 2025-07-15

---

## 问题描述

角色面板（👤 标签）中三个按钮功能为空壳：
- **主角**：有 onClick 但仅 dispatch 了一个空的 InputEvent，无实际插入效果
- **反派**：无 onClick
- **配角**：无 onClick

面板自述"完整人物卡功能待添加"，但标签插入是最基础的功能，不应为空。

---

## 允许修改的文件

| 文件 | 说明 |
|------|------|
| `src/app/editor/[id]/page.tsx` | 角色面板的三个按钮 onClick 逻辑 |
| `src/components/writing-editor.tsx` | 暴露编辑器 ref 供父组件调用 |

---

## 不允许修改的文件

| 文件 | 理由 |
|------|------|
| `src/lib/store.ts` | 不涉及存储 |
| `src/app/api/` | 后端范围 |
| `src/lib/types.ts` | 不涉及类型变更 |

---

## 实现要求

### 1. WritingEditor 暴露 editor 实例

在 `writing-editor.tsx` 中用 `forwardRef` + `useImperativeHandle` 暴露一个插入方法：

```typescript
// writing-editor.tsx 改动
import { forwardRef, useImperativeHandle } from 'react'

// 定义暴露给父组件的句柄类型
export interface EditorHandle {
  insertAtCursor: (text: string) => void
}

const WritingEditor = forwardRef<EditorHandle, WritingEditorProps>((props, ref) => {
  const editor = useEditor({
    // ... 现有配置
  })

  useImperativeHandle(ref, () => ({
    insertAtCursor(text: string) {
      editor?.chain().focus().insertContent(text).run()
    },
  }))

  // ... 现有渲染
})
```

### 2. page.tsx 中获取 ref 并调用

在 page.tsx 中：
```tsx
// 顶部：创建 ref
const editorRef = useRef<EditorHandle>(null)

// 传递给 WritingEditor
<WritingEditor ref={editorRef} ... />

// 角色面板按钮 onClick
const insertTag = (tag: string) => {
  editorRef.current?.insertAtCursor(tag)
}
```

### 3. 更新三个按钮

```tsx
<button onClick={() => insertTag('【主角】')}>👤 主角</button>
<button onClick={() => insertTag('【反派】')}>👤 反派</button>
<button onClick={() => insertTag('【配角】')}>👤 配角</button>
```

### 4. 面板文字更新

将当前提示文字"完整人物卡功能待添加"更新为"点击插入角色标签"或移除。

---

## 验收标准

1. ✅ 点击"👤 主角"，编辑器光标位置插入 `【主角】`
2. ✅ 点击"👤 反派"，编辑器光标位置插入 `【反派】`
3. ✅ 点击"👤 配角"，编辑器光标位置插入 `【配角】`
4. ✅ 插入位置为当前光标位置（不是追加到末尾）
5. ✅ 插入操作支持撤销（Ctrl+Z）
6. ✅ 编辑器未初始化时点击按钮无报错

---

## 验收命令

```bash
cd D:/建网站/mojing-app && npx tsc --noEmit
```

手动验证：
1. 进入编辑器页面
2. 在编辑器中点击任意位置设置光标
3. 切换到角色面板（👤）
4. 依次点击三个标签按钮
5. 确认标签出现在光标位置

---

## 对外影响

| 影响范围 | 说明 |
|---------|------|
| WritingEditor 组件 | 新增 `forwardRef` + `useImperativeHandle`，原有 prop 接口不变，向后兼容 |
| page.tsx | 新增 `editorRef`，不影响其他逻辑 |

---

## 替代建议（可选）

如果不想用 ref，也可以用 Context 传递插入方法：
1. 创建一个 `EditorContext`，提供 `insertAtCursor` 方法
2. WritingEditor 在 editor 就绪时将方法设置到 Context
3. 角色面板通过 `useContext` 获取方法

但 ref 方式更直接、组件关系清晰，推荐使用。
