"""
墨境 CI 统一门禁（合并增强版）
==============================
合并 ci-gate.py + auto-regression.py，新增 tsc --noEmit + pnpm lint。

执行流水线：
  1. pnpm lint          — ESLint 代码风格检查
  2. tsc --noEmit       — TypeScript 类型检查（提前阻断）
  3. pnpm build         — Next.js 生产构建
  4. .next/ 产出检查     — 关键产物完整性
  5. 合并冲突扫描        — Git 冲突标记检测
  6. HTTP 回归检查       — curl 页面+API 端点 200 验证

任一阶段失败 → decisions.jsonl 告警 → sys.exit(1)

用法：
  python ci-gate.py               # 全量流水线
  python ci-gate.py --skip-build  # 跳过构建（仅 lint + typecheck + 回归）
  python ci-gate.py --status      # 查看上次结果
"""

import json
import os
import re
import subprocess
import sys
import time
import datetime
from pathlib import Path
from typing import Optional

# ─── 路径配置 ─────────────────────────────────────────────
APP_DIR = Path("D:/建网站/mojing-app")
DOCS_DIR = Path("D:/建网站/mojing-docs")
RESULT_FILE = DOCS_DIR / "ci-last-result.json"
DECISIONS_FILE = DOCS_DIR / "context" / "decisions.jsonl"

# Next.js 构建后必须存在的关键文件
ESSENTIAL_OUTPUTS = [
    ".next/BUILD_ID",
    ".next/build-manifest.json",
    ".next/routes-manifest.json",
    ".next/prerender-manifest.json",
]

# 合并冲突标记正则
CONFLICT_PATTERN = re.compile(r"^(<<<<<<< |=======$|>>>>>>> )", re.MULTILINE)

# HTTP 回归配置
BASE_URL = os.environ.get("MOJING_BASE_URL", "http://localhost:3000")
CURL_TIMEOUT = 15
REQUEST_DELAY = 0.3

PAGE_CHECKS = [
    ("首页",       "/",                        "GET"),
    ("登录页",     "/login",                   "GET"),
    ("书桌",       "/desk",                    "GET"),
    ("后台",       "/admin",                   "GET"),
    ("页面编辑器",  "/page-editor.html?path=/", "GET"),
]

API_CHECKS = [
    ("AI 布局 API",        "/api/ai/layout",       "POST",  '{"prompt":"测试页面"}'),
    ("工具广场元数据 API",  "/api/tools",            "GET",   None),
    ("风格规则中心 API",    "/api/rules/styles",     "GET",   None),
]


# ─── 工具函数 ─────────────────────────────────────────────

def timestamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def step_header(emoji: str, title: str):
    """打印步骤分隔线"""
    print(f"\n{'='*50}")
    print(f"{emoji} {title}")
    print(f"{'='*50}\n")


def run_command(cmd: list, cwd: Path, timeout: int, label: str
                ) -> tuple[bool, str, Optional[str]]:
    """
    执行 shell 命令，返回 (成功?, 摘要消息, 完整输出)
    自动截取过长输出。
    """
    try:
        result = subprocess.run(
            cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout,
        )
        output = result.stdout + ("\n" + result.stderr if result.stderr else "")
        ok = result.returncode == 0
        icon = "✅" if ok else "❌"
        msg = f"{icon} {label} (exit {result.returncode})"

        # 打印截断输出
        lines = output.splitlines()
        show = lines[-25:] if len(lines) > 25 else lines
        if len(lines) > 25:
            print(f"... (省略 {len(lines)-25} 行) ...")
        for l in show:
            print(f"  {l}")

        return ok, msg, output
    except subprocess.TimeoutExpired:
        print(f"  ⏰ 超时 ({timeout}s)")
        return False, f"❌ {label} 超时 ({timeout}s)", None
    except FileNotFoundError:
        # 命令不存在
        cmd_str = cmd[0]
        print(f"  ⚠️  '{cmd_str}' 未安装或不在 PATH 中")
        return False, f"⚠️ {label}: '{cmd_str}' 不可用", None
    except Exception as e:
        print(f"  💥 异常: {e}")
        return False, f"💥 {label}: {e}", None


# ─── 步骤实现 ─────────────────────────────────────────────

