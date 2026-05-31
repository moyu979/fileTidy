"""
主 CLI 入口

基于 cmd 模块的命令行界面框架；挂载设备、超级设备等子命令组，后续可按相同模式扩展。
"""

from __future__ import annotations

import cmd
import sys
from typing import TYPE_CHECKING

from interface.cli.device import DeviceCLI
from interface.cli.super_device import SuperDeviceCLI
from interface.cli.volume import VolumeCLI

if TYPE_CHECKING:
    from application.app import App


class FileTidyCLI(cmd.Cmd):
    """FileTidy 主命令行界面"""

    intro = """
========================================
  FileTidy 命令行工具
========================================
输入 'help' 查看可用命令
输入 'help <command>' 查看命令详情
输入 'quit' 或 'exit' 退出
"""

    prompt = "filetidy> "

    def __init__(self, app: "App | None" = None) -> None:
        super().__init__()
        self._device_cli = DeviceCLI(app=app)
        self._volume_cli = VolumeCLI(app=app)
        self._super_device_cli = SuperDeviceCLI(app=app)

    def do_device(self, arg: str) -> None:
        """
        进入设备管理子命令组

        用法: device
        输入 'help' 查看设备相关命令
        """
        self._device_cli.cmdloop()

    def do_dev(self, arg: str) -> None:
        """device 的简写"""
        self.do_device(arg)

    def do_super_device(self, arg: str) -> None:
        """
        进入超级设备管理子命令组

        用法: super_device
        输入 'help' 查看超级设备相关命令
        """
        self._super_device_cli.cmdloop()

    def do_sdev(self, arg: str) -> None:
        """super_device 的简写"""
        self.do_super_device(arg)

    def do_volume(self,arg: str) -> None:
        self._volume_cli.cmdloop()

    def do_vol(self, arg: str) -> None:
        """volume 的简写"""
        self.do_volume(arg)

    def do_quit(self, arg: str) -> bool | None:
        """退出程序"""
        print("再见！")
        return True

    def do_exit(self, arg: str) -> bool | None:
        """退出程序（quit 的别名）"""
        return self.do_quit(arg)

    def do_EOF(self, arg: str) -> bool | None:
        """Ctrl+D 退出"""
        print("\n再见！")
        return True

    def default(self, line: str) -> None:
        """处理未知命令"""
        print(f"未知命令: {line}")
        print("输入 'help' 查看可用命令")


def main(app: "App | None" = None) -> None:
    """CLI 入口函数"""
    cli = FileTidyCLI(app=app)
    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        print("\n\n程序被中断，再见！")
        sys.exit(0)

