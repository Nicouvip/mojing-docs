// ============================================================
// bot-runner.js — 信任等级驱动的会话启动器
// 设计依据: output/信任等级-技术设计.md
// ============================================================
// 用法:
//   node bot-runner.js <角色名>              # 启动角色会话
//   node bot-runner.js --check <角色名>      # 仅检查信任等级
//   node bot-runner.js --list                # 列出所有角色信任等级
//   node bot-runner.js --verify              # 验证所有任务文件 frontmatter
// ============================================================

const fs = require('fs');
const path = require('path');

const PROJECT_ROOT = 'D:/建网站/mojing-docs';
const TASKS_DIR = path.join(PROJECT_ROOT, 'tasks');
const SESSIONS_DIR = 'C:/Users/nicou/AppData/Roaming/reasonix/projects/D--建网站/sessions';
const AUDIT_DIR = path.join(PROJECT_ROOT, 'audit');

// 确保审计目录存在
if (!fs.existsSync(AUDIT_DIR)) {
  fs.mkdirSync(AUDIT_DIR, { recursive: true });
}

// ============================================================
// 五级信任等级定义（与技术设计完全一致）
// ============================================================
const TRUST_LEVELS = {
  1: {
    name: 'L1-基础只读',
    description: '零信任 — 只能读文件、搜索代码、查看文档',
    tools: [
      'read_file', 'grep', 'glob', 'ls',
      'lsp_definition', 'lsp_diagnostics', 'lsp_hover', 'lsp_references',
      'web_fetch', 'memory', 'code_index',
    ],
    maxContextTokens: 8_000,
    skipCI: false,
    canDispatch: false,
    canReview: false,
    canManageRoles: false,
    canAccessProduction: false,
  },
  2: {
    name: 'L2-可写任务',
    description: '基本信任 — 写文件、改代码、执行命令',
    tools: [
      // L1 全部
      'read_file', 'grep', 'glob', 'ls',
      'lsp_definition', 'lsp_diagnostics', 'lsp_hover', 'lsp_references',
      'web_fetch', 'memory', 'code_index',
      // L2 新增
      'edit_file', 'write_file', 'delete_range', 'delete_symbol',
      'move_file', 'multi_edit', 'bash', 'notebook_edit',
      'todo_write', 'complete_step',
    ],
    maxContextTokens: 8_000,
    skipCI: false,
    canDispatch: false,
    canReview: false,
    canManageRoles: false,
    canAccessProduction: false,
  },
  3: {
    name: 'L3-可派发',
    description: '团队信任 — 可派发子任务、调度角色、更长推理上下文',
    tools: [
      // L2 全部
      'read_file', 'grep', 'glob', 'ls',
      'lsp_definition', 'lsp_diagnostics', 'lsp_hover', 'lsp_references',
      'web_fetch', 'memory', 'code_index',
      'edit_file', 'write_file', 'delete_range', 'delete_symbol',
      'move_file', 'multi_edit', 'bash', 'notebook_edit',
      'todo_write', 'complete_step',
      // L3 新增
      'ask', 'slash_command', 'history',
      'list_sessions', 'read_session',
    ],
    maxContextTokens: 32_000,   // ← 长上下文
    skipCI: false,
    canDispatch: true,
    canReview: false,
    canManageRoles: false,
    canAccessProduction: false,
  },
  4: {
    name: 'L4-可审代码',
    description: '审查信任 — 可审查代码、批准/拒绝 PR、跳过部分 CI',
    tools: [
      // L3 全部
      'read_file', 'grep', 'glob', 'ls',
      'lsp_definition', 'lsp_diagnostics', 'lsp_hover', 'lsp_references',
      'web_fetch', 'memory', 'code_index',
      'edit_file', 'write_file', 'delete_range', 'delete_symbol',
      'move_file', 'multi_edit', 'bash', 'notebook_edit',
      'todo_write', 'complete_step',
      'ask', 'slash_command', 'history',
      'list_sessions', 'read_session',
      // L4 新增
      'forget', 'mcp__*',
    ],
    maxContextTokens: 32_000,
    skipCI: true,               // 可跳过部分 CI
    canDispatch: true,
    canReview: true,
    canManageRoles: false,
    canAccessProduction: false,
  },
  5: {
    name: 'L5-全部权限',
    description: '完全信任 — 全部权限，无任何限制',
    tools: '__ALL__',
    maxContextTokens: 64_000,
    skipCI: true,
    canDispatch: true,
    canReview: true,
    canManageRoles: true,
    canAccessProduction: true,
  },
};

