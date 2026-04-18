import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors


def generate_lto_a4_sheet(label_folder="labels", output_pdf="LTO_Labels_A4.pdf"):
    """
    将 labels 中的 PNG 磁带机标签（79×17mm，上1/3 文字、下2/3 条码）
    排版到 A4 PDF，标签间距 1mm，带淡灰裁切辅助线。
    """

    # ====== 基本参数（磁带机标签尺寸）======
    label_width_mm = 77
    label_height_mm = 16
    margin_mm = 5
    gap_mm = 1

    label_w = label_width_mm * mm
    label_h = label_height_mm * mm
    margin = margin_mm * mm
    gap = gap_mm * mm

    page_width, page_height = A4

    # ====== 计算排布数量 ======
    x_count = int((page_width - 2 * margin + gap) // (label_w + gap))
    y_count = int((page_height - 2 * margin + gap) // (label_h + gap))

    print(f"每页可排：{x_count} × {y_count} = {x_count * y_count} 个")

    images = sorted([
        f for f in os.listdir(label_folder)
        if f.lower().endswith(".png")
    ])

    if not images:
        print("labels 文件夹中没有 PNG 文件")
        return

    c = canvas.Canvas(output_pdf, pagesize=A4)

    x_start = margin
    y_start = page_height - margin - label_h

    # 裁切线样式
    c.setStrokeColor(colors.lightgrey)
    c.setLineWidth(0.3)

    for i, img_name in enumerate(images):
        img_path = os.path.join(label_folder, img_name)

        col = i % x_count
        row = (i // x_count) % y_count

        x = x_start + col * (label_w + gap)
        y = y_start - row * (label_h + gap)

        # 画标签
        c.drawImage(
            img_path,
            x,
            y,
            width=label_w,
            height=label_h,
            preserveAspectRatio=False
        )

        # ====== 添加裁切辅助线（四边） ======
        # 上边
        c.line(x, y + label_h, x + label_w, y + label_h)
        # 下边
        c.line(x, y, x + label_w, y)
        # 左边
        c.line(x, y, x, y + label_h)
        # 右边
        c.line(x + label_w, y, x + label_w, y + label_h)

        # 满页自动换页
        if (i + 1) % (x_count * y_count) == 0:
            c.showPage()
            c.setStrokeColor(colors.lightgrey)
            c.setLineWidth(0.3)

    c.save()
    print(f"生成完成：{output_pdf}")

generate_lto_a4_sheet()