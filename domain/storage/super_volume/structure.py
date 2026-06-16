"""
超级卷-子卷 关联关系领域对象
"""

from __future__ import annotations

from datetime import datetime

from domain.storage.super_device.enum import RelationState


class SuperVolumeStructure:
    """超级卷与子卷之间的关联关系"""

    def __init__(
        self,
        super_volume_serial: str,
        volume_id: str,
        add_time: datetime | None = None,
        state: RelationState = RelationState.USING,
        info: str = "",
    ) -> None:
        self.super_volume_serial = super_volume_serial
        self.volume_id = volume_id
        self.add_time = add_time or datetime.now()
        self.state = state
        self.info = info

    def to_snapshot(self) -> dict:
        return {
            "super_volume_serial": self.super_volume_serial,
            "volume_id": self.volume_id,
            "add_time": self.add_time.isoformat() if self.add_time else None,
            "state": self.state.value if self.state else None,
            "info": self.info,
        }
