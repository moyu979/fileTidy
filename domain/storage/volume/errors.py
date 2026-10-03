# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 领域层 Volume 异常定义 - 卷业务异常
# NOTE: file 子系统未完成（设计未定稿）：files 占用参数为临时方案，后续可能移除。


class VolumeInUseError(Exception):
    """卷仍被引用（占用），无法标记为 REMOVED。

    当卷仍作为超级卷的子卷（state=USING）使用，
    或仍有未移除（非 REMOVED）的文件位于该卷上时抛出。
    """

    def __init__(
        self,
        serial: str,
        *,
        super_volumes: int = 0,
        files: int = 0,
    ) -> None:
        """初始化卷占用异常。

        Args:
            serial: 被占用的卷序列号。
            super_volumes: 仍在使用的超级卷数量，默认 0。
            files: 仍位于卷上的文件数量，默认 0。
        """
        self.serial = serial
        self.super_volumes = super_volumes
        self.files = files

        parts = []
        if super_volumes:
            parts.append(f"仍被 {super_volumes} 个超级卷使用")
        if files:
            parts.append(f"仍有 {files} 个文件位于卷上")
        detail = "、".join(parts) if parts else "仍被其他对象引用"
        super().__init__(f"volume {serial} 无法标记为 REMOVED：{detail}")


class VolumeAlreadyRegisteredError(Exception):
    """该 serial 已被一条**非 REMOVED** 的行占用，不能重复登记。

    与 `VolumeAlreadyRemovedError` 是互斥的两种事实：那个类表示「占着这个 serial 的行
    处于 REMOVED」。调用方靠异常类型区分，不需要再看 `state`。
    """

    def __init__(self, serial: str, *, state=None) -> None:
        """初始化重复登记异常。

        Args:
            serial: 已被占用的卷序列号。
            state: 已存在那行的状态（诊断用；正常为 VolumeState 成员）。
        """
        self.serial = serial
        self.state = state
        super().__init__(f"volume {serial} already registered (state={state})")


class VolumeAlreadyRemovedError(Exception):
    """该 volume（或它占用的 serial）已处于 REMOVED。

    两类命中场景共享同一个事实：
    - `reg_volume`：要登记的 serial 被一条软删除行占位（serial 是主键，墓碑不会消失）。
    - `remove_volume`：目标已经是 REMOVED，属重复移除。
    """

    def __init__(self, serial: str) -> None:
        """初始化「已移除」异常。

        Args:
            serial: 已处于 REMOVED 的卷序列号。
        """
        self.serial = serial
        super().__init__(f"volume {serial} already removed")


class VolumeNotRemovedError(Exception):
    """该 volume 未处于 REMOVED —— 复活的前提不成立。

    用于 `revive_volume` 的前置校验：只有 REMOVED 才谈得上复活。
    """

    def __init__(self, serial: str, state) -> None:
        """初始化「未移除」异常。

        Args:
            serial: 卷序列号。
            state: 卷当前状态（诊断用）。
        """
        self.serial = serial
        self.state = state
        super().__init__(f"volume {serial} not removed (state={state})")


class VolumeNotFoundError(Exception):
    """该 serial 在仓储中不存在。

    命令式方法（update / remove / revive / 改 serial）的前置校验失败时抛出；
    只读查询（`get_volume` / `list_volumes`）不抛 —— 查不到返回 None 是正常结果。
    """

    def __init__(self, serial: str) -> None:
        """初始化「卷不存在」异常。

        Args:
            serial: 未找到的卷序列号。
        """
        self.serial = serial
        super().__init__(f"volume {serial} not found")
