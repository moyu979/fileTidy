import numpy as np

def xor(file1_path, file2_path, output_path, chunk_size=1024*1024*128):
    """
    使用 NumPy 向量化高速计算两个大文件的异或。
    
    :param file1_path: 第一个文件路径
    :param file2_path: 第二个文件路径
    :param output_path: 输出文件路径
    :param chunk_size: 每次读取的字节数，默认128MB，可根据内存调整
    """
    with open(file1_path, "rb") as f1, open(file2_path, "rb") as f2, open(output_path, "wb") as fout:
        while True:
            b1 = f1.read(chunk_size)
            b2 = f2.read(chunk_size)
            
            if not b1 and not b2:
                break
            
            # 补齐长度
            if len(b1) < len(b2):
                b1 += b'\x00' * (len(b2) - len(b1))
            elif len(b2) < len(b1):
                b2 += b'\x00' * (len(b1) - len(b2))
            
            # 转为 NumPy 数组（uint8）
            arr1 = np.frombuffer(b1, dtype=np.uint8)
            arr2 = np.frombuffer(b2, dtype=np.uint8)
            
            # 向量化异或
            xor_arr = np.bitwise_xor(arr1, arr2)
            
            # 写入文件
            fout.write(xor_arr.tobytes())

# 使用示例
xor("file1.bin", "file2.bin", "output_xor.bin")
