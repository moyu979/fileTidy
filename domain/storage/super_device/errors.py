# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: ai生成，待检查 - 领域层 SuperDevice 异常定义 - 超级设备业务异常


class SubDeviceInUseError(Exception):
    """子项已被另一个超级设备以 USING 关联占用，无法挂载。

    当一个 device 或 super_device 作为子项挂载到超级设备时，
    若它已作为另一个超级设备的 USING 子项（独占约束）则抛出。
    """

    def __init__(self, sub_device_id: str, current_super_device_id: str) -> None:
        """初始化子项占用异常。

        Args:
            sub_device_id: 被占用的子项序列号。
            current_super_device_id: 当前以 USING 占用该子项的超级设备序列号。
        """
        self.sub_device_id = sub_device_id
        self.current_super_device_id = current_super_device_id
        super().__init__(
            f"sub_device {sub_device_id} 已被超级设备 {current_super_device_id} 使用，无法挂载"
        )


class SubDeviceUnavailableError(Exception):
    """子项自身不可用（已移除/故障），无法挂载。"""

    def __init__(self, sub_device_id: str, state) -> None:
        """初始化子项不可用异常。

        Args:
            sub_device_id: 不可用的子项序列号。
            state: 子项当前状态。
        """
        self.sub_device_id = sub_device_id
        self.state = state
        super().__init__(
            f"sub_device {sub_device_id} 当前状态 {state} 不可用（已移除/故障），无法挂载"
        )


class SubDeviceNotFoundError(Exception):
    """子项既不是已登记的 device，也不是已登记的 super_device。"""

    def __init__(self, sub_device_id: str) -> None:
        """初始化子项不存在异常。

        Args:
            sub_device_id: 未找到的子项序列号。
        """
        self.sub_device_id = sub_device_id
        super().__init__(
            f"sub_device {sub_device_id} 不存在（既不是 device 也不是 super_device）"
        )


class SuperDeviceInUseError(Exception):
    """超级设备仍被引用（占用），无法标记为 REMOVED。

    当超级设备仍作为其他超级设备的子设备（state=USING，层叠），
    或仍有未移除（非 REMOVED）的卷建立在其上时抛出。
    """

    def __init__(
        self,
        serial: str,
        *,
        super_device_using: int = 0,
        volumes: int = 0,
    ) -> None:
        """初始化超级设备占用异常。

        Args:
            serial: 被占用的超级设备序列号。
            super_device_using: 仍以 USING 引用该超级设备的超级设备数量，默认 0。
            volumes: 仍建立在超级设备上的卷数量，默认 0。
        """
        self.serial = serial
        self.super_device_using = super_device_using
        self.volumes = volumes

        parts = []
        if super_device_using:
            parts.append(f"仍被 {super_device_using} 个超级设备使用")
        if volumes:
            parts.append(f"仍有 {volumes} 个卷建立在超级设备上")
        detail = "、".join(parts) if parts else "仍被其他对象引用"
        super().__init__(f"super_device {serial} 无法标记为 REMOVED：{detail}")
