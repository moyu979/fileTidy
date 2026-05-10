"""
设备子命令组

与旧版 `DeviceManager` 相同的交互式命令骨架；底层能力随应用层接口逐步接入。
"""

from __future__ import annotations

import cmd

from application.app import App
from infra.system.path_manager.is_path import is_path

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

        name_input = input("请输入设备名称 (直接回车使用序列号作为名称): ").strip()
        name = name_input if name_input else None

        info_input = input("请输入设备其他信息 (直接回车则留空): ").strip()
        info = info_input if info_input else None

        path = input("请输入设备路径：\n 输入有效路径则使用路径初始化，否则使用序列号手动配置路径: ").strip()
        device_path = path if path else None

        if device_path is not None:
            result = self.app.device_service.reg_device_by_path(
                device_path=device_path,
                name=name,
                info=info,
            )
            print(f"\n成功登记设备: {result}")
            return
        else:
            serial = input("请输入设备序列号: ").strip()
            if not serial:
                print("错误: 序列号不能为空")
                return

            print(
                "请选择设备类型（与系统编号一致）:\n"
                "  1 — SSD\n"
                "  2 — HDD\n"
                "  3 — TF 卡 (tf_sd_card)\n"
                "  4x — 磁带 LTO-x（例如 45 表示 LTO5，规则同系统：去掉所有字符 4 后的部分为代次）\n"
                "  输入 None 或直接回车 — 不指定类型\n"
            )
            device_type: str | None
            
            code = input("请输入编号 (1/2/3/4…/None/回车): ").strip()
            if code == "" or code == "None":
                device_type = None
            if code == "1":
                device_type = "ssd"
            if code == "2":
                device_type = "hdd"
            if code == "3":
                device_type = "tf_sd_card"
            if code.startswith("4"):
                device_type = f"Tape-lto{code.replace('4', '')}".lower()
            else:
                print("无效输入，请按菜单输入 1、2、3、以 4 开头的磁带编号、None 或回车。")
                return

            capacity_input = input("请输入设备容量（字节，直接回车使用 None）: ").strip()
            capacity: int | None = None
            if capacity_input:
                try:
                    capacity = int(capacity_input)
                except ValueError:
                    print("警告: 容量格式不正确，将使用原输入值")
                    capacity = capacity_input
                    
            try:
                result = self.app.device_service.reg_device_by_info(
                    serial=serial,
                    name=name,
                    type=device_type,
                    add_time=None,
                    last_check_time=None,
                    capacity=capacity,
                    info=info,
                    state=None,
                    device_path=device_path,
                )
                print(f"\n成功登记设备: {result}")
            except Exception as e:
                print(f"\n错误: {e}")

    def do_get(self, arg: str) -> None:
        """
        加载设备

        用法: load
        将提示您依次输入参数，直接敲回车表示使用默认值（None 或空）
        """
        if self._missing_service():
            return
        
        target = input("请输入目标设备: 留空获取全部设备")
        target = target if target else None

        if target is None:
            self.do_list(arg)
            return

        if is_path(target):
            device = self.app.device_service.load_device(
                device_path=target,
                serial=None
            )
        else:
            device = self.app.device_service.load_device(
                serial=target,
                device_path=None
            )

        print(f"\n成功加载设备: {device}")
        

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