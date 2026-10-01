"""单测：infra/common/barcode_generator —— 条形码图片生成。

目的：验证 generate_barcode_image 生成 RGB 图片、尺寸符合常量、
落盘 PNG 可读回且可解码回原 ID；ID 过短时抛 ValueError。

输入：长度 >= 10 的 ID 字符串与输出路径。
期望输出：PIL RGB Image；落盘后可重开且像素一致、可解码；短 ID 抛 ValueError。
"""

from __future__ import annotations

import pytest

from PIL import Image

from infra.common.barcode_generator import (
    BARCODE_AVAILABLE,
    HEIGHT_PX,
    WIDTH_PX,
    generate_barcode_image,
)
from infra.common.barcode_reader import decode_barcode_text


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


def test_saved_png_read_back_matches_memory(tmp_path):
    """保存 PNG → 重新打开后模式/尺寸/像素与内存对象一致，且非空白。"""
    out = tmp_path / "barcode.png"
    img = generate_barcode_image("20260101120000_001", output_path=str(out))

    with Image.open(out) as reopened:
        assert reopened.mode == "RGB"
        assert reopened.size == (WIDTH_PX, HEIGHT_PX)
        assert list(reopened.getdata()) == list(img.getdata())

    assert len(img.getcolors(maxcolors=WIDTH_PX * HEIGHT_PX)) > 1


def test_generated_image_decodes_back_to_id():
    """生成图片 → 解码文本与 ID 一致（防止缩放破坏条宽）。"""
    id_str = "20260101120000_001"
    decoded = decode_barcode_text(generate_barcode_image(id_str))
    assert decoded == id_str


def test_saved_png_decodes_back_to_id(tmp_path):
    """落盘 PNG → 读回解码文本与 ID 一致。"""
    out = tmp_path / "barcode.png"
    id_str = "20260101120000_001"
    generate_barcode_image(id_str, output_path=str(out))
    assert decode_barcode_text(out) == id_str
