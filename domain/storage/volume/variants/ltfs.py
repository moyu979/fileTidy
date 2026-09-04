# CHECK: 待检查 - 领域层 LTFS 变体 - LTFS 文件系统卷实现

from datetime import datetime

from domain.storage.volume.base import Volume
from domain.storage.volume.enum import VolumeState


class LtfsVolume(Volume):
    """LTFS 线性磁带文件系统卷类。

    继承自 Volume 基类，代表使用 LTFS 文件系统的磁带卷。
    """
    _type_key = "ltfs"

    # TODO(P3): 当前仅透传构造函数，无任何子类特有行为，后续可添加 LTFS 特有逻辑
    def __init__(
        self,
        serial: str,
        device_id: str,
        name: str,
        add_time: datetime,
        last_check_time: datetime,
        state: str | VolumeState,
        capacity: int | None,
        unique_mount_point: str | None,
        file_system: str,
        info: str | None,
        volume_path: str | None,
    ) -> None:
        """初始化 LTFS 卷实例。

        Args:
            serial: 卷序列号。
            device_id: 关联的设备序列号。
            name: 卷名称。
            add_time: 添加时间。
            last_check_time: 最后一次检查时间。
            state: 卷状态。
            capacity: 卷容量（字节）。
            unique_mount_point: 唯一挂载点。
            file_system: 文件系统类型。
            info: 附加信息。
            volume_path: 卷路径。
        """
        super().__init__(
            serial, device_id, name, add_time, last_check_time,
            state, capacity, unique_mount_point, file_system, info, volume_path,
        )
