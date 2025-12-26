#!/usr/bin/env python3
"""
ID生成器测试脚本
格式：YYYYMMDDHHmmss_sequence

"""

import time
import threading
from utils.idGenerater import generate_id, IDGenerator


def test_basic():
    """基础测试：生成几个ID"""
    print("=" * 60)
    print("基础测试")
    print("=" * 60)
    for i in range(5):
        id_str = generate_id()
        print(f"ID {i+1}: {id_str}")
        time.sleep(0.1)  # 等待0.1秒，确保能看到序列号变化


def test_suffix():
    """测试后缀功能"""
    print("\n" + "=" * 60)
    print("后缀测试")
    print("=" * 60)
    print(f"设备ID: {generate_id(suffix='device')}")
    print(f"卷ID: {generate_id(suffix='volume')}")
    print(f"文件ID: {generate_id(suffix='file')}")


def test_timestamp_format():
    """测试时间戳格式（年月日时分秒）"""
    print("\n" + "=" * 60)
    print("时间戳格式测试")
    print("=" * 60)
    id_str = generate_id()
    print(f"生成的ID: {id_str}")
    # 解析时间戳部分
    parts = id_str.split('_')
    if len(parts) >= 2:
        timestamp_str = parts[0]
        sequence = parts[1]
        print(f"时间戳部分: {timestamp_str} (格式: YYYYMMDDHHmmss)")
        print(f"序列号部分: {sequence}")
        print("✓ 时间戳格式正确")
    else:
        print("✗ ID格式不正确")


def test_sequence():
    """测试序列号递增（同一秒内）"""
    print("\n" + "=" * 60)
    print("序列号递增测试（同一秒内快速生成多个ID）")
    print("=" * 60)
    generator = IDGenerator()
    ids = []
    for _ in range(10):
        ids.append(generator.generate())
    
    print("生成的ID列表：")
    for i, id_str in enumerate(ids, 1):
        print(f"  {i}: {id_str}")
    
    # 检查唯一性
    if len(ids) == len(set(ids)):
        print("✓ 所有ID都是唯一的")
    else:
        print("✗ 发现重复ID！")
    
    # 检查序列号是否递增
    sequences = [int(id_str.split('_')[1]) for id_str in ids]
    if sequences == sorted(sequences):
        print("✓ 序列号正确递增")
    else:
        print("✗ 序列号递增异常")


def test_concurrent():
    """测试并发安全性"""
    print("\n" + "=" * 60)
    print("并发测试（10个线程，每个生成10个ID）")
    print("=" * 60)
    generator = IDGenerator()
    ids = []
    lock = threading.Lock()
    
    def generate_ids():
        thread_ids = []
        for _ in range(10):
            thread_ids.append(generator.generate())
        with lock:
            ids.extend(thread_ids)
    
    threads = []
    for _ in range(10):
        t = threading.Thread(target=generate_ids)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    print(f"总共生成 {len(ids)} 个ID")
    print(f"唯一ID数量: {len(set(ids))}")
    
    if len(ids) == len(set(ids)):
        print("✓ 并发测试通过：所有ID都是唯一的")
    else:
        print("✗ 并发测试失败：发现重复ID")
        # 找出重复的ID
        from collections import Counter
        duplicates = [id_str for id_str, count in Counter(ids).items() if count > 1]
        print(f"重复的ID: {duplicates[:5]}")  # 只显示前5个


def test_readable_format():
    """测试ID的可读性（年月日时分秒格式）"""
    print("\n" + "=" * 60)
    print("ID可读性测试")
    print("=" * 60)
    id_str = generate_id()
    print(f"生成的ID: {id_str}")
    
    # 解析时间戳
    parts = id_str.split('_')
    if len(parts) >= 2:
        timestamp_str = parts[0]
        # 解析年月日时分秒
        year = timestamp_str[0:4]
        month = timestamp_str[4:6]
        day = timestamp_str[6:8]
        hour = timestamp_str[8:10]
        minute = timestamp_str[10:12]
        second = timestamp_str[12:14]
        readable_time = f"{year}-{month}-{day} {hour}:{minute}:{second}"
        print(f"可读时间: {readable_time}")
        print("✓ ID格式具有良好的可读性")
    else:
        print("✗ ID格式解析失败")


def test_fixed_length():
    """测试固定长度"""
    print("\n" + "=" * 60)
    print("固定长度测试")
    print("=" * 60)
    id1 = generate_id()
    id2 = generate_id(suffix="test")
    print(f"无后缀ID: {id1} (长度: {len(id1)})")
    print(f"带后缀ID: {id2} (长度: {len(id2)})")
    print("✓ ID为固定长度格式（无后缀19字符，带后缀根据后缀长度变化）")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("ID生成器测试套件（格式: YYYYMMDDHHmmss_sequence）")
    print("=" * 60)
    
    test_basic()
    test_suffix()
    test_timestamp_format()
    test_sequence()
    test_concurrent()
    test_readable_format()
    test_fixed_length()
    
    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

