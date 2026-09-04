# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - CLI 设备命令 - 设备管理命令行接口

"""
设备子命令组
"""

from __future__ import annotations

import cmd
import json

from application.app import App
from domain.storage.device.enum import (
    DeviceStateMenu,
    DeviceTypeMenu,
    FormFactorMenu,
    InterfaceMenu,
    LtoGenerationMenu,
)


def _collect_device_spec(dtype: str) -> dict:
    """按设备类型交互录入规格信息，返回要写入 info 的键值对。

    磁带 → {"generation": ...}；SSD/HDD → {"interface": ..., "form_factor": ...}；
    其他类型或用户直接回车跳过时不录入任何规格，返回空 dict。

    Args:
        dtype: 设备类型字符串（如 "tape", "ssd", "hdd"）。

    Returns:
        要合并进 info 的规格字典（可能为空）。
    """
    spec: dict = {}
    if dtype == "tape":
        print(LtoGenerationMenu.prompt_text())
        while True:
            code = input(LtoGenerationMenu.input_hint()).strip()
            if not code:
                break
            gen = LtoGenerationMenu.from_code(code)
            if gen is not None:
                spec["generation"] = gen.value
                break
            print("无效输入，请按菜单输入对应编号。")
    elif dtype in ("ssd", "hdd"):
        print(InterfaceMenu.prompt_text())
        while True:
            code = input(InterfaceMenu.input_hint()).strip()
            if not code:
                break
            iface = InterfaceMenu.from_code(code)
            if iface is not None:
                spec["interface"] = iface.value
                break
            print("无效输入，请按菜单输入对应编号。")
        if "interface" in spec:
            print(FormFactorMenu.prompt_text())
            while True:
                code = input(FormFactorMenu.input_hint()).strip()
                if not code:
                    break
                ff = FormFactorMenu.from_code(code)
                if ff is not None:
                    spec["form_factor"] = ff.value
                    break
                print("无效输入，请按菜单输入对应编号。")
    return spec


