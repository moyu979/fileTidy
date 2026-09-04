# CHECK: 待检查 - 应用层 SuperVolume 服务 - 超级卷业务用例编排

"""
超级卷服务 —— 管理 SuperVolume 的注册、查询、字段更新与子卷管理。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from domain.storage.super_volume.base import SuperVolume
from domain.storage.super_volume.enum import SuperVolumeState
from domain.storage.super_volume.events import (
    SuperVolumeFieldUpdated,
    SuperVolumeInfoChanged,
    SuperVolumeInfoSet,
    SuperVolumeRegistered,
    SuperVolumeRemoved,
    SuperVolumeSerialChanged,
    VolumesAddedToSuperVolume,
    VolumesRemovedFromSuperVolume,
)
from domain.storage.super_volume.repo import super_volume_repository_abc as SuperVolumeRepository
from domain.storage.super_volume.structure import SuperVolumeStructure
from domain.storage.volume.repo import volume_repository_abc as VolumeRepository
from infra.common.id_generator import generate_id
from infra.common.time_defaults import LAST_CHECK_TIME_ORIGIN
from infra.operation_log.operation_log import log_event

logger = logging.getLogger(__name__)


class SuperVolumeService:
    """超级卷服务类。

    提供超级卷的注册、查询、字段更新、序列号变更、子卷管理和移除等业务逻辑。
    """

    def __init__(
        self,
        super_volume_repository: SuperVolumeRepository,
        volume_repository: VolumeRepository,
    ) -> None:
        """初始化超级卷服务。

        Args:
            super_volume_repository: 超级卷仓储实例。
            volume_repository: 卷仓储实例。
        """
        self.super_volume_repository = super_volume_repository
        self.volume_repository = volume_repository
        logger.info("SuperVolumeService initialized")

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
        """注册一个新的超级卷。

        Args:
            serial: 超级卷序列号，为空则自动生成。
            name: 超级卷名称，为空则使用序列号短格式。
            svtype: 超级卷类型（必填），如 "copy"、"snapraid_raid5"。
            method: 组合方法，暂不启用。
            add_time: 添加时间，为空则使用当前时间。
            last_check_time: 最后一次检查时间，为空则使用默认值。
            state: 超级卷状态，为空则使用 UNKNOWN。
            info: 附加信息。
            volumes: 子卷 ID 列表（至少一个）。

        Returns:
            注册成功的超级卷 JSON 字符串。

        Raises:
            ValueError: svtype 为空、子卷列表为空、子卷不存在或超级卷已存在时抛出。
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

        # 校验每个子卷都存在
        for vol_id in volumes:
            vol = self.volume_repository.get_volume(vol_id)
            if vol is None:
                raise ValueError(f"卷 {vol_id} 不存在，无法创建超级卷")

        # ── 按 svtype 分派构造对应子类 ──
        super_volume = SuperVolume.create(
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
        """按序列号查询超级卷。

        Args:
            serial: 超级卷序列号。

        Returns:
            超级卷 JSON 字符串，未找到时返回 None。
        """
        sv = self.super_volume_repository.get_super_volume(serial)
        return sv.to_json() if sv else None

    def list_super_volumes(self) -> list[str]:
        """列出所有已注册超级卷的 JSON 字符串列表。

        Returns:
            超级卷 JSON 字符串列表。
        """
        return [sv.to_json() for sv in self.super_volume_repository.list_super_volume()]

    # ── 子卷管理 ────────────────────────────────────────────

    def add_volumes(
        self,
        *,
        super_volume_serial: str,
        volume_ids: list[str],
    ) -> str:
        """向已存在的超级卷添加一批子卷。

        Args:
            super_volume_serial: 目标超级卷序列号。
            volume_ids: 要添加的子卷 ID 列表。

        Returns:
            更新后的超级卷 JSON 字符串。

        Raises:
            ValueError: 超级卷或子卷不存在时抛出。
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
        return self._fresh_json(super_volume_serial)

    def remove_volumes(
        self,
        *,
        super_volume_serial: str,
        volume_ids: list[str],
    ) -> str:
        """从超级卷移除一批子卷（关联标记为 UNUSED）。

        Args:
            super_volume_serial: 目标超级卷序列号。
            volume_ids: 要移除的子卷 ID 列表。

        Returns:
            更新后的超级卷 JSON 字符串。

        Raises:
            ValueError: 超级卷不存在或存在非 USING 成员卷时抛出。
        """
        if not super_volume_serial:
            raise ValueError("super_volume_serial 不能为空")
        if not volume_ids:
            raise ValueError("至少需要提供一个子卷 ID")

        sv = self.super_volume_repository.get_super_volume(super_volume_serial)
        if sv is None:
            raise ValueError(f"超级卷 {super_volume_serial} 不存在")

        self.super_volume_repository.remove_volumes(super_volume_serial, volume_ids)
        log_event(VolumesRemovedFromSuperVolume(super_volume_serial, volume_ids))

        logger.info(
            "超级卷已移除子卷: super_volume=%s volumes=%s",
            super_volume_serial, volume_ids,
        )
        return self._fresh_json(super_volume_serial)

    def _fresh_json(self, super_volume_serial: str) -> str:
        """重新查询超级卷并返回 JSON，供变更类操作统一收尾。"""
        updated = self.super_volume_repository.get_super_volume(super_volume_serial)
        return updated.to_json() if updated else ""

    # ── 字段更新 ────────────────────────────────────────────

    def set_name(self, serial: str, name: str) -> tuple[str, str]:
        """更新超级卷名称。

        Args:
            serial: 超级卷序列号。
            name: 新名称。

        Returns:
            tuple[str, str]: (旧值, 新值)。
        """
        sv = self.super_volume_repository.get_super_volume(serial)
        if sv is None:
            raise ValueError(f"super_volume {serial} not found")
        old = sv.name
        self.super_volume_repository.update_super_volume(serial, name=name)
        log_event(SuperVolumeFieldUpdated(serial, "name", old, name))
        return (old, name)

    def set_svtype(self, serial: str, svtype: str) -> tuple[str, str]:
        """更新超级卷类型。

        Args:
            serial: 超级卷序列号。
            svtype: 新类型，如 "copy"、"snapraid_raid5"。

        Returns:
            tuple[str, str]: (旧值, 新值)。
        """
        sv = self.super_volume_repository.get_super_volume(serial)
        if sv is None:
            raise ValueError(f"super_volume {serial} not found")
        old = sv.svtype
        self.super_volume_repository.update_super_volume(serial, svtype=svtype)
        log_event(SuperVolumeFieldUpdated(serial, "svtype", old, svtype))
        return (old, svtype)

    def set_state(self, serial: str, state: SuperVolumeState) -> tuple[SuperVolumeState, SuperVolumeState]:
        """更新超级卷状态。

        Args:
            serial: 超级卷序列号。
            state: 新状态。

        Returns:
            tuple[SuperVolumeState, SuperVolumeState]: (旧值, 新值)。
        """
        sv = self.super_volume_repository.get_super_volume(serial)
        if sv is None:
            raise ValueError(f"super_volume {serial} not found")
        old = sv.state
        self.super_volume_repository.update_super_volume(serial, state=state)
        log_event(SuperVolumeFieldUpdated(serial, "state", old, state))
        return (old, state)

    # ── info 操作（JSON 文本） ──────────────────────────────

    @staticmethod
    def _parse_info(info_str: str | None) -> dict:
        """解析 info JSON 文本为字典。

        Args:
            info_str: JSON 格式的 info 字符串。

        Returns:
            解析后的字典，空值返回空字典。
        """
        if not info_str:
            return {}
        try:
            return json.loads(info_str)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_info(self, serial: str, info: dict) -> tuple[dict, dict]:
        """全量替换 info。

        Args:
            serial: 超级卷序列号。
            info: 新的 info 字典。

        Returns:
            tuple[dict, dict]: (旧info, 新info)。
        """
        sv = self.super_volume_repository.get_super_volume(serial)
        if sv is None:
            raise ValueError(f"super_volume {serial} not found")
        old = self._parse_info(sv.info)
        new_str = json.dumps(info, ensure_ascii=False)
        self.super_volume_repository.update_super_volume(serial, info=new_str)
        log_event(SuperVolumeInfoSet(serial, old, info))
        return (old, info)

    def append_info(self, serial: str, data: dict) -> tuple[dict, dict]:
        """合并键值对到现有 info。

        Args:
            serial: 超级卷序列号。
            data: 待合并的键值对字典。

        Returns:
            tuple[dict, dict]: (旧info, 新info)。
        """
        sv = self.super_volume_repository.get_super_volume(serial)
        if sv is None:
            raise ValueError(f"super_volume {serial} not found")
        old = self._parse_info(sv.info)
        new_info = {**old, **data}
        new_str = json.dumps(new_info, ensure_ascii=False)
        self.super_volume_repository.update_super_volume(serial, info=new_str)
        for key, new_val in data.items():
            if key in old:
                log_event(SuperVolumeInfoChanged(serial, "replace", key, old[key], new_val))
            else:
                log_event(SuperVolumeInfoChanged(serial, "add", key, None, new_val))
        return (old, new_info)

    def delete_info(self, serial: str, key: str) -> tuple[dict, dict]:
        """从 info 中删除指定键。

        Args:
            serial: 超级卷序列号。
            key: 待删除的键名。

        Returns:
            tuple[dict, dict]: (旧info, 新info)。
        """
        sv = self.super_volume_repository.get_super_volume(serial)
        if sv is None:
            raise ValueError(f"super_volume {serial} not found")
        old = self._parse_info(sv.info)
        new_info = dict(old)
        old_val = new_info.pop(key, None)
        new_str = json.dumps(new_info, ensure_ascii=False)
        self.super_volume_repository.update_super_volume(serial, info=new_str)
        if key in old:
            log_event(SuperVolumeInfoChanged(serial, "remove", key, old_val, None))
        return (old, new_info)

    # ── 序列号与移除 ────────────────────────────────────────

    def set_serial(self, old_serial: str, new_serial: str) -> tuple[str, str]:
        """重置超级卷序列号，同步更新关联表。返回 (旧序列号, 新序列号)。"""
        if not self.super_volume_repository.is_exist(old_serial):
            raise ValueError(f"super_volume {old_serial} not found")
        self.super_volume_repository.update_super_volume_serial(old_serial, new_serial)
        log_event(SuperVolumeSerialChanged(old_serial=old_serial, new_serial=new_serial))
        return (old_serial, new_serial)

    def remove_super_volume(self, serial: str) -> None:
        """软删除超级卷（标记 REMOVED），并释放其 USING 子卷关联。

        Args:
            serial: 超级卷序列号。

        Raises:
            ValueError: 超级卷不存在（透传自仓储层）。
        """
        self.super_volume_repository.remove_super_volume(serial)
        log_event(SuperVolumeRemoved(serial))
