# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: ai生成，待检查 - 领域层 Device 异常定义 - 设备业务异常


class DeviceInUseError(Exception):
    """设备仍被引用（占用），无法标记为 REMOVED。

    当设备仍作为超级设备的子设备（state=USING）使用，
    或仍有未移除（非 REMOVED）的卷建立在其上时抛出。
    """

    def __init__(
        self,
        serial: str,
        *,
        super_device_using: int = 0,
        volumes: int = 0,
    ) -> None:
        """初始化设备占用异常。

        Args:
            serial: 被占用的设备序列号。
            super_device_using: 仍在使用的超级设备数量，默认 0。
            volumes: 仍建立在设备上的卷数量，默认 0。
        """
        self.serial = serial
        self.super_device_using = super_device_using
        self.volumes = volumes

        parts = []
        if super_device_using:
            parts.append(f"仍被 {super_device_using} 个超级设备使用")
        if volumes:
            parts.append(f"仍有 {volumes} 个卷建立在设备上")
        detail = "、".join(parts) if parts else "仍被其他对象引用"
        super().__init__(f"device {serial} 无法标记为 REMOVED：{detail}")
