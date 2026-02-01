"""
条形码生成器

将ID（格式：YYYYMMDDHHmmss_001）转换为条形码图片。
尺寸：105.4mm × 21.5 mm
"""

import io
from typing import Optional
from PIL import Image

try:
    import barcode
    from barcode.writer import ImageWriter
    BARCODE_AVAILABLE = True
except ImportError:
    BARCODE_AVAILABLE = False


# 尺寸常量（毫米转像素，使用300 DPI）
MM_TO_INCH = 1 / 25.4
DPI = 300
WIDTH_MM = 105.4
HEIGHT_MM = 21.5
WIDTH_PX = int(WIDTH_MM * MM_TO_INCH * DPI)
HEIGHT_PX = int(HEIGHT_MM * MM_TO_INCH * DPI)


def generate_barcode_image(
    id_str: str,
    output_path: Optional[str] = None,
    barcode_format: str = "code128"
) -> Image.Image:
    """
    生成条形码图片
    
    Args:
        id_str: ID字符串，格式如 YYYYMMDDHHmmss_001
        output_path: 可选，保存图片的路径。如果为None，只返回图片对象
        barcode_format: 条形码格式，默认为 'code128'，可选 'code39', 'ean13' 等
    
    Returns:
        PIL.Image.Image: 生成的条形码图片对象
    
    Raises:
        ImportError: 如果未安装 python-barcode 库
        ValueError: 如果ID格式不正确
    """
    if not BARCODE_AVAILABLE:
        raise ImportError(
            "需要安装 python-barcode 库。请运行: pip install python-barcode[images]"
        )
    
    # 验证ID格式（基本验证）
    if not id_str or len(id_str) < 10:
        raise ValueError(f"ID格式不正确: {id_str}")
    
    # 创建条形码
    barcode_class = barcode.get_barcode_class(barcode_format)
    code = barcode_class(id_str, writer=ImageWriter())
    
    # 生成条形码图片（临时保存到内存）
    temp_buffer = io.BytesIO()
    code.write(temp_buffer)
    temp_buffer.seek(0)
    barcode_img = Image.open(temp_buffer)
    
    # 调整条形码图片大小以适应目标尺寸
    # 条形码占满整个画布（留少量边距）
    barcode_height = HEIGHT_PX - 20  # 上下各留10px边距
    barcode_width = WIDTH_PX - 40  # 左右各留20px边距
    
    # 保持条形码宽高比，调整大小
    barcode_aspect = barcode_img.width / barcode_img.height
    if barcode_width / barcode_height > barcode_aspect:
        # 以高度为准
        new_barcode_height = barcode_height
        new_barcode_width = int(new_barcode_height * barcode_aspect)
    else:
        # 以宽度为准
        new_barcode_width = barcode_width
        new_barcode_height = int(new_barcode_width / barcode_aspect)
    
    barcode_img = barcode_img.resize(
        (new_barcode_width, new_barcode_height),
        Image.Resampling.LANCZOS
    )
    
    # 创建最终图片（白色背景）
    final_img = Image.new('RGB', (WIDTH_PX, HEIGHT_PX), 'white')
    
    # 计算条形码居中位置
    barcode_x = (WIDTH_PX - new_barcode_width) // 2
    barcode_y = (HEIGHT_PX - new_barcode_height) // 2  # 垂直居中
    
    # 将条形码粘贴到最终图片
    final_img.paste(barcode_img, (barcode_x, barcode_y))
    
    # 如果指定了输出路径，保存图片
    if output_path:
        # 保存图片并设置DPI
        final_img.save(output_path, 'PNG')
        # 注意：PIL的save方法在某些格式下不支持直接设置DPI
        # 如果需要精确的DPI控制，可以使用其他方法
    
    return final_img


def save_barcode_image(id_str: str, output_path: str, barcode_format: str = "code128") -> None:
    """
    生成并保存条形码图片
    
    Args:
        id_str: ID字符串，格式如 YYYYMMDDHHmmss_001
        output_path: 保存图片的路径
        barcode_format: 条形码格式，默认为 'code128'
    
    Raises:
        ImportError: 如果未安装 python-barcode 库
        ValueError: 如果ID格式不正确
    """
    generate_barcode_image(id_str, output_path=output_path, barcode_format=barcode_format)


__all__ = [
    "generate_barcode_image",
    "save_barcode_image",
    "WIDTH_MM",
    "HEIGHT_MM",
    "WIDTH_PX",
    "HEIGHT_PX",
]


def main():
    """调试用的主函数"""
    import sys
    import os
    
    # 添加项目根目录到路径，以便导入其他模块
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # 测试ID生成（可选：使用ID生成器）
    try:
        from apps.common.utils.idGenerater import generate_id
        test_id = generate_id()
        print(f"使用ID生成器生成的ID: {test_id}")
    except ImportError:
        # 如果无法导入ID生成器，使用示例ID
        from datetime import datetime
        test_id = datetime.now().strftime("%Y%m%d%H%M%S") + "_001"
        print(f"使用示例ID: {test_id}")
    
    # 测试条形码生成
    print(f"\n开始生成条形码...")
    print(f"ID: {test_id}")
    print(f"目标尺寸: {WIDTH_MM}mm × {HEIGHT_MM}mm ({WIDTH_PX}px × {HEIGHT_PX}px)")
    
    try:
        # 生成条形码图片
        output_path = "test_barcode.png"
        img = generate_barcode_image(test_id, output_path=output_path)
        
        print(f"\n✓ 条形码生成成功！")
        print(f"  保存路径: {os.path.abspath(output_path)}")
        print(f"  图片尺寸: {img.width}px × {img.height}px")
        print(f"  图片模式: {img.mode}")
        
        # 显示图片（如果支持）
        try:
            img.show()
            print(f"  图片已打开显示")
        except Exception as e:
            print(f"  无法自动显示图片: {e}")
            print(f"  请手动打开文件查看: {output_path}")
        
    except ImportError as e:
        print(f"\n✗ 错误: {e}")
        print(f"  请安装依赖库: pip install python-barcode[images] Pillow")
    except Exception as e:
        print(f"\n✗ 生成条形码时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

