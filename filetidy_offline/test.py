from pystrich.code128 import Code128Encoder
from PIL import Image
import io

# 创建 Code128 条形码
encoder = Code128Encoder('1c75511e2fdffd3a58df23a32a1ab4f3')

# 获取条形码图像的字节数据
barcode_data = encoder.get_imagedata()

# 使用 io.BytesIO 将字节数据转换为字节流对象
image_stream = io.BytesIO(barcode_data)

# 使用 Pillow 打开字节流中的图像
image = Image.open(image_stream)
image = image.resize((500, 150))
# 保存为 PNG 文件
image.save("code128_barcode.png", "PNG")

print("PNG 图像已保存为 code128_barcode.png")


# 创建 Code128 条形码
encoder = Code128Encoder('1234567890gsgfds')

# 获取条形码图像
barcode_image = encoder.get_imagedata()
image_stream = io.BytesIO(barcode_image)

image = Image.open(barcode_image)
# 保存为 PNG 文件
image.save("code128_barcode.png","PNG")
