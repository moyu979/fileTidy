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
