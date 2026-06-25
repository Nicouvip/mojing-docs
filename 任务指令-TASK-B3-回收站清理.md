# 任务指令：回收站自动清理逻辑

## 元信息
- **任务编号：** TASK-B3
- **优先级：** P1（Should）
- **负责角色：** 前端技术负责人
- **预估工作量：** 0.5 人天
- **发出人：** 产品经理
- **发出日期：** 2025-07-15

---

## 问题描述

回收站弹窗显示"30天后自动清除"提示，但代码中没有任何定时清理或过期删除逻辑。已删除的章节永久留在回收站中。

---

## 允许修改的文件

| 文件 | 改动 |
|------|------|
| `src/lib/types.ts` | Chapter 类型新增 `deletedAt?: number` |
| `src/lib/store.ts` | 删除时记录时间戳 + 清理过期章节函数 |
| `src/app/editor/[id]/page.tsx` | 打开回收站时触发清理 |

---

## 不允许修改的文件

| 文件 | 理由 |
|------|------|
| `src/components/writing-editor.tsx` | 不涉及编辑器 |
| `src/app/api/` | 后端范围 |

---

## 实现要求

### 1. 类型扩展（types.ts）

```typescript
// Chapter 接口中新增（可选字段，向后兼容）
export interface Chapter {
  // ... 现有字段
  deletedAt?: number  // 新增：删除时间戳，毫秒
  // ... 其他字段
}
```

### 2. 删除时记录时间戳（store.ts）

当前 `deleteChapter` 函数新增 `deletedAt`：
```typescript
deleteChapter: (chapterId: string) => {
  setChaptersAll(prev => prev.map(ch =>
    ch.id === chapterId
      ? { ...ch, isDeleted: true, deletedAt: Date.now() }
      : ch
  ))
  // 现有保存逻辑
}
```

### 3. 清理函数（store.ts）

新增 `cleanExpiredChapters` 函数：
```typescript
cleanExpiredChapters: () => {
  const THIRTY_DAYS_MS = 30 * 24 * 60 * 60 * 1000
  const now = Date.now()
  setChaptersAll(prev => {
    const cleaned = prev.filter(ch => {
      if (!ch.isDeleted) return true  // 保留未删除
      if (!ch.deletedAt) return false // 无时间戳视为过期，清理
      return (now - ch.deletedAt) < THIRTY_DAYS_MS // 未过期保留
    })
    saveClient('mojing_chapters', cleaned)
    return cleaned
  })
}
```

### 4. 触发清理（page.tsx）

在打开回收站的逻辑中调用清理（轻触即清，无需用户等待）：
```typescript
// 打开回收站时
const handleOpenTrash = () => {
  cleanExpiredChapters()
  setShowRecycleBin(true)
}
```

同时，编辑器页面加载时也做一次清理。

---

## 验收标准

1. ✅ 删除章节后，`deletedAt` 时间戳被记录
2. ✅ 打开回收站时，过期（>30天）的章节自动清除
3. ✅ 未过期章节正常显示在回收站中
4. ✅ 旧数据（已删除但无 `deletedAt`）自动清理，不报错

---

## 验收命令

```bash
cd D:/建网站/mojing-app && npx tsc --noEmit
```

---

## 对外影响

无。deletedAt 为可选字段，不破坏现有类型。
