# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 应用层 Volume 服务 - 卷业务用例编排

import json
import logging
from datetime import datetime
import shutil
from pathlib import Path

import pandas as pd

from application.storage.file.file_service import FileService
from domain.storage.file.new_file import NewFile
from domain.storage.device.repo import DeviceRepositoryABC as DeviceRepository
from domain.storage.super_device.repo import SuperDeviceRepositoryABC as SuperDeviceRepository
from domain.storage.volume.base import Volume
from domain.storage.volume.enum import VolumeState
from domain.storage.volume.events import (
    VolumeFieldUpdated,
    VolumeInfoChanged,
    VolumeInfoSet,
    VolumeRegistered,
    VolumeRemoved,
    VolumeSerialChanged,
)
from domain.storage.volume.repo import VolumeRepositoryABC as VolumeRepository
from infra.operation_log.operation_log import log_event
from infra.system.storage.volume.get_file_system import get_file_system
from infra.system.storage.volume.get_path import get_path
from infra.system.storage.volume.get_super_device_id import get_super_device_id
from infra.system.storage.volume.get_volume_capacity import get_volume_capacity
from infra.system.storage.volume.get_volume_serial_by_path import get_volume_serial_by_path
from infra.system.storage.volume.is_mount_point import is_mount_point
from infra.system.storage.volume.is_volume import is_volume
from infra.common.id_generator import generate_id
from infra.common.time_defaults import LAST_CHECK_TIME_ORIGIN

# NOTE: file 子系统未完成（设计未定稿）：本服务对 file_service / NewFile 的依赖，
#       以及初始化/登记时扫描文件、CSV 登记文件等流程均为临时接入，待 file 重新设计后统一调整或摘除。

logger = logging.getLogger(__name__)


