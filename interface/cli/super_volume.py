"""
超级卷子命令组
"""

from __future__ import annotations

import cmd

from application.app import App


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
        super().__init__()
        self.app = app

    def _missing_service(self) -> bool:
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

        print(
            "请选择超级卷类型:\n"
            "  1 — manual_copy (手动拷贝)\n"
            "  2 — stack (堆叠)\n"
        )
        code = input("请输入编号 (1/2): ").strip()
        if code == "1":
            svtype = "manual_copy"
        elif code == "2":
            svtype = "stack"
        else:
            print("无效输入，请输入 1 或 2。")
            return

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
