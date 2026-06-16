"""
超级卷服务 —— 管理 SuperVolume 的注册、查询
"""

from __future__ import annotations

import logging
from datetime import datetime

from datetime import datetime

from application.storage.super_volume.factory import super_volume_factory
from domain.storage.super_volume.enum import SuperVolumeState
from domain.storage.super_volume.events import (
    SuperVolumeRegistered,
    VolumesAddedToSuperVolume,
)
from domain.storage.super_volume.repo import super_volume_repository_abc as SuperVolumeRepository
from domain.storage.super_volume.structure import SuperVolumeStructure
from domain.storage.volume.repo import volume_repository_abc as VolumeRepository
from infra.operate_log.operate_log import log_event
from shared.id_generator import generate_id
from shared.time_defaults import LAST_CHECK_TIME_ORIGIN

logger = logging.getLogger(__name__)


class super_volume_service:
    """超级卷服务"""

    def __init__(
        self,
        super_volume_repository: SuperVolumeRepository,
        volume_repository: VolumeRepository,
    ) -> None:
        self.super_volume_repository = super_volume_repository
        self.volume_repository = volume_repository
        logger.info("super_volume service initialized")

    def reg_super_volume(
        self,
        *,
        serial: str | None = None,
        name: str | None = None,
        svtype: str | None = None,
        method: str | None = None,
        add_time: datetime | None = None,
        last_check_time: datetime | None = None,
        state: SuperVolumeState | None = None,
        info: str | None = None,
        volumes: list[str] | None = None,
    ) -> str:
        """
        注册一个超级卷。

        字段说明：
        - serial: 为空则自动生成
        - name: 为空则使用 serial 的短格式
        - svtype: 必填，如 "manual_copy"、"stack"
        - method: 暂不启用，默认空字符串
        - add_time: 为空则使用当前时间
        - last_check_time: 为空则使用 LAST_CHECK_TIME_ORIGIN
        - state: 为空则使用 UNKNOWN（刚创建尚未检测）
        - info: 默认为空字符串
        - volumes: 子卷 ID 列表，用于写入 SuperVolumeStructure
        """
        # ── 默认值处理 ──
        if serial is None:
            serial = generate_id()
        if name is None:
            name = serial[:8]
        if svtype is None:
            raise ValueError("svtype（超级卷类型）是必填字段")
        if method is None:
            method = ""
        if add_time is None:
            add_time = datetime.now()
        if last_check_time is None:
            last_check_time = LAST_CHECK_TIME_ORIGIN
        if state is None:
            state = SuperVolumeState.UNKNOWN
        if info is None:
            info = ""
        if volumes is None:
            volumes = []

        # ── 校验 ──
        if not volumes:
            raise ValueError("至少需要提供一个子卷 ID")

        if self.super_volume_repository.is_exist(serial):
            raise ValueError(f"超级卷 {serial} 已存在")

        # ── 通过工厂创建（含子卷存在性校验）─
        super_volume = super_volume_factory.new_super_volume(
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

        # ── 持久化 ──
        self.super_volume_repository.reg_super_volume(super_volume)
        log_event(SuperVolumeRegistered(super_volume))

        logger.info(
            "超级卷已注册: serial=%s name=%s type=%s volumes=%s",
            serial, name, svtype, volumes,
        )
        return super_volume.to_json()

    def get_super_volume(self, serial: str) -> str | None:
        """按序列号查询超级卷。"""
        sv = self.super_volume_repository.get_super_volume(serial)
        return sv.to_json() if sv else None

    def list_super_volumes(self) -> list[str]:
        """列出所有超级卷。"""
        return [sv.to_json() for sv in self.super_volume_repository.list_super_volume()]

    def add_volumes(
        self,
        *,
        super_volume_serial: str,
        volume_ids: list[str],
    ) -> str:
        """
        向已存在的超级卷添加一批子卷。

        参数:
        - super_volume_serial: 目标超级卷序列号
        - volume_ids: 要添加的子卷 ID 列表
        """
        if not super_volume_serial:
            raise ValueError("super_volume_serial 不能为空")
        if not volume_ids:
            raise ValueError("至少需要提供一个子卷 ID")

        # 校验超级卷存在
        sv = self.super_volume_repository.get_super_volume(super_volume_serial)
        if sv is None:
            raise ValueError(f"超级卷 {super_volume_serial} 不存在")

        # 校验每个子卷存在
        for vol_id in volume_ids:
            vol = self.volume_repository.get_volume(vol_id)
            if vol is None:
                raise ValueError(f"卷 {vol_id} 不存在")

        # 构建领域结构对象
        now = datetime.now()
        structures = [
            SuperVolumeStructure(
                super_volume_serial=super_volume_serial,
                volume_id=vol_id,
                add_time=now,
            )
            for vol_id in volume_ids
        ]

        # 持久化 structure 关联
        self.super_volume_repository.add_volumes(structures)
        log_event(VolumesAddedToSuperVolume(super_volume_serial, volume_ids))

        logger.info(
            "超级卷已添加子卷: super_volume=%s volumes=%s",
            super_volume_serial, volume_ids,
        )

        # 重新查询返回最新状态
        updated = self.super_volume_repository.get_super_volume(super_volume_serial)
        return updated.to_json() if updated else ""
