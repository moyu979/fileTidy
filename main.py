"""
DDD 过渡版本入口：仅负责命令行参数解析，启动逻辑后续再接。
"""

from __future__ import annotations
import logging
import argparse
from pathlib import Path

from bootstrap import bootstrap
from infra.config.config import Config
from interface.cli.cli import FileTidyCLI
from interface.fastapi import run_service
from setup import setup

logger = logging.getLogger(__name__)
def _api_port(value: str) -> int:
    try:
        port = int(value, 10)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"无效端口: {value!r}") from e
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError(f"端口必须在 1–65535 之间: {port}")
    return port


def build_parser() -> argparse.ArgumentParser:
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
    args = parse_args()
    setup(args)
    app,config=bootstrap(args)
    if "cli" in args.modes:
        cli = FileTidyCLI(app=app)
        cli.cmdloop()
        logger.info("cli mode completed")
    if "api" in args.modes:
        run_service(app,config)
        logger.info("api mode completed")


if __name__ == "__main__":
    main()
