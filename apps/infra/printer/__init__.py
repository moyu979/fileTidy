"""
打印机模块

提供条形码生成和打印功能。
"""

from .barcode_generator import generate_barcode_image, save_barcode_image

__all__ = [
    "generate_barcode_image",
    "save_barcode_image",
]



