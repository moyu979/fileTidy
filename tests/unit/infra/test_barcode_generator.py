# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/common/barcode_generator —— 条形码图片生成。

目的：验证 generate_barcode_image 生成 RGB 图片、尺寸符合常量、
可选保存到文件；ID 过短时抛 ValueError。

输入：长度 >= 10 的 ID 字符串与输出路径。
期望输出：PIL RGB Image；保存后文件存在；短 ID 抛 ValueError。
"""

from __future__ import annotations

import pytest

from infra.common.barcode_generator import (
    BARCODE_AVAILABLE,
    HEIGHT_PX,
    WIDTH_PX,
    generate_barcode_image,
)


def test_barcode_library_available():
    """当前环境应已安装 python-barcode。"""
    assert BARCODE_AVAILABLE


def test_generate_returns_rgb_image():
    """合法 ID → RGB 图片且尺寸与常量一致。"""
    img = generate_barcode_image("20260101120000_001")
    assert img.mode == "RGB"
    assert img.width == WIDTH_PX
    assert img.height == HEIGHT_PX


def test_generate_saves_to_path(tmp_path):
    """传入 output_path → 文件落盘。"""
    out = tmp_path / "barcode.png"
    generate_barcode_image("20260101120000_001", output_path=str(out))
    assert out.is_file()
    assert out.stat().st_size > 0


def test_short_id_raises():
    """ID 过短（<10 字符）→ ValueError。"""
    with pytest.raises(ValueError):
        generate_barcode_image("short")
