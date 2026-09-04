# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - CLI 超级卷命令 - 超级卷管理命令行接口

"""
超级卷子命令组
"""

from __future__ import annotations

import cmd

from application.app import App
from domain.storage.super_volume.enum import SuperVolumeStateMenu, SuperVolumeTypeMenu


class SuperVolumeCLI(cmd.Cmd):
    """超级卷相关命令行界面"""

    intro = """
========================================
  超级卷管理
========================================
输入 'help' 查看可用命令
输入 'back' 或 Ctrl+D 返回主菜单
"""

    prompt = "filetidy/super_volume> "

    def __init__(self, app: App | None) -> None:
        """初始化 SuperVolumeCLI 实例。

        Args:
            app: 应用实例，可为 None。
        """
        super().__init__()
        self.app = app

    def _missing_service(self) -> bool:
        """检查超级卷服务是否可用。

        Returns:
            如果应用未初始化或超级卷服务不可用返回 True，否则返回 False。
        """
        if self.app is None:
            print("错误: 应用未初始化，无法执行超级卷操作。")
            return True
        if getattr(self.app, "super_volume_service", None) is None:
            print("错误: 超级卷服务不可用。")
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
        添加超级卷

        用法: reg
        将提示您依次输入参数，直接敲回车表示使用默认值
        """
        if self._missing_service():
            return

        name = input("请输入超级卷名称，可以留空: ").strip() or None

        print(SuperVolumeTypeMenu.prompt_text())
        svtype = None
        while svtype is None:
            code = input(SuperVolumeTypeMenu.input_hint()).strip()
            svtype = SuperVolumeTypeMenu.from_code(code)
            if svtype is None:
                print("无效输入，请重新选择。")

        info = input("请输入超级卷其他信息: ").strip() or None

        # 输入子卷 ID，直到输入 q 或空为止
        volumes = []
        while True:
            vol_id = input("请输入子卷 ID（输入 q 或回车结束）: ").strip()
            if vol_id == "q" or vol_id == "":
                break
            volumes.append(vol_id)

        if not volumes:
            print("错误: 至少需要提供一个子卷 ID。")
            return

        try:
            result = self.app.super_volume_service.reg_super_volume(
                name=name,
                svtype=svtype,
                info=info,
                volumes=volumes,
            )
            print(f"\n成功登记超级卷: {result}")
        except Exception as e:
            print(f"\n错误: {e}")

    def do_add_volume(self, arg: str) -> None:
        """
        向已有超级卷添加子卷

        用法: add_volume
        将提示输入超级卷序列号和子卷 ID 列表
        """
        if self._missing_service():
            return

        super_volume_serial = input("请输入目标超级卷序列号: ").strip()
        if not super_volume_serial:
            print("错误: 超级卷序列号不能为空。")
            return

        volumes = []
        while True:
            vol_id = input("请输入要添加的子卷 ID（输入 q 或回车结束）: ").strip()
            if vol_id == "q" or vol_id == "":
                break
            volumes.append(vol_id)

        if not volumes:
            print("错误: 至少需要提供一个子卷 ID。")
            return

        try:
            result = self.app.super_volume_service.add_volumes(
                super_volume_serial=super_volume_serial,
                volume_ids=volumes,
            )
            print(f"\n添加成功: {result}")
        except Exception as e:
            print(f"\n错误: {e}")

    def do_get(self, arg: str) -> None:
        """
        查询超级卷

        用法: get
        输入超级卷序列号，留空则列出全部
        """
        if self._missing_service():
            return

        target = input("请输入超级卷序列号（留空则列出全部）: ").strip()
        if not target:
            self.do_list(arg)
            return

        sv = self.app.super_volume_service.get_super_volume(target)
        if sv is None:
            print("\n未找到该超级卷。")
            return

        print(f"\n{sv}")

    def do_list(self, arg: str) -> None:
        """
        列出所有超级卷

        用法: list
        """
        if self._missing_service():
            return
        volumes = self.app.super_volume_service.list_super_volumes()
        if not volumes:
            print("（无超级卷）")
            return
        for v in volumes:
            print(v)

    # ── 字段更新 ────────────────────────────────────────────

    def do_set_name(self, arg: str) -> None:
        """更新超级卷名称。用法: set_name <序列号> <新名称>"""
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
        old, new = self.app.super_volume_service.set_name(serial, name)
        print(f"名称: {old} → {new}")

    def do_set_svtype(self, arg: str) -> None:
        """更新超级卷类型。用法: set_svtype <序列号>"""
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
        print(SuperVolumeTypeMenu.prompt_text())
        svtype = None
        while svtype is None:
            code = input(SuperVolumeTypeMenu.input_hint()).strip()
            svtype = SuperVolumeTypeMenu.from_code(code)
            if svtype is None:
                print("无效输入，请重新选择。")
        old, new = self.app.super_volume_service.set_svtype(serial, svtype)
        print(f"类型: {old} → {new}")

    def do_set_state(self, arg: str) -> None:
        """更新超级卷状态。用法: set_state <序列号>"""
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
        print(SuperVolumeStateMenu.prompt_text())
        while True:
            code = input(SuperVolumeStateMenu.input_hint()).strip()
            state = SuperVolumeStateMenu.from_code(code)
            if state is not None:
                break
            print("无效输入，请按菜单输入对应编号。")
        old, new = self.app.super_volume_service.set_state(serial, state)
        print(f"状态: {old.value} → {new.value}")

    # ── info 操作 ───────────────────────────────────────────

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
        old, new = self.app.super_volume_service.set_info(serial, info)
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
        old, new = self.app.super_volume_service.append_info(serial, data)
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
        old, new = self.app.super_volume_service.delete_info(serial, key)
        self._print_info_diff(old, new)

    # ── 序列号与子卷/移除 ──────────────────────────────────

    def do_set_serial(self, arg: str) -> None:
        """重置超级卷序列号。用法: set_serial <旧序列号> <新序列号>"""
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
        old, new = self.app.super_volume_service.set_serial(old_serial, new_serial)
        print(f"序列号: {old} → {new}")

    def do_remove_volumes(self, arg: str) -> None:
        """
        从超级卷移除子卷

        用法: remove_volumes
        将提示输入超级卷序列号和子卷 ID 列表
        """
        if self._missing_service():
            return

        super_volume_serial = input("请输入目标超级卷序列号: ").strip()
        if not super_volume_serial:
            print("错误: 超级卷序列号不能为空。")
            return

        volumes = []
        while True:
            vol_id = input("请输入要移除的子卷 ID（输入 q 或回车结束）: ").strip()
            if vol_id == "q" or vol_id == "":
                break
            volumes.append(vol_id)

        if not volumes:
            print("错误: 至少需要提供一个子卷 ID。")
            return

        try:
            result = self.app.super_volume_service.remove_volumes(
                super_volume_serial=super_volume_serial,
                volume_ids=volumes,
            )
            print(f"\n移除成功: {result}")
        except Exception as e:
            print(f"\n错误: {e}")

    def do_remove(self, arg: str) -> None:
        """软删除超级卷（标记 REMOVED）。用法: remove <序列号>"""
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
            self.app.super_volume_service.remove_super_volume(serial)
        except Exception as e:
            print(f"\n错误: {e}")
            return
        print(f"已移除超级卷: {serial}")
