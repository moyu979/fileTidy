from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import os

# ======================
# 工具函数
# ======================
def mm_to_px(mm, dpi):
    return int(mm / 25.4 * dpi)


def generate_label_png(tag, target_path, dpi=300, label_width_mm=79, label_height_mm=17, font_size=None):
    """
    生成标签PNG文件（磁带机标签 79mm×17mm）
    布局：上 1/3 一行文字，下 2/3 条形码（全宽，更清晰）

    参数:
        tag: 17位标签字符串，格式为 YYYYMMDDHHmmss + 3位序列号
        target_path: 目标保存路径
        dpi: 分辨率，默认300（可改为600更清晰）
        label_width_mm: 标签宽度（毫米），默认79mm
        label_height_mm: 标签高度（毫米），默认17mm
        font_size: 上排文字字体大小（像素），None 时自动适配
    """
    # 确保目标目录存在
    target_dir = os.path.dirname(target_path)
    if target_dir and not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    # 计算像素尺寸
    label_w = mm_to_px(label_width_mm, dpi)
    label_h = mm_to_px(label_height_mm, dpi)

    # 上 1/3：文字区高度；下 2/3：条形码区高度
    text_zone_h = label_h // 3
    barcode_zone_h = label_h - text_zone_h

    # ======================
    # 生成条形码（占满下 2/3 区域，全宽，不缩放以保持清晰）
    # ======================
    barcode = Code128(tag, writer=ImageWriter())
    temp_img = barcode.render(
        writer_options={
            "module_height": barcode_zone_h,
            "module_width": 1.0,
            "quiet_zone": 2,
            "font_size": 0,
            "dpi": dpi
        }
    )
    actual_width = temp_img.width
    target_module_width = (label_w / actual_width) if actual_width > 0 else 1.0

    barcode_img = barcode.render(
        writer_options={
            "module_height": barcode_zone_h,
            "module_width": target_module_width,
            "quiet_zone": 2,
            "font_size": 0,
            "dpi": dpi
        }
    )

    # ======================
    # 创建标签画布：上 1/3 文字，下 2/3 条码
    # ======================
    label = Image.new("RGB", (label_w, label_h), "white")
    draw = ImageDraw.Draw(label)

    # 条形码贴在下 2/3 区域（全宽）
    label.paste(barcode_img, (0, text_zone_h))

    # ======================
    # 上 1/3：一行文字（YYYYMMDD-HHmmss-序号）
    # ======================
    display_text = f"{tag[:8]}-{tag[8:14]}-{tag[14:]}"
    text_margin = 8
    available_width = label_w - 2 * text_margin

    if font_size is None:
        font_size = 40
        try:
            test_font = ImageFont.truetype("DejaVuSans-Bold.ttf", size=font_size)
        except Exception:
            test_font = ImageFont.load_default(size=font_size)
        draw_temp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        bbox = draw_temp.textbbox((0, 0), display_text, font=test_font)
        text_w = bbox[2] - bbox[0]
        if text_w > available_width:
            font_size = max(12, int(font_size * available_width / text_w * 0.95))

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", size=font_size)
    except Exception:
        font = ImageFont.load_default(size=font_size)

    # 文字在 1/3 区域内垂直居中
    bbox = draw.textbbox((0, 0), display_text, font=font)
    text_height = bbox[3] - bbox[1]
    text_y = (text_zone_h - text_height) // 2
    draw.text((text_margin, text_y), display_text, fill="black", font=font)
    
    # ======================
    # 在标签外再加一圈黑边
    # ======================
    border_px = 5  # 四周各加 5 像素黑边，可根据需要调整
    bordered_w = label_w + border_px * 2
    bordered_h = label_h + border_px * 2

    # 创建黑底画布
    bordered_img = Image.new("RGB", (bordered_w, bordered_h), "black")
    # 把原来的白色标签贴到中间
    bordered_img.paste(label, (border_px, border_px))

    # ======================
    # 保存为PNG文件
    # ======================
    # 确保文件扩展名为.png
    if not target_path.lower().endswith('.png'):
        target_path += '.png'
    
    # 用加了边框的图像保存
    bordered_img.save(target_path, format='PNG', dpi=(dpi, dpi))
    
    print(f"生成完成：{target_path}")
    return target_path


# ======================
# 示例使用
# ======================
if __name__ == "__main__":
    TAG = "20260127143025001"   # 17 位：YYYYMMDDHHmmss + 3 位序列号
    target_path = f"LTO_TAG_{TAG}.png"
    generate_label_png(TAG, target_path)  # 79×17mm，上1/3文字、下2/3条码