const DEFAULT_TRUST_LEVEL = 1;
const VALID_LEVELS = Object.keys(TRUST_LEVELS).map(Number);

// ============================================================
// Frontmatter 解析器（支持 YAML 和简易回退）
// ============================================================
function extractFrontmatter(content) {
  // 匹配 YAML frontmatter: 支持 \n 和 \r\n
  const match = content.match(/^---[\r\n]+([\s\S]*?)[\r\n]+---/);
  if (!match) return null;

  const yamlText = match[1];
  const result = {};

  // 简易 YAML 解析（处理信任等级所需的字段类型）
  const lines = yamlText.split('\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;

    // 处理数组: skills: [a, b, c] 或 skills:\n  - a\n  - b
    if (trimmed.startsWith('- ')) {
      // 数组项，需要知道上一个 key
      continue;
    }

    const colonIdx = trimmed.indexOf(':');
    if (colonIdx === -1) continue;

    const key = trimmed.slice(0, colonIdx).trim();
    let value = trimmed.slice(colonIdx + 1).trim();

    // 跳过空值
    if (value === '') continue;

    // 尝试解析数组 [item1, item2]
    if (value.startsWith('[') && value.endsWith(']')) {
      try {
        value = JSON.parse(value.replace(/'/g, '"'));
      } catch {
        value = value.slice(1, -1).split(',').map(s => s.trim().replace(/['"]/g, ''));
      }
    }
    // 解析数字
    else if (/^\d+$/.test(value)) {
      value = parseInt(value, 10);
    }
    // 解析布尔值
    else if (value === 'true') value = true;
    else if (value === 'false') value = false;
    // 去掉可能的多余引号
    else if ((value.startsWith('"') && value.endsWith('"')) ||
             (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }

    result[key] = value;
  }

  return result;
}

// ============================================================
// 核心函数: 读取角色的信任等级
// ============================================================
function getTrustLevel(roleName) {
  const taskFile = path.join(TASKS_DIR, `${roleName}.md`);

  if (!fs.existsSync(taskFile)) {
    console.warn(`  ⚠️  未找到任务文件: ${taskFile}`);
    console.warn(`  → 使用默认等级 L1（基础只读）`);
    return { level: DEFAULT_TRUST_LEVEL, source: 'default', file: null };
  }

  try {
    const content = fs.readFileSync(taskFile, 'utf-8');
    const frontmatter = extractFrontmatter(content);

    if (!frontmatter) {
      console.warn(`  ⚠️  ${roleName}: 无 YAML frontmatter，使用默认 L1`);
      return { level: DEFAULT_TRUST_LEVEL, source: 'default-no-frontmatter', file: taskFile };
    }

    if (frontmatter.trustLevel === undefined || frontmatter.trustLevel === null) {
      console.warn(`  ⚠️  ${roleName}: 未定义 trustLevel，使用默认 L1`);
      console.warn(`  → 请在 tasks/${roleName}.md 中添加: trustLevel: N`);
      return { level: DEFAULT_TRUST_LEVEL, source: 'default-no-field', file: taskFile };
    }

    const level = parseInt(frontmatter.trustLevel, 10);
    if (isNaN(level) || level < 1 || level > 5) {
      console.warn(`  ⚠️  ${roleName}: trustLevel=${frontmatter.trustLevel} 超出范围 [1-5]，使用默认 L1`);
      return { level: DEFAULT_TRUST_LEVEL, source: 'default-out-of-range', file: taskFile };
    }

    // 检查信任是否过期
    if (frontmatter.trustExpires) {
      const expires = new Date(frontmatter.trustExpires);
      if (!isNaN(expires.getTime()) && expires < new Date()) {
        console.warn(`  ⚠️  ${roleName}: 信任已于 ${frontmatter.trustExpires} 过期，降级至 L1`);
        return { level: DEFAULT_TRUST_LEVEL, source: 'expired', file: taskFile };
      }
    }

    return { level, source: 'frontmatter', file: taskFile, frontmatter };
  } catch (err) {
    console.error(`  ❌ 读取 ${roleName} 信任等级失败:`, err.message);
    return { level: DEFAULT_TRUST_LEVEL, source: 'error', file: taskFile };
  }
}

// ============================================================
// 核心函数: 构建系统提示词（注入等级约束）
// ============================================================
function buildSystemPrompt(roleName, trustInfo) {
  const level = trustInfo.level;
  const config = TRUST_LEVELS[level];
  const allowedTools = Array.isArray(config.tools)
    ? config.tools.join(', ')
    : config.tools;  // '__ALL__'

  return `你正在以「${roleName}」身份运行，信任等级为 ${config.name}。

## 你的信任等级权限

${config.description}

## 你的权限边界

${
  allowedTools === '__ALL__'
    ? '- ✅ 你拥有全部系统权限，无任何限制。'
    : `- ✅ 允许使用的工具集（${config.tools.length} 项）:
  ${allowedTools}
- ❌ 禁止使用清单之外的任何工具。`
}

## 其他约束

- 上下文窗口上限: ${(config.maxContextTokens / 1000).toFixed(0)}K tokens
- ${
  config.canReview
    ? '✅ 你拥有代码审查权限。'
    : '❌ 你无权进行代码审查。'
}
- ${
  config.canDispatch
    ? '✅ 你拥有任务派发权限。'
    : '❌ 你无权向他人派发任务。'
}
- ${
  config.skipCI
    ? '✅ 你可以跳过部分 CI 检查（L4+ 特权）。'
    : '❌ 你必须完整通过 CI 检查。'
}
- ${
  config.canAccessProduction
    ? '✅ 你有权操作生产环境。'
    : '❌ 你无权操作生产环境。'
}

## 信任来源

${trustInfo.source === 'frontmatter' ? `- 信任等级从 tasks/${roleName}.md 的 frontmatter 读取` :
  trustInfo.source === 'expired' ? `- ⚠️ 信任已过期，临时降级至 L1。请联系总管更新 trustExpires` :
  `- 使用默认信任等级 L1（未在 frontmatter 中声明 trustLevel）`}

请严格遵守上述权限边界。超出权限的操作将被系统拒绝。`;
}

// ============================================================
// 审计日志
// ============================================================
function auditLog(entry) {
  const logFile = path.join(AUDIT_DIR, 'trust-level.log');
  const logEntry = JSON.stringify({
    timestamp: new Date().toISOString(),
    ...entry,
  }) + '\n';

  try {
    fs.appendFileSync(logFile, logEntry, 'utf-8');
  } catch (err) {
    console.error(`  ⚠️ 审计日志写入失败: ${err.message}`);
  }
}

// ============================================================
// 核心函数: 启动角色会话
// ============================================================
function startRoleSession(roleName) {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`  🚀 启动角色: ${roleName}`);
  console.log(`${'='.repeat(60)}\n`);

  // 1. 读取信任等级
  const trustInfo = getTrustLevel(roleName);
  const level = trustInfo.level;
  const config = TRUST_LEVELS[level];

  console.log(`\n  📊 信任等级: ${config.name} (L${level})`);
  console.log(`  📐 上下文窗口: ${(config.maxContextTokens / 1000).toFixed(0)}K tokens`);
  console.log(`  🛡️  跳过 CI: ${config.skipCI ? '是 (L4+ 特权)' : '否'}`);
  console.log(`  📤 可派发任务: ${config.canDispatch ? '是' : '否'}`);
  console.log(`  👁️  可审查代码: ${config.canReview ? '是' : '否'}`);
  console.log(`  🏭 可操作生产: ${config.canAccessProduction ? '是' : '否'}`);
  console.log(`  🔧 工具白名单: ${config.tools === '__ALL__' ? '全部（无限制）' : config.tools.length + ' 项工具'}`);

  // 2. 构建系统提示词
  const systemPrompt = buildSystemPrompt(roleName, trustInfo);

  // 3. 审计日志
  auditLog({
    action: 'SESSION_START',
    role: roleName,
    trustLevel: level,
    levelName: config.name,
    source: trustInfo.source,
  });

  // 4. 输出会话启动包
  console.log(`\n  📋 ── 系统提示词 ──────────────────────────`);
  console.log(systemPrompt);
  console.log(`  ────────────────────────────────────────────`);

  // 5. 写入会话上下文文件
  const sessionTag = `trust-${roleName}-${Date.now()}`;
  const sessionFile = path.join(SESSIONS_DIR, `${sessionTag}.jsonl`);

  // 如果是 L3+，加载长上下文记忆
  let privilegedMemory = '';
  if (level >= 3) {
    privilegedMemory = loadPrivilegedMemory(roleName, level);
    if (privilegedMemory) {
      console.log(`\n  🧠 L3+ 特权记忆已加载`);
    }
  }

  const userMessage = `启动会话。你将作为 ${roleName}（L${level}）开始工作。${
    privilegedMemory ? '\n\n【预加载上下文】\n' + privilegedMemory : ''
  }`;

  const initialPayload = [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: userMessage },
  ];

  try {
    if (!fs.existsSync(SESSIONS_DIR)) {
      fs.mkdirSync(SESSIONS_DIR, { recursive: true });
    }
    fs.writeFileSync(
      sessionFile,
      initialPayload.map(m => JSON.stringify(m, null, 0) + '\n').join(''),
      'utf-8',
    );
    console.log(`\n  ✅ 会话文件已创建: ${sessionFile}`);
  } catch (err) {
    console.error(`  ❌ 会话文件写入失败: ${err.message}`);
    console.log(`  → 会话内容已输出到上方，可手动复制到对话框。`);
  }

  console.log(`\n${'='.repeat(60)}\n`);

  return { roleName, level, sessionFile, config, trustInfo };
}

// ============================================================
// L3+ 长上下文: 加载特权记忆
// ============================================================
function loadPrivilegedMemory(roleName, level) {
  if (level < 3) return '';

  const memories = [];

  // 1. 尝试获取角色所属组
  const groupName = getGroupByRole(roleName);
  if (groupName) {
    const groupTodos = loadGroupTodos(groupName);
    if (groupTodos) {
      memories.push(`【当前组待办】${groupTodos}`);
    }
    const latestReports = loadLatestReports(groupName, 3);
    if (latestReports) {
      memories.push(`【组内最新汇报】${latestReports}`);
    }
  }

  // 2. 加载最近会话摘要
  const recentSessions = loadRecentSessionSummaries(roleName);
  if (recentSessions) {
    memories.push(`【最近会话摘要】${recentSessions}`);
  }

  return memories.join('\n\n');
}

function getGroupByRole(roleName) {
  // 从角色名推断所属组
  const groupMap = {
    'A组-前端技术负责人': 'A组',
    '后端技术负责人': 'A组',
    'B组-架构审查员': 'B组',
    'C组-工具组长': 'C组',
    'D组-基础组长': 'D组',
    'E组-测试组长': 'E组',
    'F组-审查组长': 'F组',
    'G组-文档组长': 'G组',
    '前端技术负责人': 'A组',
    '调度副手': '总管组',
  };

  // 尝试从任务文件 frontmatter 中读取 group 字段
  try {
    const taskFile = path.join(TASKS_DIR, `${roleName}.md`);
    if (fs.existsSync(taskFile)) {
      const content = fs.readFileSync(taskFile, 'utf-8');
      const fm = extractFrontmatter(content);
      if (fm && fm.group) {
        return fm.group;
      }
    }
  } catch {}

  return groupMap[roleName] || null;
}

function loadGroupTodos(groupName) {
  // 扫描 tasks 目录，收集本组待办
  try {
    const files = fs.readdirSync(TASKS_DIR);
    const groupFiles = files.filter(f =>
      f.startsWith(groupName) && f.endsWith('.md')
    );
    if (groupFiles.length === 0) return '';
    return `本组有 ${groupFiles.length} 个任务文件待处理`;
  } catch {
    return '';
  }
}

function loadLatestReports(groupName, count) {
  // 从 output 目录加载最近的汇报
  try {
    const outputDir = path.join(PROJECT_ROOT, 'output');
    if (!fs.existsSync(outputDir)) return '';

    const files = fs.readdirSync(outputDir)
      .filter(f => f.endsWith('.md'))
      .map(f => ({
        name: f,
        time: fs.statSync(path.join(outputDir, f)).mtimeMs,
      }))
      .sort((a, b) => b.time - a.time)
      .slice(0, count);

    if (files.length === 0) return '';

    return `最近的 ${files.length} 个产出文件: ${files.map(f => f.name).join(', ')}`;
  } catch {
    return '';
  }
}

function loadRecentSessionSummaries(roleName) {
  // 读取最近 3 条该角色的会话摘要
  try {
    if (!fs.existsSync(SESSIONS_DIR)) return '';

    const files = fs.readdirSync(SESSIONS_DIR)
      .filter(f => f.includes(roleName) && f.endsWith('.jsonl'))
      .sort()
      .reverse()
      .slice(0, 3);

    if (files.length === 0) return '';

    return `存在 ${files.length} 个历史会话文件可回溯`;
  } catch {
    return '';
  }
}

// ============================================================
// 辅助: 检查所有角色信任等级分布
// ============================================================
function listAllTrustLevels() {
  console.log(`\n${'='.repeat(60)}`);
  console.log('  📋 墨境项目 — 全体角色信任等级分布');
  console.log(`${'='.repeat(60)}\n`);

  try {
    const files = fs.readdirSync(TASKS_DIR)
      .filter(f => f.endsWith('.md'))
      .sort();

    const levels = { 1: [], 2: [], 3: [], 4: [], 5: [] };

    for (const file of files) {
      const roleName = file.replace(/\.md$/, '');
      // 跳过微任务文件（它们是子任务，不单独计信任等级）
      if (roleName.includes('微任务')) continue;
      if (roleName.includes('设定')) continue;

      const trustInfo = getTrustLevel(roleName);
      const level = trustInfo.level;

      if (!levels[level]) levels[level] = [];
      levels[level].push({
        name: roleName,
        source: trustInfo.source,
        file: trustInfo.file,
      });
    }

    // 输出汇总表
    console.log('  ┌─────────┬──────────────────────────────────┬──────────┐');
    console.log('  │ 等级    │ 角色名                            │ 来源      │');
    console.log('  ├─────────┼──────────────────────────────────┼──────────┤');

    for (const level of VALID_LEVELS) {
      const roles = levels[level] || [];
      for (let i = 0; i < roles.length; i++) {
        const role = roles[i];
        const levelLabel = i === 0
          ? `L${level} ${TRUST_LEVELS[level].name.padEnd(12)}`
          : ' '.repeat(25);
        console.log(
          `  │ ${levelLabel} │ ${role.name.padEnd(32)} │ ${role.source.padEnd(8)} │`
        );
      }
      if (roles.length > 0) {
        console.log(`  ├─────────┼──────────────────────────────────┼──────────┤`);
      }
    }

    // 汇总统计
    console.log(`\n  📊 统计:`);
    for (const level of VALID_LEVELS) {
      const count = (levels[level] || []).length;
      const pct = ((count / Object.values(levels).flat().length) * 100).toFixed(1);
      console.log(`     ${TRUST_LEVELS[level].name}: ${count} 人 (${pct}%)`);
    }
    console.log(`     总计: ${Object.values(levels).flat().length} 个角色`);

  } catch (err) {
    console.error(`  ❌ 列表读取失败:`, err.message);
  }
}

// ============================================================
// 辅助: 验证所有任务文件的 frontmatter
// ============================================================
function verifyAllFrontmatter() {
  console.log(`\n${'='.repeat(60)}`);
  console.log('  🔍 验证所有任务文件 frontmatter');
  console.log(`${'='.repeat(60)}\n`);

  let total = 0;
  let valid = 0;
  let invalid = [];

  try {
    const files = fs.readdirSync(TASKS_DIR)
      .filter(f => f.endsWith('.md'))
      .sort();

    for (const file of files) {
      const filePath = path.join(TASKS_DIR, file);
      const content = fs.readFileSync(filePath, 'utf-8');
      const fm = extractFrontmatter(content);
      total++;

      if (!fm) {
        invalid.push({ file, issue: '无 YAML frontmatter' });
        console.log(`  ⚠️  ${file}: ⛔ 无 frontmatter`);
        continue;
      }

      if (fm.trustLevel === undefined) {
        invalid.push({ file, issue: '缺少 trustLevel 字段' });
        console.log(`  ⚠️  ${file}: ⚠️ 缺少 trustLevel`);
        continue;
      }

      const level = parseInt(fm.trustLevel, 10);
      if (isNaN(level) || level < 1 || level > 5) {
        invalid.push({ file, issue: `trustLevel=${fm.trustLevel} 无效` });
        console.log(`  ⚠️  ${file}: ❌ trustLevel=${fm.trustLevel} 无效`);
        continue;
      }

      valid++;
      console.log(`  ✅  ${file}: trustLevel=${level} ${TRUST_LEVELS[level].name}`);
    }

    console.log(`\n  📊 结果: ${valid}/${total} 通过, ${invalid.length} 个问题`);
    if (invalid.length > 0) {
      console.log(`\n  ⚠️  需要修复:`);
      for (const { file, issue } of invalid) {
        console.log(`     - ${file}: ${issue}`);
      }
    }
  } catch (err) {
    console.error(`  ❌ 验证失败:`, err.message);
  }
}

// ============================================================
// CI 跳过审计
// ============================================================
function auditCISkip(roleName, level, skippedStages) {
  if (level < 4) {
    console.log(`  ⛔ L${level} 角色无权跳过 CI`);
    return false;
  }

  const logEntry = {
    timestamp: new Date().toISOString(),
    actor: roleName,
    trustLevel: level,
    action: 'CI_SKIP',
    skippedStages,
    reason: `L${level} 特权: 自动跳过非关键 CI 阶段`,
    commitSha: process.env.GITHUB_SHA || 'unknown',
  };

  const logFile = path.join(AUDIT_DIR, 'ci-skip.log');
  try {
    fs.appendFileSync(logFile, JSON.stringify(logEntry) + '\n', 'utf-8');
    console.log(`  ✅ CI 跳过已审计: ${skippedStages.join(', ')}`);
    return true;
  } catch (err) {
    console.error(`  ❌ CI 审计日志失败: ${err.message}`);
    return false;
  }
}

// ============================================================
// 熔断器 — 自动降级
// ============================================================
const circuitBreaker = {
  violations: {},

  MAX_VIOLATIONS: 3,
  COOLDOWN_MS: 24 * 60 * 60 * 1000,  // 24 小时

  recordViolation(roleName, tool, currentLevel) {
    if (!this.violations[roleName]) {
      this.violations[roleName] = [];
    }

    this.violations[roleName].push({
      timestamp: Date.now(),
      tool,
      level: currentLevel,
    });

    // 审计
    auditLog({
      action: 'TOOL_VIOLATION',
      role: roleName,
      tool,
      currentLevel,
    });

    // 检查 24 小时内违规次数
    const recentViolations = this.violations[roleName]
      .filter(v => Date.now() - v.timestamp < this.COOLDOWN_MS);

    console.warn(`  ⚠️  ${roleName} 违规记录: ${recentViolations.length}/${this.MAX_VIOLATIONS}`);

    if (recentViolations.length >= this.MAX_VIOLATIONS) {
      this.downgrade(roleName, 1);
    }
  },

  downgrade(roleName, targetLevel) {
    const taskFile = path.join(TASKS_DIR, `${roleName}.md`);
    if (!fs.existsSync(taskFile)) {
      console.error(`  ❌ 无法降级，任务文件不存在: ${taskFile}`);
      return false;
    }

    try {
      let content = fs.readFileSync(taskFile, 'utf-8');
      const timestamp = new Date().toISOString();

      // 替换或添加 trustLevel
      if (content.includes('trustLevel:')) {
        content = content.replace(
          /^trustLevel:\s*\d+/m,
          `trustLevel: ${targetLevel}  # 🔒 自动降级 ${timestamp}`
        );
      } else {
        // 在文件顶部添加 frontmatter
        content = `---\ntrustLevel: ${targetLevel}  # 🔒 自动降级 ${timestamp}\n---\n\n${content}`;
      }

      fs.writeFileSync(taskFile, content, 'utf-8');

      auditLog({
        action: 'DOWNGRADE',
        role: roleName,
        fromLevel: undefined, // 可以从 violations 推断
        toLevel: targetLevel,
        reason: `连续 ${this.MAX_VIOLATIONS} 次违规，自动降级`,
      });

      console.error(`  🔒 ${roleName} 已自动降级至 L${targetLevel}`);
      return true;
    } catch (err) {
      console.error(`  ❌ 降级失败: ${err.message}`);
      return false;
    }
  },

  getViolationCount(roleName) {
    if (!this.violations[roleName]) return 0;
    return this.violations[roleName]
      .filter(v => Date.now() - v.timestamp < this.COOLDOWN_MS)
      .length;
  },
};

// ============================================================
// CLI 入口
// ============================================================
function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('墨境项目 — bot-runner.js (信任等级驱动)');
    console.log('');
    console.log('用法:');
    console.log('  node bot-runner.js <角色名>             启动角色会话');
    console.log('  node bot-runner.js --check <角色名>     仅检查信任等级');
    console.log('  node bot-runner.js --list               列出所有角色信任等级');
    console.log('  node bot-runner.js --verify             验证所有任务文件 frontmatter');
    console.log('');
    console.log('示例:');
    console.log('  node bot-runner.js "A组-前端技术负责人"');
    console.log('  node bot-runner.js --check "产品经理"');
    console.log('  node bot-runner.js --list');
    console.log('  node bot-runner.js --verify');
    return;
  }

  const command = args[0];

  switch (command) {
    case '--list':
      listAllTrustLevels();
      break;

    case '--verify':
      verifyAllFrontmatter();
      break;

    case '--check':
      if (!args[1]) {
        console.error('用法: node bot-runner.js --check <角色名>');
        process.exit(1);
      }
      {
        const trustInfo = getTrustLevel(args[1]);
        const config = TRUST_LEVELS[trustInfo.level];
        console.log(`\n  📊 ${args[1]}: ${config.name} (L${trustInfo.level})`);
        console.log(`  来源: ${trustInfo.source}`);
        console.log(`  文件: ${trustInfo.file || 'N/A'}`);
        if (trustInfo.frontmatter) {
          console.log(`  元数据:`, JSON.stringify(trustInfo.frontmatter, null, 2));
        }
      }
      break;

    default:
      // 直接启动角色会话
      startRoleSession(command);
      break;
  }
}

// ============================================================
// 执行
// ============================================================
if (require.main === module) {
  main();
}

// ============================================================
// 导出
// ============================================================
module.exports = {
  TRUST_LEVELS,
  DEFAULT_TRUST_LEVEL,
  getTrustLevel,
  extractFrontmatter,
  buildSystemPrompt,
  startRoleSession,
  listAllTrustLevels,
  verifyAllFrontmatter,
  circuitBreaker,
  auditCISkip,
};
