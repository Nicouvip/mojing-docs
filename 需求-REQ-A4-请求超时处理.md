# 需求文档：AI 请求超时处理（AbortController）

## 元信息
- **需求编号：** REQ-A4
- **优先级：** P0 (Must)
- **RICE 评分：** 24/100
- **涉及角色：** 后端技术负责人
- **预估工作量：** 0.5 人天
- **依赖：** 无

---

## 用户故事

> **As a** 使用 AI 写作功能的作者
> **I want** 如果 AI 请求超时或卡住，界面能给出反馈而不是一直转圈
> **So that** 我不会浪费等待时间，可以及时重试或换用其他功能

**现状问题：** 当前 4 个 AI 接口的 fetch 调用没有任何超时机制。如果 DeepSeek API 响应慢或网络故障，用户会一直看到加载状态，没有任何反馈。

---

## 功能拆解

### 4.1 前端：AI 请求添加 AbortController
涉及文件：`src/app/editor/[id]/page.tsx`（或当前调用 AI 接口的组件）

在每次调用 AI 接口时创建 `AbortController`：
```typescript
// 每次请求创建 AbortController
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 秒超时

try {
  const res = await fetch('/api/ai/continue', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ context, instruction }),
    signal: controller.signal,
  });
  // ... 处理响应
} catch (err) {
  if (err.name === 'AbortError') {
    // 显示超时提示，非"请求失败"
    setAiResult('请求超时，请稍后重试');
  } else {
    // 其他网络错误
  }
} finally {
  clearTimeout(timeoutId);
}
```

### 4.2 超时时间设置
| 场景 | 建议超时时间 | 说明 |
|------|:-----------:|------|
| AI 续写 (continue) | 30s | 生成 200-400 字，通常 10-20s |
| AI 润色 (polish) | 20s | 处理已有文本，通常 5-15s |
| AI 扩写 (expand) | 30s | 扩写至 2-3 倍，通常 10-25s |
| 脑洞喷射 (brainstorm) | 40s | 生成多个创意，通常 15-30s |

### 4.3 超时 UI 反馈
- 超时时，AI 面板显示橘色提示文字："⏱️ 请求超时，请稍后重试"
- 超时不关闭 AI 面板，保留已输入内容，允许用户直接点击重试
- 提供"重试"按钮，点击后重新发起相同请求

### 4.4 组件卸载时取消请求
- 在 `useEffect` 的清理函数中调用 `controller.abort()`
- 防止组件卸载后仍执行 setState 导致的 React 警告

---

## 验收标准

1. ✅ AI 续写/润色/扩写/脑洞喷射 4 个功能，如果超时，显示"⏱️ 请求超时"提示而非一直转圈
2. ✅ 超时后保留用户输入，提供"重试"按钮
3. ✅ 正常响应时（未超时），超时定时器被清除，不影响正常结果展示
4. ✅ 切换章节或关闭面板时，未完成的请求被取消，无 React 状态泄漏警告
5. ✅ 超时时间建议 30 秒（可配置）

---

## 边界条件

- 精准超时：如果服务器在第 29 秒返回响应而在第 30 秒触发 abort，确保不会错误中止正常响应（使用 `finally` 清除定时器）
- 快速双击：用户快速点击两次 AI 按钮，应取消第一个请求，只保留第二个（避免重复请求）
- 网络离线：浏览器 `navigator.onLine` 状态变化时，应提前中止请求

---

## 团队备注

- 前端改动为主，后端不需要改
- 如果后续迁移到流式响应（Streaming），超时逻辑需重新设计（SSE 连接有了首个 chunk 就算 alive）
- AbortController 的 signal 需透传到 fetch 调用层级
