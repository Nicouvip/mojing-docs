【强制技能 — systematic-debugging + chinese-documentation】
────────────────────────

**微任务：提示词 A/B 测试脚手架 —— 双盲比对、一键出报告**

1. 在 `scripts/` 下创建 `ab-test-prompt.ts`，功能：
   - 读取 `src/lib/prompts/` 下指定的提示词文件（两版本：A 版原文件，B 版带 `-v2` 后缀）
   - 用同一组测试输入（`scripts/ab-test-inputs.json`）分别调两版，收集输出
2. 评测维度：风格一致性 / 指令遵循度 / 幻觉率 / 响应时长（4 项，每项 1-5 分）
3. 自动生成对比报告 `output/ai-ab-test-result.md`，含表格 + 胜出版本推荐
4. 输出到 `output/AI评测-AB测试脚手架方案.md`

验收标准：`npx ts-node scripts/ab-test-prompt.ts` 跑通，控制台打印分项分数和推荐版本，输出 markdown 报告。
