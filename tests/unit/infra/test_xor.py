# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/common/xor —— FileXor 文件按位异或。

目的：验证单/双缓冲两条路径的结果一致，长度不等时短者按 0 补齐；
输入文件不存在时抛 FileNotFoundError。

输入：两个临时文件的字节内容。
期望输出：逐字节异或结果写入输出文件。
"""

from __future__ import annotations

import pytest

from infra.common.xor import FileXor


def _xor(a: bytes, b: bytes) -> bytes:
    n = max(len(a), len(b))
    return bytes(
        (a[i] if i < len(a) else 0) ^ (b[i] if i < len(b) else 0)
        for i in range(n)
    )


@pytest.mark.parametrize(
    ("a", "b"),
    [
        (b"\x0f\x00\xaa", b"\x00\x0f\xaa"),
        (b"\xff", b"\x00\xff"),
        (b"same-length-bytes!", b"other-bytes-....."),
        (b"", b"only-one-side"),
    ],
)
@pytest.mark.parametrize("double", [False, True])
def test_xor_single_and_double(tmp_path, a, b, double):
    """两输入字节序列 → 输出与逐字节异或一致（短者按 0 补齐）。"""
    f1 = tmp_path / "a.bin"
    f2 = tmp_path / "b.bin"
    out = tmp_path / "out.bin"
    f1.write_bytes(a)
    f2.write_bytes(b)

    FileXor.from_params(hash_once=4, enable_double_buffer=double).compute_xor(
        str(f1), str(f2), str(out)
    )

    assert out.read_bytes() == _xor(a, b)


@pytest.mark.parametrize("double", [False, True])
def test_xor_missing_input_raises(tmp_path, double):
    """输入文件缺失 → FileNotFoundError。"""
    f1 = tmp_path / "a.bin"
    f1.write_bytes(b"x")
    with pytest.raises(FileNotFoundError):
        FileXor.from_params(hash_once=4, enable_double_buffer=double).compute_xor(
            str(f1), str(tmp_path / "missing.bin"), str(tmp_path / "out.bin")
        )
