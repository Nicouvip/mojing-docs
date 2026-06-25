# 任务指令：卷管理（重命名/删除）

## 元信息
- **任务编号：** TASK-B4
- **优先级：** P1（Should）
- **负责角色：** 前端技术负责人
- **预估工作量：** 1.5 人天
- **发出人：** 产品经理
- **发出日期：** 2025-07-15

---

## 问题描述

卷管理功能严重残缺：
1. 卷右侧"···"按钮点击弹出 `alert('卷功能待实现')`
2. 章节并非用户自定义分配到卷，而是按等分公式自动分配
3. 无法重命名卷、无法删除卷

---

## 允许修改的文件

| 文件 | 改动量 |
|------|:------:|
| `src/lib/types.ts` | Volume 类型新增字段 |
| `src/lib/store.ts` | 新增卷操作函数 |
| `src/app/editor/[id]/page.tsx` | 卷 UI 交互重写 |

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
export interface Volume {
  id: string
  projectId: string
  name: string
  order: number
  createdAt: number
  updatedAt: number
}

// Chapter 新增
export interface Chapter {
  // ... 现有字段
  volumeId: string    // 所属卷 ID
  // ... 其他字段
}
```

### 2. 新增卷操作（store.ts）

| 函数 | 说明 |
|------|------|
| `getVolumes(projectId)` | 按 order 排序返回卷列表 |
| `createVolume(projectId, name)` | 创建新卷，自动 id+order |
| `renameVolume(volumeId, name)` | 重命名，name 为空则恢复原名 |
| `deleteVolume(volumeId)` | 删除空卷，非空卷拒绝并提示 |

### 3. 卷菜单改造（page.tsx）

将当前 `<button onClick={e => { ... alert('卷功能待实现') }}>` 替换为下拉菜单：

**菜单触发器：** 卷名称右侧的"···"按钮

**菜单项：**
| 菜单项 | 操作 |
|--------|------|
| ✏️ 重命名 | 卷名变为内联输入框，回车确认/Esc取消 |
| ❌ 删除卷 | 检查章节数 → 空卷直接删；非空卷弹确认"卷内有 N 篇章节，删除后章节将移入未分类" |

### 4. 默认卷与迁移兼容

- 每个项目至少有 1 个默认卷
- 新章节默认归入第一个卷
- 旧数据的章节（无 `volumeId`）自动归入"未分类"或第一卷

---

## 验收标准

1. ✅ 点击卷"···"按钮，弹出菜单含"✏️ 重命名"和"❌ 删除卷"
2. ✅ 重命名时内联编辑，回车确认、Esc取消，空名恢复原名
3. ✅ 删除空卷时卷直接消失
4. ✅ 删除非空卷时提示用户，确认后章节移入"未分类"
5. ✅ 已有旧数据兼容（不报错）

---

## 验收命令

```bash
cd D:/建网站/mojing-app && npx tsc --noEmit
```

---

## 对外影响

| 影响范围 | 说明 |
|---------|------|
| types.ts | Volume/Chapter 类型变更，影响 store.ts 和 page.tsx |
| store.ts | 新增函数，不破坏旧接口 |

---

## 替代建议（可选）

如果实现内联编辑太复杂，可以用 Dialog 弹窗做重命名。先做删除逻辑，重命名用弹窗兜底。
