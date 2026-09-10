"""
条形码生成器

将ID（格式：YYYYMMDDHHmmss_001）转换为条形码图片。
尺寸：105.4mm × 21.5 mm，符合磁带标签规格。输出为 PNG 格式，RGB 模式。
"""

import io
from typing import Optional

from PIL import Image

try:
    import barcode
    from barcode.writer import ImageWriter, mm2px, pt2mm

    BARCODE_AVAILABLE = True
except ImportError:
    BARCODE_AVAILABLE = False


# 尺寸常量（毫米转像素，使用 300 DPI）
MM_TO_INCH = 1 / 25.4
DPI = 300
WIDTH_MM = 105.4
HEIGHT_MM = 21.5
WIDTH_PX = int(WIDTH_MM * MM_TO_INCH * DPI)
HEIGHT_PX = int(HEIGHT_MM * MM_TO_INCH * DPI)
MM_TO_PX = DPI / 25.4

# 渲染参数
_FONT_SIZE_PT = 8
# 文字与条码底部的间隙要大于 8pt 字体的上伸高度，避免数字顶进条码
_TEXT_DISTANCE_MM = 4.0
_MARGIN_MM = 0.5
_QUIET_ZONE_MM = 2.54
_BAR_PAD_PX = 2
_MIN_MODULE_PX = 2
_MAX_RENDER_ATTEMPTS = 5


def _render_barcode(
    id_str: str,
    barcode_format: str,
    module_width_px: int,
    module_height_px: int,
) -> Image.Image:
    """按整数像素模块宽度直接渲染条形码，避免后期缩放破坏条宽。"""
    barcode_class = barcode.get_barcode_class(barcode_format)
    options = {
        "module_width": module_width_px / MM_TO_PX,
        "module_height": module_height_px / MM_TO_PX,
        "quiet_zone": _QUIET_ZONE_MM,
        "font_size": _FONT_SIZE_PT,
        "text_distance": _TEXT_DISTANCE_MM,
        "margin_top": _MARGIN_MM,
        "margin_bottom": _MARGIN_MM,
        "write_text": True,
        "center_text": True,
    }
    code = barcode_class(id_str, writer=ImageWriter(format="PNG"))
    buffer = io.BytesIO()
    code.write(buffer, options=options)
    buffer.seek(0)
    image = Image.open(buffer)
    image.load()
    return image


def generate_barcode_image(
    id_str: str,
    output_path: Optional[str] = None,
    barcode_format: str = "code128",
) -> Image.Image:
    """
    生成条形码图片。

    Args:
        id_str: ID字符串，格式如 YYYYMMDDHHmmss_001
        output_path: 可选，保存图片的路径。如果为None，只返回图片对象
        barcode_format: 条形码格式，默认为 'code128'，可选 'code39', 'ean13' 等

    Returns:
        PIL.Image.Image: 生成的条形码图片对象

    Raises:
        ImportError: 如果未安装 python-barcode 库
        ValueError: 如果ID格式不正确或过长无法放入画布
    """
    if not BARCODE_AVAILABLE:
        raise ImportError(
            "需要安装 python-barcode 库。请运行: pip install python-barcode[images]"
        )

    # 校验ID格式（基本校验）
    if not id_str or len(id_str) < 10:
        raise ValueError(f"ID格式不正确: {id_str}")

    # 先取模块数，据此选择恰好放满画布的整数像素条宽
    barcode_class = barcode.get_barcode_class(barcode_format)
    module_count = len(barcode_class(id_str).build()[0])
    quiet_zone_px = round(_QUIET_ZONE_MM * MM_TO_PX)
    module_width_px = max(
        _MIN_MODULE_PX, (WIDTH_PX - 2 * quiet_zone_px) // module_count
    )

    # 画布高度减去边距与文字区，剩余给条形码本体
    margin_px = round(_MARGIN_MM * MM_TO_PX)
    text_distance_px = round(_TEXT_DISTANCE_MM * MM_TO_PX)
    font_half_px = round(mm2px(pt2mm(_FONT_SIZE_PT), DPI) / 2)
    module_height_px = (
        HEIGHT_PX
        - 2 * margin_px
        - font_half_px
        - text_distance_px
        - _BAR_PAD_PX
    )

    # 极端长ID下逐步收窄条宽/条高，直到能放入目标画布
    barcode_img = None
    for _ in range(_MAX_RENDER_ATTEMPTS):
        barcode_img = _render_barcode(
            id_str, barcode_format, module_width_px, module_height_px
        )
        if barcode_img.width <= WIDTH_PX and barcode_img.height <= HEIGHT_PX:
            break
        module_width_px = max(_MIN_MODULE_PX, module_width_px - 1)
        module_height_px = max(1, module_height_px - 4)

    if (
        barcode_img is None
        or barcode_img.width > WIDTH_PX
        or barcode_img.height > HEIGHT_PX
    ):
        raise ValueError(
            f"ID过长，无法放入 {WIDTH_MM}mm × {HEIGHT_MM}mm 的画布: {id_str}"
        )

    # 白色背景画布，条形码整体居中
    final_img = Image.new("RGB", (WIDTH_PX, HEIGHT_PX), "white")
    barcode_x = (WIDTH_PX - barcode_img.width) // 2
    barcode_y = (HEIGHT_PX - barcode_img.height) // 2
    final_img.paste(barcode_img, (barcode_x, barcode_y))

    # 如果指定了输出路径，保存图片
    if output_path:
        final_img.save(output_path, "PNG")

    return final_img


def save_barcode_image(
    id_str: str, output_path: str, barcode_format: str = "code128"
) -> None:
    """
    生成并保存条形码图片。

    Args:
        id_str: ID字符串，格式如 YYYYMMDDHHmmss_001
        output_path: 保存图片的路径
        barcode_format: 条形码格式，默认为 'code128'

    Raises:
        ImportError: 如果未安装 python-barcode 库
        ValueError: 如果ID格式不正确
    """
    generate_barcode_image(
        id_str, output_path=output_path, barcode_format=barcode_format
    )


__all__ = [
    "generate_barcode_image",
    "save_barcode_image",
    "WIDTH_MM",
    "HEIGHT_MM",
    "WIDTH_PX",
    "HEIGHT_PX",
]


def main():
    """调试用的主函数：生成示例图片到当前目录。"""
    import os
    from datetime import datetime

    test_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_001"
    output_path = "test_barcode.png"

    print(f"开始生成条形码...")
    print(f"ID: {test_id}")
    print(
        f"目标尺寸: {WIDTH_MM}mm × {HEIGHT_MM}mm "
        f"({WIDTH_PX}px × {HEIGHT_PX}px)"
    )

    try:
        img = generate_barcode_image(test_id, output_path=output_path)
        print(f"✓ 条形码生成成功！")
        print(f"  保存路径: {os.path.abspath(output_path)}")
        print(f"  图片尺寸: {img.width}px × {img.height}px")
        print(f"  图片模式: {img.mode}")
    except ImportError as exc:
        print(f"✗ 错误: {exc}")
        print("  请安装依赖库: pip install python-barcode[images] Pillow")
    except Exception as exc:
        print(f"✗ 生成条形码时出错: {exc}")


if __name__ == "__main__":
    main()
