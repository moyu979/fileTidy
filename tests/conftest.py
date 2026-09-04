# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""tests/ 公共夹具。

保证从任意子目录运行 pytest 时，项目根目录都在 sys.path 上；
同时关闭 pytest 自身的字节码缓存，避免测试产物污染工作区。
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
