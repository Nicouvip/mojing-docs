#!/usr/bin/env python3
"""auto-backup.py — 每周自动打包 mojing-app + mojing-docs 到备份目录。

可被 Windows 任务计划程序直接调用（无交互）。
用法:
    python auto-backup.py                     # 完整备份（app + docs）
    python auto-backup.py --app-only           # 仅备份 mojing-app
    python auto-backup.py --docs-only          # 仅备份 mojing-docs
"""

import argparse
import datetime
import os
import shutil
import sys
import tarfile
from pathlib import Path


# ── 路径常量 ──────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent  # D:\建网站
APP_DIR = BASE_DIR / "mojing-app"
DOCS_DIR = BASE_DIR / "mojing-docs"
BACKUP_DIR = BASE_DIR / "backups" / "auto"


def now_str() -> str:
    """返回 YYYYMMDD-HHmmss 格式的时间字符串。"""
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def make_tar_gz(source_dir: Path, archive_path: str) -> int:
    """将 source_dir 打包为 .tar.gz，返回文件大小（字节）。"""
    source_str = str(source_dir)
    arcname = source_dir.name  # 归档内直接用目录名，不含父路径

    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(source_str, arcname=arcname)

    return os.path.getsize(archive_path)


def backup_single(name: str, source: Path, suffix: str = "") -> str | None:
    """备份单个目录，返回归档文件路径，失败返回 None。"""
    if not source.is_dir():
        print(f"  ⚠ 跳过 {name}：目录不存在 → {source}")
        return None

    ts = now_str()
    tag = f"-{suffix}" if suffix else ""
    archive_name = f"mojing-{name}-backup-{ts}{tag}.tar.gz"
    archive_path = str(BACKUP_DIR / archive_name)

    print(f"  📦 {name}: {source}")
    size = make_tar_gz(source, archive_path)
    print(f"  ✅ → {archive_name}  ({_fmt_size(size)})")
    return archive_path


def backup_combined(app_ok: bool, docs_ok: bool) -> str | None:
    """将 mojing-app + mojing-docs 合并打到一个包。"""
    ts = now_str()
    archive_name = f"mojing-full-backup-{ts}.tar.gz"
    archive_path = str(BACKUP_DIR / archive_name)

    with tarfile.open(archive_path, "w:gz") as tar:
        if app_ok:
            tar.add(str(APP_DIR), arcname=APP_DIR.name)
        if docs_ok:
            tar.add(str(DOCS_DIR), arcname=DOCS_DIR.name)

    size = os.path.getsize(archive_path)
    print(f"  ✅ → {archive_name}  ({_fmt_size(size)})")
    return archive_path


def _fmt_size(size: int) -> str:
    """人性化文件大小。"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024**2:
        return f"{size / 1024:.1f} KB"
    elif size < 1024**3:
        return f"{size / 1024**2:.1f} MB"
    else:
        return f"{size / 1024**3:.2f} GB"


def main():
    parser = argparse.ArgumentParser(description="墨境DevOps — 自动备份")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--app-only", action="store_true", help="仅备份 mojing-app")
    group.add_argument("--docs-only", action="store_true", help="仅备份 mojing-docs")
    args = parser.parse_args()

    # 确保备份目录存在
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    print(f"🕒 {now_str()}  备份目标: {BACKUP_DIR}\n")

    # 检查源目录
    app_ok = APP_DIR.is_dir()
    docs_ok = DOCS_DIR.is_dir()

    if not app_ok and not docs_ok:
        print("❌ 错误: mojing-app 和 mojing-docs 都不存在，无法备份。")
        sys.exit(1)

    if args.app_only:
        backup_single("app", APP_DIR)
    elif args.docs_only:
        backup_single("docs", DOCS_DIR)
    else:
        # 完整备份：合并为一个包
        print(f"  📂 {APP_DIR.name}  {'✓' if app_ok else '✗'}")
        print(f"  📂 {DOCS_DIR.name}  {'✓' if docs_ok else '✗'}\n")
        backup_combined(app_ok, docs_ok)

    # 清理：保留最近 30 天的备份，删除更旧的
    print("\n🧹 清理 30 天前的旧备份...")
    cutoff = datetime.datetime.now() - datetime.timedelta(days=30)
    cleaned = 0
    for f in BACKUP_DIR.glob("mojing-*-backup-*.tar.gz"):
        mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime)
        if mtime < cutoff:
            f.unlink()
            cleaned += 1
    print(f"  已清理 {cleaned} 个旧文件。\n")

    print("✅ 备份完成。")


if __name__ == "__main__":
    main()
