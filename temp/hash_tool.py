# CHECK: 临时工具 - 独立哈希入口：现场构造 dict 配置，调用 FileHasher
#
# 用法:
#   python temp/hash_tool.py [文件路径]
#
# 说明:
#   FileHasher 以 [] 下标读取 hash 配置（hash_once / enable_double_buffer），
#   所以这里直接现场构造一个 dict 作为配置传入，无需依赖配置系统。

from __future__ import annotations

import sys
from pathlib import Path

# 确保可从项目根导入 infra
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from infra.common.hash import FileHasher

# 现场构造 hash 配置 dict（键与 hash.yaml 对应）
HASH_CONF: dict = {
    "hash_once": 16 * 1024 * 1024,  # 16 MB
    "enable_double_buffer": False,
}


def main() -> int:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1]).resolve()
    else:
        path = Path("README.md").resolve()

    if not path.is_file():
        print(f"错误: 文件不存在: {path}", file=sys.stderr)
        return 1

    hasher = FileHasher(HASH_CONF)
    result = hasher.compute_hash(str(path))

    print(f"文件     : {path}")
    print(f"分块大小 : {HASH_CONF['hash_once']} 字节 | 双缓冲: {HASH_CONF['enable_double_buffer']}")
    print(f"MD5      : {result['md5']}")
    print(f"SHA-512  : {result['sha512']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
