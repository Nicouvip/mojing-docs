# 任务指令：AI 请求超时处理 (AbortController)

## 元信息
- **任务编号：** TASK-B1
- **优先级：** P1（Should）
- **负责角色：** 前端技术负责人
- **预估工作量：** 0.5 人天
- **发出人：** 产品经理
- **发出日期：** 2025-07-15

---

## 问题描述

当前页面中 2 处 AI 请求（第 43 行 brainstorm、第 61 行 continue/polish/expand）均未设置超时。如果 DeepSeek API 响应慢或网络故障，用户会无限等待。

---

## 允许修改的文件

| 文件 | 说明 |
|------|------|
| `src/app/editor/[id]/page.tsx` | 2 处 fetch 调用加上 AbortController |

---

## 不允许修改的文件

| 文件 | 理由 |
|------|------|
| `src/app/api/ai/*/route.ts` | 后端范围 |
| `src/lib/store.ts` | 不涉及存储 |
| `src/components/writing-editor.tsx` | 不涉及编辑器组件 |

---

## 实现要求

### 1. 为 brainstorm fetch（第 43 行）添加超时

当前代码：
```typescript
const res = await fetch('/api/ai/brainstorm', { 
  method: 'POST', 
  headers: { 'Content-Type': 'application/json' }, 
  body: JSON.stringify({ genre: bsGenre }) 
})
```

改为：
```typescript
const controller = new AbortController()
const timeoutId = setTimeout(() => controller.abort(), 40000) // 脑洞 40 秒超时
try {
  const res = await fetch('/api/ai/brainstorm', { 
    method: 'POST', 
    headers: { 'Content-Type': 'application/json' }, 
    body: JSON.stringify({ genre: bsGenre }),
    signal: controller.signal,
  })
  // ... 现有响应处理
} catch (err: unknown) {
  if (err instanceof Error && err.name === 'AbortError') {
    setBsIdeas('⏱️ 请求超时，请稍后重试')
  } else {
    setBsIdeas('请求失败: ' + (err instanceof Error ? err.message : '未知错误'))
  }
} finally {
  clearTimeout(timeoutId)
}
```

### 2. 为 AI 通用 fetch（第 61 行）添加超时

当前代码：
```typescript
const res = await fetch(endpoint, { 
  method: 'POST', 
  headers: { 'Content-Type': 'application/json' }, 
  body: JSON.stringify(body) 
})
```

改为（类似结构，超时设为 30 秒）：
```typescript
const controller = new AbortController()
const timeoutId = setTimeout(() => controller.abort(), 30000)
try {
  const res = await fetch(endpoint, { 
    method: 'POST', 
    headers: { 'Content-Type': 'application/json' }, 
    body: JSON.stringify(body),
    signal: controller.signal,
  })
  // ... 现有响应处理
} catch (err: unknown) {
  if (err instanceof Error && err.name === 'AbortError') {
    setAiMsg('⏱️ 请求超时，请稍后重试')
  } else {
    setAiMsg('请求失败: ' + (err instanceof Error ? err.message : '未知错误'))
  }
} finally {
  clearTimeout(timeoutId)
}
```

### 3. 超时时间配置

| 接口 | 超时时间 |
|------|:--------:|
| 脑洞喷射 (brainstorm) | 40 秒（生成多条创意较慢） |
| 续写/润色/扩写 (continue/polish/expand) | 30 秒 |

---

## 验收标准

1. ✅ AI 续写/润色/扩写/脑洞喷射 4 个功能，如果在对应超时时间内未返回，显示"⏱️ 请求超时"提示
2. ✅ 正常响应时，超时定时器被清除，不影响正常结果
3. ✅ 组件卸载时自动 abort 未完成的请求，无 React 状态泄漏警告

---

## 验收命令

```bash
cd D:/建网站/mojing-app && npx tsc --noEmit
```

手动测试：启动开发服务器，触发 AI 请求，观察 30-40 秒后是否显示超时提示。

---

## 对外影响

无。纯前端改动，不涉及 API 路由和数据层。

---

## 替代建议（可选）

如果希望可配置超时时间，可以把超时值提取为常量：
```typescript
const AI_TIMEOUT = {
  brainstorm: 40000,
  default: 30000,
}
```
