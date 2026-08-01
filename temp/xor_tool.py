# CHECK: 临时工具 - 独立 XOR 入口：现场构造 dict 配置，调用 FileXor
#
# 用法:
#   python temp/xor_tool.py <文件1> <文件2> [输出文件]
#
# 说明:
#   FileXor 以 [] 下标读取 hash 配置（hash_once / enable_double_buffer），
#   所以这里直接现场构造一个 dict 作为配置传入，无需依赖配置系统。
#   长度不等的两个文件按短者以 0 补齐后异或。

from __future__ import annotations

import sys
from pathlib import Path

# 确保可从项目根导入 infra
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from infra.common.xor import FileXor

# 现场构造 hash 配置 dict（键与 hash.yaml 对应，XOR 复用分块/双缓冲参数）
HASH_CONF: dict = {
    "hash_once": 16 * 1024 * 1024,  # 16 MB
    "enable_double_buffer": False,
}


def main() -> int:
    if len(sys.argv) < 3:
        print("用法: python temp/xor_tool.py <文件1> <文件2> [输出文件]", file=sys.stderr)
        return 1

    f1 = Path(sys.argv[1]).resolve()
    f2 = Path(sys.argv[2]).resolve()
    out = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else Path("output_xor.bin").resolve()

    if not f1.is_file() or not f2.is_file():
        print(f"错误: 输入文件不存在: {f1} / {f2}", file=sys.stderr)
        return 1

    xor = FileXor(HASH_CONF)
    xor.compute_xor(str(f1), str(f2), str(out))

    print(f"文件 1    : {f1}")
    print(f"文件 2    : {f2}")
    print(f"输出      : {out}")
    print(f"分块大小  : {HASH_CONF['hash_once']} 字节 | 双缓冲: {HASH_CONF['enable_double_buffer']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
