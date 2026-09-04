# CHECK: 待检查 - CLI 文件命令 - 文件管理命令行接口
# NOTE: file 子系统未完成（设计未定稿），以下为探索/临时实现，勿作为稳定功能依赖；后续可能整体重写或删除。

"""
文件操作子命令组：move / copy
"""

from __future__ import annotations

import cmd
from datetime import datetime
from pathlib import Path

import pandas as pd

from application.app import App


class FileCLI(cmd.Cmd):
    """文件操作相关命令行界面"""

    intro = """
========================================
  文件操作
========================================
输入 'help' 查看可用命令
输入 'back' 或 Ctrl+D 返回主菜单
"""

    prompt = "filetidy/file> "

    def __init__(self, app: App | None) -> None:
        """初始化 FileCLI 实例。

        Args:
            app: 应用实例，可为 None。
        """
        super().__init__()
        self.app = app

    def _missing_service(self) -> bool:
        """检查文件服务是否可用。

        Returns:
            如果应用未初始化或文件服务不可用返回 True，否则返回 False。
        """
        if self.app is None:
            print("错误: 应用未初始化。")
            return True
        if getattr(self.app, "file_service", None) is None:
            print("错误: 文件服务不可用。")
            return True
        return False

    def _parse_args(self, arg: str) -> dict[str, str]:
        """解析 --key value 风格参数为字典。

        Args:
            arg: 包含 --key value 风格参数的字符串。

        Returns:
            解析后的参数字典，key 为参数名，value 为参数值。
        """
        tokens = arg.split()
        d = {}
        i = 0
        while i < len(tokens):
            if tokens[i].startswith("--"):
                key = tokens[i][2:]
                if i + 1 < len(tokens) and not tokens[i + 1].startswith("--"):
                    d[key] = tokens[i + 1]
                    i += 2
                else:
                    d[key] = ""
                    i += 1
            else:
                i += 1
        return d

    def do_back(self, arg: str) -> bool:
        """返回主菜单"""
        return True

    def do_EOF(self, arg: str) -> bool:
        """Ctrl+D 返回主菜单"""
        print()
        return True

    # ── move ──────────────────────────────────────────────────

    def do_move(self, arg: str) -> None:
        """
        按 CSV 清单移动文件。

        用法: move --src-vol VOL001 --src-root /path/src/datas
                    --src-dir aaa --dst-vol VOL002
                    --dst-root /path/dst/datas --dst-dir bbb
                    --csv ./move.csv
                    [--time "2026-06-23T12:00:00"]

        参数说明:
          --src-vol    源卷号
          --src-root   源卷根目录（含 datas）
          --src-dir    源目录
          --dst-vol    目标卷号
          --dst-root   目标卷根目录（含 datas）
          --dst-dir    目标目录
          --csv        CSV 文件路径（列: sha256, hash, size, path）
          --time       可选，操作时间，ISO 格式，不传则用当前时间
        """
        if self._missing_service():
            return

        kwargs = self._parse_args(arg)
        missing = [k for k in ("src-vol", "src-root", "src-dir",
                                "dst-vol", "dst-root", "dst-dir", "csv") if k not in kwargs]
        if missing:
            print(f"缺少必要参数: {', '.join(missing)}")
            print("使用 help move 查看用法")
            return

        csv_path = Path(kwargs["csv"])
        if not csv_path.exists():
            print(f"错误: CSV 文件不存在: {csv_path}")
            return

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"错误: 读取 CSV 失败: {e}")
            return

        for col in ("sha256", "hash", "size", "path"):
            if col not in df.columns:
                print(f"错误: CSV 缺少列「{col}」")
                return

        add_time = None
        if raw := kwargs.get("time"):
            try:
                add_time = datetime.fromisoformat(raw)
            except ValueError as e:
                print(f"错误: 时间格式无效「{raw}」: {e}")
                return

        try:
            self.app.file_service.moveFile(
                src_volume=kwargs["src-vol"],
                src_root=kwargs["src-root"],
                src_dir=kwargs["src-dir"],
                dst_volume=kwargs["dst-vol"],
                dst_root=kwargs["dst-root"],
                dst_dir=kwargs["dst-dir"],
                df=df,
                add_time=add_time,
            )
            print(f"移动完成，共处理 {len(df)} 个文件。")
        except Exception as e:
            print(f"错误: 移动失败: {e}")

    # ── copy ──────────────────────────────────────────────────

    def do_copy(self, arg: str) -> None:
        """
        按 CSV 清单复制文件。

        用法: copy --src-vol VOL001 --src-root /path/src/datas
                    --src-dir aaa --dst-vol VOL002
                    --dst-root /path/dst/datas --dst-dir bbb
                    --csv ./copy.csv
                    [--time "2026-06-23T12:00:00"]

        参数说明:
          --src-vol    源卷号
          --src-root   源卷根目录（含 datas）
          --src-dir    源目录
          --dst-vol    目标卷号
          --dst-root   目标卷根目录（含 datas）
          --dst-dir    目标目录
          --csv        CSV 文件路径（列: sha256, hash, size, path）
          --time       可选，操作时间，ISO 格式，不传则用当前时间
        """
        if self._missing_service():
            return

        kwargs = self._parse_args(arg)
        missing = [k for k in ("src-vol", "src-root", "src-dir",
                                "dst-vol", "dst-root", "dst-dir", "csv") if k not in kwargs]
        if missing:
            print(f"缺少必要参数: {', '.join(missing)}")
            print("使用 help copy 查看用法")
            return

        csv_path = Path(kwargs["csv"])
        if not csv_path.exists():
            print(f"错误: CSV 文件不存在: {csv_path}")
            return

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"错误: 读取 CSV 失败: {e}")
            return

        for col in ("sha256", "hash", "size", "path"):
            if col not in df.columns:
                print(f"错误: CSV 缺少列「{col}」")
                return

        add_time = None
        if raw := kwargs.get("time"):
            try:
                add_time = datetime.fromisoformat(raw)
            except ValueError as e:
                print(f"错误: 时间格式无效「{raw}」: {e}")
                return

        try:
            self.app.file_service.copyFile(
                src_volume=kwargs["src-vol"],
                src_root=kwargs["src-root"],
                src_dir=kwargs["src-dir"],
                dst_volume=kwargs["dst-vol"],
                dst_root=kwargs["dst-root"],
                dst_dir=kwargs["dst-dir"],
                df=df,
                add_time=add_time,
            )
            print(f"复制完成，共处理 {len(df)} 个文件。")
        except Exception as e:
            print(f"错误: 复制失败: {e}")
