#!/usr/bin/env python3
"""
墨境 自动化回归脚本
=====================
基于 curl 的 HTTP 状态检查，零 UI 交互。
检查项：
  - 关键页面 GET 200
  - 核心 API 端点正确方法 200
输出 PASS/FAIL 计分表，结果写入 regression-last.json
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime

# ── 配置 ──────────────────────────────────────────────────────────────
BASE_URL = os.environ.get("MOJING_BASE_URL", "http://localhost:3000")
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "regression-last.json")
CURL_TIMEOUT = 15          # 单次 curl 超时秒数
CURL_RETRIES = 1           # 失败重试次数
REQUEST_DELAY = 0.3        # 请求间延迟（秒），避免压垮 dev server

# ── 检查清单 ──────────────────────────────────────────────────────────
PAGE_CHECKS = [
    ("首页",         "/",                  "GET"),
    ("登录页",       "/login",             "GET"),
    ("书桌",         "/desk",              "GET"),
    ("后台",         "/admin",             "GET"),
    ("页面编辑器",   "/page-editor.html?path=/", "GET"),
]

API_CHECKS = [
    ("AI 布局 API",          "/api/ai/layout",       "POST",  '{"prompt":"测试页面"}'),
    ("工具广场元数据 API",   "/api/tools",              "GET",   None),
    ("风格规则中心 API",     "/api/rules/styles",       "GET",   None),
]

# ── 工具函数 ──────────────────────────────────────────────────────────

def curl_check(method: str, path: str, body: str = None, retries: int = CURL_RETRIES) -> tuple:
    """
    执行 curl 请求，返回 (http_code, elapsed_seconds) 或 (None, error_msg)。
    自动处理网络级失败和超时。
    """
    url = f"{BASE_URL}{path}"
    cmd = [
        "curl", "-s", "-o", "NUL",
        "-w", "%{http_code}",
        "--max-time", str(CURL_TIMEOUT),
    ]
    if method == "POST":
        cmd += ["-X", "POST"]
        cmd += ["-H", "Content-Type: application/json"]
        if body:
            cmd += ["-d", body]
    cmd.append(url)

    last_error = None
    for attempt in range(1 + retries):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=CURL_TIMEOUT + 2
            )
            code_str = result.stdout.strip()
            if code_str and code_str.isdigit():
                http_code = int(code_str)
                # curl 退出码 !=0 说明网络级失败，即使 stdout 有数字也标记为错误
                if result.returncode != 0 and http_code == 0:
                    last_error = result.stderr.strip() or f"curl exit {result.returncode}"
                    if attempt < retries:
                        time.sleep(1)
                        continue
                    return None, last_error
                return http_code, None
            # curl 可能输出错误到 stderr
            err = result.stderr.strip() or "empty response"
            last_error = err
        except subprocess.TimeoutExpired:
            last_error = "TIMEOUT"
        except FileNotFoundError:
            last_error = "curl not found in PATH"
            break  # 无重试意义
        except Exception as e:
            last_error = str(e)

        if attempt < retries:
            time.sleep(1)

    return None, last_error


def run_checks() -> list:
    """执行全部检查，返回结果列表。"""
    results = []

    # ── 页面检查 ──
    for label, path, method in PAGE_CHECKS:
        code, err = curl_check(method, path)
        passed = code == 200
        results.append({
            "type": "page",
            "label": label,
            "path": path,
            "method": method,
            "expected": 200,
            "actual": code,
            "passed": passed,
            "error": err,
        })
        _print_result(label, "PAGE", method, code, passed, err)
        time.sleep(REQUEST_DELAY)

    # ── API 检查 ──
    for label, path, method, body in API_CHECKS:
        code, err = curl_check(method, path, body)
        passed = code == 200
        results.append({
            "type": "api",
            "label": label,
            "path": path,
            "method": method,
            "body": body,
            "expected": 200,
            "actual": code,
            "passed": passed,
            "error": err,
        })
        _print_result(label, "API", method, code, passed, err)
        time.sleep(REQUEST_DELAY)

    return results


def _print_result(label: str, kind: str, method: str, code, passed: bool, err: str = None):
    """打印单行检查结果。"""
    method_str = method.ljust(4)
    if passed:
        mark = "✅ PASS"
        detail = f"HTTP {code}"
    elif code is not None:
        mark = "❌ FAIL"
        detail = f"HTTP {code} (期望 200)"
    else:
        mark = "💥 FAIL"
        detail = err or "连接失败"
    print(f"  [{kind:5s}] {mark}  {label:<18s}  {method_str}  {path_summary(detail)}")


def path_summary(s: str) -> str:
    """截断过长消息以便对齐显示。"""
    return s if len(s) < 60 else s[:57] + "..."


# ── 主流程 ────────────────────────────────────────────────────────────

def main():
    print(f"╔══════════════════════════════════════════════════════════╗")
    print(f"║       墨境 · 自动化回归检查                              ║")
    print(f"║       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                  ║")
    print(f"║       目标: {BASE_URL}         ║")
    print(f"╚══════════════════════════════════════════════════════════╝")
    print()

    # ── 环境预检 ──
    try:
        subprocess.run(["curl", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ curl 不可用，请安装 curl 或将其加入 PATH。")
        sys.exit(1)

    # ── 连通性预检 ──
    print(f"🔍 连通性预检 → {BASE_URL}")
    code, err = curl_check("GET", "/", retries=0)
    if code != 200:
        print(f"   ⚠️  首页返回 {code}，服务器可能未启动，继续检查…")
    else:
        print(f"   ✅ 服务器可达")
    print()

    # ── 执行全部检查 ──
    print("📋 开始检查\n")
    start = time.time()
    results = run_checks()
    elapsed = time.time() - start

    # ── 统计 ──
    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    failed = [r for r in results if not r["passed"]]
    score = round(passed_count / total * 100, 1) if total else 0

    print()
    print(f"{'='*58}")
    print(f"  计分汇总")
    print(f"{'='*58}")
    print(f"  总计: {total} 项")
    print(f"  ✅ PASS: {passed_count}")
    print(f"  ❌ FAIL: {len(failed)}")
    print(f"  🎯 得分: {score}%")
    print(f"  ⏱  耗时: {elapsed:.1f}s")
    print()

    if failed:
        print(f"  ── 失败明细 ──")
        for r in failed:
            method = r.get("method", "GET")
            detail = r.get("error") or f"HTTP {r['actual']}"
            print(f"    ❌ [{r['type'].upper()}] {r['label']:<16s}  {method}  {detail}")
        print()

    # ── 保存结果 ──
    report = {
        "title": "墨境自动化回归检查",
        "timestamp": datetime.now().isoformat(),
        "base_url": BASE_URL,
        "summary": {
            "total": total,
            "passed": passed_count,
            "failed": len(failed),
            "score_pct": score,
            "elapsed_seconds": round(elapsed, 2),
        },
        "checks": results,
    }

    try:
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"  💾 结果已保存 → {OUTPUT_PATH}")
    except Exception as e:
        print(f"  ❌ 保存失败: {e}")

    # ── 退出码 ──
    sys.exit(0 if passed_count == total else 1)


if __name__ == "__main__":
    main()
