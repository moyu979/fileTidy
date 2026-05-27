from datetime import datetime
import shutil
from pathlib import Path

from application.storage.file.file_service import file_service
from application.storage.volume.factory import volume_factory
from domain.storage.device.base import Device as DeviceBase
from domain.storage.volume.base import Volume
from domain.storage.volume.enum import VolumeState
from domain.storage.volume.events import VolumeRegistered
from domain.storage.volume.volume_repo import volume_repository_abc as VolumeRepository
from domain.storage.device.repo import device_repository_abc as DeviceRepository
from infra.operate_log.operate_log import log_event
from infra.persistence.storage import device_repository
from infra.system.storage.volume.get_file_system import get_file_system
from infra.system.storage.volume.get_super_device_id import get_super_device_id
from infra.system.storage.volume.get_volume_capacity import get_volume_capacity
from infra.system.storage.volume.is_volume import is_volume
from infra.system.storage.volume.is_mountPoint import is_mount_point
from shared.id_generator import generate_id
from shared.time_defaults import LAST_CHECK_TIME_ORIGIN

class volume_service:
    def __init__(
        self,
        volume_repository: VolumeRepository,
        device_repository: DeviceRepository,
        file_svc: file_service,
    ) -> None:
        self.volume_repository = volume_repository
        self.device_repository = device_repository
        self.file_service = file_svc

    def init_volume(self, path: str,name,unique_mount_point,info) -> Volume:
        if not is_mount_point(path):
            raise ValueError("不可以将一个非挂载点设置为卷")

        if is_volume(path):
            raise ValueError("这个卷已经是一个volume了，请使用“reg对已有卷进行登记”")

        serial = generate_id()

        base = Path(path).resolve()
        if not base.is_dir():
            raise ValueError(f"路径不是目录: {path}")

        # 先建临时目录，把卷根下除临时目录外的子文件与子目录全部移入，再整体重命名为 datas
        staging = base / f".filetidy_volume_init_{serial}"
        if staging.exists():
            raise ValueError(f"临时目录已存在，请重试: {staging}")
        staging.mkdir()
        children = [
            p for p in base.iterdir() if p.resolve() != staging.resolve()
        ]
        for child in children:
            dest = staging / child.name
            if dest.exists():
                raise ValueError(
                    f"无法在临时目录下收纳 {child.name!r}：{dest} 已存在"
                )
            shutil.move(str(child), str(dest))

        data_dir = base / "data"
        if data_dir.exists():
            raise ValueError(f"收纳后仍存在 data，无法完成初始化: {data_dir}")
        shutil.move(str(staging), str(data_dir))

        meta_dir = base / "meta"
        if meta_dir.exists():
            raise ValueError(f"已存在 meta，无法初始化: {meta_dir}")
        meta_dir.mkdir()
        (meta_dir / serial).touch()

        supuer_device_id=get_super_device_id(path)
        name=name if name else serial
        add_time=datetime.now()
        last_check_time = LAST_CHECK_TIME_ORIGIN

        state=VolumeState.HEALTHY
        capacity=get_volume_capacity(path)
        unique_mount_point=unique_mount_point

        file_system=get_file_system(path)


        volume = volume_factory.new_volume(
            serial=serial,
            super_device_id=supuer_device_id,
            name=name,
            add_time=add_time,
            last_check_time=last_check_time,
            state=state,
            capacity=capacity,
            unique_mount_point=unique_mount_point,
            file_system=file_system,
            info=info,
            volume_path=str(base),
        )

        self.volume_repository.reg_volume(volume)
        log_event(VolumeRegistered(volume))
        
        for file_path in data_dir.rglob("*"):
            if file_path.is_file():
                self.file_service.reg_file_by_path(file_path,volume)