def step_lint() -> tuple[bool, str]:
    """① pnpm lint — ESLint 代码风格检查"""
    step_header("🧹", "步骤 1/6: pnpm lint (ESLint)")
    if not (APP_DIR / "eslint.config.mjs").exists():
        return True, "⏭️  无 eslint.config.mjs，跳过 lint"
    return run_command(
        ["pnpm", "lint"], APP_DIR, 120, "pnpm lint"
    )[:2]


def step_typecheck() -> tuple[bool, str]:
    """② tsc --noEmit — TypeScript 类型检查"""
    step_header("🔍", "步骤 2/6: tsc --noEmit (类型检查)")
    return run_command(
        ["npx", "tsc", "--noEmit"], APP_DIR, 120, "tsc --noEmit"
    )[:2]


def step_build() -> tuple[bool, str]:
    """③ pnpm build — Next.js 生产构建"""
    step_header("📦", "步骤 3/6: pnpm build")
    if not (APP_DIR / "package.json").exists():
        return False, f"[错误] 未找到 {APP_DIR / 'package.json'}"
    return run_command(
        ["pnpm", "build"], APP_DIR, 300, "pnpm build"
    )[:2]


def step_output_files() -> tuple[bool, list[str]]:
    """④ 检查 .next/ 关键产出文件"""
    step_header("📂", "步骤 4/6: 检查产出文件")
    missing = []
    for rel in ESSENTIAL_OUTPUTS:
        f = APP_DIR / rel
        if not f.exists():
            missing.append(rel)
    if not missing:
        print("✅ 所有关键产出文件存在")
        return True, []
    print(f"❌ 缺失 {len(missing)} 个文件:")
    for m in missing:
        print(f"   • {m}")
    return False, missing


def step_merge_conflicts() -> tuple[bool, list[str]]:
    """⑤ 检查 Git 合并冲突标记"""
    step_header("🔍", "步骤 5/6: 检查合并冲突")
    try:
        result = subprocess.run(
            ["git", "ls-files"], cwd=str(APP_DIR),
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return True, []

        SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".ttf",
                     ".woff", ".woff2", ".eot", ".svg", ".lock", ".tsbuildinfo"}
        conflicted = []

        for rel in result.stdout.strip().splitlines():
            ext = Path(rel).suffix.lower()
            if ext in SKIP_EXT:
                continue
            abspath = APP_DIR / rel
            if not abspath.exists():
                continue
            try:
                content = abspath.read_text(encoding="utf-8", errors="ignore")
                matches = CONFLICT_PATTERN.findall(content)
                if matches:
                    counts = {}
                    for m in matches:
                        tag = m.strip().split()[0] if m.strip() else m.strip()
                        counts[tag] = counts.get(tag, 0) + 1
                    conflicted.append(
                        f"{rel} ({', '.join(f'{k}×{v}' for k, v in counts.items())})"
                    )
            except Exception:
                continue

        if not conflicted:
            print("✅ 无未解决的合并冲突")
            return True, []
        print(f"❌ 发现 {len(conflicted)} 个文件含冲突标记:")
        for c in conflicted:
            print(f"   • {c}")
        return False, conflicted

    except subprocess.TimeoutExpired:
        return False, ["git ls-files 超时"]
    except FileNotFoundError:
        return False, ["git 不可用"]
    except Exception as e:
        return False, [f"检查冲突时出错: {e}"]


def curl_check(method: str, path: str, body: str = None) -> tuple:
    """执行 curl 请求，返回 (http_code, error)"""
    url = f"{BASE_URL}{path}"
    cmd = [
        "curl", "-s", "-o", "NUL",
        "-w", "%{http_code}",
        "--max-time", str(CURL_TIMEOUT),
    ]
    if method == "POST":
        cmd += ["-X", "POST", "-H", "Content-Type: application/json"]
        if body:
            cmd += ["-d", body]
    cmd.append(url)

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=CURL_TIMEOUT + 2
        )
        code_str = result.stdout.strip()
        if code_str and code_str.isdigit():
            http_code = int(code_str)
            if result.returncode != 0 and http_code == 0:
                return None, result.stderr.strip() or f"curl exit {result.returncode}"
            return http_code, None
        return None, result.stderr.strip() or "empty response"
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT"
    except FileNotFoundError:
        return None, "curl not found in PATH"
    except Exception as e:
        return None, str(e)


