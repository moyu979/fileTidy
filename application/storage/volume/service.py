import json
from datetime import datetime
import shutil
from pathlib import Path

import pandas as pd

from application.storage.file.file_service import file_service
from application.storage.volume.factory import volume_factory
from domain.storage.file.new_file import NewFile
from domain.storage.device.repo import device_repository_abc as DeviceRepository
from domain.storage.super_device.repo import super_device_repository_abc as SuperDeviceRepository
from domain.storage.volume.base import Volume
from domain.storage.volume.enum import VolumeState
from domain.storage.volume.events import VolumeRegistered
from domain.storage.volume.repo import volume_repository_abc as VolumeRepository
from infra.operate_log.operate_log import log_event
from infra.system.storage.volume.get_file_system import get_file_system
from infra.system.storage.volume.get_path import get_path
from infra.system.storage.volume.get_super_device_id import get_super_device_id
from infra.system.storage.volume.get_volume_capacity import get_volume_capacity
from infra.system.storage.volume.get_volume_serial_by_path import get_volume_serial_by_path
from infra.system.storage.volume.is_mountPoint import is_mount_point
from infra.system.storage.volume.is_volume import is_volume
from shared.id_generator import generate_id
from shared.time_defaults import LAST_CHECK_TIME_ORIGIN


class volume_service:
    def __init__(
        self,
        volume_repository: VolumeRepository,
        file_svc: file_service,
        device_repository: DeviceRepository,
        super_device_repository: SuperDeviceRepository,
    ) -> None:
        self.volume_repository = volume_repository
        self.file_service = file_svc
        self.device_repository = device_repository
        self.super_device_repository = super_device_repository

    # ── 内部辅助 ──────────────────────────────────────────────

    def _resolve_device_id(self, device_id: str, add_time) -> str:
        """校验 device_id 是有效的 Device 或 SuperDevice，不自动升级。"""
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
        """将 info 统一序列化为 JSON 字符串存储。"""
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
            state: 卷状态，不传则自动检测（默认 HEALTHY）。
            file_system: 文件系统类型，不传则自动检测。
            device_id: 所属设备 ID，不传则自动从路径解析。
            capacity: 卷容量（字节），不传则自动检测。
            add_time: 卷登记时间，不传则使用当前时间。
        """
        device_id = device_id or get_super_device_id(str(base))
        add_time = add_time or datetime.now()
        last_check_time = LAST_CHECK_TIME_ORIGIN
        state = state or VolumeState.HEALTHY
        capacity = capacity or get_volume_capacity(str(base))
        file_system = file_system or get_file_system(str(base))

        # 确保 device_id 指向一个真正的 Device 或 SuperDevice
        device_id = self._resolve_device_id(device_id, add_time)

        volume = volume_factory.new_volume(
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

        # 注册 datas 下所有文件
        # TODO: 新增 skip_exist 参数，跳过数据库中已存在的文件
        datas_dir = base / "datas"
        if datas_dir.is_dir():
            self.file_service.register_folder(
                folder_path=str(datas_dir),
                volume_serial=volume.serial,
                volume_path=str(datas_dir),
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
        if not is_mount_point(path):
            raise ValueError("路径不是挂载点")

        base = Path(path).resolve()
        datas_dir = base / "datas"
        meta_dir = base / "meta"

        if not datas_dir.is_dir():
            raise ValueError("卷目录下缺少 datas 文件夹")
        if not meta_dir.is_dir():
            raise ValueError("卷目录下缺少 meta 文件夹")

        actual_dirs = {p.name for p in base.iterdir() if p.is_dir()}
        expected = {"datas", "meta"}
        if extra := actual_dirs - expected:
            raise ValueError(f"卷目录下只能有 datas 和 meta，发现多余项: {extra}")

        meta_files = [f for f in meta_dir.iterdir() if f.is_file()]
        if len(meta_files) != 1:
            raise ValueError(f"meta 目录下应当只有一个文件作为序列号，发现 {len(meta_files)} 个")
        serial = meta_files[0].name

        volume = self._build_and_save_volume(
            serial=serial,
            base=base,
            name=name,
            info=info,
            unique_mount_point=unique_mount_point,
        )

        if register_files:
            # 注册 datas 下所有文件
            # TODO: 新增 skip_exist 参数，跳过数据库中已存在的文件
            datas_dir = base / "datas"
            if datas_dir.is_dir():
                self.file_service.register_folder(
                    folder_path=str(datas_dir),
                    volume_serial=volume.serial,
                    volume_path=str(datas_dir),
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

        volume = volume_factory.new_volume(
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
            volume_path=volume_path,
        )

        if self.volume_repository.is_exist(volume):
            raise ValueError(f"卷 {serial} 已存在")
        self.volume_repository.reg_volume(volume)
        log_event(VolumeRegistered(volume))
        return volume.to_json()

    # ── 通过 CSV 登记 ────────────────────────────────────────

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
        datas_dir = base / "datas"
        meta_dir = base / "meta"
        add_time = add_time or datetime.now()

        if not datas_dir.is_dir():
            raise ValueError("卷目录下缺少 datas 文件夹")
        if not meta_dir.is_dir():
            raise ValueError("卷目录下缺少 meta 文件夹")

        actual_dirs = {p.name for p in base.iterdir() if p.is_dir()}
        expected = {"datas", "meta"}
        if extra := actual_dirs - expected:
            raise ValueError(f"卷目录下只能有 datas 和 meta，发现多余项: {extra}")

        meta_files = [f for f in meta_dir.iterdir() if f.is_file()]
        if len(meta_files) != 1:
            raise ValueError(f"meta 目录下应当只有一个文件作为序列号，发现 {len(meta_files)} 个")
        serial = meta_files[0].name

        # 只登记卷（不含文件遍历）
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

        # 通过 DataFrame 登记文件
        # TODO: 新增 skip_exist 参数，跳过数据库中已存在的文件
        self.file_service.register_by_csv(
            df=df,
            volume_serial=volume.serial,
            volume_path=str(datas_dir),
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
        volume_json = self.register_volume_by_info(
            serial=serial,
            device_id=device_id,
            name=name,
            file_system=file_system,
            capacity=capacity,
            unique_mount_point=unique_mount_point,
            info=info,
            volume_path=volume_path,
            add_time=add_time,
        )

        self.file_service.register_by_csv(
            df=df,
            volume_serial=serial,
            volume_path=volume_path or "",
            add_time=add_time,
        )

        return volume_json

    # ── 查询 ────────────────────────────────────────────────

    def list_volumes(self) -> list[str]:
        """列出所有卷（返回 JSON 字符串列表）。"""
        return [v.to_json() for v in self.volume_repository.list_volume()]

    def get_volume(self, serial: str) -> str | None:
        """按序列号查询卷。"""
        v = self.volume_repository.get_volume(serial)
        return v.to_json() if v else None

    # ── 卷内文件查询 / 扫描 ────────────────────────────────

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

