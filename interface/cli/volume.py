"""
卷管理子命令组
"""

from __future__ import annotations

import cmd

from application.app import App


class VolumeCLI(cmd.Cmd):
    """卷相关命令行界面"""

    intro = """
========================================
  卷管理
========================================
输入 'help' 查看可用命令
输入 'back' 或 Ctrl+D 返回主菜单
"""

    prompt = "filetidy/volume> "

    def __init__(self, app: App | None) -> None:
        super().__init__()
        self.app = app

    def _missing_service(self) -> bool:
        if self.app is None:
            print("错误: 应用未初始化，无法执行卷操作。")
            return True
        if getattr(self.app, "volume_service", None) is None:
            print("错误: 卷服务不可用。")
            return True
        return False

    def do_back(self, arg: str) -> bool:
        """返回主菜单"""
        return True

    def do_EOF(self, arg: str) -> bool:
        """Ctrl+D 返回主菜单"""
        print()
        return True

    def do_init(self, arg: str) -> None:
        """
        初始化一个新卷，并且将其中的文件标记到file的初始化目录里
        """
        if self._missing_service():
            return

        print("\n初始化新卷（会整理挂载点目录下的内容并登记 data 内已有文件）...")
        print("（与 volume_service.init_volume 参数一致；卷名留空则使用自动生成的序列号）\n")

        path = input("请输入卷挂载点路径（须为已挂载目录）: ").strip()
        if not path:
            print("错误: 路径不能为空。")
            return

        name_input = input(
            "请输入卷名称（直接回车则使用自动生成的序列号作为名称）: "
        ).strip()
        name = name_input if name_input else None

        ump_input = input(
            "请输入全局唯一挂载点标识 unique_mount_point（直接回车则默认为/unknown）: "
        ).strip()
        unique_mount_point = ump_input if ump_input else None

        info_input = input("请输入卷备注/其他信息（直接回车则留空）: ").strip()
        info = info_input if info_input else ""

        try:
            volume = self.app.volume_service.init_volume(
                path=path,
                name=name,
                unique_mount_point=unique_mount_point,
                info=info,
            )
            print(f"\n初始化成功: {volume}")
        except Exception as e:
            print(f"\n初始化失败: {e}")

    def do_reg(self, arg: str) -> None:
        """
        将一个已经初始化过的卷记录到数据库，只需提供路径
        """
        if self._missing_service():
            return

        path = input("请输入卷路径: ").strip()
        if not path:
            print("错误: 路径不能为空。")
            return

        name_input = input("请输入卷名称（直接回车则使用序列号）: ").strip()
        name = name_input if name_input else None

        ump = input("请输入全局唯一挂载点标识 unique_mount_point（直接回车则留空）: ").strip()
        unique_mount_point = ump if ump else None

        from pathlib import Path as P
        abs_path = str(P(path).resolve())

        try:
            result = self.app.volume_service.reg_volume(
                path=abs_path,
                name=name,
                unique_mount_point=unique_mount_point,
            )
            print(f"\n登记成功: {result}")
        except Exception as e:
            print(f"\n登记失败: {e}")

    def do_get(self, arg: str) -> None:
        """
        查询卷

        用法: get
        输入卷序列号查询，留空则列出全部。
        """
        if self._missing_service():
            return

        target = input("请输入卷序列号（留空则列出全部）: ").strip()
        if not target:
            self.do_list(arg)
            return

        volume = self.app.volume_service.get_volume(target)
        if volume is None:
            print("\n未找到该卷。")
            return
        print(f"\n{volume}")

    def do_list(self, arg: str) -> None:
        """
        列出所有卷

        用法: list
        """
        if self._missing_service():
            return
        volumes = self.app.volume_service.list_volumes()
        if not volumes:
            print("（无卷）")
            return
        for v in volumes:
            print(v)