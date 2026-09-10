"""单测：infra/common/hash —— FileHasher 文件哈希。

目的：验证单缓冲/双缓冲两条路径的 MD5、SHA-512 与官方 hashlib 一致；
文件不存在时抛出 FileNotFoundError；配置缺键或 hash_once 过小时 fail-fast。

输入：临时文件内容与分块大小（hash_once 最小 1 MiB）。
期望输出：正确的十六进制哈希；异常类型符合文档。
"""

from __future__ import annotations

import hashlib
import os

import pytest

from infra.common.hash import FileHasher, MIN_HASH_ONCE

TEN_MIB = 10 * MIN_HASH_ONCE


def _binary_content(size: int) -> bytes:
    """确定性内容：循环 0x00..0xFF，覆盖含 NUL 在内的所有字节值。"""
    pattern = bytes(range(256))
    return (pattern * ((size + 255) // 256))[:size]


class _FakeConfig:
    """最小配置替身：按下标从 dict 读取，构造后可改 dict 模拟热更。"""

    def __init__(self, values: dict[str, object]) -> None:
        self._values = values

    def __getitem__(self, key: str) -> object:
        if key not in self._values:
            raise KeyError(key)
        return self._values[key]


@pytest.mark.parametrize("double", [False, True])
def test_hashes_match_hashlib(tmp_path, double):
    """随机 10 MiB 文件 → 单/双缓冲结果均与 hashlib 一致（跨多个分块）。"""
    content = os.urandom(TEN_MIB)
    path = tmp_path / "data.bin"
    path.write_bytes(content)
    hasher = FileHasher.from_params(hash_once=MIN_HASH_ONCE, enable_double_buffer=double)

    result = hasher.compute_hash(str(path))

    assert result["md5"] == hashlib.md5(content).hexdigest()
    assert result["sha512"] == hashlib.sha512(content).hexdigest()


def test_hash_of_empty_file(tmp_path):
    """空文件 → 空输入的标准摘要（如 md5 为 d41d8c...，并非空字符串）。"""
    path = tmp_path / "empty.bin"
    path.write_bytes(b"")
    result = FileHasher.from_params(
        hash_once=MIN_HASH_ONCE, enable_double_buffer=False
    ).compute_hash(str(path))
    assert result["md5"] == hashlib.md5(b"").hexdigest()
    assert result["sha512"] == hashlib.sha512(b"").hexdigest()


@pytest.mark.parametrize("double", [False, True])
def test_missing_file_raises(tmp_path, double):
    """不存在的文件 → FileNotFoundError，且异常信息含路径（两种缓冲模式）。"""
    missing = tmp_path / "missing.bin"
    hasher = FileHasher.from_params(
        hash_once=MIN_HASH_ONCE, enable_double_buffer=double
    )
    with pytest.raises(FileNotFoundError) as exc:
        hasher.compute_hash(str(missing))
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
        FileHasher(_FakeConfig(values))


@pytest.mark.parametrize(
    "too_small",
    [0, 1, 1024, MIN_HASH_ONCE - 1],
)
def test_hash_once_below_minimum_raises(too_small):
    """hash_once < 1 MiB → 构造期 ValueError（两种模式都不允许静默降级）。"""
    with pytest.raises(ValueError):
        FileHasher.from_params(hash_once=too_small, enable_double_buffer=False)
    with pytest.raises(ValueError):
        FileHasher.from_params(hash_once=too_small, enable_double_buffer=True)


@pytest.mark.parametrize(
    "size",
    [3, MIN_HASH_ONCE - 1, MIN_HASH_ONCE, MIN_HASH_ONCE + 1, MIN_HASH_ONCE * 2 + 5],
)
def test_chunk_boundary_sizes_match_hashlib(tmp_path, size):
    """块边界附近（整块、差 1、跨块）的文件两种模式哈希一致。"""
    content = _binary_content(size)
    path = tmp_path / "boundary.bin"
    path.write_bytes(content)
    expected = {
        "md5": hashlib.md5(content).hexdigest(),
        "sha512": hashlib.sha512(content).hexdigest(),
    }

    for double in (False, True):
        result = FileHasher.from_params(
            hash_once=MIN_HASH_ONCE, enable_double_buffer=double
        ).compute_hash(str(path))
        assert result == expected


def test_reused_hasher_has_no_state_leak(tmp_path):
    """同一实例连续计算不同文件 → 结果独立、与 hashlib 一致。"""
    contents = {
        "small.bin": _binary_content(3 * 1024),  # 小于单块
        "large.bin": _binary_content(MIN_HASH_ONCE + 17),  # 跨块
    }
    expected = {
        name: {
            "md5": hashlib.md5(content).hexdigest(),
            "sha512": hashlib.sha512(content).hexdigest(),
        }
        for name, content in contents.items()
    }
    for name, content in contents.items():
        (tmp_path / name).write_bytes(content)

    hasher = FileHasher.from_params(
        hash_once=MIN_HASH_ONCE, enable_double_buffer=True
    )
    assert hasher.compute_hash(str(tmp_path / "small.bin")) == expected["small.bin"]
    assert hasher.compute_hash(str(tmp_path / "large.bin")) == expected["large.bin"]
    assert hasher.compute_hash(str(tmp_path / "small.bin")) == expected["small.bin"]


def test_config_value_read_at_use_time(monkeypatch):
    """构造后修改 enable_double_buffer → 下次 compute 按新值分发（热更语义）。"""
    values: dict[str, object] = {
        "hash_once": MIN_HASH_ONCE,
        "enable_double_buffer": False,
    }
    hasher = FileHasher(_FakeConfig(values))
    calls: list[str] = []
    monkeypatch.setattr(
        hasher, "_compute_single", lambda path: calls.append("single") or {}
    )
    monkeypatch.setattr(
        hasher,
        "_compute_double_buffer",
        lambda path: calls.append("double") or {},
    )

    assert hasher.compute_hash("irrelevant") == {}
    values["enable_double_buffer"] = True
    assert hasher.compute_hash("irrelevant") == {}

    assert calls == ["single", "double"]
