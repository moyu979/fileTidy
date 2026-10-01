"""功能测试：Device → SuperDevice → Volume → SuperVolume 生命周期。

目的：用真实 SQLite 仓储 + 真实服务，验证四层对象的登记链、事件日志、
删除占用保护与“先释放下级再删除上级”的业务规则。

输入：手工登记数据。
期望输出：各服务返回值、数据库状态与事件记录符合文档。
"""

from __future__ import annotations

import pytest

from domain.storage.device.enum import DeviceState
from domain.storage.super_device.enum import SuperDeviceState
from domain.storage.super_device.errors import SuperDeviceInUseError
from domain.storage.volume.enum import VolumeState
from domain.storage.volume.errors import VolumeInUseError
from domain.storage.device.errors import DeviceInUseError
from infra.operation_log.operation_log import load_events
from application.storage.device.service import DeviceService
from application.storage.super_device.service import SuperDeviceService
from application.storage.super_volume.service import SuperVolumeService
from application.storage.volume.service import VolumeService


class _NoopFileService:
    def register_folder(self, *args, **kwargs):
        return []

    def register_by_csv(self, *args, **kwargs):
        return []


@pytest.fixture
def services(repos, event_log_dir):
    """真实仓储 + 真实服务集合。"""
    device_svc = DeviceService(repos["device"])
    super_device_svc = SuperDeviceService(
        repos["super_device"], device_repository=repos["device"]
    )
    volume_svc = VolumeService(
        volume_repository=repos["volume"],
        file_svc=_NoopFileService(),
        device_repository=repos["device"],
        super_device_repository=repos["super_device"],
    )
    super_volume_svc = SuperVolumeService(
        repos["super_volume"], volume_repository=repos["volume"]
    )
    return {
        "device": device_svc,
        "super_device": super_device_svc,
        "volume": volume_svc,
        "super_volume": super_volume_svc,
        "repos": repos,
    }


def _register_chain(svc, device_serials=("D1", "D2")):
    for serial in device_serials:
        svc["device"].reg_device_manual({
            "serial": serial,
            "name": serial,
            "type": "hdd",
            "state": DeviceState.HEALTHY,
        })
    sd_serial = svc["super_device"].reg_super_device_manual({
        "serial": "SD1",
        "name": "阵列",
        "sdtype": "raidz",
        "need_all_devices_online": True,
        "devices": list(device_serials),
    })
    svc["volume"].register_volume_by_info(
        serial="V1",
        device_id=sd_serial,
        name="卷1",
        file_system="ntfs",
        capacity=1000,
        unique_mount_point="/mnt/V1",
        volume_path="/mnt/V1",
    )
    svc["super_volume"].reg_super_volume(
        serial="SV1",
        name="超级卷",
        svtype="copy",
        volumes=["V1"],
    )


def test_registration_chain_persists_and_logs(services):
    """登记链后：四层均落库且事件日志包含对应注册事件。"""
    _register_chain(services)
    repos = services["repos"]

    assert {d.serial for d in repos["device"].list_devices()} == {"D1", "D2"}
    sd = repos["super_device"].get_super_device("SD1")
    assert sd.devices == ["D1", "D2"]
    assert repos["volume"].get_volume("V1").device_id == "SD1"
    assert repos["super_volume"].get_super_volume("SV1").volumes == ["V1"]

    records = load_events()
    types = [r["type"] for r in records]
    assert types.count("DeviceRegistered") == 2
    assert "SuperDeviceRegistered" in types
    assert "VolumeRegistered" in types
    assert "SuperVolumeRegistered" in types


def test_removal_requires_releasing_dependents(services):
    """被依赖时删除 → 领域占用异常；逐级释放后全部可软删除。"""
    _register_chain(services, device_serials=("D1",))
    svc = services
    repos = svc["repos"]

    # 卷仍属于超级卷 → 卷不能删
    with pytest.raises(VolumeInUseError):
        svc["volume"].remove_volume("V1")

    # 超级设备上仍有卷 → 超级设备不能删
    with pytest.raises(SuperDeviceInUseError):
        svc["super_device"].remove_super_device("SD1")

    # 逐级释放
    svc["super_volume"].remove_super_volume("SV1")
    svc["volume"].remove_volume("V1")
    assert repos["volume"].get_volume("V1").state == VolumeState.REMOVED

    svc["super_device"].remove_super_device("SD1")
    assert repos["super_device"].get_super_device("SD1").state == SuperDeviceState.REMOVED

    # 设备仍是超级设备的 USING 子项 → 不能直接删除
    with pytest.raises(DeviceInUseError):
        svc["device"].remove_device("D1")
    svc["super_device"].remove_device("SD1", "D1")
    svc["device"].remove_device("D1")
    assert repos["device"].get_device("D1").state == DeviceState.REMOVED


def test_volume_requires_registered_device(services):
    """卷建立在未登记设备上 → ValueError。"""
    svc = services
    with pytest.raises(ValueError, match="既不是有效 Device"):
        svc["volume"].register_volume_by_info(
            serial="V1",
            device_id="GHOST",
            file_system="ntfs",
            volume_path="/mnt/x",
        )


def test_super_volume_requires_registered_volume(services):
    """超级卷引用不存在的卷 → ValueError。"""
    svc = services
    with pytest.raises(ValueError, match="不存在"):
        svc["super_volume"].reg_super_volume(
            serial="SVX",
            svtype="copy",
            volumes=["GHOST-VOL"],
        )


def test_set_serial_via_services_cascades(services):
    """服务层 set_serial → 仓储改名 + 子表级联 + 事件日志。"""
    _register_chain(services, device_serials=("D1",))
    svc = services
    repos = svc["repos"]

    svc["device"].set_serial("D1", "D1B")
    assert repos["super_device"].get_super_device("SD1").devices == ["D1B"]
    assert not repos["device"].is_exist("D1")

    svc["volume"].set_serial("V1", "V1B")
    assert repos["volume"].get_volume("V1B").device_id == "SD1"
    assert repos["super_volume"].get_super_volume("SV1").volumes == ["V1B"]
    assert not repos["volume"].is_exist("V1")

    records = load_events()
    types = [r["type"] for r in records]
    assert "DeviceSerialChanged" in types
    assert "VolumeSerialChanged" in types
