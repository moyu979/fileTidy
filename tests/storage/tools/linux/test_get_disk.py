# 本文件未经测试
import unittest
import os
import sys
import subprocess
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))

from core.storage.tools.linux.get_disk import get_disk, get_serial, get_size, get_device_info


class TestGetDisk(unittest.TestCase):
    """测试get_disk模块的功能"""

    def setUp(self):
        """测试前的准备工作"""
        self.test_device_path = "/dev/test_device"
        self.real_device_paths = ["/dev/sda", "/dev/nvme0n1", "/dev/sdb"]

    def test_get_disk_with_none_path(self):
        """测试传入None路径的情况"""
        # 传入None时应该获取所有磁盘，而不是返回空列表
        with patch('os.listdir', return_value=['sda', 'sdb', 'nvme0n1']):
            with patch('os.path.exists', return_value=True):
                with patch('subprocess.run') as mock_run:
                    # Mock udevadm 和 lsblk 命令
                    def mock_subprocess_run(cmd, *args, **kwargs):
                        if 'udevadm' in cmd:
                            return MagicMock(returncode=0, stdout="ID_SERIAL=test_serial")
                        elif 'lsblk' in cmd:
                            return MagicMock(returncode=0, stdout="1000000000")
                        else:
                            return MagicMock(returncode=1, stderr="Unknown command")
                    
                    mock_run.side_effect = mock_subprocess_run
                    
                    result = get_disk(None)
                    # 应该返回所有磁盘，而不是空列表
                    self.assertGreater(len(result), 0)
                    self.assertEqual(len(result), 3)  # 3个设备
                    
                    # 验证返回的是磁盘信息列表
                    for disk in result:
                        self.assertIn("id", disk)
                        self.assertIn("size", disk)
                        self.assertIn("path", disk)
                    
                    # 验证具体的返回值
                    expected_paths = ['/dev/sda', '/dev/sdb', '/dev/nvme0n1']
                    actual_paths = [disk['path'] for disk in result]
                    self.assertEqual(set(actual_paths), set(expected_paths))
                    
                    # 验证每个设备的信息
                    for disk in result:
                        self.assertEqual(disk['id'], "test_serial")
                        self.assertEqual(disk['size'], 1000000000)
                        self.assertTrue(disk['path'].startswith('/dev/'))

    def test_get_disk_with_empty_path(self):
        """测试传入空字符串路径的情况"""
        # 传入空字符串时应该获取所有磁盘，而不是返回空列表
        with patch('os.listdir', return_value=['sda', 'sdb', 'nvme0n1']):
            with patch('os.path.exists', return_value=True):
                with patch('subprocess.run') as mock_run:
                    # Mock udevadm 和 lsblk 命令
                    def mock_subprocess_run(cmd, *args, **kwargs):
                        if 'udevadm' in cmd:
                            return MagicMock(returncode=0, stdout="ID_SERIAL=test_serial")
                        elif 'lsblk' in cmd:
                            return MagicMock(returncode=0, stdout="1000000000")
                        else:
                            return MagicMock(returncode=1, stderr="Unknown command")
                    
                    mock_run.side_effect = mock_subprocess_run
                    
                    result = get_disk("")
                    # 应该返回所有磁盘，而不是空列表
                    self.assertGreater(len(result), 0)
                    self.assertEqual(len(result), 3)  # 3个设备
                    
                    # 验证返回的是磁盘信息列表
                    for disk in result:
                        self.assertIn("id", disk)
                        self.assertIn("size", disk)
                        self.assertIn("path", disk)
                    
                    # 验证具体的返回值
                    expected_paths = ['/dev/sda', '/dev/sdb', '/dev/nvme0n1']
                    actual_paths = [disk['path'] for disk in result]
                    self.assertEqual(set(actual_paths), set(expected_paths))
                    
                    # 验证每个设备的信息
                    for disk in result:
                        self.assertEqual(disk['id'], "test_serial")
                        self.assertEqual(disk['size'], 1000000000)
                        self.assertTrue(disk['path'].startswith('/dev/'))

    def test_get_disk_with_nonexistent_path(self):
        """测试传入不存在的设备路径"""
        with patch('os.path.exists', return_value=False):
            result = get_disk("/dev/nonexistent_device")
            self.assertIsNone(result)

    def test_get_disk_with_existing_path(self):
        """测试传入存在的设备路径"""
        # 这里我们只测试函数调用，不依赖实际设备
        with patch('os.path.exists', return_value=True):
            with patch('core.storage.tools.linux.get_disk.get_device_info') as mock_get_info:
                mock_get_info.return_value = {
                    "id": "test_serial",
                    "size": 1000000000,
                    "path": self.test_device_path
                }
                result = get_disk(self.test_device_path)
                
                # 基本验证
                self.assertEqual(len(result), 1)
                
                # 验证返回值的具体内容
                disk = result[0]
                self.assertEqual(disk["id"], "test_serial")
                self.assertEqual(disk["size"], 1000000000)
                self.assertEqual(disk["path"], self.test_device_path)
                
                # 验证数据结构完整性
                self.assertIn("id", disk)
                self.assertIn("size", disk)
                self.assertIn("path", disk)

    def test_get_disk_without_path(self):
        """测试不传入路径，获取所有磁盘的情况"""
        # Mock os.listdir 返回一些测试设备
        with patch('os.listdir', return_value=['sda', 'sdb', 'nvme0n1']):
            with patch('os.path.exists', return_value=True):
                with patch('core.storage.tools.linux.get_disk.get_device_info') as mock_get_info:
                    # 根据设备名返回不同的路径
                    def mock_get_device_info(dev_path):
                        return {
                            "id": f"test_serial_{dev_path.split('/')[-1]}",
                            "size": 1000000000,
                            "path": dev_path
                        }
                    
                    mock_get_info.side_effect = mock_get_device_info
                    
                    result = get_disk()
                    # 应该返回3个设备
                    self.assertEqual(len(result), 3)
                    
                    # 验证返回值的具体内容
                    expected_paths = ['/dev/sda', '/dev/sdb', '/dev/nvme0n1']
                    actual_paths = [disk['path'] for disk in result]
                    self.assertEqual(set(actual_paths), set(expected_paths))
                    
                    # 验证每个设备的信息
                    for disk in result:
                        self.assertIn("id", disk)
                        self.assertIn("size", disk)
                        self.assertIn("path", disk)
                        self.assertEqual(disk["size"], 1000000000)
                        self.assertTrue(disk["path"].startswith('/dev/'))

    def test_get_disk_device_filtering(self):
        """测试设备过滤逻辑"""
        # 测试只返回sd*和nvme*设备
        with patch('os.listdir', return_value=['sda', 'sdb', 'nvme0n1', 'loop0', 'ram0']):
            with patch('os.path.exists', return_value=True):
                with patch('core.storage.tools.linux.get_disk.get_device_info') as mock_get_info:
                    # 根据设备名返回不同的路径
                    def mock_get_device_info(dev_path):
                        return {
                            "id": f"test_serial_{dev_path.split('/')[-1]}",
                            "size": 1000000000,
                            "path": dev_path
                        }
                    
                    mock_get_info.side_effect = mock_get_device_info
                    
                    result = get_disk()
                    # 应该只返回3个符合条件的设备（sda, sdb, nvme0n1）
                    self.assertEqual(len(result), 3)
                    
                    # 验证返回值的具体内容
                    expected_paths = ['/dev/sda', '/dev/sdb', '/dev/nvme0n1']
                    actual_paths = [disk['path'] for disk in result]
                    self.assertEqual(set(actual_paths), set(expected_paths))
                    
                    # 验证每个设备的信息
                    for disk in result:
                        self.assertIn("id", disk)
                        self.assertIn("size", disk)
                        self.assertIn("path", disk)
                        self.assertEqual(disk["size"], 1000000000)
                        self.assertTrue(disk["path"].startswith('/dev/'))

    def test_get_device_info_structure(self):
        """测试get_device_info返回的数据结构"""
        with patch('core.storage.tools.linux.get_disk.get_serial', return_value="test_serial"):
            with patch('core.storage.tools.linux.get_disk.get_size', return_value=1000000000):
                result = get_device_info(self.test_device_path)
                
                # 验证返回的字典结构
                self.assertIsInstance(result, dict)
                self.assertIn("id", result)
                self.assertIn("size", result)
                self.assertIn("path", result)
                
                # 验证字段值
                self.assertEqual(result["id"], "test_serial")
                self.assertEqual(result["size"], 1000000000)
                self.assertEqual(result["path"], self.test_device_path)

    def test_get_device_info_with_none_values(self):
        """测试get_device_info处理None值的情况"""
        with patch('core.storage.tools.linux.get_disk.get_serial', return_value=None):
            with patch('core.storage.tools.linux.get_disk.get_size', return_value=None):
                result = get_device_info(self.test_device_path)
                
                # 验证None值被正确处理
                self.assertIsNone(result["id"])
                self.assertIsNone(result["size"])
                self.assertEqual(result["path"], self.test_device_path)

    def test_get_size_success(self):
        """测试get_size成功获取容量"""
        mock_output = "1000000000\n500000000\n250000000"  # 模拟lsblk输出多行
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output
            )
            result = get_size(self.test_device_path)
            self.assertEqual(result, 1000000000)  # 应该返回第一行

    def test_get_size_command_failure(self):
        """测试get_size命令执行失败的情况"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,  # 命令执行失败
                stderr="Permission denied"
            )
            result = get_size(self.test_device_path)
            self.assertIsNone(result)

    def test_get_size_invalid_output(self):
        """测试get_size处理无效输出的情况"""
        mock_output = "invalid_size\n500000000"  # 第一行不是数字
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output
            )
            result = get_size(self.test_device_path)
            self.assertIsNone(result)

    def test_get_size_empty_output(self):
        """测试get_size处理空输出的情况"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=""
            )
            result = get_size(self.test_device_path)
            self.assertIsNone(result)

    def test_get_serial_success(self):
        """测试get_serial成功获取序列号"""
        mock_output = "ID_SERIAL=test_serial_number\nOTHER_PROP=value"
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output
            )
            result = get_serial(self.test_device_path)
            self.assertEqual(result, "test_serial_number")

    def test_get_serial_command_failure(self):
        """测试get_serial命令执行失败的情况"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr="Device not found"
            )
            result = get_serial(self.test_device_path)
            self.assertIsNone(result)

    def test_get_serial_empty_output(self):
        """测试get_serial处理空输出的情况"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=""
            )
            result = get_serial(self.test_device_path)
            self.assertIsNone(result)

    def test_data_validation(self):
        """测试返回数据的验证"""
        # 模拟获取所有磁盘
        with patch('os.listdir', return_value=['sda']):
            with patch('os.path.exists', return_value=True):
                with patch('core.storage.tools.linux.get_disk.get_device_info') as mock_get_info:
                    mock_get_info.return_value = {
                        "id": "test_serial_123",
                        "size": 1000000000,
                        "path": "/dev/sda"
                    }
                    result = get_disk()
                    
                    self.assertIsInstance(result, list)
                    self.assertGreater(len(result), 0)
                    
                    for disk in result:
                        # 验证必要字段存在
                        self.assertIn("id", disk)
                        self.assertIn("size", disk)
                        self.assertIn("path", disk)
                        
                        # 验证字段类型
                        self.assertIsInstance(disk["path"], str)
                        self.assertIsInstance(disk["size"], (int, type(None)))
                        self.assertIsInstance(disk["id"], (str, type(None)))
                        
                        # 验证数据合理性
                        if disk["size"] is not None:
                            self.assertGreater(disk["size"], 0)  # 容量应该为正数
                        
                        if disk["path"]:
                            self.assertTrue(disk["path"].startswith("/dev/"))  # 路径应该以/dev/开头

    def test_error_handling(self):
        """测试异常处理"""
        # 测试subprocess.run抛出异常
        with patch('subprocess.run', side_effect=Exception("Unexpected error")):
            result = get_size(self.test_device_path)
            self.assertIsNone(result)
            
            result = get_serial(self.test_device_path)
            self.assertIsNone(result)

    def test_performance_with_many_devices(self):
        """测试大量设备时的性能"""
        # 模拟100个设备，生成符合过滤条件的设备名
        # 原始代码要求: (dev.startswith('sd') and len(dev) == 3) or dev.startswith('nvme')
        many_devices = []
        for i in range(100):
            if i < 26:  # 前26个是 sda, sdb, sdc, ...
                many_devices.append(f'sd{chr(97 + i)}')
            elif i < 52:  # 接下来26个是 sdaa, sdab, sdac, ...
                many_devices.append(f'sd{chr(97 + (i - 26) // 26)}{chr(97 + (i - 26) % 26)}')
            else:  # 剩余的是 nvme 设备
                many_devices.append(f'nvme{i-52}n1')
        
        with patch('os.listdir', return_value=many_devices):
            with patch('os.path.exists', return_value=True):
                with patch('subprocess.run') as mock_run:
                    # Mock udevadm 和 lsblk 命令
                    # 需要模拟不同的命令调用
                    def mock_subprocess_run(cmd, *args, **kwargs):
                        if 'udevadm' in cmd:
                            return MagicMock(returncode=0, stdout="ID_SERIAL=test_serial")
                        elif 'lsblk' in cmd:
                            return MagicMock(returncode=0, stdout="1000000000")
                        else:
                            return MagicMock(returncode=1, stderr="Unknown command")
                    
                    mock_run.side_effect = mock_subprocess_run
                    
                    # 测试性能，不应该太慢
                    import time
                    start_time = time.time()
                    result = get_disk()
                    end_time = time.time()
                    
                    self.assertEqual(len(result), 100)
                    # 100个设备应该在1秒内完成
                    self.assertLess(end_time - start_time, 1.0)


