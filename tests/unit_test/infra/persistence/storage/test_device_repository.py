# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/persistence/storage/device_repository.py —— DeviceRepository 隔离单测。

目的（测什么）：
- 构造与 `is_exist`（接受字符串或 Device 对象）；
- `reg_device` / `get_device` / `list_devices` 的字段往返（含 state 字符串归一化、device_path 不落库）；
- `update_device` 的字段更新、state 归一化、不存在时 ValueError；
- `update_serial` 的主键迁移与对 volumes.device_id、super_device_structures.sub_device_id 的级联；
- `remove_device` 的软删除与占用保护（DeviceInUseError）；
- 主键冲突（重复 serial / 改成已存在 serial）触发 IntegrityError 且事务回滚。

输入：`tmp_path` 下每个用例独占的临时 SQLite 库 + `_helpers` 构造的领域对象。

期望输出：查询结果、数据库行与异常类型符合仓储 docstring。
"""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from domain.storage.device.base import Device
from domain.storage.device.enum import DeviceState
from domain.storage.device.errors import DeviceInUseError
from domain.storage.device.repo import DeviceRepositoryABC
from domain.storage.volume.enum import VolumeState
from infra.persistence.models import DeviceModel
from tests.unit_test.infra.persistence import _helpers as H


@pytest.fixture
def db(tmp_path):
    """每个用例独占的临时 SQLite 库（仅建表）。"""
    handle = H.new_db(tmp_path / "device.db")
    yield handle
    handle.dispose()


@pytest.fixture
def repo(db):
    """绑定该库的 DeviceRepository。"""
    return db.repos["device"]


# ── 构造与查询 ────────────────────────────────────────────────────


def test_repository_is_abc_implementation(db, repo):
    """输入 新建仓储 → 期望输出 是 DeviceRepositoryABC 实例且复用同一会话工厂。"""
    assert isinstance(repo, DeviceRepositoryABC)
    assert repo.session_factory is db.factory


def test_is_exist_accepts_string_and_device(db, repo):
    """输入 未登记/已登记的 serial 与 Device 对象 → 期望输出 False / True。"""
    assert repo.is_exist("GHOST") is False
    assert repo.is_exist(H.make_device("GHOST")) is False

    repo.reg_device(H.make_device("D1"))

    assert repo.is_exist("D1") is True
    assert repo.is_exist(H.make_device("D1")) is True


def test_reg_device_then_get_round_trip(db, repo):
    """输入 登记 ssd 设备 → 期望输出 读回字段与写入一致（device_path 不落库）。"""
    repo.reg_device(
        H.make_device("D1", dtype="ssd", capacity=512, info='{"a": 1}')
    )

    got = repo.get_device("D1")

    assert isinstance(got, Device)
    assert got.serial == "D1"
    assert got.name == "D1"
    assert got.dtype == "ssd"
    assert got.capacity == 512
    assert got.info == '{"a": 1}'
    assert got.state is DeviceState.HEALTHY
    assert got.add_time == H.FIXED_TIME
    assert got.last_check_time == H.FIXED_TIME
    assert got.device_path is None
    assert H.count(db, DeviceModel) == 1


def test_get_device_missing_returns_none(repo):
    """输入 不存在的 serial → 期望输出 None。"""
    assert repo.get_device("GHOST") is None


def test_list_devices_returns_all_registered(db, repo):
    """输入 空库/登记两台设备 → 期望输出 [] / 两台设备。"""
    assert repo.list_devices() == []

    repo.reg_device(H.make_device("D1", dtype="ssd"))
    repo.reg_device(H.make_device("D2", dtype="hdd"))

    assert sorted(d.serial for d in repo.list_devices()) == ["D1", "D2"]


def test_list_devices_includes_default_placeholder(tmp_path):
    """输入 已填充默认数据的库 → 期望输出 列表包含 EXTERNAL_DEVICE 占位设备。"""
    handle = H.new_db(tmp_path / "seeded.db", with_defaults=True)
    try:
        serials = [d.serial for d in handle.repos["device"].list_devices()]
        assert serials == ["EXTERNAL_DEVICE"]
    finally:
        handle.dispose()


# ── 更新 ──────────────────────────────────────────────────────────


def test_update_device_updates_given_fields_only(db, repo):
    """输入 只更新 name 与 capacity → 期望输出 两字段生效、其余字段保持原值。"""
    repo.reg_device(H.make_device("D1", dtype="ssd", capacity=512))

    repo.update_device("D1", name="new-name", capacity=1024)

    got = repo.get_device("D1")
    assert got.name == "new-name"
    assert got.capacity == 1024
    assert got.dtype == "ssd"
    assert got.state is DeviceState.HEALTHY


def test_update_device_missing_raises_value_error(repo):
    """输入 更新不存在的 serial → 期望输出 ValueError。"""
    with pytest.raises(ValueError, match="not found"):
        repo.update_device("GHOST", name="x")


def test_update_device_coerces_state_strings(db, repo):
    """输入 state 传值形式 'fault' 与名称形式 'REMOVED' → 期望输出 落库为对应枚举成员。"""
    repo.reg_device(H.make_device("D1"))

    repo.update_device("D1", state="fault")
    assert repo.get_device("D1").state is DeviceState.FAULT

    repo.update_device("D1", state="REMOVED")
    assert repo.get_device("D1").state is DeviceState.REMOVED


def test_update_device_invalid_state_raises(db, repo):
    """输入 state='bogus' → 期望输出 ValueError 且原状态不变。"""
    repo.reg_device(H.make_device("D1"))

    with pytest.raises(ValueError, match="不是 DeviceState 的合法状态"):
        repo.update_device("D1", state="bogus")

    assert repo.get_device("D1").state is DeviceState.HEALTHY


def test_reg_device_normalizes_state_strings(db, repo):
    """输入 登记时 state 传 'fault' / 'REMOVED' → 期望输出 读回对应枚举成员。"""
    repo.reg_device(H.make_device("D1", state="fault"))
    repo.reg_device(H.make_device("D2", state="REMOVED"))

    assert repo.get_device("D1").state is DeviceState.FAULT
    assert repo.get_device("D2").state is DeviceState.REMOVED


def test_reg_device_invalid_state_string_raises(db, repo):
    """输入 登记时 state='not-a-state' → 期望输出 ValueError 且未落库。"""
    with pytest.raises(ValueError, match="不是 DeviceState 的合法状态"):
        repo.reg_device(H.make_device("D1", state="not-a-state"))

    assert repo.is_exist("D1") is False


def test_reg_device_duplicate_serial_raises_integrity_error(db, repo):
    """输入 登记已存在的 serial → 期望输出 IntegrityError（主键冲突）。"""
    repo.reg_device(H.make_device("D1", dtype="ssd"))

    with pytest.raises(IntegrityError):
        repo.reg_device(H.make_device("D1", dtype="hdd"))

    assert H.count(db, DeviceModel) == 1


# ── 主键迁移 ──────────────────────────────────────────────────────


def test_update_serial_cascades_to_volumes_and_structures(db, repo):
    """输入 设备改名且被卷与超级设备引用 → 期望输出 三处引用一起迁移到新 serial。"""
    repo.reg_device(H.make_device("D1"))
    repo.reg_device(H.make_device("D2"))
    db.repos["super_device"].reg_super_device(
        H.make_super_device("SD1", devices=["D1", "D2"])
    )
    db.repos["volume"].reg_volume(H.make_volume("V1", device_id="D1"))

    repo.update_serial("D1", "D1-NEW")

    assert repo.is_exist("D1-NEW") is True
    assert repo.is_exist("D1") is False
    # 迁移只改主键，name 等业务字段保持原值
    assert repo.get_device("D1-NEW").name == "D1"
    assert db.repos["volume"].get_volume("V1").device_id == "D1-NEW"
    assert db.repos["super_device"].get_super_device("SD1").devices == ["D1-NEW", "D2"]


def test_update_serial_same_serial_is_noop(db, repo):
    """输入 新旧 serial 相同 → 期望输出 提前返回，记录仍在。"""
    repo.reg_device(H.make_device("D1"))

    repo.update_serial("D1", "D1")

    assert repo.is_exist("D1") is True


def test_update_serial_missing_raises_value_error(repo):
    """输入 迁移不存在的 serial → 期望输出 ValueError。"""
    with pytest.raises(ValueError, match="not found"):
        repo.update_serial("GHOST", "NEW")


def test_update_serial_to_existing_serial_raises_and_rolls_back(db, repo):
    """输入 把 D1 改名为已存在的 D2 → 期望输出 IntegrityError 且两张记录都还在。"""
    repo.reg_device(H.make_device("D1"))
    repo.reg_device(H.make_device("D2"))

    with pytest.raises(IntegrityError):
        repo.update_serial("D1", "D2")

    assert sorted(d.serial for d in repo.list_devices()) == ["D1", "D2"]


# ── 软删除与占用保护 ──────────────────────────────────────────────


def test_remove_device_marks_removed_and_keeps_row(db, repo):
    """输入 无引用的设备 → 期望输出 state 变 REMOVED，行仍保留。"""
    repo.reg_device(H.make_device("D1"))

    repo.remove_device("D1")

    assert repo.get_device("D1").state is DeviceState.REMOVED
    assert H.count(db, DeviceModel) == 1


def test_remove_device_missing_raises_value_error(repo):
    """输入 删除不存在的设备 → 期望输出 ValueError。"""
    with pytest.raises(ValueError, match="not found"):
        repo.remove_device("GHOST")


def test_remove_device_blocked_by_using_super_device(db, repo):
    """输入 设备仍是超级设备 USING 子项 → 期望输出 DeviceInUseError(super_device_using=1)。"""
    repo.reg_device(H.make_device("D1"))
    sd_repo = db.repos["super_device"]
    sd_repo.reg_super_device(H.make_super_device("SD1", devices=["D1"]))

    with pytest.raises(DeviceInUseError) as excinfo:
        repo.remove_device("D1")

    assert excinfo.value.serial == "D1"
    assert excinfo.value.super_device_using == 1
    assert repo.get_device("D1").state is DeviceState.HEALTHY

    sd_repo.remove_device("SD1", "D1")
    repo.remove_device("D1")
    assert repo.get_device("D1").state is DeviceState.REMOVED


def test_remove_device_blocked_by_active_volume(db, repo):
    """输入 设备上仍有非 REMOVED 卷 → 期望输出 DeviceInUseError(volumes=1)；卷移除后可删。"""
    repo.reg_device(H.make_device("D1"))
    volume_repo = db.repos["volume"]
    volume_repo.reg_volume(H.make_volume("V1", device_id="D1"))

    with pytest.raises(DeviceInUseError) as excinfo:
        repo.remove_device("D1")

    assert excinfo.value.volumes == 1
    assert excinfo.value.super_device_using == 0

    volume_repo.update_volume("V1", state=VolumeState.REMOVED)
    repo.remove_device("D1")

    assert repo.get_device("D1").state is DeviceState.REMOVED
