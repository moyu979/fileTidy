from datetime import datetime
from main import generate_label_png
import os

# ======================
# 批量生成标签
# ======================
def generate_batch_labels(count=25, output_dir="labels"):
    """
    批量生成序列号递增的磁带机标签（79×17mm，上1/3 文字 YYYYMMDD-HHmmss-序号，下2/3 条码）

    参数:
        count: 生成标签数量，默认25个
        output_dir: 输出目录，默认"labels"
    """
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 获取当前时间（YYYYMMDDHHmmss格式）
    now = datetime.now()
    time_str = now.strftime("%Y%m%d%H%M%S")
    
    print(f"开始生成 {count} 个标签...")
    print(f"基准时间: {time_str}")
    print(f"输出目录: {output_dir}")
    print("-" * 50)
    
    # 生成count个标签，序列号从001开始递增
    for i in range(1, count + 1):
        # 序列号格式化为3位数字（001, 002, ..., 025）
        seq = f"{i:03d}"
        
        # 组合完整的标签字符串：时间 + 序列号（共17位）
        tag = time_str + seq
        
        # 生成文件名
        filename = f"LTO_TAG_{tag}.png"
        target_path = os.path.join(output_dir, filename)
        
        # 生成标签（79×17mm，上1/3 带连字符文字、下2/3 条码）
        generate_label_png(tag, target_path)
        
        print(f"[{i:2d}/{count}] 生成完成: {filename}")
    
    print("-" * 50)
    print(f"全部完成！共生成 {count} 个标签文件")
    print(f"文件保存在: {os.path.abspath(output_dir)}")


# ======================
# 主程序
# ======================
if __name__ == "__main__":
    # 生成25个序列号递增的标签
    generate_batch_labels(count=25, output_dir="labels")
