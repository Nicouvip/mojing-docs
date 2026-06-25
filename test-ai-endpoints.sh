#!/usr/bin/env python3
"""
墨境 QA — AI 端点连通性测试
对 6 个 AI 端点分别发送最小 POST body，检查 HTTP 状态码，
输出 PASS/FAIL 并汇总到 test-result.json
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

BASE_URL = os.environ.get("MOJING_BASE_URL", "http://localhost:3000")
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test-result.json")
TIMEOUT = "15"

ENDPOINTS = [
    ("continue",   "/api/ai/continue",   '{"context":"test"}',      200),
    ("polish",     "/api/ai/polish",     '{"text":"测试文字"}',      200),
    ("expand",     "/api/ai/expand",     '{"text":"测试文字"}',      200),
    ("brainstorm", "/api/ai/brainstorm", '{"genre":"都市"}',         200),
    ("inspire",    "/api/ai/inspire",    '{"mode":"direct-diverge"}',200),
    ("alchemy",    "/api/ai/alchemy",    '{"genre":"玄幻"}',         200),
]

def curl_post(url, body, timeout):
    """Run curl POST and return (http_code, response_preview)"""
    try:
        proc = subprocess.run(
            ["curl", "-s", "-w", "%{http_code}", "-o", "-",
             "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", body,
             "--max-time", timeout,
             url],
            capture_output=True, text=True, timeout=int(timeout)+5
        )
        stdout = proc.stdout
        if len(stdout) < 3:
            return ("000", "empty response")
        http_code = stdout[-3:]
        resp_body = stdout[:-3]
        preview = resp_body[:120].replace("\n", " ").strip()
        return (http_code, preview)
    except subprocess.TimeoutExpired:
        return ("000", "timeout")
    except Exception as e:
        return ("000", str(e)[:120])

def main():
    sep = "=" * 67
    print(sep)
    print(f"  墨境 AI 端点连通性测试")
    print(f"  目标: {BASE_URL}")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(sep)
    print()

    # ── Server alive check ──
    print("▸ 服务器存活检查...")
    try:
        r = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "--max-time", "5", f"{BASE_URL}/"],
            capture_output=True, text=True, timeout=10
        )
        if r.stdout.strip() and int(r.stdout.strip()) < 500:
            print(f"  ✅ 服务器运行中 ({BASE_URL})")
        else:
            raise RuntimeError(f"HTTP {r.stdout.strip()}")
    except Exception as e:
        print(f"  ❌ 服务器不可达 ({BASE_URL}): {e} — 终止测试")
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "baseUrl": BASE_URL,
                "serverAlive": False,
                "total": 0, "passed": 0, "failed": 0,
                "results": [],
                "summary": "SERVER_UNREACHABLE"
            }, f, ensure_ascii=False, indent=2)
        sys.exit(1)
    print()

    # ── Test 6 endpoints ──
    print("▸ 测试 6 个 AI 端点...")
    print()

    results = []
    total = passed = failed = 0

    for name, path, body, expected in ENDPOINTS:
        total += 1
        url = f"{BASE_URL}{path}"
        http_code, preview = curl_post(url, body, TIMEOUT)

        if http_code == str(expected):
            status = "PASS"
            passed += 1
            detail = f"HTTP {http_code}"
        else:
            status = "FAIL"
            failed += 1
            detail = f"expected HTTP {expected}, got HTTP {http_code} — {preview}"

        print(f"{status:4s} | {name} ({path}) → {detail}")

        results.append({
            "name": name,
            "path": path,
            "method": "POST",
            "body": body,
            "expectedStatus": expected,
            "actualStatus": int(http_code) if http_code.isdigit() else 0,
            "result": status,
            "detail": detail
        })

        time.sleep(0.3)

    # ── Summary ──
    print()
    print(sep)
    summary = "ALL_PASS" if failed == 0 else "SOME_FAIL"
    print(f"  测试完成")
    print(f"  总计: {total}  |  PASS: {passed}  |  FAIL: {failed}")
    print(sep)
    print()

    output = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "baseUrl": BASE_URL,
        "serverAlive": True,
        "total": total,
        "passed": passed,
        "failed": failed,
        "summary": summary,
        "results": results
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"结果已保存到: {OUTPUT_PATH}")
    sys.exit(failed)

if __name__ == "__main__":
    main()