def step_regression() -> tuple[bool, list[dict]]:
    """⑥ HTTP 回归检查（页面 + API）"""
    step_header("🌐", "步骤 6/6: HTTP 回归检查")
    results = []
    failed_count = 0
    MAX_FAILURES = 3  # 快速失败：连续 3 项失败则中止

    def _check(label: str, kind: str, method: str, path: str, body: str = None):
        nonlocal failed_count
        code, err = curl_check(method, path, body)
        passed = code == 200
        icon = "✅" if passed else "❌"
        detail = f"HTTP {code}" if code else (err or "连接失败")
        print(f"  [{kind:5s}] {icon}  {label:<18s}  {method:<4s}  {detail}")
        results.append({
            "type": kind.lower(), "label": label, "path": path,
            "method": method, "expected": 200, "actual": code,
            "passed": passed, "error": err,
        })
        if not passed:
            failed_count += 1
        time.sleep(REQUEST_DELAY)

    # 连通性预检
    print(f"🔍 连通性预检 → {BASE_URL}")
    code, err = curl_check("GET", "/")
    if code != 200:
        print(f"   ⚠️  首页返回 {code}，服务器可能未启动")
    else:
        print(f"   ✅ 服务器可达")
    print()

    # 页面检查
    for label, path, method in PAGE_CHECKS:
        _check(label, "PAGE", method, path)
        if failed_count >= MAX_FAILURES:
            print(f"\n   ⛔ 连续 {MAX_FAILURES} 项失败，中止回归")
            break

    # API 检查
    if failed_count < MAX_FAILURES:
        for label, path, method, body in API_CHECKS:
            _check(label, "API", method, path, body)
            if failed_count >= MAX_FAILURES:
                print(f"\n   ⛔ 连续 {MAX_FAILURES} 项失败，中止回归")
                break

    # 统计
    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    all_pass = failed_count == 0
    score = round(passed_count / total * 100, 1) if total else 0
    print(f"\n   📊 回归得分: {passed_count}/{total} = {score}%")
    if not all_pass:
        print(f"\n  ── 失败明细 ──")
        for r in results:
            if not r["passed"]:
                detail = r.get("error") or f"HTTP {r['actual']}"
                print(f"    ❌ [{r['type'].upper()}] {r['label']:<16s}  {r['method']}  {detail}")

    return all_pass, results


# ─── 结果写入 ─────────────────────────────────────────────

def write_result(passed: bool, details: dict):
    """写入 ci-last-result.json"""
    result = {
        "passed": passed,
        "status": "PASS" if passed else "FAIL",
        "timestamp": timestamp(),
        "details": details,
    }
    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULT_FILE.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n📄 结果已写入: {RESULT_FILE}")


def append_decision(role: str, decision: str, reasoning: str):
    """失败时追加决策到 decisions.jsonl（与 cluster.py log_decision 格式一致）"""
    DECISIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "role": role,
        "decision": decision,
        "reasoning": reasoning,
        "timestamp": timestamp(),
    }
    with open(DECISIONS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"📝 告警已记录: {DECISIONS_FILE}")


def show_last_status():
    """显示上次门禁结果"""
    if not RESULT_FILE.exists():
        print("ℹ️  尚无上次门禁结果")
        return
    try:
        data = json.loads(RESULT_FILE.read_text(encoding="utf-8"))
        status_icon = "✅" if data.get("passed") else "❌"
        print(f"\n{status_icon} 上次门禁: {data['status']} (at {data.get('timestamp', '?')})")
        for key, val in data.get("details", {}).items():
            if isinstance(val, list):
                if val:
                    print(f"   ├─ {key}:")
                    for item in val:
                        print(f"   │  • {item}")
                else:
                    print(f"   ├─ {key}: ✅ 无问题")
            elif isinstance(val, dict):
                # regression 详情
                print(f"   ├─ {key}:")
                for k2, v2 in val.items():
                    if k2 == "checks":
                        print(f"   │  • {k2}: {len(v2)} 项")
                    else:
                        print(f"   │  • {k2}: {v2}")
            else:
                print(f"   ├─ {key}: {val}")
    except Exception as e:
        print(f"⚠️  读取上次结果失败: {e}")