def _merge_spec_info(user_info: str | None, spec: dict) -> str:
    """把规格信息合并进用户输入的 info（JSON 文本）。

    若用户 info 是合法 JSON 对象则作为基座合并；否则将其视为备注文本存入
    "note" 键，再合并规格。

    Args:
        user_info: 用户输入的 info（JSON 文本，可为 None）。
        spec: 要合并的规格字典。

    Returns:
        合并后的 JSON 文本。
    """
    base: dict = {}
    if user_info:
        try:
            parsed = json.loads(user_info)
            base = parsed if isinstance(parsed, dict) else {"note": user_info}
        except json.JSONDecodeError:
            base = {"note": user_info}
    base.update(spec)
    return json.dumps(base, ensure_ascii=False)


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
        """初始化 DeviceCLI 实例。

        Args:
            app: 应用实例，可为 None。
        """
        super().__init__()
        self.app = app

    def _missing_service(self) -> bool:
        """检查设备服务是否可用。

        Returns:
            如果应用未初始化或设备服务不可用返回 True，否则返回 False。
        """
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
        添加新设备（离线手动登记）

        用法: reg
        将提示您依次输入参数，直接敲回车表示使用默认值（None 或空）
        仅支持离线手动登记：系统不探测设备，信息完全由您录入。
        （在线登记：系统自动采集 + 冲突确认，规划中。）
        """
        if self._missing_service():
            return

        print("\n开始添加设备（离线手动登记）...")
        print("（直接敲回车表示使用默认值 None 或留空）\n")

        name_input = input("请输入设备名称 (直接回车使用序列号作为名称): ").strip()
        name = name_input if name_input else None

        info_input = input("请输入设备其他信息 (直接回车则留空): ").strip()
        info = info_input if info_input else None

        serial = input("请输入设备序列号: ").strip()
        if not serial:
            print("错误: 序列号不能为空")
            return

        # 系统不探测：类型/规格完全由用户录入
        print(DeviceTypeMenu.prompt_text())
        while True:
            code = input(DeviceTypeMenu.input_hint()).strip()
            device_type = DeviceTypeMenu.from_code(code)
            if device_type is not None:
                break
            print("无效输入，请按菜单输入对应编号。")

        data: dict = {
            "serial": serial,
            "name": name,
            "type": device_type,
            "info": _merge_spec_info(info, _collect_device_spec(device_type)),
        }

        try:
            result = self.app.device_service.reg_device_manual(data)
        except Exception as e:
            print(f"\n错误: {e}")
            return
        print(f"\n成功登记设备: {result}")

    def do_get(self, arg: str) -> None:
        """
        加载设备

        用法: get
        将提示您依次输入参数，直接敲回车表示使用默认值（None 或空）
        """
        if self._missing_service():
            return

        target = input("请输入目标设备: 留空获取全部设备\n").strip()
        target = target if target else None

        if target is None:
            self.do_list(arg)
            return

        device = self.app.device_service.load_device_by_target(target)

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

    # ── 字段更新 ──────────────────────────────────────────────────

    def do_set_name(self, arg: str) -> None:
        """更新设备名称。用法: set_name <序列号> <新名称>"""
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
        old, new = self.app.device_service.set_name(serial, name)
        print(f"名称: {old} → {new}")

    def do_set_type(self, arg: str) -> None:
        """更新设备类型。用法: set_type <序列号>"""
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
        print(DeviceTypeMenu.prompt_text())
        while True:
            code = input(DeviceTypeMenu.input_hint()).strip()
            dtype = DeviceTypeMenu.from_code(code)
            if dtype is not None:
                break
            print("无效输入，请按菜单输入对应编号。")
        old, new = self.app.device_service.set_type(serial, dtype)
        print(f"类型: {old} → {new}")

    def do_set_state(self, arg: str) -> None:
        """更新设备状态。用法: set_state <序列号>"""
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
        print(DeviceStateMenu.prompt_text())
        while True:
            code = input(DeviceStateMenu.input_hint()).strip()
            state = DeviceStateMenu.from_code(code)
            if state is not None:
                break
            print("无效输入，请按菜单输入对应编号。")
        old, new = self.app.device_service.set_state(serial, state)
        print(f"状态: {old.value} → {new.value}")

    def do_set_capacity(self, arg: str) -> None:
        """更新设备容量。用法: set_capacity <序列号> <容量>"""
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
        old, new = self.app.device_service.set_capacity(serial, capacity)
        print(f"容量: {old} → {new}")

    # ── info 操作 ─────────────────────────────────────────────────

    @staticmethod
    def _print_info_diff(old: dict, new: dict) -> None:
        """打印 info 变更对比，每行一个 key。

        Args:
            old: 旧的 info 字典。
            new: 新的 info 字典。
        """
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
        """将 key:value 字符串列表解析为字典。

        Args:
            *pairs: 格式为 "key:value" 的字符串列表。

        Returns:
            解析后的键值对字典。

        Raises:
            ValueError: 如果某个字符串不包含冒号分隔符则抛出。
        """
        d = {}
        for pair in pairs:
            if ":" not in pair:
                raise ValueError(f"无法解析「{pair}」，应为 key:value 格式")
            key, val = pair.split(":", maxsplit=1)
            d[key.strip()] = val.strip()
        return d

    def _interactive_kv(self) -> dict[str, str]:
        """交互输入 key:value 对，空行结束。

        Returns:
            用户输入的键值对字典。
        """
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
        old, new = self.app.device_service.set_info(serial, info)
        self._print_info_diff(old, new)

    def do_append_info(self, arg: str) -> None:
        """合并键值对到 info。用法: append_info <序列号> <key:value> ..."""
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
        old, new = self.app.device_service.append_info(serial, data)
        self._print_info_diff(old, new)

    def do_delete_info(self, arg: str) -> None:
        """从 info 中删除键。用法: delete_info <序列号> <键名>"""
        if self._missing_service():
            return
        parts = arg.strip().split()
        if len(parts) == 2:
            serial, key = parts
        elif len(parts) == 1:
            serial = parts[0]
            key = input("要删除的键名: ").strip()
            if not key:
                print("键名不能为空。")
                return
        else:
            serial = input("序列号: ").strip()
            key = input("要删除的键名: ").strip()
            if not serial or not key:
                print("序列号和键名不能为空。")
                return
        old, new = self.app.device_service.delete_info(serial, key)
        self._print_info_diff(old, new)

    def do_set_serial(self, arg: str) -> None:
        """重置设备序列号。用法: set_serial <旧序列号> <新序列号>"""
        if self._missing_service():
            return
        parts = arg.strip().split()
        if len(parts) == 2:
            old_serial, new_serial = parts
        else:
            old_serial = input("旧序列号: ").strip()
            new_serial = input("新序列号: ").strip()
            if not old_serial or not new_serial:
                print("旧序列号和新序列号不能为空。")
                return
        old, new = self.app.device_service.set_serial(old_serial, new_serial)
        print(f"序列号: {old} → {new}")

    def do_remove(self, arg: str) -> None:
        """软删除设备（标记 REMOVED）。用法: remove <序列号>"""
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
        try:
            self.app.device_service.remove_device(serial)
        except Exception as e:
            print(f"\n错误: {e}")
            return
        print(f"已移除设备: {serial}")