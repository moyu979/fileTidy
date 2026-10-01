# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：domain/storage/super_volume/base —— SuperVolume 实体基类。

目的（测什么）：
- 验证 SuperVolume._resolve / SuperVolume.create 按 svtype 的工厂分派
  （含 None 与未注册类型回退基类、子类声明 _type_key 后自动注册）；
- 验证 serial 必填校验与 method 字段透传；
- 验证 create 的默认值填充、from_dict 重建与 volumes 快照为拷贝；
- 验证 to_snapshot 字段集合、to_json 序列化、_parse_info 兜底。

输入：
- svtype 字符串（"copy" / "snapraid_raid5" / None / 未注册的 "zzz"）；
- 超级卷字段字典（完整字段、只含 serial、缺 serial）；
- info 字符串（None / "" / "not-json" / "[1, 2]" / 合法对象 JSON）。

期望输出：
- 对应变体实例；serial 为空时 ValueError；未知 svtype 回退 SuperVolume 基类；
- 快照含全部 9 个字段、JSON 可反序列化且中文不转义；
- 非法 info 一律解析为 {}，合法对象 JSON 解析为对应 dict。
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

# 导入包即触发变体注册，保证工厂分派可用
from domain.storage.super_volume import SuperVolume
from domain.storage.super_volume.enum import SuperVolumeState
from domain.storage.super_volume.variants.copy import CopySuperVolume
from domain.storage.super_volume.variants.snapraid_raid5 import SnapraidRaid5SuperVolume

SNAPSHOT_KEYS = {
    "serial", "name", "type", "method", "add_time",
    "last_check_time", "state", "info", "volumes",
}


def _sv(svtype: str | None = "copy", volumes: list[str] | None = None, **overrides) -> SuperVolume:
    """构造一个 SuperVolume 实例，未显式给出的字段使用固定测试值。"""
    data = {
        "serial": "SV-1",
        "name": "超级卷",
        "svtype": svtype,
        "method": "copy",
        "add_time": datetime(2026, 1, 1),
        "last_check_time": None,
        "state": SuperVolumeState.HEALTHY,
        "info": "{}",
        "volumes": volumes if volumes is not None else ["V1", "V2"],
    }
    data.update(overrides)
    return SuperVolume.create(**data)


@pytest.mark.parametrize(
    ("svtype", "expected"),
    [
        ("copy", CopySuperVolume),
        ("snapraid_raid5", SnapraidRaid5SuperVolume),
        (None, SuperVolume),
        ("zzz", SuperVolume),
    ],
)
def test_create_dispatches_by_svtype(svtype, expected):
    """输入 svtype（copy / snapraid_raid5 / None / 未注册）→ 返回对应变体类，未注册回退基类。"""
    assert isinstance(_sv(svtype), expected)


def test_resolve_returns_registered_variant_class():
    """输入已注册 svtype → _resolve 返回注册表中的变体类本身。"""
    assert SuperVolume._resolve("copy") is CopySuperVolume
    assert SuperVolume._resolve("snapraid_raid5") is SnapraidRaid5SuperVolume


def test_resolve_falls_back_to_base_class():
    """输入 None 或未注册 svtype → _resolve 返回 SuperVolume 基类本身。"""
    assert SuperVolume._resolve(None) is SuperVolume
    assert SuperVolume._resolve("zzz") is SuperVolume


def test_registry_contains_builtin_variants():
    """导入包后 → 注册表包含 copy / snapraid_raid5 两个内置变体且指向对应类。"""
    assert {"copy", "snapraid_raid5"} <= set(SuperVolume._registry)
    assert SuperVolume._registry["copy"] is CopySuperVolume


def test_subclass_without_type_key_is_not_registered():
    """定义未声明 _type_key 的子类 → 不进入注册表，_resolve 仍回退基类。"""
    class _AnonymousSuperVolume(SuperVolume):
        """未声明 _type_key 的临时子类。"""

    assert "anonymous_super_volume" not in SuperVolume._registry
    assert SuperVolume._resolve("anonymous_super_volume") is SuperVolume


