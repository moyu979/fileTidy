# CHECK: 待检查 - 主入口文件 - 应用的启动入口

"""
DDD 过渡版本入口：仅负责命令行参数解析，启动逻辑后续再接。
"""

from __future__ import annotations
import logging
import argparse
from pathlib import Path

from bootstrap import bootstrap
from infra.config.app_config import AppConfig
from interface.cli.cli import FileTidyCLI
from interface.fastapi import run_service
from infra.pre_setup import pre_setup
from infra.check import post_check

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。

    定义 --data-dir（数据目录）和 --mode（运行模式）两个参数。

    Returns:
        配置好的 ArgumentParser 实例。
    """
    parser = argparse.ArgumentParser(
        description="fileTidy DDD 过渡版：数据库目录、运行模式与日志等级配置",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("./datas"),
        metavar="DIR",
        help="存放运行所需数据库等数据的目录（默认：./datas）",
    )
    parser.add_argument(
        "--mode",
        action="append",
        choices=("cli", "api"),
        dest="modes",
        metavar="MODE",
        help=(
            "运行模式，可重复指定以同时启用：cli=命令行，api=FastAPI。"
            "示例：--mode cli --mode api。省略时默认仅 api。"
        ),
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """解析命令行参数。

    对 --mode 进行去重处理，未指定时默认值为 ["cli"]。
    对 --data-dir 进行用户目录展开和绝对路径解析。

    Args:
        argv: 命令行参数列表，为 None 时从 sys.argv 读取。

    Returns:
        解析后的命名空间对象，包含 modes（列表）和 data_dir（Path）等属性。
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    # 去重；未传 --mode 时与旧行为一致，默认只启动 cli
    if args.modes:
        args.modes = list(set(args.modes))
    else:
        args.modes = ["cli"]
    args.data_dir = args.data_dir.expanduser().resolve()
    return args


def main():
    """主入口函数。

    执行流程：
    1. 解析命令行参数
    2. 初始化数据目录结构
    3. 启动应用（数据库、日志等）
    4. 根据 --mode 参数决定运行模式：
       - cli: 启动命令行交互界面
       - api: 启动 FastAPI 服务
    """
    args = parse_args()
    pre_setup(args)
    app,config=bootstrap(args)
    # if "cli" in args.modes:
    #     cli = FileTidyCLI(app=app)
    #     cli.cmdloop()
    #     logger.info("cli mode completed")
    # if "api" in args.modes:
    #     run_service(app,config)
    #     logger.info("api mode completed")


if __name__ == "__main__":
    main()
