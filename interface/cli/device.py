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

    def do_add(self, arg: str) -> None:
        """
        添加新设备

        用法: add
        将提示您依次输入参数，直接敲回车表示使用默认值（None 或空）
        """
        if self._missing_service():
            return

        print("\n开始添加设备...")
        print("（直接敲回车表示使用默认值 None 或留空）\n")

        serial = input("请输入设备序列号: ").strip()
        if not serial:
            print("错误: 序列号不能为空")
            return

        path = input("请输入设备路径: ").strip()
        device_path = path if path else None

        name_input = input("请输入设备名称 (直接回车使用占位名): ").strip()
        name = name_input if name_input else f"device-{serial[:8]}"

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

        info_input = input("请输入设备其他信息 (直接回车使用 None): ").strip()
        info = info_input if info_input else None

        try:
            self.app.device_service.reg_device(
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
