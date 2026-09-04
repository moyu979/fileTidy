# CHECK: 待检查 - CLI 卷命令 - 卷管理命令行接口

"""
卷管理子命令组
"""

from __future__ import annotations

import cmd

from application.app import App
from domain.storage.volume.enum import VolumeStateMenu, VolumeTypeMenu


class VolumeCLI(cmd.Cmd):
    """卷相关命令行界面"""

    # ── KV 输入辅助 ───────────────────────────────────────────

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

    # ── 核心逻辑 ─────────────────────────────────────────────

    intro = """
========================================
  卷管理
========================================
输入 'help' 查看可用命令
输入 'back' 或 Ctrl+D 返回主菜单
"""

    prompt = "filetidy/volume> "

    def __init__(self, app: App | None) -> None:
        """初始化 VolumeCLI 实例。

        Args:
            app: 应用实例，可为 None。
        """
        super().__init__()
        self.app = app

    def _missing_service(self) -> bool:
        """检查卷服务是否可用。

        Returns:
            如果应用未初始化或卷服务不可用返回 True，否则返回 False。
        """
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
        print("（卷名留空则使用自动生成的序列号）\n")

        path = input("请输入卷挂载点路径（须为已挂载目录）: ").strip()
        if not path:
            print("错误: 路径不能为空。")
            return

        name_input = input(
            "请输入卷名称（直接回车则使用自动生成的序列号作为名称）: "
        ).strip()
        name = name_input if name_input else None

        ump_input = input(
            "请输入全局唯一挂载点标识 unique_mount_point（直接回车则默认为 /unknown，建议使用绝对路径）: "
        ).strip()
        unique_mount_point = ump_input if ump_input else None

        print("—— 以下为卷其他信息（info）——")
        info = self._interactive_kv()

        from pathlib import Path as P
        abs_path = str(P(path).resolve())

        try:
            volume = self.app.volume_service.init_volume(
                path=abs_path,
                name=name,
                unique_mount_point=unique_mount_point,
                info=info,
            )
            print(f"\n初始化成功: {volume}")
        except Exception as e:
            print(f"\n初始化失败: {e}")

    def do_reg(self, arg: str) -> None:
        """
        登记已有卷

        用法: reg
          - 输入路径 → 自动检测卷信息（需挂载）
          - 留空    → 手动输入所有卷信息（无需挂载）
        """
        if self._missing_service():
            return

        path = input("请输入卷路径（直接回车则手动输入所有卷信息，无需挂载）: ").strip()

        name_input = input("请输入卷名称（直接回车则使用序列号）: ").strip()
        name = name_input if name_input else None

        ump = input("请输入全局唯一挂载点标识 unique_mount_point（直接回车则留空，建议使用绝对路径）: ").strip()
        unique_mount_point = ump if ump else None

        print("—— 以下为卷其他信息（info）——")
        info = self._interactive_kv()

        if path:
            # ── 有路径 → 自动检测 ──
            from pathlib import Path as P
            abs_path = str(P(path).resolve())

            reg_files_input = input("是否同时登记 datas 下的文件（y/N，默认 N）: ").strip().lower()
            register_files = reg_files_input in ("y", "yes")

            try:
                result = self.app.volume_service.reg_volume(
                    path=abs_path,
                    name=name,
                    unique_mount_point=unique_mount_point,
                    info=info,
                    register_files=register_files,
                )
                print(f"\n登记成功: {result}")
            except Exception as e:
                print(f"\n登记失败: {e}")
        else:
            # ── 无路径 → 全手动 ──
            serial = input("请输入卷序列号: ").strip()
            if not serial:
                print("错误: 序列号不能为空。")
                return

            device_id = input("请输入所属设备序列号（直接回车默认 EXTERNAL_DEVICE）: ").strip() or "EXTERNAL_DEVICE"

            print("\n" + VolumeTypeMenu.prompt_text())
            while True:
                code = input(VolumeTypeMenu.input_hint()).strip()
                file_system = VolumeTypeMenu.from_code(code)
                if file_system is not None:
                    break
                print("无效输入，请按菜单输入对应编号。")

            capacity_input = input("请输入卷容量（字节，直接回车则留空）: ").strip()
            capacity: int | None = None
            if capacity_input:
                try:
                    capacity = int(capacity_input)
                except ValueError:
                    print("警告: 容量格式不正确，将留空")

            path_input = input("请输入卷路径（直接回车则留空）: ").strip()
            volume_path = path_input if path_input else None

            try:
                result = self.app.volume_service.register_volume_by_info(
                    serial=serial,
                    device_id=device_id,
                    name=name,
                    file_system=file_system,
                    capacity=capacity,
                    unique_mount_point=unique_mount_point,
                    volume_path=volume_path,
                    info=info,
                )
                print(f"\n登记成功: {result}")
            except Exception as e:
                print(f"\n登记失败: {e}")

    def do_register_volume_by_csv(self, arg: str) -> None:
        """
        通过 CSV 文件登记卷及其文件记录

        用法: register_volume_by_csv
        输入卷路径，CSV 须包含列: sha256, hash, size, path
          - 输入有效路径 → 自动检测卷信息（需挂载）
          - 留空 → 手动输入所有卷信息（无需挂载）
        """
        if self._missing_service():
            return

        csv_path = input("请输入 CSV 文件路径: ").strip()
        if not csv_path:
            print("错误: CSV 文件路径不能为空。")
            return

        volume_path = input("请输入卷路径（直接回车则手动输入所有卷信息，无需挂载）: ").strip()

        from pathlib import Path as P
        abs_csv = str(P(csv_path).resolve())
        from datetime import datetime as dt
        csv_mtime = dt.fromtimestamp(P(abs_csv).stat().st_mtime)

        name_input = input("请输入卷名称（直接回车则使用序列号）: ").strip()
        name = name_input if name_input else None

        ump = input("请输入全局唯一挂载点标识 unique_mount_point（直接回车则留空，建议使用绝对路径）: ").strip()
        unique_mount_point = ump if ump else None

        print("—— 以下为卷其他信息（info）——")
        info = self._interactive_kv()

        if volume_path:
            # ── 有路径 → 自动检测 ──
            abs_path = str(P(volume_path).resolve())
        else:
            # ── 无路径 → 全手动 ──
            serial = input("请输入卷序列号: ").strip()
            if not serial:
                print("错误: 序列号不能为空。")
                return

            device_id = input("请输入所属设备序列号（直接回车默认 EXTERNAL_DEVICE）: ").strip() or "EXTERNAL_DEVICE"

            print("\n" + VolumeTypeMenu.prompt_text())
            while True:
                code = input(VolumeTypeMenu.input_hint()).strip()
                file_system = VolumeTypeMenu.from_code(code)
                if file_system is not None:
                    break
                print("无效输入，请按菜单输入对应编号。")

            capacity_input = input("请输入卷容量（字节，直接回车则留空）: ").strip()
            capacity: int | None = None
            if capacity_input:
                try:
                    capacity = int(capacity_input)
                except ValueError:
                    print("警告: 容量格式不正确，将留空")

            path_input = input("请输入卷的根路径（用于计算文件相对路径，直接回车则留空）: ").strip()
            volume_root_path = path_input if path_input else None

        try:
            import pandas as pd
            df = pd.read_csv(abs_csv)
            required = {"sha512", "hash", "size", "path"}
            missing = required - set(df.columns)
            if missing:
                print(f"错误: CSV 缺少必要列: {missing}")
                return

            if volume_path:
                result = self.app.volume_service.register_volume_by_csv(
                    path=str(P(volume_path).resolve()),
                    df=df,
                    name=name,
                    unique_mount_point=unique_mount_point,
                    info=info,
                    add_time=csv_mtime,
                )
            else:
                result = self.app.volume_service.register_volume_by_csv_data(
                    df=df,
                    serial=serial,
                    device_id=device_id,
                    name=name,
                    file_system=file_system,
                    capacity=capacity,
                    unique_mount_point=unique_mount_point,
                    info=info,
                    volume_path=volume_root_path,
                    add_time=csv_mtime,
                )
            print(f"\n登记成功: {result}")
        except Exception as e:
            print(f"\n登记失败: {e}")

    def do_get(self, arg: str) -> None:
        """
        查询卷

        用法: get
        输入卷序列号查询，留空则列出全部。
        """
        if self._missing_service():
            return

        target = input("请输入卷序列号（留空则列出全部）: ").strip()
        if not target:
            self.do_list(arg)
            return

        volume = self.app.volume_service.get_volume(target)
        if volume is None:
            print("\n未找到该卷。")
            return
        print(f"\n{volume}")

    def do_list(self, arg: str) -> None:
        """
        列出所有卷

        用法: list
        """
        if self._missing_service():
            return
        volumes = self.app.volume_service.list_volumes()
        if not volumes:
            print("（无卷）")
            return
        for v in volumes:
            print(v)

    # ── 字段更新 ────────────────────────────────────────────

    def do_set_name(self, arg: str) -> None:
        """更新卷名称。用法: set_name <序列号> <新名称>"""
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
        old, new = self.app.volume_service.set_name(serial, name)
        print(f"名称: {old} → {new}")

    def do_set_device_id(self, arg: str) -> None:
        """更新卷所属设备。用法: set_device_id <序列号> <新设备序列号>"""
        if self._missing_service():
            return
        parts = arg.strip().split()
        if len(parts) == 2:
            serial, device_id = parts
        else:
            serial = input("序列号: ").strip()
            device_id = input("新所属设备序列号（Device 或 SuperDevice）: ").strip()
            if not serial or not device_id:
                print("序列号和新设备序列号不能为空。")
                return
        old, new = self.app.volume_service.set_device_id(serial, device_id)
        print(f"所属设备: {old} → {new}")

    def do_set_state(self, arg: str) -> None:
        """更新卷状态。用法: set_state <序列号>"""
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
        print(VolumeStateMenu.prompt_text())
        while True:
            code = input(VolumeStateMenu.input_hint()).strip()
            state = VolumeStateMenu.from_code(code)
            if state is not None:
                break
            print("无效输入，请按菜单输入对应编号。")
        old, new = self.app.volume_service.set_state(serial, state)
        print(f"状态: {old.value} → {new.value}")

    def do_set_capacity(self, arg: str) -> None:
        """更新卷容量。用法: set_capacity <序列号> <容量>"""
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
        old, new = self.app.volume_service.set_capacity(serial, capacity)
        print(f"容量: {old} → {new}")

    # ── info 操作 ───────────────────────────────────────────

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
        old, new = self.app.volume_service.set_info(serial, info)
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
        old, new = self.app.volume_service.append_info(serial, data)
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
        old, new = self.app.volume_service.delete_info(serial, key)
        self._print_info_diff(old, new)

    # ── 序列号与移除 ────────────────────────────────────────

    def do_set_serial(self, arg: str) -> None:
        """重置卷序列号。用法: set_serial <旧序列号> <新序列号>"""
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
        old, new = self.app.volume_service.set_serial(old_serial, new_serial)
        print(f"序列号: {old} → {new}")

    def do_remove(self, arg: str) -> None:
        """软删除卷（标记 REMOVED）。用法: remove <序列号>"""
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
            self.app.volume_service.remove_volume(serial)
        except Exception as e:
            print(f"\n错误: {e}")
            return
        print(f"已移除卷: {serial}")
