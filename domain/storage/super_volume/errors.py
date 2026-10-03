# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: ai生成，待检查 - 领域层 SuperVolume 异常定义 - 超级卷业务异常


class SuperVolumeNotFoundError(Exception):
    """该 serial 在仓储中不存在。

    命令式方法（update / remove / 改 serial）的前置校验失败时抛出；
    只读查询（`get_super_volume` / `list_super_volume`）不抛 —— 查不到返回 None 是正常结果。
    """

    def __init__(self, serial: str) -> None:
        """初始化「超级卷不存在」异常。

        Args:
            serial: 未找到的超级卷序列号。
        """
        self.serial = serial
        super().__init__(f"super_volume {serial} not found")


class SubVolumeInUseError(Exception):
    """子卷已被另一个超级卷以 USING 关联占用，无法挂载。"""

    def __init__(self, sub_volume_id: str, current_super_volume_id: str) -> None:
        """初始化子卷占用异常。

        Args:
            sub_volume_id: 被占用的子卷序列号。
            current_super_volume_id: 当前以 USING 占用该子卷的超级卷序列号。
        """
        self.sub_volume_id = sub_volume_id
        self.current_super_volume_id = current_super_volume_id
        super().__init__(
            f"sub_volume {sub_volume_id} 已被超级卷 {current_super_volume_id} 使用，无法挂载"
        )


class SubVolumeUnavailableError(Exception):
    """子卷自身不可用（已移除/故障），无法挂载。"""

    def __init__(self, sub_volume_id: str, state) -> None:
        """初始化子卷不可用异常。

        Args:
            sub_volume_id: 不可用的子卷序列号。
            state: 子卷当前状态。
        """
        self.sub_volume_id = sub_volume_id
        self.state = state
        super().__init__(
            f"sub_volume {sub_volume_id} 当前状态 {state} 不可用（已移除/故障），无法挂载"
        )


class SubVolumeNotFoundError(Exception):
    """子卷不是已登记的 volume。"""

    def __init__(self, sub_volume_id: str) -> None:
        """初始化子卷不存在异常。

        Args:
            sub_volume_id: 未找到的子卷序列号。
        """
        self.sub_volume_id = sub_volume_id
        super().__init__(f"sub_volume {sub_volume_id} 不存在（不是有效 volume）")


class SuperVolumeAlreadyRegisteredError(Exception):
    """该 serial 已被一条**非 REMOVED** 的行占用，不能重复登记。

    与 `SuperVolumeAlreadyRemovedError` 是互斥的两种事实：那个类表示
    「占着这个 serial 的行处于 REMOVED」。调用方靠异常类型区分，不需要再看 `state`。
    """

    def __init__(self, serial: str, *, state=None) -> None:
        """初始化重复登记异常。

        Args:
            serial: 已被占用的超级卷序列号。
            state: 已存在那行的状态（诊断用；正常为 SuperVolumeState 成员）。
        """
        self.serial = serial
        self.state = state
        super().__init__(f"super_volume {serial} already registered (state={state})")


class SuperVolumeAlreadyRemovedError(Exception):
    """该 super_volume（或它占用的 serial）已处于 REMOVED。

    两类命中场景共享同一个事实：
    - `reg_super_volume`：要登记的 serial 被一条软删除行占位。
    - `remove_super_volume`：目标已经是 REMOVED，属重复移除。
    """

    def __init__(self, serial: str) -> None:
        """初始化「已移除」异常。

        Args:
            serial: 已处于 REMOVED 的超级卷序列号。
        """
        self.serial = serial
        super().__init__(f"super_volume {serial} already removed")


class SuperVolumeNotRemovedError(Exception):
    """该 super_volume 未处于 REMOVED —— 复活的前提不成立。

    用于 `revive_super_volume` 的前置校验：只有 REMOVED 才谈得上复活。
    """

    def __init__(self, serial: str, state) -> None:
        """初始化「未移除」异常。

        Args:
            serial: 超级卷序列号。
            state: 超级卷当前状态（诊断用）。
        """
        self.serial = serial
        self.state = state
        super().__init__(f"super_volume {serial} not removed (state={state})")
