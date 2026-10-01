"""单测：infra/common/barcode_reader —— 条形码图片读回解码。"""

from __future__ import annotations

from PIL import Image

from infra.common.barcode_generator import generate_barcode_image
from infra.common.barcode_reader import (
    BARCODE_READER_AVAILABLE,
    decode_barcode_text,
    decode_barcodes,
)


def test_reader_library_available():
    """当前环境应已安装 zxing-cpp。"""
    assert BARCODE_READER_AVAILABLE


def test_decode_barcode_text_accepts_pil_image():
    """PIL 图片 → 解码文本与原 ID 一致。"""
    id_str = "20260101120000_001"
    assert decode_barcode_text(generate_barcode_image(id_str)) == id_str


def test_decode_barcode_text_accepts_path(tmp_path):
    """本地图片路径 → 解码文本与原 ID 一致。"""
    out = tmp_path / "barcode.png"
    id_str = "20260101120000_001"
    generate_barcode_image(id_str, output_path=str(out))
    assert decode_barcode_text(str(out)) == id_str


def test_decode_barcodes_returns_list():
    """返回值类型为字符串列表。"""
    id_str = "20260101120000_001"
    decoded = decode_barcodes(generate_barcode_image(id_str))
    assert isinstance(decoded, list)
    assert decoded == [id_str]


def test_decode_blank_image_returns_none():
    """无条码的空白图片 → 返回 None / 空列表。"""
    blank = Image.new("RGB", (300, 100), "white")
    assert decode_barcode_text(blank) is None
    assert decode_barcodes(blank) == []