# ─── 主流程 ───────────────────────────────────────────────

def main():
    skip_build = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "--skip-build":
            skip_build = True
        elif sys.argv[1] == "--status":
            show_last_status()
            return
        elif sys.argv[1] in ("--help", "-h"):
            print(__doc__)
            return
        else:
            print(f"未知参数: {sys.argv[1]}")
            print(__doc__)
            sys.exit(1)

    print("🌙 墨境 CI 统一门禁（合并增强版）")
    print("=" * 50)
    print(f"    时间: {timestamp()}")
    print(f"    项目: {APP_DIR}")
    print(f"    回归基址: {BASE_URL}")
    print("=" * 50)

    details = {}
    errors = []
    passed = True

    # ── 步骤 1: pnpm lint ──
    lint_ok, lint_msg = step_lint()
    details["lint"] = lint_msg
    if not lint_ok:
        errors.append(f"lint 失败: {lint_msg}")
        # lint 失败，立即阻断（代码风格问题需就地修复）
        write_result(False, details)
        append_decision(
            role="CI门禁",
            decision="流水线阻断 — ESLint 检查未通过",
            reasoning="代码风格/规范问题，需修复后重新提交",
        )
        sys.exit(1)

    # ── 步骤 2: tsc --noEmit ──
    tc_ok, tc_msg = step_typecheck()
    details["typecheck"] = tc_msg
    if not tc_ok:
        errors.append(f"类型检查失败: {tc_msg}")
        write_result(False, details)
        append_decision(
            role="CI门禁",
            decision="流水线阻断 — TypeScript 类型检查未通过",
            reasoning=f"类型错误，需修复。\n  • {tc_msg}",
        )
        sys.exit(1)

    # ── 步骤 3: pnpm build ──
    if skip_build:
        print("\n⏭️  跳过构建 (--skip-build)")
        details["build"] = "已跳过"
    else:
        build_ok, build_msg = step_build()
        details["build"] = build_msg
        if not build_ok:
            errors.append(f"构建失败: {build_msg}")
            passed = False  # 继续检查后续，收集完整报告

    # ── 步骤 4: 检查产出文件 ──
    if skip_build:
        details["output_files"] = "已跳过（因 --skip-build）"
    else:
        output_ok, missing = step_output_files()
        if not output_ok:
            errors.append(f"产出文件缺失: {', '.join(missing)}")
            passed = False
        details["output_files"] = missing if not output_ok else "✅ 完整"

    # ── 步骤 5: 检查合并冲突 ──
    conflict_ok, conflicted = step_merge_conflicts()
    if not conflict_ok:
        errors.append(f"合并冲突: {', '.join(conflicted[:10])}" +
                       (f"…(还有 {len(conflicted)-10} 个)" if len(conflicted) > 10 else ""))
        passed = False
    details["merge_conflicts"] = conflicted if not conflict_ok else "✅ 无"

    # ── 步骤 6: HTTP 回归检查 ──
    reg_ok, reg_results = step_regression()
    if not reg_ok:
        failed_reg = [r for r in reg_results if not r["passed"]]
        errors.append(f"回归检查失败: {len(failed_reg)} 项未通过")
        passed = False
    details["regression"] = {
        "total": len(reg_results),
        "passed": sum(1 for r in reg_results if r["passed"]),
        "score": round(sum(1 for r in reg_results if r["passed"]) / len(reg_results) * 100, 1)
        if reg_results else 0,
        "checks": reg_results,
    }

    # ── 输出结果 ──
    print(f"\n{'='*50}")
    verdict = "✅ PASS" if passed else "❌ FAIL"
    print(f"🏁 门禁判定: {verdict}")
    print(f"{'='*50}\n")

    write_result(passed, details)

    if not passed:
        reasoning = f"CI 门禁未通过，共 {len(errors)} 项问题:\n" + "\n".join(f"  • {e}" for e in errors)
        append_decision(
            role="CI门禁",
            decision=f"流水线{'完成但检查失败' if not skip_build and 'build' in details and details['build'].startswith('✅') else '阻断'} — {len(errors)} 项问题",
            reasoning=reasoning,
        )
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
