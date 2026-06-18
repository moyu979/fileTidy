from datetime import datetime
import shutil
from pathlib import Path

import pandas as pd

from application.storage.file.file_service import file_service
from application.storage.volume.factory import volume_factory
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

    def _resolve_super_device_id(self, super_device_id: str, add_time) -> str:
        """校验 super_device_id 是有效的 Device 或 SuperDevice，不自动升级。"""
        if self.super_device_repository.is_exist(super_device_id):
            return super_device_id

        if self.device_repository.is_exist(super_device_id):
            return super_device_id

        raise ValueError(
            f"无法解析 super_device_id '{super_device_id}'："
            f"该 ID 既不是 SuperDevice，也不是 Device"
        )

    def _build_and_save_volume(
        self,
        *,
        serial: str,
        base: Path,
        name: str,
        info: str,
        unique_mount_point: str | None,
    ) -> Volume:
        """构造 Volume 对象、写入仓库、打事件日志（不含文件注册）。"""
        super_device_id = get_super_device_id(str(base))
        add_time = datetime.now()
        last_check_time = LAST_CHECK_TIME_ORIGIN
        state = VolumeState.HEALTHY
        capacity = get_volume_capacity(str(base))
        file_system = get_file_system(str(base))

        # 确保 super_device_id 指向一个真正的 SuperDevice
        super_device_id = self._resolve_super_device_id(super_device_id, add_time)

        volume = volume_factory.new_volume(
            serial=serial,
            device_id=super_device_id,
            name=name or serial,
            add_time=add_time,
            last_check_time=last_check_time,
            state=state,
            capacity=capacity,
            unique_mount_point=unique_mount_point,
            file_system=file_system,
            info=info or "",
            volume_path=str(base),
        )

        self.volume_repository.reg_volume(volume)
        log_event(VolumeRegistered(volume))

        return volume

    # ── 初始化新卷 ────────────────────────────────────────────

    def init_volume(self, path: str, name, unique_mount_point, info) -> Volume:
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
            info="",
            unique_mount_point=unique_mount_point,
        )

        # 注册 datas 下所有文件
        datas_dir = base / "datas"
        if datas_dir.is_dir():
            self.file_service.register_folder(
                folder_path=str(datas_dir),
                volume_serial=volume.serial,
                volume_path=str(datas_dir),
            )

        return volume.to_json()

    # ── 通过 CSV 登记 ────────────────────────────────────────

    def register_volume_by_csv(
        self,
        path: str,
        df: pd.DataFrame,
        name: str | None = None,
        unique_mount_point: str | None = None,
        info: str = "",
    ) -> str:
        """通过 DataFrame 登记卷及其文件记录。

        卷信息由参数直接传入，文件信息由 DataFrame 提供。
        DataFrame 必须包含列: sha256, hash, size, path
        不校验挂载点，适用于卷已卸载的场景。
        """
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

        # 只登记卷（不含文件遍历）
        volume = self._build_and_save_volume(
            serial=serial,
            base=base,
            name=name or serial,
            info=info,
            unique_mount_point=unique_mount_point,
        )

        # 通过 DataFrame 登记文件
        self.file_service.register_by_csv(
            df=df,
            volume_serial=volume.serial,
            volume_path=str(datas_dir),
        )

        return volume.to_json()

    # ── 查询 ────────────────────────────────────────────────

    def list_volumes(self) -> list[str]:
        """列出所有卷（返回 JSON 字符串列表）。"""
        return [v.to_json() for v in self.volume_repository.list_volume()]

    def get_volume(self, serial: str) -> str | None:
        """按序列号查询卷。"""
        v = self.volume_repository.get_volume(serial)
        return v.to_json() if v else None

