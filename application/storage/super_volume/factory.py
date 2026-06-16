"""
应用层工厂：创建 SuperVolume 前校验子卷均存在
"""

from domain.storage.super_volume.factory import create_super_volume
from domain.storage.volume.repo import volume_repository_abc as VolumeRepository


class super_volume_factory:
    """SuperVolume 应用层工厂，校验所有子卷 ID 有效后再委托领域工厂创建"""

    volume_repository: VolumeRepository | None = None

    @classmethod
    def set_volume_repository(cls, vr: VolumeRepository) -> None:
        cls.volume_repository = vr

    @classmethod
    def new_super_volume(
        cls,
        *,
        serial: str,
        name: str,
        svtype: str,
        method: str,
        add_time,
        last_check_time,
        state,
        info: str,
        volumes: list[str],
    ) -> "SuperVolume":
        from domain.storage.super_volume.base import SuperVolume

        if not serial:
            raise ValueError("serial is required")
        if not svtype:
            raise ValueError("svtype is required")

        # 校验每个子卷都存在
        if cls.volume_repository is None:
            raise RuntimeError("super_volume_factory.volume_repository 未初始化")

        for vol_id in volumes:
            vol = cls.volume_repository.get_volume(vol_id)
            if vol is None:
                raise ValueError(f"卷 {vol_id} 不存在，无法创建超级卷")

        return create_super_volume(
            serial=serial,
            name=name,
            svtype=svtype,
            method=method,
            add_time=add_time,
            last_check_time=last_check_time,
            state=state,
            info=info,
            volumes=volumes,
        )
