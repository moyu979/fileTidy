# CHECK: 待检查 - 领域层 SuperVolume 结构定义 - 超级卷层级结构模型

"""
超级卷-子卷 关联关系领域对象
"""

from __future__ import annotations

from datetime import datetime

from domain.storage.super_device.enum import RelationState


class SuperVolumeStructure:
    """超级卷与子卷之间的关联关系领域对象。"""

    def __init__(
        self,
        super_volume_serial: str,
        volume_id: str,
        add_time: datetime | None = None,
        state: RelationState = RelationState.USING,
        info: str = "",
    ) -> None:
        """初始化超级卷-子卷关联关系。

        Args:
            super_volume_serial: 超级卷序列号。
            volume_id: 子卷序列号。
            add_time: 关联时间，默认为当前时间。
            state: 关联状态，默认为 USING。
            info: 附加信息。
        """
        self.super_volume_serial = super_volume_serial
        self.volume_id = volume_id
        self.add_time = add_time or datetime.now()
        self.state = state
        self.info = info

    def to_snapshot(self) -> dict:
        """将关联关系转换为快照字典。

        Returns:
            包含关联关系所有字段的字典。
        """
        return {
            "super_volume_serial": self.super_volume_serial,
            "volume_id": self.volume_id,
            "add_time": self.add_time.isoformat() if self.add_time else None,
            "state": self.state.value if self.state else None,
            "info": self.info,
        }
