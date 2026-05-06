"""
设备子命令组

与旧版 `DeviceManager` 相同的交互式命令骨架；底层能力随应用层接口逐步接入。
"""

from __future__ import annotations

import cmd

from application.app import App


class DeviceCLI(cmd.Cmd):
    """卷相关命令行界面"""

    intro = """
========================================
  设备管理
========================================
输入 'help' 查看可用命令
输入 'back' 返回主菜单
"""

    prompt = "filetidy/volume> "

    def __init__(self, app: App | None) -> None:
        super().__init__()
        self.app = app

    def _missing_service(self) -> bool:
        if self.app is None:
            print("错误: 应用未初始化，无法执行设备操作。")
            return True
        if getattr(self.app, "device_service", None) is None:
            print("错误: 设备服务不可用。")
            return True
        return False

    def do_init(self, arg: str) -> None:
        """
        添加新设备

        用法: add
        将提示您依次输入参数，直接敲回车表示使用默认值（None 或空）
        """

        path=input("请输入卷路径: ").strip()

        
        if self._missing_service():
            return

        print("\n开始添加卷...")
        print("（直接敲回车表示使用默认值 None 或留空）\n")

        # todo：后面再写