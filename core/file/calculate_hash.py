import hashlib
from core.conf import conf
import os


def calculate_md5(path):
    """
    计算单个文件的md5，分块读取，块大小由conf['hash_once']（单位MB）决定。
    """
    if not os.path.isfile(path):
        raise ValueError(f"{path} 不是文件")
    hash_once_mb = conf.get("hash_once") or 1
    chunk_size = int(hash_once_mb) * 1024 * 1024
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            md5.update(chunk)
    return md5.hexdigest()


if __name__ == "__main__":
    # 测试代码
    test_file = "./readme.md"  # 替换为实际的测试文件路径
    try:
        md5_value = calculate_md5(test_file)
        print(f"{test_file} 的MD5值是: {md5_value}")
    except Exception as e:
        print(f"计算MD5失败: {e}")