def test_create_requires_serial():
    """输入空 serial → ValueError。"""
    with pytest.raises(ValueError, match="serial"):
        SuperVolume.create(serial="")


def test_from_dict_without_serial_raises():
    """输入缺 serial 的字典 → ValueError（由 create 统一校验）。"""
    with pytest.raises(ValueError, match="serial"):
        SuperVolume.from_dict({"name": "无序列号"})


def test_create_fills_defaults():
    """只传 serial → 其余字段取默认值（空串 / None / 空列表）。"""
    sv = SuperVolume.create(serial="SV-1")
    assert sv.serial == "SV-1"
    assert sv.name == ""
    assert sv.svtype is None
    assert sv.method == ""
    assert sv.add_time is None
    assert sv.last_check_time is None
    assert sv.state is None
    assert sv.info is None
    assert sv.volumes == []
    assert type(sv) is SuperVolume


def test_create_keeps_explicit_fields():
    """传入全部字段 → 实例属性与入参一致，且类型为 copy 变体。"""
    sv = _sv("copy", ["V1"], name="卷组", method="mirror", state=SuperVolumeState.DANGER)
    assert isinstance(sv, CopySuperVolume)
    assert (sv.name, sv.svtype, sv.method) == ("卷组", "copy", "mirror")
    assert sv.state is SuperVolumeState.DANGER
    assert sv.volumes == ["V1"]


def test_from_dict_rebuilds_variant_and_copies_volumes_snapshot():
    """输入完整字典 → 重建 CopySuperVolume，且 volumes 快照是拷贝。"""
    data = {
        "serial": "SV-2",
        "name": "sv",
        "type": "copy",
        "method": "copy",
        "add_time": "2026-01-01T00:00:00",
        "last_check_time": None,
        "state": SuperVolumeState.HEALTHY,
        "info": "{}",
        "volumes": ["V1"],
    }
    sv = SuperVolume.from_dict(data)
    assert isinstance(sv, CopySuperVolume)
    snapshot = sv.to_snapshot()
    assert snapshot["volumes"] == ["V1"]
    snapshot["volumes"].append("x")
    assert sv.volumes == ["V1"]


def test_from_dict_defaults_for_missing_optional_fields():
    """输入只有 serial 的字典 → 可选字段取默认值且回退基类。"""
    sv = SuperVolume.from_dict({"serial": "SV-3"})
    assert type(sv) is SuperVolume
    assert sv.name == ""
    assert sv.method == ""
    assert sv.volumes == []


def test_to_snapshot_fields_and_json():
    """输入完整实体 → 快照含全部 9 个字段，JSON 可反序列化且中文不转义。"""
    sv = _sv("copy", ["V1", "V2"], name="超级卷")
    snapshot = sv.to_snapshot()
    assert set(snapshot) == SNAPSHOT_KEYS
    assert snapshot["type"] == "copy"
    assert snapshot["add_time"] == "2026-01-01T00:00:00"
    assert snapshot["last_check_time"] is None

    payload = json.loads(sv.to_json())
    assert "超级卷" in sv.to_json()
    assert payload["type"] == "copy"
    assert payload["state"] == "healthy"


def test_to_snapshot_keeps_none_timestamps_for_base_instance():
    """输入只有 serial 的实体 → 快照时间字段为 None 且不抛错。"""
    snapshot = SuperVolume.create(serial="SV-1").to_snapshot()
    assert snapshot["add_time"] is None
    assert snapshot["last_check_time"] is None


@pytest.mark.parametrize("info", [None, "", "not-json", "[1, 2]"])
def test_parse_info_returns_empty_for_invalid(info):
    """输入空 / 非法 JSON / 非对象 JSON → _parse_info 返回 {}。"""
    assert _sv("copy", ["V1"], info=info)._parse_info() == {}


def test_parse_info_returns_dict_for_valid_object():
    """输入合法对象 JSON → _parse_info 返回对应 dict。"""
    assert _sv("copy", ["V1"], info='{"k": 1}')._parse_info() == {"k": 1}
