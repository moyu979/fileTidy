"""
超级设备子命令组
"""

from __future__ import annotations

import cmd

from application.app import App
from domain.storage.super_device.enum import SuperDeviceStateMenu, SuperDeviceTypeMenu
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

        print(SuperDeviceTypeMenu.prompt_text())
        super_device_type = None
        while super_device_type is None:
            code = input(SuperDeviceTypeMenu.input_hint()).strip()
            super_device_type = SuperDeviceTypeMenu.from_code(code)
            if super_device_type is None:
                print("无效输入，请重新选择。")

        info = input("请输入超级设备其他信息: ").strip() or None

        need_all_devices_online = None
        while need_all_devices_online is None:
            val = input("是否需要全部设备同时上线? (y/n): ").strip().lower()
            if val == "y":
                need_all_devices_online = True
            elif val == "n":
                need_all_devices_online = False
            else:
                print("无效输入，请输入 y 或 n。")

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

    # ── 字段更新 ──────────────────────────────────────────────────

    def do_set_name(self, arg: str) -> None:
        """更新超级设备名称。用法: set_name <序列号> <新名称>"""
        if self._missing_service():
            return
        parts = arg.strip().split()
        if len(parts) == 2:
            serial, name = parts
        else:
            serial = input("序列号: ").strip()
            name = input("新名称: ").strip()
            if not serial or not name:
                print("序列号和新名称不能为空。")
                return
        old, new = self.app.super_device_service.set_name(serial, name)
        print(f"名称: {old} → {new}")

    def do_set_sdtype(self, arg: str) -> None:
        """更新超级设备类型。用法: set_sdtype <序列号>"""
        if self._missing_service():
            return
        parts = arg.strip().split()
        if len(parts) == 1:
            serial = parts[0]
        else:
            serial = input("序列号: ").strip()
            if not serial:
                print("序列号不能为空。")
                return
        print(SuperDeviceTypeMenu.prompt_text())
        super_device_type = None
        while super_device_type is None:
            code = input(SuperDeviceTypeMenu.input_hint()).strip()
            super_device_type = SuperDeviceTypeMenu.from_code(code)
            if super_device_type is None:
                print("无效输入，请重新选择。")
        old, new = self.app.super_device_service.set_sdtype(serial, super_device_type)
        print(f"类型: {old} → {new}")

    def do_set_state(self, arg: str) -> None:
        """更新超级设备状态。用法: set_state <序列号>"""
        if self._missing_service():
            return
        parts = arg.strip().split()
        if len(parts) == 1:
            serial = parts[0]
        else:
            serial = input("序列号: ").strip()
            if not serial:
                print("序列号不能为空。")
                return
        print(SuperDeviceStateMenu.prompt_text())
        while True:
            code = input(SuperDeviceStateMenu.input_hint()).strip()
            state = SuperDeviceStateMenu.from_code(code)
            if state is not None:
                break
            print("无效输入，请按菜单输入对应编号。")
        old, new = self.app.super_device_service.set_state(serial, state)
        print(f"状态: {old.value} → {new.value}")

    def do_set_capacity(self, arg: str) -> None:
        """更新超级设备容量。用法: set_capacity <序列号> <容量>"""
        if self._missing_service():
            return
        parts = arg.strip().split()
        if len(parts) == 2:
            serial, cap_str = parts
        else:
            serial = input("序列号: ").strip()
            cap_str = input("容量（字节）: ").strip()
            if not serial or not cap_str:
                print("序列号和容量不能为空。")
                return
        try:
            capacity = int(cap_str)
        except ValueError:
            print("容量必须为整数（字节）。")
            return
        old, new = self.app.super_device_service.set_capacity(serial, capacity)
        print(f"容量: {old} → {new}")

    def do_set_need_all_devices_online(self, arg: str) -> None:
        """更新是否需要全部设备同时上线。用法: set_need_all_devices_online <序列号>"""
        if self._missing_service():
            return
        parts = arg.strip().split()
        if len(parts) == 1:
            serial = parts[0]
        else:
            serial = input("序列号: ").strip()
            if not serial:
                print("序列号不能为空。")
                return
        need_all_devices_online = None
        while need_all_devices_online is None:
            val = input("是否需要全部设备同时上线? (y/n): ").strip().lower()
            if val == "y":
                need_all_devices_online = True
            elif val == "n":
                need_all_devices_online = False
            else:
                print("无效输入，请输入 y 或 n。")
        old, new = self.app.super_device_service.set_need_all_devices_online(serial, need_all_devices_online)
        print(f"need_all_devices_online: {old} → {new}")

    # ── info 操作 ─────────────────────────────────────────────────

    @staticmethod
    def _print_info_diff(old: dict, new: dict) -> None:
        """打印 info 变更对比，每行一个 key。"""
        all_keys = sorted(set(old) | set(new))
        if not all_keys:
            print("info 无变化。")
            return
        print(f"{'key':<20} {'旧值':<30} {'新值':<30}")
        print("-" * 80)
        for k in all_keys:
            ov = old.get(k, "--")
            nv = new.get(k, "--")
            print(f"{k:<20} {str(ov):<30} {str(nv):<30}")

    @staticmethod
    def _parse_kv_pairs(*pairs: str) -> dict[str, str]:
        """将 key:value 字符串列表解析为字典。"""
        d = {}
        for pair in pairs:
            if ":" not in pair:
                raise ValueError(f"无法解析「{pair}」，应为 key:value 格式")
            key, val = pair.split(":", maxsplit=1)
            d[key.strip()] = val.strip()
        return d

    def _interactive_kv(self) -> dict[str, str]:
        """交互输入 key:value 对，空行结束。"""
        print("输入 key:value 对（每行一对，空行结束）:")
        d = {}
        while True:
            line = input().strip()
            if not line:
                break
            try:
                k, v = line.split(":", maxsplit=1)
                d[k.strip()] = v.strip()
            except ValueError:
                print(f"跳过无效行「{line}」，应为 key:value")
        return d

    def do_set_info(self, arg: str) -> None:
        """全量替换 info。用法: set_info <序列号> <key:value> ..."""
        if self._missing_service():
            return
        parts = arg.strip().split()
        if len(parts) >= 3:
            serial = parts[0]
            try:
                info = self._parse_kv_pairs(*parts[1:])
            except ValueError as e:
                print(e)
                return
        elif len(parts) == 2:
            serial = parts[0]
            info = self._interactive_kv()
        else:
            serial = input("序列号: ").strip()
            if not serial:
                print("序列号不能为空。")
                return
            info = self._interactive_kv()
        old, new = self.app.super_device_service.set_info(serial, info)
        self._print_info_diff(old, new)

    def do_append_info(self, arg: str) -> None:
        """追加 info 键值对。用法: append_info <序列号> <key:value> ..."""
        if self._missing_service():
            return
        parts = arg.strip().split()
        if len(parts) >= 3:
            serial = parts[0]
            try:
                data = self._parse_kv_pairs(*parts[1:])
            except ValueError as e:
                print(e)
                return
        elif len(parts) == 2:
            serial = parts[0]
            data = self._interactive_kv()
        else:
            serial = input("序列号: ").strip()
            if not serial:
                print("序列号不能为空。")
                return
            data = self._interactive_kv()
        old, new = self.app.super_device_service.append_info(serial, data)
        self._print_info_diff(old, new)

    def do_delete_info(self, arg: str) -> None:
        """删除 info 中的指定键。用法: delete_info <序列号> <key>"""
        if self._missing_service():
            return
        parts = arg.strip().split()
        if len(parts) == 2:
            serial, key = parts
        else:
            serial = input("序列号: ").strip()
            key = input("要删除的 key: ").strip()
            if not serial or not key:
                print("序列号和 key 不能为空。")
                return
        old, new = self.app.super_device_service.delete_info(serial, key)
        self._print_info_diff(old, new)

    # ── 子设备管理 ────────────────────────────────────────────────

    def do_add_device(self, arg: str) -> None:
        """向超级设备新增子设备。用法: add_device <超级设备序列号> <子设备序列号>"""
        if self._missing_service():
            return
        parts = arg.strip().split()
        if len(parts) == 2:
            sd_serial, dev_serial = parts
        else:
            sd_serial = input("超级设备序列号: ").strip()
            dev_serial = input("子设备序列号: ").strip()
            if not sd_serial or not dev_serial:
                print("序列号不能为空。")
                return
        try:
            self.app.super_device_service.add_device(sd_serial, dev_serial)
            print(f"子设备 {dev_serial} 已添加到超级设备 {sd_serial}")
        except Exception as e:
            print(f"错误: {e}")

    def do_replace_device(self, arg: str) -> None:
        """替换超级设备的子设备。用法: replace_device <超级设备序列号> <旧设备序列号> <新设备序列号>"""
        if self._missing_service():
            return
        parts = arg.strip().split()
        if len(parts) == 3:
            sd_serial, old_serial, new_serial = parts
        else:
            sd_serial = input("超级设备序列号: ").strip()
            old_serial = input("旧子设备序列号: ").strip()
            new_serial = input("新子设备序列号: ").strip()
            if not sd_serial or not old_serial or not new_serial:
                print("所有序列号不能为空。")
                return
        try:
            self.app.super_device_service.replace_device(sd_serial, old_serial, new_serial)
            print(f"子设备 {old_serial} 已替换为 {new_serial}")
        except Exception as e:
            print(f"错误: {e}")

    def do_remove_device(self, arg: str) -> None:
        """从超级设备移除子设备。用法: remove_device <超级设备序列号> <子设备序列号>"""
        if self._missing_service():
            return
        parts = arg.strip().split()
        if len(parts) == 2:
            sd_serial, dev_serial = parts
        else:
            sd_serial = input("超级设备序列号: ").strip()
            dev_serial = input("子设备序列号: ").strip()
            if not sd_serial or not dev_serial:
                print("序列号不能为空。")
                return
        try:
            self.app.super_device_service.remove_device(sd_serial, dev_serial)
            print(f"子设备 {dev_serial} 已从超级设备 {sd_serial} 移除")
        except Exception as e:
            print(f"错误: {e}")