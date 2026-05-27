"""
超级设备子命令组
"""

from __future__ import annotations

import cmd

from application.app import App
from infra.system.path_manager.is_path import is_path


class SuperDeviceCLI(cmd.Cmd):
    """超级设备相关命令行界面"""

    intro = """
========================================
  超级设备管理
========================================
输入 'help' 查看可用命令
输入 'back' 或 Ctrl+D 返回主菜单
"""

    prompt = "filetidy/super_device> "

    def __init__(self, app: App | None) -> None:
        super().__init__()
        self.app = app

    def _missing_service(self) -> bool:
        if self.app is None:
            print("错误: 应用未初始化，无法执行超级设备操作。")
            return True
        if getattr(self.app, "super_device_service", None) is None:
            print("错误: 超级设备服务不可用。")
            return True
        return False

    def do_back(self, arg: str) -> bool:
        """返回主菜单"""
        return True

    def do_EOF(self, arg: str) -> bool:
        """Ctrl+D 返回主菜单"""
        print()
        return True

    def do_reg(self, arg: str) -> None:
        """
        添加超级设备

        用法: reg
        将提示您依次输入参数，直接敲回车表示使用默认值（None 或空）
        """
        if self._missing_service():
            return
        name = input("请输入超级设备名称，可以留空: ").strip() or None
        print(
            "请选择超级设备类型（与系统编号一致）:\n"
            "  1 — single\n"
        )
        code = input("请输入编号 (1): ").strip()
        if code == "1":
            super_device_type = "single"
        else:
            print("无效输入，请输入 1 表示 single。")
            return

        info = input("请输入超级设备其他信息: ").strip() or None

        need_all_devices_online = input("请输入是否需要全部设备同时上线: (y or n)").strip() or None
        if need_all_devices_online == "y":
            need_all_devices_online = True
        else:
            need_all_devices_online = False

        # 这里加一个，输入设备id，直到输入q或空为止
        devices = []
        while True:
            device_id = input("请输入设备id: ").strip()
            if device_id == "q":
                break
            if device_id == "":
                break
            devices.append(device_id)
        assert len(devices) > 0

        try:
            result = self.app.super_device_service.reg_super_device(
                name=name,
                sdtype=super_device_type,
                need_all_devices_online=need_all_devices_online,
                add_time=None,
                last_check_time=None,
                state=None,
                capacity=None,
                devices=devices,
                info=info,
            )
            print(f"\n成功登记超级设备: {result}")
        except Exception as e:
            print(f"\n错误: {e}")

    def do_get(self, arg: str) -> None:
        """
        加载超级设备

        用法: get
        输入超级设备序列号，留空则列出全部
        """
        if self._missing_service():
            return

        target = input("请输入目标超级设备（序列号或路径，留空则列出全部）: ").strip()
        if not target:
            self.do_list(arg)
            return

        if is_path(target):
            sd = self.app.super_device_service.load_super_device(
                super_device_path=target,
            )
        else:
            sd = self.app.super_device_service.load_super_device(
                serial=target,
            )

        if sd is None:
            print("\n未找到该超级设备。")
            return

        print(f"\n{sd}")

    def do_list(self, arg: str) -> None:
        """
        列出所有超级设备

        用法: list
        """
        if self._missing_service():
            return
        devices = self.app.super_device_service.list_super_devices()
        if not devices:
            print("（无超级设备）")
            return
        for d in devices:
            print(d)