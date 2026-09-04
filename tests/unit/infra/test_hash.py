# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/common/hash —— FileHasher 文件哈希。

目的：验证单缓冲/双缓冲两条路径的 MD5、SHA-512 与官方 hashlib 一致；
文件不存在时抛出 FileNotFoundError；构造配置缺键时抛 KeyError。

输入：临时文件内容与分块大小。
期望输出：正确的十六进制哈希；异常类型符合文档。
"""

from __future__ import annotations

import hashlib

import pytest

from infra.common.hash import FileHasher


def _content() -> bytes:
    return b"hello fileTidy hash test, chunked into pieces"


@pytest.mark.parametrize("double", [False, True])
def test_hashes_match_hashlib(tmp_path, double):
    """content + hash_once=4 → 单/双缓冲结果均与 hashlib 一致。"""
    path = tmp_path / "data.bin"
    path.write_bytes(_content())
    hasher = FileHasher.from_params(hash_once=4, enable_double_buffer=double)

    result = hasher.compute_hash(str(path))

    assert result["md5"] == hashlib.md5(_content()).hexdigest()
    assert result["sha512"] == hashlib.sha512(_content()).hexdigest()


def test_hash_of_empty_file(tmp_path):
    """空文件 → 空串哈希。"""
    path = tmp_path / "empty.bin"
    path.write_bytes(b"")
    result = FileHasher.from_params(hash_once=1024, enable_double_buffer=False).compute_hash(str(path))
    assert result["md5"] == hashlib.md5(b"").hexdigest()


@pytest.mark.parametrize("double", [False, True])
def test_missing_file_raises(tmp_path, double):
    """不存在的文件 → FileNotFoundError（两种缓冲模式）。"""
    hasher = FileHasher.from_params(hash_once=4, enable_double_buffer=double)
    with pytest.raises(FileNotFoundError):
        hasher.compute_hash(str(tmp_path / "missing.bin"))


def test_missing_config_key_raises_on_construct():
    """hash_config 缺 hash_once → KeyError（fail-fast 设计）。"""

    class EmptyConfig:
        def __getitem__(self, key):
            raise KeyError(key)

    with pytest.raises(KeyError):
        FileHasher(EmptyConfig())