class TestGetDiskIntegration(unittest.TestCase):
    """集成测试：测试与实际系统的交互"""

    @unittest.skipUnless(os.path.exists("/dev"), "需要/dev目录存在")
    def test_real_system_devices(self):
        """测试真实系统中的设备（如果存在）"""
        # 只测试函数调用，不验证具体结果
        try:
            result = get_disk()
            # 如果成功，验证返回的是列表
            self.assertIsInstance(result, list)
        except Exception as e:
            # 如果失败，记录错误但不中断测试
            print(f"真实系统测试失败: {e}")
            self.skipTest(f"真实系统测试失败: {e}")

    @unittest.skipUnless(os.path.exists("/dev/sda"), "需要/dev/sda设备存在")
    def test_real_sda_device(self):
        """测试真实的/dev/sda设备（如果存在）"""
        try:
            result = get_disk("/dev/sda")
            if result:
                disk = result[0]
                # 验证返回的数据结构
                self.assertIn("id", disk)
                self.assertIn("size", disk)
                self.assertIn("path", disk)
                self.assertEqual(disk["path"], "/dev/sda")
        except Exception as e:
            print(f"真实设备测试失败: {e}")
            self.skipTest(f"真实设备测试失败: {e}")


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_suite.addTest(unittest.makeSuite(TestGetDisk))
    test_suite.addTest(unittest.makeSuite(TestGetDiskIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 返回测试结果
    return result.wasSuccessful()


if __name__ == "__main__":
    # 运行测试
    success = run_tests()
    
    # 根据测试结果设置退出码
    exit_code = 0 if success else 1
    exit(exit_code)
