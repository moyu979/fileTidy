#!/usr/bin/env python3
"""
get_hash 模块测试脚本
"""

import os
import tempfile
import hashlib
from utils.get_hash import get_hash, _hash_file


def create_test_file(content: bytes, suffix: str = ".txt") -> str:
    """创建临时测试文件"""
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        return path
    except Exception:
        os.close(fd)
        raise


def get_expected_hash(content: bytes) -> str:
    """计算预期哈希值"""
    return hashlib.md5(content).hexdigest()


def test_single_file():
    """测试单个文件的哈希计算"""
    print("=" * 60)
    print("测试1: 单个文件哈希计算")
    print("=" * 60)
    
    content = b"Hello, World! This is a test file."
    file_path = create_test_file(content)
    
    try:
        result = get_hash(file_path)
        expected_hash = get_expected_hash(content)
        
        print(f"文件路径: {file_path}")
        print(f"计算结果: {result}")
        print(f"预期哈希: {expected_hash}")
        
        assert len(result) == 1, "应该返回一个结果"
        assert result[0][0] == file_path, "路径应该匹配"
        assert result[0][1] == expected_hash, "哈希值应该匹配"
        print("✓ 单个文件哈希计算测试通过")
    finally:
        os.unlink(file_path)


def test_directory():
    """测试目录的哈希计算"""
    print("\n" + "=" * 60)
    print("测试2: 目录哈希计算")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 创建多个测试文件
        files_content = {
            "file1.txt": b"Content of file 1",
            "file2.txt": b"Content of file 2",
            "subdir/file3.txt": b"Content of file 3",
        }
        
        expected_hashes = {}
        for rel_path, content in files_content.items():
            file_path = os.path.join(temp_dir, rel_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(content)
            expected_hashes[file_path] = get_expected_hash(content)
        
        # 计算目录哈希
        results = get_hash(temp_dir)
        
        print(f"目录路径: {temp_dir}")
        print(f"找到文件数: {len(results)}")
        print(f"预期文件数: {len(files_content)}")
        
        assert len(results) == len(files_content), f"应该找到 {len(files_content)} 个文件"
        
        # 验证每个文件的哈希
        result_dict = {path: hash_val for path, hash_val in results}
        for file_path, expected_hash in expected_hashes.items():
            assert file_path in result_dict, f"文件 {file_path} 应该在结果中"
            assert result_dict[file_path] == expected_hash, f"文件 {file_path} 的哈希值应该匹配"
        
        print("✓ 目录哈希计算测试通过")
    finally:
        # 清理临时目录
        import shutil
        shutil.rmtree(temp_dir)


def test_large_file():
    """测试大文件的分块读取"""
    print("\n" + "=" * 60)
    print("测试3: 大文件分块读取")
    print("=" * 60)
    
    # 创建一个较大的文件（10MB）
    large_content = b"X" * (10 * 1024 * 1024)
    file_path = create_test_file(large_content)
    
    try:
        result = get_hash(file_path)
        expected_hash = get_expected_hash(large_content)
        
        print(f"文件大小: {len(large_content) / 1024 / 1024:.2f} MB")
        print(f"计算结果: {result[0][1]}")
        print(f"预期哈希: {expected_hash}")
        
        assert result[0][1] == expected_hash, "大文件的哈希值应该匹配"
        print("✓ 大文件分块读取测试通过")
    finally:
        os.unlink(file_path)


def test_file_not_found():
    """测试文件不存在的情况"""
    print("\n" + "=" * 60)
    print("测试4: 文件不存在错误处理")
    print("=" * 60)
    
    non_existent_path = "/tmp/non_existent_file_12345.txt"
    
    try:
        result = get_hash(non_existent_path)
        print("✗ 应该抛出 FileNotFoundError")
        assert False, "应该抛出异常"
    except FileNotFoundError as e:
        print(f"✓ 正确抛出 FileNotFoundError: {e}")


def test_empty_file():
    """测试空文件"""
    print("\n" + "=" * 60)
    print("测试5: 空文件哈希计算")
    print("=" * 60)
    
    file_path = create_test_file(b"")
    
    try:
        result = get_hash(file_path)
        expected_hash = get_expected_hash(b"")
        
        print(f"计算结果: {result[0][1]}")
        print(f"预期哈希: {expected_hash}")
        print(f"空文件MD5: d41d8cd98f00b204e9800998ecf8427e")
        
        assert result[0][1] == expected_hash, "空文件的哈希值应该匹配"
        assert result[0][1] == "d41d8cd98f00b204e9800998ecf8427e", "空文件的MD5应该是固定的"
        print("✓ 空文件哈希计算测试通过")
    finally:
        os.unlink(file_path)


def test_different_file_types():
    """测试不同文件类型的哈希计算"""
    print("\n" + "=" * 60)
    print("测试6: 不同文件类型")
    print("=" * 60)
    
    test_files = {
        ".txt": b"Text file content",
        ".bin": b"\x00\x01\x02\x03\xFF\xFE\xFD",
        ".json": b'{"key": "value", "number": 123}',
    }
    
    results = {}
    file_paths = []
    
    try:
        for suffix, content in test_files.items():
            file_path = create_test_file(content, suffix=suffix)
            file_paths.append(file_path)
            result = get_hash(file_path)
            results[suffix] = result[0][1]
            print(f"{suffix} 文件哈希: {result[0][1]}")
        
        # 验证不同文件有不同的哈希值
        hashes = list(results.values())
        assert len(hashes) == len(set(hashes)), "不同文件应该有不同哈希值"
        print("✓ 不同文件类型测试通过")
    finally:
        for path in file_paths:
            os.unlink(path)


def test_hash_consistency():
    """测试哈希值的一致性（相同内容应该产生相同哈希）"""
    print("\n" + "=" * 60)
    print("测试7: 哈希值一致性")
    print("=" * 60)
    
    content = b"Same content for consistency test"
    file_path1 = create_test_file(content)
    file_path2 = create_test_file(content)
    
    try:
        result1 = get_hash(file_path1)
        result2 = get_hash(file_path2)
        
        hash1 = result1[0][1]
        hash2 = result2[0][1]
        
        print(f"文件1哈希: {hash1}")
        print(f"文件2哈希: {hash2}")
        
        assert hash1 == hash2, "相同内容应该产生相同哈希值"
        print("✓ 哈希值一致性测试通过")
    finally:
        os.unlink(file_path1)
        os.unlink(file_path2)


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("get_hash 模块测试套件")
    print("=" * 60)
    
    try:
        test_single_file()
        test_directory()
        test_large_file()
        test_file_not_found()
        test_empty_file()
        test_different_file_types()
        test_hash_consistency()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        raise


if __name__ == "__main__":
    main()

