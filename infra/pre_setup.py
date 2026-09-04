# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 前置准备 - bootstrap 前的目录结构、环境检查、静态工具初始化

import argparse
import logging
from pathlib import Path

from infra.common.merge_dir import merge_dir

logger = logging.getLogger(__name__)


def pre_setup(args: argparse.Namespace) -> None:
    """运行前准备阶段：目录结构、环境检查、静态工具初始化。

    在 bootstrap（框架/业务初始化）之前执行，负责所有不依赖 Config
    的前置准备工作。

    执行顺序说明：
    1. setup_file_structure — 先确保数据目录存在，后续函数才能依赖它
    2. check_external_tools — 检查系统环境中的外部命令是否齐备
    3. prepare_environment — 创建临时目录、设置环境变量等

    Args:
        args: 命令行参数命名空间对象，包含 data_dir 等属性。
    """
    logger.info("=== pre_setup 阶段开始 ===")

    setup_file_structure(args.data_dir)

    check_external_tools()

    prepare_environment()

    logger.info("=== pre_setup 阶段完成 ===")


def setup_file_structure(data_dir: Path) -> None:
    """检查并创建数据目录结构，从 assets 合并默认内容（补缺）。

    如果 data_dir 未设置，默认为 ./datas。
    如果 data_dir 是文件则抛出异常。
    合并策略：data_dir 已有的文件保留，assets 中缺失的补上。

    Args:
        data_dir: 数据目录路径。为 None 时回退到 ./datas。

    Raises:
        NotADirectoryError: data_dir 或 src_assets_dir 指向一个已存在的文件时抛出。
        FileNotFoundError: 默认 assets 目录不存在时抛出。
    """
    # 未指定时回退到 ./datas
    if data_dir is None:
        data_dir = Path("./datas")
        logger.info("data_dir 未指定，使用默认值: %s", data_dir)

    logger.info("data_dir: %s", data_dir)

    # 防止意外覆盖已有文件
    if data_dir.is_file():
        logger.error("data_dir 指向一个已存在的文件: %s", data_dir)
        raise NotADirectoryError(f"data_dir 指向一个已存在的文件，而非目录: {data_dir}")

    # 确保 data_dir 根目录存在
    data_dir.mkdir(parents=True, exist_ok=True)

    # 从包内 assets 合并默认内容（补缺：已有的保留，缺失的补上）
    src_assets_dir = Path(__file__).resolve().parent.parent / "assets"
    if not src_assets_dir.exists():
        logger.error("默认 assets 目录不存在: %s", src_assets_dir)
        raise FileNotFoundError(f"默认 assets 目录不存在: {src_assets_dir}")
    if not src_assets_dir.is_dir():
        logger.error("默认 assets 路径不是目录: %s", src_assets_dir)
        raise NotADirectoryError(f"默认 assets 路径是一个文件，而非目录: {src_assets_dir}")

    logger.info("从 %s 合并默认设置和文件到 %s", src_assets_dir, data_dir)
    try:
        merge_dir(src_assets_dir, data_dir)
    except OSError as e:
        logger.error("合并默认内容时发生系统错误: %s", e)
        raise
    logger.info("data_dir 内容已就绪: %s", data_dir)


def check_external_tools() -> None:
    """检查外部依赖工具是否可用。

    TODO(P0): 实现对外部命令行工具（如 ffprobe、rsync 等）的可用性检查，
              缺失时打印警告或直接报错。
    """
    logger.info("检查外部工具…（暂未实现）")
    ...


def prepare_environment() -> None:
    """准备运行时环境。

    TODO(P0): 实现临时目录/缓存目录创建、环境变量设置、权限检查等。
    """
    logger.info("准备运行时环境…（暂未实现）")
    ...


def main() -> None:
    """独立运行入口，用于手动验证 pre_setup 阶段的各步骤。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("pre_setup 独立调试启动")

    parser = argparse.ArgumentParser(description="运行前准备（独立调试）")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("./datas"),
        metavar="DIR",
        help="数据目录路径（默认：./datas）",
    )
    args = parser.parse_args()
    pre_setup(args)

    logger.info("pre_setup 独立调试结束")


if __name__ == "__main__":
    main()
    