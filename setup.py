import argparse
from pathlib import Path
import shutil


def setup(args: argparse.Namespace) -> None:
    setup_file_structure(args)
    setup_database(args)
    
def setup_file_structure(args: argparse.Namespace) -> None:
    if args.data_dir is None:
        # 如果工作目录没有被输入的话，就注册一个新的
        args.data_dir = Path("./datas")

    if args.data_dir.is_file():
        # 如果工作目录是一个文件的话，就报错
        raise ValueError("data_dir is a file")
    
    if not args.data_dir.exists():
        # 如果工作目录不存在的话，就把默认 assets 的内容直接拷贝到 args.data_dir。
        # 也就是说：args.data_dir 对应的就是 assets 目录本身。
        src_assets_dir = Path(__file__).resolve().parent / "assets"
        if not src_assets_dir.exists() or not src_assets_dir.is_dir():
            raise FileNotFoundError(f"默认 assets 目录不存在: {src_assets_dir}")

        shutil.copytree(src_assets_dir, args.data_dir, dirs_exist_ok=False)

    