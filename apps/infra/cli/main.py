"""
CLI 命令行工具入口

使用方式:
    python -m apps.infra.cli.main
    或
    python apps/infra/cli/main.py
"""

import sys
import os

# 添加项目根目录到路径，以便导入其他模块
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from apps.core.initer import init
from apps.infra.cli.cli import main

if __name__ == '__main__':
    # 初始化系统（配置、日志、数据库等）
    init()
    # 启动 CLI
    main()
