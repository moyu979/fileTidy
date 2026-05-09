"""
设备子命令组

与旧版 `DeviceManager` 相同的交互式命令骨架；底层能力随应用层接口逐步接入。
"""

from __future__ import annotations

import cmd

from application.app import App


class DeviceCLI(cmd.Cmd):
    """设备相关命令行界面"""

    intro = """
========================================
  设备管理
========================================
输入 'help' 查看可用命令
输入 'back' 或 Ctrl+D 返回主菜单
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

    def do_back(self, arg: str) -> bool:
        """返回主菜单"""
        return True

    def do_EOF(self, arg: str) -> bool:
        """Ctrl+D 返回主菜单"""
        print()
        return True

    def do_reg(self, arg: str) -> None:
        """
        添加新设备

        用法: add
        将提示您依次输入参数，直接敲回车表示使用默认值（None 或空）
        """
        if self._missing_service():
            return

        print("\n开始添加设备...")
        print("（直接敲回车表示使用默认值 None 或留空）\n")

        name_input = input("请输入设备名称 (直接回车使用占位名): ").strip()
        name = name_input if name_input else None

        info_input = input("请输入设备其他信息 (直接回车使用 None): ").strip()
        info = info_input if info_input else None

        path = input("请输入设备路径: ").strip()
        device_path = path if path else None

        if device_path is not None:
            self.app.device_service.reg_device_by_path(
                device_path=device_path,
                name=name,
                info=info,
            )
            return
        else:
            serial = input("请输入设备序列号: ").strip()
            if not serial:
                print("错误: 序列号不能为空")
                return

            type_input = input("请输入设备类型 (hdd/ssd/tape/tf_sd_card，直接回车使用 None): ").strip()
            type = type_input if type_input else None

            capacity_input = input("请输入设备容量（字节，直接回车使用 None）: ").strip()
            capacity: int | None = None
            if capacity_input:
                try:
                    capacity = int(capacity_input)
                except ValueError:
                    print("警告: 容量格式不正确，将使用 None")
                    capacity = None
            try:
                self.app.device_service.reg_device_by_info(
                    serial=serial,
                    name=name,
                    type=type,
                    add_time=None,
                    last_check_time=None,
                    capacity=capacity,
                    info=info,
                    state=None,
                    device_path=device_path,
                )
                print(f"\n成功登记设备: {name} (序列号: {serial})")
            except Exception as e:
                print(f"\n错误: {e}")

    def do_load(self, arg: str) -> None:
        """
        加载设备

        用法: load
        将提示您依次输入参数，直接敲回车表示使用默认值（None 或空）
        """
        if self._missing_service():
            return
        serial = input("请输入设备序列号: ").strip() or None
        device_path = input("请输入设备路径: ").strip() or None

        device = self.app.device_service.load_device(
            serial=serial,
            device_path=device_path,
        )
        if device is None:
            print("\n未找到对应设备记录。")
            return
        print(f"\n成功加载设备: {device.name} (序列号: {device.serial})")
        print(device.to_json())
    def do_list(self, arg: str) -> None:
        """
        列出所有设备

        用法: list
        """
        if self._missing_service():
            return
        devices = self.app.device_service.list_devices()
        for device in devices:
            print(device)