"""
设备子命令组

与旧版 `DeviceManager` 相同的交互式命令骨架；底层能力随应用层接口逐步接入。
"""

from __future__ import annotations

import cmd

from application.app import App


class SuperDeviceCLI(cmd.Cmd):
    """设备相关命令行界面"""

    intro = """
========================================
  设备管理
========================================
输入 'help' 查看可用命令
输入 'back' 返回主菜单
"""

    prompt = "filetidy/device> "

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

    def do_reg(self, arg: str) -> None:
        """
        添加超级设备

        用法: reg
        将提示您依次输入参数，直接敲回车表示使用默认值（None 或空）
        """
        if self._missing_service():
            return
        name = input("请输入超级设备名称，可以留空: ").strip() or None
        type = input("请输入超级设备类型: ").strip() or None
        info = input("请输入超级设备其他信息: ").strip() or None
        need_all_devices_online = input("请输入是否需要全部设备同时上线: ").strip() or None

        if need_all_devices_online == "y":
            need_all_devices_online = True
        else:
            need_all_devices_online = False

        # 这里加一个，输入设备id，直到输入q为止
        devices = []
        while True:
            device_id = input("请输入设备id: ").strip()
            if device_id == "q":
                break
            devices.append(device_id)

        self.app.super_device_service.reg_super_device(
            name=name,
            type=type,
            info=info,
            need_all_devices_online=need_all_devices_online,
            devices=devices,
        )