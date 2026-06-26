---
trustLevel: 2
---

【强制技能 — verification-before-completion · systematic-debugging · gstack】
────────────────────────

T-P1-1：回归测试 + 验证已修复项

1. 验证以下已修复项是否真的好了：
   - writing-editor无限循环
   - 登录页苔绿玻璃样式
   - 角色面板显示角色列表
   - 后端认证localStorage fallback

2. 回归测试全部页面：
   - 首页 200
   - 编辑器 200（进demo-1）
   - 登录/注册页 200
   - /admin 200
   - /works /features /templates /tools /cases /library 200

3. 输出Bug清单

输出：output/QA-回归测试.md