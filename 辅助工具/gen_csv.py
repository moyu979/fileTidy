#!/usr/bin/env python3
# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 临时脚本 - CSV 文件生成器

"""
独立工具 —— 遍历文件夹，生成 fileTidy 所需的 CSV 文件。

输出 CSV 列: sha512, md5, size, path
  - sha512: SHA-512 十六进制摘要
  - md5:    MD5 十六进制摘要
  - size:   文件大小（字节）
  - path:   文件的绝对路径

本脚本仅依赖 Python 标准库，可独立复制到任何地方使用。
"""
# TODO(P2): 此文件位于 临时工具/ 目录下，应移入 scripts/ 目录并清理中文目录名

import hashlib
import csv
import os
import sys
from pathlib import Path

# 每次读取的块大小（字节），可通过环境变量 `GEN_CSV_CHUNK` 调整
# 推荐默认值 4MiB：在大多数场景下能平衡系统调用和内存占用。
DEFAULT_CHUNK = 512 * 1024 * 1024
try:
    CHUNK_SIZE = int(os.environ.get("GEN_CSV_CHUNK", DEFAULT_CHUNK))
except Exception:
    CHUNK_SIZE = DEFAULT_CHUNK


def sha512_of(path: str) -> str:
    """计算文件的 SHA-512 摘要。

    Args:
        path: 文件路径。

    Returns:
        文件的 SHA-512 十六进制摘要字符串。
    """
    h = hashlib.sha512()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()


def md5_of(path: str) -> str:
    """计算文件的 MD5 摘要。

    Args:
        path: 文件路径。

    Returns:
        文件的 MD5 十六进制摘要字符串。
    """
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_csv(target_dir: str, output_path: str) -> int:
    """遍历目标目录，为每个文件计算哈希并写入 CSV 文件。

    Args:
        target_dir: 要扫描的目标目录路径。
        output_path: 输出 CSV 文件路径。

    Returns:
        处理的文件总数。

    Raises:
        SystemExit: 如果目标路径不存在或不是目录则退出。
    """
    target = Path(target_dir).resolve()
    if not target.is_dir():
        print(f"错误: 路径不存在或不是目录: {target}")
        sys.exit(1)

    files = sorted([p for p in target.rglob("*") if p.is_file()])
    if not files:
        print(f"未找到文件: {target}")
        return 0

    total_size = sum(p.stat().st_size for p in files)
    processed_size = 0
    processed_count = 0

    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["sha512", "md5", "size", "path"])
        writer.writeheader()

        print(f"正在扫描: {target}")
        first = True
        bar_len = 40
        for fpath in files:
            abs_path = str(fpath)
            size = fpath.stat().st_size

            if first:
                print(abs_path)
                prev_percent = processed_size / total_size if total_size else 1.0
                filled = int(prev_percent * bar_len)
                bar = "[" + "#" * filled + "-" * (bar_len - filled) + "]"
                print(f"{bar} {prev_percent*100:6.2f}%")
                first = False
            else:
                # 上一次输出占两行，向上移动两行并覆盖
                print("\x1b[2A", end="")
                print("\x1b[2K" + abs_path)
                prev_percent = processed_size / total_size if total_size else 1.0
                filled = int(prev_percent * bar_len)
                bar = "[" + "#" * filled + "-" * (bar_len - filled) + "]"
                print("\x1b[2K" + f"{bar} {prev_percent*100:6.2f}%")
            sys.stdout.flush()

            # 单次读取文件，同时计算 sha512 和 md5（节省 I/O 成本）
            sha_h = hashlib.sha512()
            md5_h = hashlib.md5()
            with open(abs_path, "rb") as fh:
                for chunk in iter(lambda: fh.read(CHUNK_SIZE), b""):
                    sha_h.update(chunk)
                    md5_h.update(chunk)
            sha = sha_h.hexdigest()
            md5 = md5_h.hexdigest()

            writer.writerow({
                "sha512": sha,
                "md5": md5,
                "size": str(size),
                "path": abs_path,
            })

            processed_size += size
            processed_count += 1
            percent = processed_size / total_size if total_size else 1.0
            filled = int(percent * bar_len)
            new_bar = "[" + "#" * filled + "-" * (bar_len - filled) + "]"
            # 更新进度条行（向上移动一行覆盖进度行）
            print("\x1b[1A", end="")
            print("\x1b[2K" + f"{new_bar} {percent*100:6.2f}%")
            sys.stdout.flush()

    # 输出空行，确保光标移到进度显示下方
    print()

    print(f"\n完成! 共 {processed_count} 个文件，已写入: {out}")
    return processed_count


def main() -> None:
    """gen_csv 工具的主入口函数。

    支持命令行参数模式和交互式输入模式，遍历指定目录生成包含
    sha512、hash、size、path 列的 CSV 文件。
    """
    if len(sys.argv) == 3:
        target_dir = sys.argv[1].strip()
        memo = sys.argv[2].strip()
    else:
        print("用法: python gen_csv.py <目录路径> <CSV助记名>")
        print("未提供参数，回退到人工输入模式——\n")
        target_dir = input("请输入要扫描的文件夹路径: ").strip()
        memo = input("请输入助记词（用作 CSV 文件名）: ").strip()

    if not target_dir:
        print("错误: 路径不能为空。")
        sys.exit(1)

    if not os.path.isdir(target_dir):
        print(f"错误: 路径不存在或不是目录: {target_dir}")
        sys.exit(1)

    if not memo:
        print("错误: 助记词不能为空。")
        sys.exit(1)

    # 输出到当前目录
    output_path = Path.cwd() / f"{memo}.csv"
    generate_csv(target_dir, output_path)


if __name__ == "__main__":
    main()