class VolumeService:
    """卷服务类。

    提供卷的初始化、登记、查询等业务逻辑。
    """
    def __init__(
        self,
        volume_repository: VolumeRepository,
        file_svc: FileService,
        device_repository: DeviceRepository,
        super_device_repository: SuperDeviceRepository,
    ) -> None:
        """初始化卷服务。

        Args:
            volume_repository: 卷仓储实例。
            file_svc: 文件服务实例。
            device_repository: 设备仓储实例。
            super_device_repository: 超级设备仓储实例。
        """
        self.volume_repository = volume_repository
        self.file_service = file_svc
        self.device_repository = device_repository
        self.super_device_repository = super_device_repository
        logger.info("VolumeService constructed")

    # ── 内部辅助 ──────────────────────────────────────────────

    def _resolve_device_id(self, device_id: str, add_time) -> str:
        """校验 device_id 是有效的 Device 或 SuperDevice。

        Args:
            device_id: 设备 ID。
            add_time: 添加时间。

        Returns:
            验证通过的设备 ID。

        Raises:
            ValueError: device_id 既不是 Device 也不是 SuperDevice 时抛出。
        """
        if self.super_device_repository.is_exist(device_id):
            return device_id

        if self.device_repository.is_exist(device_id):
            return device_id

        raise ValueError(
            f"无法解析 device_id '{device_id}'："
            f"该 ID 既不是 Device，也不是 SuperDevice"
        )

    @staticmethod
    def _normalize_info(info: str | dict | None) -> str:
        """将 info 统一序列化为 JSON 字符串存储。

        Args:
            info: 信息字典、JSON 字符串或 None。

        Returns:
            序列化后的 JSON 字符串。
        """
        if info is None or info == "":
            return ""
        if isinstance(info, dict):
            return json.dumps(info, ensure_ascii=False)
        return info

    def _build_and_save_volume(
        self,
        *,
        serial: str,
        base: Path,
        name: str,
        info: str | dict | None,
        unique_mount_point: str | None,
        state: VolumeState | None = None,
        file_system: str | None = None,
        device_id: str | None = None,
        capacity: int | None = None,
        add_time: datetime | None = None,
    ) -> Volume:
        """构造 Volume 对象、写入仓库、打事件日志（不含文件注册）。

        当传入 device_id / capacity / file_system 时跳过自动检测，
        适用于卷已卸载等需要手动指定信息的场景。

        Args:
            serial: 卷序列号。
            base: 卷的基本路径。
            name: 卷名称。
            info: 附加信息。
            unique_mount_point: 唯一挂载点。
            state: 卷状态，不传则自动检测（默认 HEALTHY）。
            file_system: 文件系统类型，不传则自动检测。
            device_id: 所属设备 ID，不传则自动从路径解析。
            capacity: 卷容量（字节），不传则自动检测。
            add_time: 卷登记时间，不传则使用当前时间。

        Returns:
            创建的 Volume 实例。
        """
        device_id = device_id or get_super_device_id(str(base))
        add_time = add_time or datetime.now()
        last_check_time = LAST_CHECK_TIME_ORIGIN
        state = state or VolumeState.HEALTHY
        capacity = capacity or get_volume_capacity(str(base))
        file_system = file_system or get_file_system(str(base))

        # 确保 device_id 指向一个真正的 Device 或 SuperDevice
        device_id = self._resolve_device_id(device_id, add_time)

        volume = Volume.create(
            serial=serial,
            device_id=device_id,
            name=name or serial,
            add_time=add_time,
            last_check_time=last_check_time,
            state=state,
            capacity=capacity,
            unique_mount_point=unique_mount_point,
            file_system=file_system,
            info=self._normalize_info(info),
            volume_path=str(base),
        )

        self.volume_repository.reg_volume(volume)
        log_event(VolumeRegistered(volume))

        return volume

    # ── 初始化新卷 ────────────────────────────────────────────

    def init_volume(
        self,
        path: str,
        name,
        unique_mount_point,
        info,
        state: VolumeState | None = None,
        file_system: str | None = None,
    ) -> Volume:
        """初始化一个新的卷。

        在指定路径创建卷结构（datas 和 meta 目录），注册卷信息并扫描已有文件。

        Args:
            path: 卷路径。
            name: 卷名称。
            unique_mount_point: 唯一挂载点。
            info: 附加信息。
            state: 卷状态。
            file_system: 文件系统类型。

        Returns:
            创建的 Volume 实例。

        Raises:
            ValueError: 路径不是挂载点、路径不是目录或已经是卷时抛出。
        """
        if not is_mount_point(path):
            raise ValueError("不可以将一个非挂载点设置为卷")
        if is_volume(path):
            raise ValueError("该路径已经是 volume，请使用 reg 登记")

        serial = generate_id()
        base = Path(path).resolve()
        if not base.is_dir():
            raise ValueError(f"路径不是目录: {path}")

        # 将根目录下所有内容暂移入临时目录，再重命名为 datas
        staging = base / f".filetidy_volume_init_{serial}"
        if staging.exists():
            raise ValueError(f"临时目录已存在，请重试: {staging}")
        staging.mkdir()
        for child in list(base.iterdir()):
            if child.resolve() == staging.resolve():
                continue
            shutil.move(str(child), str(staging / child.name))

        datas_dir = base / "datas"
        if datas_dir.exists():
            raise ValueError(f"收纳后仍存在 datas，无法完成初始化: {datas_dir}")
        shutil.move(str(staging), str(datas_dir))

        meta_dir = base / "meta"
        if meta_dir.exists():
            raise ValueError(f"已存在 meta，无法初始化: {meta_dir}")
        meta_dir.mkdir()
        (meta_dir / serial).touch()

        volume = self._build_and_save_volume(
            serial=serial,
            base=base,
            name=name or serial,
            info=info,
            unique_mount_point=unique_mount_point,
        )

        # NOTE: file 子系统未完成（设计未定稿）：注册 datas 下文件为临时行为，待重设计后决定保留/删除
        if volume.datas_path:
            self.file_service.register_folder(
                folder_path=volume.datas_path,
                volume_serial=volume.serial,
                volume_path=volume.datas_path,
            )

        return volume

    # ── 登记已有卷 ────────────────────────────────────────────

    def reg_volume(
        self,
        path: str,
        name: str | None = None,
        unique_mount_point: str | None = None,
        info: str | dict | None = None,
        register_files: bool = True,
    ) -> str:
        """登记一个已有的卷。

        Args:
            path: 卷路径。
            name: 卷名称。
            unique_mount_point: 唯一挂载点。
            info: 附加信息。
            register_files: 是否同时注册卷中的文件。

        Returns:
            卷的 JSON 字符串。

        Raises:
            ValueError: 路径不是挂载点时抛出。
        """
        if not is_mount_point(path):
            raise ValueError("路径不是挂载点")

        base = Path(path).resolve()
        if not is_volume(str(base)):
            raise ValueError("卷目录结构不完整，需要 datas 和 meta 文件夹")

        serial = next((base / "meta").iterdir()).name

        if self.volume_repository.is_exist(serial):
            raise ValueError(f"卷 {serial} 已存在")

        volume = self._build_and_save_volume(
            serial=serial,
            base=base,
            name=name,
            info=info,
            unique_mount_point=unique_mount_point,
        )

        if register_files and volume.datas_path:
            # NOTE: file 子系统未完成（设计未定稿）：注册 datas 下文件为临时行为，待重设计后决定保留/删除
            self.file_service.register_folder(
                folder_path=volume.datas_path,
                volume_serial=volume.serial,
                volume_path=volume.datas_path,
            )

        return volume.to_json()

    # ── 手动信息登记 ──────────────────────────────────────────

    def register_volume_by_info(
        self,
        serial: str,
        device_id: str = "",
        name: str | None = None,
        add_time: datetime | None = None,
        last_check_time: datetime | None = None,
        state: VolumeState | None = None,
        capacity: int | None = None,
        unique_mount_point: str | None = None,
        file_system: str | None = None,
        info: str | dict | None = None,
        volume_path: str | None = None,
    ) -> str:
        """全手动登记卷，所有参数由调用方传入，不进行任何自动检测。

        与 reg_volume 不同：不依赖挂载点目录结构，卷已卸载时也可用。
        """
        if add_time is None:
            add_time = datetime.now()
        if last_check_time is None:
            last_check_time = LAST_CHECK_TIME_ORIGIN
        if state is None:
            state = VolumeState.UNKNOWN

        volume = Volume.create(
            serial=serial,
            device_id=device_id,
            name=name or serial,
            add_time=add_time,
            last_check_time=last_check_time,
            state=state,
            capacity=capacity,
            unique_mount_point=unique_mount_point,
            file_system=file_system,
            info=self._normalize_info(info),
            volume_path=volume_path if volume_path is not None else get_path(serial),
        )

        if self.volume_repository.is_exist(volume):
            raise ValueError(f"卷 {serial} 已存在")
        self.volume_repository.reg_volume(volume)
        log_event(VolumeRegistered(volume))
        return volume.to_json()

    # ── 通过 CSV 登记 ────────────────────────────────────────
    # TODO: 对 datas 相对路径的计算逻辑有点乱，
    #       register_volume_by_csv 自动加 datas，
    #       register_volume_by_csv_data 不加，
    #       后面需要统一梳理一下设计。

    def register_volume_by_csv(
        self,
        path: str,
        df: pd.DataFrame,
        name: str | None = None,
        unique_mount_point: str | None = None,
        info: str | dict | None = None,
        device_id: str | None = None,
        capacity: int | None = None,
        file_system: str | None = None,
        add_time: datetime | None = None,
    ) -> str:
        """通过 DataFrame 登记卷及其文件记录。

        卷信息由参数直接传入，文件信息由 DataFrame 提供。
        DataFrame 必须包含列: sha256, hash, size, path
        \n        当 device_id / capacity / file_system 传入时跳过自动检测，
        适用于卷已挂载但不想遍历文件系统的场景。
        """
        base = Path(path).resolve()
        add_time = add_time or datetime.now()
        if not is_volume(str(base)):
            raise ValueError("卷目录结构不完整，需要 datas 和 meta 文件夹")

        serial = next((base / "meta").iterdir()).name

        volume = self._build_and_save_volume(
            serial=serial,
            base=base,
            name=name or serial,
            info=info,
            unique_mount_point=unique_mount_point,
            device_id=device_id,
            capacity=capacity,
            file_system=file_system,
            add_time=add_time,
        )

        # NOTE: file 子系统未完成（设计未定稿）：通过 DataFrame 登记文件为临时行为
        self.file_service.register_by_csv(
            df=df,
            volume_serial=volume.serial,
            volume_path=volume.datas_path or "",
            add_time=add_time,
        )

        return volume.to_json()

    # ── 纯数据 CSV 登记（无需挂载）────────────────────────────

    def register_volume_by_csv_data(
        self,
        df: pd.DataFrame,
        serial: str,
        device_id: str = "",
        name: str | None = None,
        file_system: str | None = None,
        capacity: int | None = None,
        unique_mount_point: str | None = None,
        info: str | dict | None = None,
        volume_path: str | None = None,
        add_time: datetime | None = None,
    ) -> str:
        """纯数据驱动的 CSV 登记，不依赖任何目录结构，卷可完全卸载。

        卷信息全部通过参数手动传入，文件信息由 DataFrame 提供。
        DataFrame 必须包含列: sha256, hash, size, path
        """
        volume = self._build_and_save_volume(
            serial=serial,
            base=Path(volume_path) if volume_path else Path(),
            name=name or serial,
            info=info,
            unique_mount_point=unique_mount_point,
            device_id=device_id,
            capacity=capacity,
            file_system=file_system,
            add_time=add_time,
        )

        # NOTE: file 子系统未完成（设计未定稿）：通过 DataFrame 登记文件为临时行为
        self.file_service.register_by_csv(
            df=df,
            volume_serial=volume.serial,
            volume_path=volume.datas_path or "",
            add_time=add_time,
        )

        return volume.to_json()

    # ── 查询 ────────────────────────────────────────────────

    def list_volumes(self) -> list[str]:
        """列出所有卷（返回 JSON 字符串列表）。"""
        return [v.to_json() for v in self.volume_repository.list_volumes()]

    def get_volume(self, serial: str) -> str | None:
        """按序列号查询卷。"""
        v = self.volume_repository.get_volume(serial)
        return v.to_json() if v else None

    # ── 字段更新 ────────────────────────────────────────────

    def set_name(self, serial: str, name: str) -> tuple[str, str]:
        """更新卷名称。

        Args:
            serial: 卷序列号。
            name: 新名称。

        Returns:
            tuple[str, str]: (旧值, 新值)。
        """
        volume = self.volume_repository.get_volume(serial)
        if volume is None:
            raise ValueError(f"volume {serial} not found")
        old = volume.name
        self.volume_repository.update_volume(serial, name=name)
        log_event(VolumeFieldUpdated(serial, "name", old, name))
        return (old, name)

    def set_device_id(self, serial: str, device_id: str) -> tuple[str, str]:
        """更新卷所属设备/超级设备。

        校验新的 device_id 必须指向已登记的 Device 或 SuperDevice。

        Args:
            serial: 卷序列号。
            device_id: 新所属设备序列号。

        Returns:
            tuple[str, str]: (旧值, 新值)。
        """
        volume = self.volume_repository.get_volume(serial)
        if volume is None:
            raise ValueError(f"volume {serial} not found")
        validated = self._resolve_device_id(device_id, volume.add_time)
        old = volume.device_id
        self.volume_repository.update_volume(serial, device_id=validated)
        log_event(VolumeFieldUpdated(serial, "device_id", old, validated))
        return (old, validated)

    def set_state(self, serial: str, state: VolumeState) -> tuple[VolumeState, VolumeState]:
        """更新卷状态。

        Args:
            serial: 卷序列号。
            state: 新状态。

        Returns:
            tuple[VolumeState, VolumeState]: (旧值, 新值)。
        """
        volume = self.volume_repository.get_volume(serial)
        if volume is None:
            raise ValueError(f"volume {serial} not found")
        old = volume.state
        self.volume_repository.update_volume(serial, state=state)
        log_event(VolumeFieldUpdated(serial, "state", old, state))
        return (old, state)

    def set_capacity(self, serial: str, capacity: int) -> tuple[int | None, int]:
        """更新卷容量。

        Args:
            serial: 卷序列号。
            capacity: 新容量（字节）。

        Returns:
            tuple[int | None, int]: (旧值, 新值)。
        """
        volume = self.volume_repository.get_volume(serial)
        if volume is None:
            raise ValueError(f"volume {serial} not found")
        old = volume.capacity
        self.volume_repository.update_volume(serial, capacity=capacity)
        log_event(VolumeFieldUpdated(serial, "capacity", old, capacity))
        return (old, capacity)

    # ── info 操作（JSON 文本） ──────────────────────────────

    @staticmethod
    def _parse_info(info_str: str | None) -> dict:
        """解析 info JSON 文本为字典，空值返回空字典。"""
        if not info_str:
            return {}
        try:
            return json.loads(info_str)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_info(self, serial: str, info: dict) -> tuple[dict, dict]:
        """全量替换 info（JSON 文本）。返回 (旧info, 新info)。"""
        volume = self.volume_repository.get_volume(serial)
        if volume is None:
            raise ValueError(f"volume {serial} not found")
        old = self._parse_info(volume.info)
        new_str = json.dumps(info, ensure_ascii=False)
        self.volume_repository.update_volume(serial, info=new_str)
        log_event(VolumeInfoSet(serial, old, info))
        return (old, info)

    def append_info(self, serial: str, data: dict) -> tuple[dict, dict]:
        """合并键值对到现有 info（JSON 文本）。返回 (旧info, 新info)。

        逐键记录 VolumeInfoChanged：旧有键 → replace；新增键 → add。
        """
        volume = self.volume_repository.get_volume(serial)
        if volume is None:
            raise ValueError(f"volume {serial} not found")
        old = self._parse_info(volume.info)
        new_info = {**old, **data}
        new_str = json.dumps(new_info, ensure_ascii=False)
        self.volume_repository.update_volume(serial, info=new_str)
        for key, new_val in data.items():
            if key in old:
                log_event(VolumeInfoChanged(serial, "replace", key, old[key], new_val))
            else:
                log_event(VolumeInfoChanged(serial, "add", key, None, new_val))
        return (old, new_info)

    def delete_info(self, serial: str, key: str) -> tuple[dict, dict]:
        """从 info 中删除指定键（JSON 文本）。返回 (旧info, 新info)。"""
        volume = self.volume_repository.get_volume(serial)
        if volume is None:
            raise ValueError(f"volume {serial} not found")
        old = self._parse_info(volume.info)
        new_info = dict(old)
        old_val = new_info.pop(key, None)
        new_str = json.dumps(new_info, ensure_ascii=False)
        self.volume_repository.update_volume(serial, info=new_str)
        if key in old:
            log_event(VolumeInfoChanged(serial, "remove", key, old_val, None))
        return (old, new_info)

    # ── 序列号与移除 ────────────────────────────────────────

    def set_serial(self, old_serial: str, new_serial: str) -> tuple[str, str]:
        """重置卷序列号，同步更新关联表。返回 (旧序列号, 新序列号)。"""
        if not self.volume_repository.is_exist(old_serial):
            raise ValueError(f"volume {old_serial} not found")
        self.volume_repository.update_serial(old_serial, new_serial)
        log_event(VolumeSerialChanged(old_serial=old_serial, new_serial=new_serial))
        return (old_serial, new_serial)

    def remove_volume(self, serial: str) -> None:
        """软删除卷（标记 REMOVED）。

        Args:
            serial: 卷序列号。

        Raises:
            ValueError: 卷不存在。
            VolumeInUseError: 卷仍被文件/超级卷引用（透传自仓储层）。
        """
        self.volume_repository.remove_volume(serial)
        log_event(VolumeRemoved(serial))

    # ── 卷内文件查询 / 扫描（file 子系统未完成，暂未实现）─────

    def list_files(
        self,
        volume_or_path: str,
        directory: str = "/",
    ) -> list[NewFile]:
        """列出指定卷在数据库中记录的文件。

        参数可以是卷序列号（serial），也可以是卷所在路径。
        directory 为卷内相对路径，默认 "/" 表示 datas 下全部，
        例如传入 "videos/2024" 则只返回该目录下的文件。

        返回：
            list[NewFile]: 匹配的文件列表；无匹配时返回空列表。
        """
        # TODO: 实现——解析 volume → 获取 volume_path → 调 file_repo 按 volume_id 查询
        ...

    def scan_files(
        self,
        volume_or_path: str,
        directory: str = "/",
    ) -> tuple[list[NewFile], list[NewFile]]:
        """扫描指定卷下实际存在的文件，与数据库记录交叉比对。

        参数可以是卷序列号（serial），也可以是卷所在路径。
        遍历 volume_path/datas/<directory> 下所有实际文件，
        计算哈希后与数据库比对，返回 (已登记列表, 未登记列表)。

        不同文件系统类型（ntfs/exfat/ltfs 等）可通过注册对应
        Scanner 策略来定制扫描行为。

        返回：
            tuple[list[NewFile], list[NewFile]]:
                (存在于数据库的文件列表, 不存在于数据库的文件列表)
        """
        # TODO: 实现——解析 volume → 获取 volume_path → 遍历文件系统 →
        #        计算哈希 → 查 DB 比对 → 分类返回
        ...
