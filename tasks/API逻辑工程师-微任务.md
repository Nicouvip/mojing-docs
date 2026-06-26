【强制技能 — executing-plans + flow-review】
────────────────────────

**微任务：API 端点超时熔断 + 错误码规范统一**

1. 审计 `src/app/api/` 下所有 14 个端点的错误处理：确认每个端点是否都用了统一错误响应格式 `{ ok, error, code, detail }`，未统一的逐个修正
2. 对第三方服务调用（大模型 / 数据库 / 外部 API）添加**超时熔断**：fetch/axios 请求设 `AbortController` 超时（默认 15s），超时后返回 `429 / timeout` 而非挂死
3. 在 `src/lib/api-utils.ts` 中新增 `safeFetch(url, options, timeout?)` 工具函数，封装超时 + 重试（最多 1 次）+ 统一错误格式化
4. 将所有端点迁移到此工具函数，删除内联超时逻辑
5. 输出到 `output/API-超时熔断与错误码规范.md`

验收标准：`curl` 调用任意端点如果超时 → 返回 `{ ok: false, code: "TIMEOUT", error: "请求超时" }`；调用现有成功端点返回结构不变；无重复超时逻辑。
