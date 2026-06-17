#!/usr/bin/env python3
"""
独立工具 —— 遍历文件夹，生成 fileTidy 所需的 CSV 文件。

输出 CSV 列: sha256, hash, size, path
  - sha256: SHA-256 十六进制摘要
  - hash:   MD5 十六进制摘要
  - size:   文件大小（字节）
  - path:   文件的绝对路径

本脚本仅依赖 Python 标准库，可独立复制到任何地方使用。
"""

import hashlib
import csv
import os
import sys
from pathlib import Path


def sha256_of(path: str) -> str:
    """计算文件的 SHA-256 摘要。"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def md5_of(path: str) -> str:
    """计算文件的 MD5 摘要。"""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_csv(target_dir: str, output_path: str) -> int:
    """遍历 target_dir，为每个文件计算哈希并写入 CSV。返回处理的文件数。"""
    target = Path(target_dir).resolve()
    if not target.is_dir():
        print(f"错误: 路径不存在或不是目录: {target}")
        sys.exit(1)

    rows: list[dict[str, str]] = []

    print(f"正在扫描: {target}")
    for fpath in sorted(target.rglob("*")):
        if not fpath.is_file():
            continue
        abs_path = str(fpath)
        print(f"  处理: {abs_path}")
        rows.append(
            {
                "sha256": sha256_of(abs_path),
                "hash": md5_of(abs_path),
                "size": str(fpath.stat().st_size),
                "path": abs_path,
            }
        )

    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["sha256", "hash", "size", "path"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n完成! 共 {len(rows)} 个文件，已写入: {out}")
    return len(rows)


def main() -> None:
    target_dir = input("请输入要扫描的文件夹路径: ").strip()
    if not target_dir:
        print("错误: 路径不能为空。")
        sys.exit(1)

    if not os.path.isdir(target_dir):
        print(f"错误: 路径不存在或不是目录: {target_dir}")
        sys.exit(1)

    memo = input("请输入助记词（用作 CSV 文件名）: ").strip()
    if not memo:
        print("错误: 助记词不能为空。")
        sys.exit(1)

    # 输出到当前目录
    output_path = Path.cwd() / f"{memo}.csv"
    generate_csv(target_dir, output_path)


if __name__ == "__main__":
    main()
