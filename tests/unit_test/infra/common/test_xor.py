# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/common/xor —— FileXor 文件按位异或。

目的：验证单缓冲/双缓冲两条路径的输出与参考实现一致，长度不等时短者按 0 补齐；
输入文件不存在时抛 FileNotFoundError；配置缺键或 hash_once 过小时 fail-fast。

输入：两个临时文件的字节内容与分块大小（hash_once 最小 1 MiB，下限常量与
FileHasher 同源，统一取自 infra/common/hash.py）。
期望输出：输出文件内容等于参考异或结果；异常类型符合文档。
"""

from __future__ import annotations

import os

import pytest

from infra.common.hash import MIN_HASH_ONCE
from infra.common.xor import FileXor

TEN_MIB = 10 * MIN_HASH_ONCE


def _binary_content(size: int) -> bytes:
    """确定性内容：循环 0x00..0xFF，覆盖含 NUL 在内的所有字节值。"""
    pattern = bytes(range(256))
    return (pattern * ((size + 255) // 256))[:size]


def _reference_xor(a: bytes, b: bytes) -> bytes:
    """参考实现：右补齐（短文件读尽后视为 0），大整数异或等价于逐字节异或。"""
    size = max(len(a), len(b))
    left = int.from_bytes(a.ljust(size, b"\x00"), "big")
    right = int.from_bytes(b.ljust(size, b"\x00"), "big")
    return (left ^ right).to_bytes(size, "big")


class _FakeConfig:
    """最小配置替身：按下标从 dict 读取，构造后可改 dict 模拟热更。"""

    def __init__(self, values: dict[str, object]) -> None:
        self._values = values

    def __getitem__(self, key: str) -> object:
        if key not in self._values:
            raise KeyError(key)
        return self._values[key]


@pytest.mark.parametrize("double", [False, True])
def test_xor_matches_reference(tmp_path, double):
    """随机 10 MiB 双文件 → 单/双缓冲输出均与参考实现一致（跨多个分块）。"""
    a = os.urandom(TEN_MIB)
    b = os.urandom(TEN_MIB)
    f1 = tmp_path / "a.bin"
    f2 = tmp_path / "b.bin"
    out = tmp_path / "out.bin"
    f1.write_bytes(a)
    f2.write_bytes(b)

    FileXor.from_params(
        hash_once=MIN_HASH_ONCE, enable_double_buffer=double
    ).compute_xor(str(f1), str(f2), str(out))

    assert out.read_bytes() == _reference_xor(a, b)


def test_xor_of_empty_file(tmp_path):
    """空与空 → 空输出；空与非空 → 等于非空内容（补齐侧全 0），两个方向都验。"""
    empty = tmp_path / "empty.bin"
    empty.write_bytes(b"")
    other = tmp_path / "other.bin"
    other.write_bytes(_binary_content(3 * 1024))
    xor = FileXor.from_params(hash_once=MIN_HASH_ONCE, enable_double_buffer=False)
    out = tmp_path / "out.bin"

    xor.compute_xor(str(empty), str(empty), str(out))
    assert out.read_bytes() == b""

    xor.compute_xor(str(empty), str(other), str(out))
    assert out.read_bytes() == other.read_bytes()

    xor.compute_xor(str(other), str(empty), str(out))
    assert out.read_bytes() == other.read_bytes()


@pytest.mark.parametrize("missing", ["file1", "file2"])
@pytest.mark.parametrize("double", [False, True])
def test_missing_input_raises(tmp_path, double, missing):
    """任一路输入不存在 → FileNotFoundError，且异常信息含路径（两种缓冲模式）。"""
    f1 = tmp_path / "a.bin"
    f1.write_bytes(b"x")
    f2 = tmp_path / "b.bin"
    f2.write_bytes(b"y")
    not_found = tmp_path / "missing.bin"
    target1, target2 = (not_found, f2) if missing == "file1" else (f1, not_found)

    xor = FileXor.from_params(hash_once=MIN_HASH_ONCE, enable_double_buffer=double)
    with pytest.raises(FileNotFoundError) as exc:
        xor.compute_xor(str(target1), str(target2), str(tmp_path / "out.bin"))
    assert "missing.bin" in str(exc.value)


@pytest.mark.parametrize("missing_key", ["hash_once", "enable_double_buffer"])
def test_missing_config_key_raises_on_construct(missing_key):
    """hash_config 缺任一必填键 → KeyError（fail-fast 设计）。"""
    values: dict[str, object] = {
        "hash_once": MIN_HASH_ONCE,
        "enable_double_buffer": False,
    }
    del values[missing_key]

    with pytest.raises(KeyError):
        FileXor(_FakeConfig(values))


@pytest.mark.parametrize(
    "too_small",
    [0, 1, 1024, MIN_HASH_ONCE - 1],
)
def test_hash_once_below_minimum_raises(too_small):
    """hash_once < 1 MiB → 构造期 ValueError（两种模式都不允许静默降级）。"""
    with pytest.raises(ValueError):
        FileXor.from_params(hash_once=too_small, enable_double_buffer=False)
    with pytest.raises(ValueError):
        FileXor.from_params(hash_once=too_small, enable_double_buffer=True)


@pytest.mark.parametrize(
    ("size1", "size2"),
    [
        (3, MIN_HASH_ONCE),
        (MIN_HASH_ONCE - 1, MIN_HASH_ONCE + 1),
        (MIN_HASH_ONCE, MIN_HASH_ONCE),
        (MIN_HASH_ONCE * 2 + 5, MIN_HASH_ONCE),
        (MIN_HASH_ONCE * 2 + 5, MIN_HASH_ONCE * 2 + 3),
    ],
)
def test_chunk_boundary_sizes_match_reference(tmp_path, size1, size2):
    """块边界附近（整块、差 1、跨块）与长度不等组合，两种模式结果一致。"""
    a = _binary_content(size1)
    b = _binary_content(size2)
    f1 = tmp_path / "a.bin"
    f2 = tmp_path / "b.bin"
    out = tmp_path / "out.bin"
    f1.write_bytes(a)
    f2.write_bytes(b)
    expected = _reference_xor(a, b)

    for double in (False, True):
        FileXor.from_params(
            hash_once=MIN_HASH_ONCE, enable_double_buffer=double
        ).compute_xor(str(f1), str(f2), str(out))
        assert out.read_bytes() == expected


def test_reused_xor_has_no_state_leak(tmp_path):
    """同一实例连续处理不同文件对 → 结果独立、与参考实现一致。"""
    cases = {
        "small": (_binary_content(3 * 1024), _binary_content(5 * 1024)),
        "large": (_binary_content(MIN_HASH_ONCE + 17), _binary_content(MIN_HASH_ONCE)),
    }
    expected = {name: _reference_xor(*pair) for name, pair in cases.items()}
    for name, (a, b) in cases.items():
        (tmp_path / f"{name}-1.bin").write_bytes(a)
        (tmp_path / f"{name}-2.bin").write_bytes(b)

    xor = FileXor.from_params(hash_once=MIN_HASH_ONCE, enable_double_buffer=True)
    for name in ("small", "large", "small"):
        out = tmp_path / f"{name}-out.bin"
        xor.compute_xor(
            str(tmp_path / f"{name}-1.bin"), str(tmp_path / f"{name}-2.bin"), str(out)
        )
        assert out.read_bytes() == expected[name]


def test_config_value_read_at_use_time(monkeypatch):
    """构造后修改 enable_double_buffer → 下次 compute 按新值分发（热更语义）。"""
    values: dict[str, object] = {
        "hash_once": MIN_HASH_ONCE,
        "enable_double_buffer": False,
    }
    xor = FileXor(_FakeConfig(values))
    calls: list[str] = []
    monkeypatch.setattr(xor, "_xor_single", lambda *args: calls.append("single"))
    monkeypatch.setattr(xor, "_xor_double_buffer", lambda *args: calls.append("double"))

    assert xor.compute_xor("f1", "f2", "out") is None
    values["enable_double_buffer"] = True
    assert xor.compute_xor("f1", "f2", "out") is None

    assert calls == ["single", "double"]
