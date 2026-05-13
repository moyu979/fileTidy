"""
卷管理子命令组

与旧版 `DeviceManager` 相同的交互式命令骨架；底层能力随应用层接口逐步接入。
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
            "请输入全局唯一挂载点标识 unique_mount_point（直接回车则留空）: "
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

    def reg_init(self, arg: str) -> None:
        """
        将一个卷记录到数据库
        """

        pass