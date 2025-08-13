#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HDD健康检查工具的测试文件
测试hdd_check函数的各种功能和边界条件
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
import tempfile

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from core.storage.tools.linux.hdd_check import hdd_check, run_command


class TestHDDCheck(unittest.TestCase):
    """HDD健康检查工具的测试类"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.valid_device = "/dev/sda"
        self.invalid_device = "/dev/nonexistent"
        self.non_block_device = "/etc/passwd"
        
    def tearDown(self):
        """测试后的清理工作"""
        pass
    
    @patch('core.storage.tools.linux.hdd_check.os.path.exists')
    @patch('core.storage.tools.linux.hdd_check.run_command')
    def test_hdd_check_success_health(self, mock_run_command, mock_exists):
        """测试成功情况：硬盘健康"""
        # 模拟文件存在和块设备有效
        mock_exists.side_effect = lambda x: True if x in [self.valid_device, "/sys/block/sda"] else False
        
        # 模拟SMART检查成功
        mock_run_command.return_value = (0, "SMART overall-health self-assessment test result: PASSED", "")
        
        result = hdd_check(self.valid_device, scan_blocks=False)
        self.assertEqual(result, "health")
    
    @patch('core.storage.tools.linux.hdd_check.os.path.exists')
    @patch('core.storage.tools.linux.hdd_check.run_command')
    def test_hdd_check_success_danger(self, mock_run_command, mock_exists):
        """测试成功情况：硬盘有警告"""
        # 模拟文件存在和块设备有效
        mock_exists.side_effect = lambda x: True if x in [self.valid_device, "/sys/block/sda"] else False
        
        # 模拟SMART检查失败
        mock_run_command.return_value = (0, "SMART overall-health self-assessment test result: FAILED", "")
        
        result = hdd_check(self.valid_device, scan_blocks=False)
        self.assertEqual(result, "danger")
    
    @patch('core.storage.tools.linux.hdd_check.os.path.exists')
    @patch('core.storage.tools.linux.hdd_check.run_command')
    def test_hdd_check_with_scan_success(self, mock_run_command, mock_exists):
        """测试开启扫描且成功的情况"""
        # 模拟文件存在和块设备有效
        mock_exists.side_effect = lambda x: True if x in [self.valid_device, "/sys/block/sda"] else False
        
        # 模拟SMART检查成功
        mock_run_command.side_effect = [
            (0, "SMART overall-health self-assessment test result: PASSED", ""),
            (0, "", "")  # badblocks检查成功，无坏道
        ]
        
        result = hdd_check(self.valid_device, scan_blocks=True)
        self.assertEqual(result, "health")
        self.assertEqual(mock_run_command.call_count, 2)
    
    @patch('core.storage.tools.linux.hdd_check.os.path.exists')
    @patch('core.storage.tools.linux.hdd_check.run_command')
    def test_hdd_check_with_scan_danger(self, mock_run_command, mock_exists):
        """测试开启扫描且发现坏道的情况"""
        # 模拟文件存在和块设备有效
        mock_exists.side_effect = lambda x: True if x in [self.valid_device, "/sys/block/sda"] else False
        
        # 模拟SMART检查成功，但badblocks发现坏道
        mock_run_command.side_effect = [
            (0, "SMART overall-health self-assessment test result: PASSED", ""),
            (0, "12345 67890", "")  # badblocks发现坏道
        ]
        
        result = hdd_check(self.valid_device, scan_blocks=True)
        self.assertEqual(result, "danger")
    
    def test_hdd_check_device_none(self):
        """测试设备路径为None的情况"""
        result = hdd_check(None)
        self.assertIsNone(result)
    
    def test_hdd_check_device_empty_string(self):
        """测试设备路径为空字符串的情况"""
        result = hdd_check("")
        self.assertIsNone(result)
    
    def test_hdd_check_device_whitespace(self):
        """测试设备路径只包含空白字符的情况"""
        result = hdd_check("   ")
        self.assertIsNone(result)
    
    def test_hdd_check_device_not_string(self):
        """测试设备路径不是字符串的情况"""
        result = hdd_check(123)
        self.assertIsNone(result)
    
    @patch('core.storage.tools.linux.hdd_check.os.path.exists')
    def test_hdd_check_device_not_exist(self, mock_exists):
        """测试设备文件不存在的情况"""
        mock_exists.return_value = False
        
        result = hdd_check(self.invalid_device)
        self.assertIsNone(result)
    
    @patch('core.storage.tools.linux.hdd_check.os.path.exists')
    def test_hdd_check_not_block_device(self, mock_exists):
        """测试不是块设备的情况"""
        # 模拟文件存在但不是块设备
        mock_exists.side_effect = lambda x: True if x == self.non_block_device else False
        
        result = hdd_check(self.non_block_device)
        self.assertIsNone(result)
    
    @patch('core.storage.tools.linux.hdd_check.os.path.exists')
    @patch('core.storage.tools.linux.hdd_check.run_command')
    def test_hdd_check_smart_command_failed(self, mock_run_command, mock_exists):
        """测试SMART命令执行失败的情况"""
        # 模拟文件存在和块设备有效
        mock_exists.side_effect = lambda x: True if x in [self.valid_device, "/sys/block/sda"] else False
        
        # 模拟SMART命令失败
        mock_run_command.return_value = (1, "", "Permission denied")
        
        result = hdd_check(self.valid_device)
        self.assertIsNone(result)
    
    @patch('core.storage.tools.linux.hdd_check.os.path.exists')
    @patch('core.storage.tools.linux.hdd_check.run_command')
    def test_hdd_check_badblocks_command_failed(self, mock_run_command, mock_exists):
        """测试badblocks命令执行失败的情况"""
        # 模拟文件存在和块设备有效
        mock_exists.side_effect = lambda x: True if x in [self.valid_device, "/sys/block/sda"] else False
        
        # 模拟SMART成功，但badblocks失败
        mock_run_command.side_effect = [
            (0, "SMART overall-health self-assessment test result: PASSED", ""),
            (1, "", "Permission denied")
        ]
        
        result = hdd_check(self.valid_device, scan_blocks=True)
        self.assertIsNone(result)
    
    @patch('core.storage.tools.linux.hdd_check.os.path.exists')
    @patch('core.storage.tools.linux.hdd_check.run_command')
    def test_hdd_check_device_parameter_stripped(self, mock_run_command, mock_exists):
        """测试设备路径参数会被正确去除空白字符"""
        # 模拟文件存在和块设备有效
        mock_exists.side_effect = lambda x: True if x in [self.valid_device, "/sys/block/sda"] else False
        
        # 模拟SMART检查成功
        mock_run_command.return_value = (0, "SMART overall-health self-assessment test result: PASSED", "")
        
        # 测试带空白字符的设备路径
        result = hdd_check("  /dev/sda  ", scan_blocks=False)
        self.assertEqual(result, "health")
        
        # 验证调用时路径已被清理
        mock_run_command.assert_called_with(["sudo", "smartctl", "-H", "/dev/sda"])


class TestRunCommand(unittest.TestCase):
    """run_command函数的测试类"""
    
    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        """测试命令执行成功的情况"""
        # 模拟subprocess.run的返回值
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b"success output"
        mock_result.stderr = b""
        mock_run.return_value = mock_result
        
        code, out, err = run_command(["echo", "test"])
        
        self.assertEqual(code, 0)
        self.assertEqual(out, "success output")
        self.assertEqual(err, "")
    
    @patch('subprocess.run')
    def test_run_command_failure(self, mock_run):
        """测试命令执行失败的情况"""
        # 模拟subprocess.run的返回值
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = b""
        mock_result.stderr = b"error message"
        mock_run.return_value = mock_result
        
        code, out, err = run_command(["invalid", "command"])
        
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertEqual(err, "error message")
    
    @patch('subprocess.run')
    def test_run_command_with_unicode(self, mock_run):
        """测试命令输出包含Unicode字符的情况"""
        # 模拟包含Unicode的输出
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "测试输出".encode('utf-8')
        mock_result.stderr = "".encode('utf-8')
        mock_run.return_value = mock_result
        
        code, out, err = run_command(["echo", "test"])
        
        self.assertEqual(code, 0)
        self.assertEqual(out, "测试输出")
        self.assertEqual(err, "")


if __name__ == '__main__':
    # 设置测试输出格式
    unittest.main(verbosity=2)
