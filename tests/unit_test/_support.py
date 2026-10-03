# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单元测试公共支持代码：内存仓储替身与假对象。

这些替身实现与真实仓储相同的**接口契约**，但只驻留内存，
用于隔离 application 层测试，避免依赖 SQLite / 文件系统。
"""

from __future__ import annotations

import copy
from contextlib import contextmanager
from datetime import datetime

from domain.storage.device.base import Device
from domain.storage.device.enum import DeviceState
from domain.storage.device.errors import (
    DeviceAlreadyRegisteredError,
    DeviceAlreadyRemovedError,
    DeviceNotFoundError,
    DeviceNotRemovedError,
)
from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.enum import SuperDeviceState
from domain.storage.super_device.errors import (
    SuperDeviceAlreadyRegisteredError,
    SuperDeviceAlreadyRemovedError,
    SuperDeviceNotFoundError,
    SuperDeviceNotRemovedError,
)
from domain.storage.super_volume.base import SuperVolume
from domain.storage.super_volume.errors import SuperVolumeNotFoundError
from domain.storage.volume.base import Volume
from domain.storage.volume.enum import VolumeState
from domain.storage.volume.errors import VolumeNotFoundError
from domain.storage.file.new_file import NewFile


def _field_name(field: str) -> str:
    """把数据库列名（type）映射回领域属性名（dtype）。"""
    return field


def _state_value(state):
    """枚举成员或原始字符串统一取 value，便于替身做状态比较。"""
    return getattr(state, "value", state)


class FakeDeviceRepository:
    """内存版 Device 仓储。"""

    def __init__(self, initial: list[Device] | None = None) -> None:
        self._store: dict[str, Device] = {}
        for device in initial or []:
            self.reg_device(device)

    def is_exist(self, device: Device | str) -> bool:
        serial = device.serial if isinstance(device, Device) else device
        return serial in self._store

    def reg_device(self, device: Device) -> None:
        existing = self._store.get(device.serial)
        if existing is not None:
            # 与真仓储同口径：REMOVED 行占位 与 活跃占用 是互斥的两种事实异常
            if _state_value(existing.state) == DeviceState.REMOVED.value:
                raise DeviceAlreadyRemovedError(device.serial)
            raise DeviceAlreadyRegisteredError(device.serial, state=existing.state)
        self._store[device.serial] = copy.deepcopy(device)

    def get_device(self, serial: str, exclude_removed: bool = True) -> Device | None:
        device = self._store.get(serial)
        if device is None:
            return None
        if exclude_removed and _state_value(device.state) == DeviceState.REMOVED.value:
            return None
        return copy.deepcopy(device)

    def list_devices(self, exclude_removed: bool = True) -> list[Device]:
        devices = list(self._store.values())
        if exclude_removed:
            devices = [
                d for d in devices
                if _state_value(d.state) != DeviceState.REMOVED.value
            ]
        return [copy.deepcopy(d) for d in devices]

    def update_device(self, serial: str, **fields) -> None:
        if serial not in self._store:
            raise DeviceNotFoundError(serial)
        device = self._store[serial]
        for key, value in fields.items():
            if value is None:  # None = 未提供该字段 → 保持原样
                continue
            if _field_name(key) == "state" and _state_value(value) == DeviceState.REMOVED.value:
                raise ValueError(
                    f"device {serial} 不允许通过 update_device 置为 REMOVED，"
                    f"请改用 remove_device（带引用校验）"
                )
            setattr(device, _field_name(key), value)

    def update_serial(self, old_serial: str, new_serial: str) -> None:
        if old_serial not in self._store:
            raise DeviceNotFoundError(old_serial)
        device = self._store.pop(old_serial)
        device.serial = new_serial
        self._store[new_serial] = device

    def remove_device(self, serial: str) -> None:
        if serial not in self._store:
            raise DeviceNotFoundError(serial)
        device = self._store[serial]
        if _state_value(device.state) == DeviceState.REMOVED.value:
            raise DeviceAlreadyRemovedError(serial)
        device.state = DeviceState.REMOVED

    def revive_device(self, serial: str) -> None:
        """复活设备（state → UNKNOWN）。不校验占用（被引用的设备进不了 REMOVED）。"""
        if serial not in self._store:
            raise DeviceNotFoundError(serial)
        device = self._store[serial]
        if _state_value(device.state) != DeviceState.REMOVED.value:
            raise DeviceNotRemovedError(serial, device.state)
        device.state = DeviceState.UNKNOWN


class FakeVolumeRepository:
    """内存版 Volume 仓储。"""

    def __init__(self, initial: list[Volume] | None = None) -> None:
        self._store: dict[str, Volume] = {}
        for volume in initial or []:
            self.reg_volume(volume)

    def is_exist(self, volume: Volume | str) -> bool:
        serial = volume.serial if isinstance(volume, Volume) else volume
        return serial in self._store

    def reg_volume(self, volume: Volume) -> None:
        self._store[volume.serial] = copy.deepcopy(volume)

    def get_volume(self, serial: str, exclude_removed: bool = True) -> Volume | None:
        volume = self._store.get(serial)
        if volume is None:
            return None
        if exclude_removed and _state_value(volume.state) == VolumeState.REMOVED.value:
            return None
        return copy.deepcopy(volume)

    def list_volumes(self, exclude_removed: bool = True) -> list[Volume]:
        volumes = list(self._store.values())
        if exclude_removed:
            volumes = [
                v for v in volumes
                if _state_value(v.state) != VolumeState.REMOVED.value
            ]
        return [copy.deepcopy(v) for v in volumes]

    def update_volume(self, serial: str, **fields) -> None:
        if serial not in self._store:
            raise VolumeNotFoundError(serial)
        for key, value in fields.items():
            if value is None:  # None = 未提供该字段 → 保持原样
                continue
            setattr(self._store[serial], _field_name(key), value)

    def update_serial(self, old_serial: str, new_serial: str) -> None:
        if old_serial not in self._store:
            raise VolumeNotFoundError(old_serial)
        volume = self._store.pop(old_serial)
        volume.serial = new_serial
        self._store[new_serial] = volume

    def remove_volume(self, serial: str) -> None:
        if serial not in self._store:
            raise VolumeNotFoundError(serial)
        self._store[serial].state = VolumeState.REMOVED


class FakeSuperDeviceRepository:
    """内存版 SuperDevice 仓储。"""

    def __init__(self, initial: list[SuperDevice] | None = None) -> None:
        self._store: dict[str, SuperDevice] = {}
        self._released: dict[str, list[str]] = {}  # 软删时释放的子项，供复活时恢复拓扑
        for sd in initial or []:
            self.reg_super_device(sd)

    def is_exist(self, super_device: SuperDevice | str) -> bool:
        serial = super_device.serial if isinstance(super_device, SuperDevice) else super_device
        return serial in self._store

    def reg_super_device(self, super_device: SuperDevice) -> None:
        existing = self._store.get(super_device.serial)
        if existing is not None:
            # 与真仓储同口径：REMOVED 行占位 与 活跃占用 是互斥的两种事实异常
            if _state_value(existing.state) == SuperDeviceState.REMOVED.value:
                raise SuperDeviceAlreadyRemovedError(super_device.serial)
            raise SuperDeviceAlreadyRegisteredError(
                super_device.serial, state=existing.state
            )
        self._store[super_device.serial] = copy.deepcopy(super_device)

    def get_super_device(self, serial: str, exclude_removed: bool = True) -> SuperDevice | None:
        sd = self._store.get(serial)
        if sd is None:
            return None
        if exclude_removed and _state_value(sd.state) == SuperDeviceState.REMOVED.value:
            return None
        return copy.deepcopy(sd)

    def list_super_device(self, exclude_removed: bool = True) -> list[SuperDevice]:
        items = list(self._store.values())
        if exclude_removed:
            items = [
                sd for sd in items
                if _state_value(sd.state) != SuperDeviceState.REMOVED.value
            ]
        return [copy.deepcopy(sd) for sd in items]

    def update_super_device(self, serial: str, **fields) -> None:
        if serial not in self._store:
            raise SuperDeviceNotFoundError(serial)
        for key, value in fields.items():
            if value is None:  # None = 未提供该字段 → 保持原样
                continue
            if _field_name(key) == "state" and _state_value(value) == SuperDeviceState.REMOVED.value:
                raise ValueError(
                    f"super_device {serial} 不允许通过 update_super_device 置为 REMOVED，"
                    f"请改用 remove_super_device（带引用校验）"
                )
            setattr(self._store[serial], _field_name(key), value)

    def update_super_device_serial(self, old_serial: str, new_serial: str) -> None:
        if old_serial not in self._store:
            raise SuperDeviceNotFoundError(old_serial)
        sd = self._store.pop(old_serial)
        sd.serial = new_serial
        self._store[new_serial] = sd

    def add_device(self, super_device_serial: str, device_serial: str, add_time: datetime) -> None:
        if super_device_serial not in self._store:
            raise SuperDeviceNotFoundError(super_device_serial)
        self._store[super_device_serial].devices.append(device_serial)

    def replace_device(
        self, super_device_serial: str, old_device_serial: str,
        new_device_serial: str, add_time: datetime,
    ) -> None:
        sd = self._store.get(super_device_serial)
        if sd is None:
            raise SuperDeviceNotFoundError(super_device_serial)
        try:
            idx = sd.devices.index(old_device_serial)
        except ValueError:
            raise ValueError(
                f"device {old_device_serial} not found in super_device {super_device_serial}"
            ) from None
        sd.devices[idx] = new_device_serial

    # TODO(P1): 「摘子项」功能暂缓，与真实仓储/ABC 同步停用。恢复时取消注释。
    #
    # def remove_device(self, super_device_serial: str, device_serial: str) -> None:
    #     sd = self._store.get(super_device_serial)
    #     if sd is None:
    #         raise ValueError(f"super_device {super_device_serial} not found")
    #     try:
    #         sd.devices.remove(device_serial)
    #     except ValueError:
    #         raise ValueError(
    #             f"device {device_serial} not found in super_device {super_device_serial}"
    #         ) from None

    def remove_super_device(self, serial: str) -> None:
        if serial not in self._store:
            raise SuperDeviceNotFoundError(serial)
        sd = self._store[serial]
        if _state_value(sd.state) == SuperDeviceState.REMOVED.value:
            raise SuperDeviceAlreadyRemovedError(serial)
        self._released[serial] = list(sd.devices)  # 记住被释放的子项，供复活恢复拓扑
        sd.devices = []  # 释放子项关联行（对应结构行 USING → SUPER_DEVICE_REMOVED）
        sd.state = SuperDeviceState.REMOVED

    def revive_super_device(self, serial: str) -> None:
        """复活超级设备（state → UNKNOWN），并挂回软删时释放的子项（恢复拓扑）。

        替身不做子项占用校验（无跨仓储占用关系）；真仓储会逐个校验并整体回滚。
        """
        if serial not in self._store:
            raise SuperDeviceNotFoundError(serial)
        sd = self._store[serial]
        if _state_value(sd.state) != SuperDeviceState.REMOVED.value:
            raise SuperDeviceNotRemovedError(serial, sd.state)
        sd.devices = self._released.pop(serial, [])
        sd.state = SuperDeviceState.UNKNOWN


class FakeSuperVolumeRepository:
    """内存版 SuperVolume 仓储。"""

    def __init__(self, initial: list[SuperVolume] | None = None) -> None:
        self._store: dict[str, SuperVolume] = {}
        for sv in initial or []:
            self.reg_super_volume(sv)

    def is_exist(self, super_volume: SuperVolume | str) -> bool:
        serial = super_volume.serial if isinstance(super_volume, SuperVolume) else super_volume
        return serial in self._store

    def reg_super_volume(self, super_volume: SuperVolume) -> None:
        self._store[super_volume.serial] = copy.deepcopy(super_volume)

    def get_super_volume(self, serial: str) -> SuperVolume | None:
        sv = self._store.get(serial)
        return copy.deepcopy(sv) if sv is not None else None

    def list_super_volume(self) -> list[SuperVolume]:
        return [copy.deepcopy(sv) for sv in self._store.values()]

    def add_volumes(self, structures) -> None:
        for st in structures:
            if st.super_volume_serial not in self._store:
                raise SuperVolumeNotFoundError(st.super_volume_serial)
            self._store[st.super_volume_serial].volumes.append(st.volume_id)

    def update_super_volume(self, serial: str, **fields) -> None:
        if serial not in self._store:
            raise SuperVolumeNotFoundError(serial)
        for key, value in fields.items():
            if value is None:  # None = 未提供该字段 → 保持原样
                continue
            setattr(self._store[serial], _field_name(key), value)

    def update_super_volume_serial(self, old_serial: str, new_serial: str) -> None:
        if old_serial not in self._store:
            raise SuperVolumeNotFoundError(old_serial)
        sv = self._store.pop(old_serial)
        sv.serial = new_serial
        self._store[new_serial] = sv

    def remove_volumes(self, super_volume_serial: str, volume_ids: list[str]) -> None:
        if super_volume_serial not in self._store:
            raise SuperVolumeNotFoundError(super_volume_serial)
        sv = self._store[super_volume_serial]
        for volume_id in volume_ids:
            if volume_id not in sv.volumes:
                raise ValueError(
                    f"卷 {volume_id} 不是超级卷 {super_volume_serial} 的 USING 成员，无法移除"
                )
            sv.volumes.remove(volume_id)

    def remove_super_volume(self, serial: str) -> None:
        if serial not in self._store:
            raise SuperVolumeNotFoundError(serial)
        from domain.storage.super_volume.enum import SuperVolumeState

        self._store[serial].state = SuperVolumeState.REMOVED


class FakeFileRepository:
    """内存版 File 仓储：记录行由 (now_volume, now_path) 唯一标识。

    `transaction()` yield 一个哨兵会话对象，写方法把它记入 `calls`，
    供用例断言同一事务内的组合调用。
    """

    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], dict] = {}
        self.sources: list[dict] = []
        self.calls: list[tuple[str, object]] = []
        self.session_sentinel = object()

    def is_exist(self) -> bool:
        return False

    @contextmanager
    def transaction(self):
        self.calls.append(("transaction", self.session_sentinel))
        yield self.session_sentinel

    def reg_source(self, new_file: NewFile, session=None) -> None:
        self.calls.append(("reg_source", session))
        self.sources.append({
            "sha512": new_file.sha512,
            "md5": new_file.md5,
            "size": new_file.size,
            "add_time": new_file.add_time,
            "from_path": str(new_file.from_path),
            "state": new_file.state,
            "info": new_file.info,
        })

    def reg_location(self, new_file: NewFile, session=None) -> None:
        self.calls.append(("reg_location", session))
        row = {
            "sha512": new_file.sha512,
            "md5": new_file.md5,
            "size": new_file.size,
            "add_time": new_file.add_time,
            "now_volume": new_file.now_volume,
            "now_path": str(new_file.now_path),
            "state": new_file.state,
            "info": new_file.info,
        }
        self.rows[(row["now_volume"], row["now_path"])] = row

    def list_by_volume_dir(self, volume: str, dir_path: str) -> list[dict]:
        prefix = f"{dir_path.rstrip('/')}/"
        return [
            dict(row)
            for key, row in self.rows.items()
            if key[0] == volume and row["now_path"].startswith(prefix)
        ]

    def move_file(self, sha512, md5, src_volume, src_path, dst_volume, dst_path, add_time=None):
        key = (src_volume, src_path)
        if key not in self.rows:
            raise LookupError(f"源位置不存在: 卷={src_volume}, 路径={src_path}")
        row = self.rows.pop(key)
        row["now_volume"] = dst_volume
        row["now_path"] = dst_path
        self.rows[(dst_volume, dst_path)] = row

    def copy_file(self, sha512, md5, src_volume, src_path, dst_volume, dst_path, add_time=None):
        key = (src_volume, src_path)
        if key not in self.rows:
            raise LookupError(f"源位置不存在: 卷={src_volume}, 路径={src_path}")
        row = dict(self.rows[key])
        row["now_volume"] = dst_volume
        row["now_path"] = dst_path
        self.rows[(dst_volume, dst_path)] = row


class FakeHasher:
    """假哈希器：返回可预测的假 sha512/md5。"""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def compute_hash(self, path: str) -> dict[str, str]:
        self.calls.append(path)
        return {"sha512": f"sha512:{path}", "md5": f"md5:{path}"}


class FakeFileService:
    """记录型假 file_service：只记录调用，不注册文件。"""

    def __init__(self) -> None:
        self.register_folder_calls: list[dict] = []
        self.register_by_csv_calls: list[dict] = []

    def register_folder(self, folder_path, volume_serial, volume_path, add_time=None):
        self.register_folder_calls.append({
            "folder_path": folder_path,
            "volume_serial": volume_serial,
            "volume_path": volume_path,
            "add_time": add_time,
        })
        return []

    def register_by_csv(self, df, volume_serial, volume_path, add_time=None):
        self.register_by_csv_calls.append({
            "df": df,
            "volume_serial": volume_serial,
            "volume_path": volume_path,
            "add_time": add_time,
        })
        return []
