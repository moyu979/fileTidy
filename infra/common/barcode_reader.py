"""
条形码/二维码解析器

基于 zxing-cpp（ZXing 的 C++ 移植版）对图片做轻量解码：
可直接传入 PIL.Image，或传入本地图片路径；返回文本内容。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from PIL import Image

try:
    import zxingcpp

    BARCODE_READER_AVAILABLE = True
except ImportError:
    zxingcpp = None
    BARCODE_READER_AVAILABLE = False

ImageInput = Union[str, Path, Image.Image]


def _load_image(image: ImageInput):
    """将路径或 PIL 图片统一转为 zxing-cpp 可读的 RGB 图片对象。"""
    if isinstance(image, (str, Path)):
        with Image.open(image) as handle:
            return handle.convert("RGB")
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    return image


def decode_barcodes(
    image: ImageInput,
) -> list[str]:
    """解码图片中的全部条形码/二维码，返回文本列表（按检出顺序）。"""
    if not BARCODE_READER_AVAILABLE:
        raise ImportError("需要安装 zxing-cpp 库。请运行: pip install zxing-cpp")
    results = zxingcpp.read_barcodes(_load_image(image))
    return [
        result.text
        for result in results
        if getattr(result, "valid", True)
    ]


def decode_barcode_text(
    image: ImageInput,
) -> Optional[str]:
    """解码图片中的第一个条形码/二维码，返回其文本；未识别到返回 None。"""
    barcodes = decode_barcodes(image)
    return barcodes[0] if barcodes else None


__all__ = [
    "BARCODE_READER_AVAILABLE",
    "decode_barcode_text",
    "decode_barcodes",
]
