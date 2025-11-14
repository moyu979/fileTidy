#!/usr/bin/env python3
"""
API 测试命令行工具
用于测试 device 和 volume 相关的 REST API 接口
"""

import argparse
import json
import sys
import requests
from typing import Optional, Dict, Any


class APITester:
    """API 测试工具类"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:5000"):
        """
        初始化 API 测试工具
        
        Args:
            base_url: API 服务器的基础 URL
        """
        self.base_url = base_url.rstrip('/')
    
    def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送 POST 请求
        
        Args:
            endpoint: API 端点
            data: 请求数据
        
        Returns:
            响应 JSON 数据
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            print(f"错误: 无法连接到服务器 {url}")
            print("请确保 API 服务器正在运行")
            sys.exit(1)
        except requests.exceptions.Timeout:
            print(f"错误: 请求超时")
            sys.exit(1)
        except requests.exceptions.HTTPError as e:
            try:
                error_data = response.json()
                return error_data
            except:
                print(f"错误: HTTP {response.status_code} - {e}")
                sys.exit(1)
        except Exception as e:
            print(f"错误: {e}")
            sys.exit(1)
    
    def _print_result(self, result: Dict[str, Any], success_message: str = None):
        """
        打印结果
        
        Args:
            result: API 响应结果
            success_message: 成功时的自定义消息
        """
        if result.get("success"):
            if success_message:
                print(success_message)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"失败: {result.get('message', '未知错误')}")
            sys.exit(1)
    
    # Device API 方法
    def device_reg(self, path: str):
        """注册设备"""
        result = self._post("/api/device/reg", {"path": path})
        self._print_result(result, f"设备注册成功: {path}")
    
    def device_replace(self, path1: str, path2: str):
        """替换设备"""
        result = self._post("/api/device/replace", {"path1": path1, "path2": path2})
        self._print_result(result, f"设备替换成功: {path1} -> {path2}")
    
    def device_check(self, path: str):
        """检查设备"""
        result = self._post("/api/device/check", {"path": path})
        self._print_result(result, f"设备检查完成: {path}")
    
    def device_exists(self, path: str):
        """检查设备是否存在"""
        result = self._post("/api/device/exists", {"path": path})
        exists = result.get("exists", False)
        status = "存在" if exists else "不存在"
        print(f"设备 {path}: {status}")
        self._print_result(result)
    
    def device_get_path(self, serial: str):
        """根据序列号获取设备路径"""
        result = self._post("/api/device/path", {"serial": serial})
        path = result.get("path")
        if path:
            print(f"序列号 {serial} 对应的路径: {path}")
        else:
            print(f"序列号 {serial} 对应的设备未挂载或不存在")
        self._print_result(result)
    
    def device_get_serial(self, path: str):
        """根据设备路径获取序列号"""
        result = self._post("/api/device/serial", {"path": path})
        serial = result.get("serial")
        if serial:
            print(f"设备路径 {path} 对应的序列号: {serial}")
        else:
            print(f"无法获取设备 {path} 的序列号")
        self._print_result(result)
    
    def device_get_capacity(self, path: str):
        """获取设备容量"""
        result = self._post("/api/device/capacity", {"path": path})
        capacity = result.get("capacity")
        if capacity is not None:
            print(f"设备 {path} 的容量: {capacity}")
        self._print_result(result)
    
    # Volume API 方法
    def volume_reg(self, volume_path: str, volume_id: Optional[str] = None):
        """注册卷"""
        data = {"volume_path": volume_path}
        if volume_id:
            data["volume_id"] = volume_id
        result = self._post("/api/volume/reg", data)
        volume_id_result = result.get("volume_id")
        if volume_id_result:
            print(f"卷注册成功: {volume_path} (ID: {volume_id_result})")
        self._print_result(result)
    
    def volume_exists(self, volume_path: Optional[str] = None, name: Optional[str] = None):
        """检查卷是否存在"""
        if not volume_path and not name:
            print("错误: 必须提供 volume_path 或 name 至少一个")
            sys.exit(1)
        if volume_path and name:
            print("错误: 不能同时提供 volume_path 和 name")
            sys.exit(1)
        
        data = {}
        if volume_path:
            data["volume_path"] = volume_path
        if name:
            data["name"] = name
        
        result = self._post("/api/volume/exists", data)
        exists = result.get("exists", False)
        identifier = volume_path or name
        status = "存在" if exists else "不存在"
        print(f"卷 {identifier}: {status}")
        self._print_result(result)
    
    def volume_get_path(self, device_path: str):
        """获取卷路径"""
        result = self._post("/api/volume/path", {"device_path": device_path})
        path = result.get("path")
        if path:
            print(f"设备 {device_path} 对应的卷路径: {path}")
        else:
            print(f"设备 {device_path} 对应的卷未挂载或不存在")
        self._print_result(result)
    
    def volume_get(self, volume_path: str, strict: bool = False):
        """获取卷信息"""
        result = self._post("/api/volume/get", {
            "volume_path": volume_path,
            "strict": strict
        })
        volume_id = result.get("volume_id")
        path = result.get("volume_path")
        if volume_id:
            print(f"卷 ID: {volume_id}")
            print(f"卷路径: {path}")
        else:
            print(f"未找到卷: {volume_path}")
        self._print_result(result)
    
    def volume_check(self, volume_path: str):
        """检查卷"""
        result = self._post("/api/volume/check", {"volume_path": volume_path})
        self._print_result(result, f"卷检查完成: {volume_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="API 测试命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 设备相关
  %(prog)s device reg /dev/sda
  %(prog)s device exists /dev/sda
  %(prog)s device get-serial /dev/sda
  %(prog)s device get-capacity /dev/sda
  
  # 卷相关
  %(prog)s volume reg /mnt/volume1
  %(prog)s volume exists --volume-path /mnt/volume1
  %(prog)s volume get /mnt/volume1
  %(prog)s volume check /mnt/volume1
        """
    )
    
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:5000",
        help="API 服务器 URL (默认: http://127.0.0.1:5000)"
    )
    
    subparsers = parser.add_subparsers(dest="category", help="API 类别")
    
    # Device 子命令
    device_parser = subparsers.add_parser("device", help="设备相关 API")
    device_subparsers = device_parser.add_subparsers(dest="action", help="操作")
    
    # device reg
    device_reg_parser = device_subparsers.add_parser("reg", help="注册设备")
    device_reg_parser.add_argument("path", help="设备路径")
    
    # device replace
    device_replace_parser = device_subparsers.add_parser("replace", help="替换设备")
    device_replace_parser.add_argument("path1", help="新设备路径")
    device_replace_parser.add_argument("path2", help="要被替换的设备路径")
    
    # device check
    device_check_parser = device_subparsers.add_parser("check", help="检查设备")
    device_check_parser.add_argument("path", help="设备路径")
    
    # device exists
    device_exists_parser = device_subparsers.add_parser("exists", help="检查设备是否存在")
    device_exists_parser.add_argument("path", help="设备路径")
    
    # device get-path
    device_get_path_parser = device_subparsers.add_parser("get-path", help="根据序列号获取设备路径")
    device_get_path_parser.add_argument("serial", help="设备序列号")
    
    # device get-serial
    device_get_serial_parser = device_subparsers.add_parser("get-serial", help="根据设备路径获取序列号")
    device_get_serial_parser.add_argument("path", help="设备路径")
    
    # device get-capacity
    device_get_capacity_parser = device_subparsers.add_parser("get-capacity", help="获取设备容量")
    device_get_capacity_parser.add_argument("path", help="设备路径")
    
    # Volume 子命令
    volume_parser = subparsers.add_parser("volume", help="卷相关 API")
    volume_subparsers = volume_parser.add_subparsers(dest="action", help="操作")
    
    # volume reg
    volume_reg_parser = volume_subparsers.add_parser("reg", help="注册卷")
    volume_reg_parser.add_argument("volume_path", help="卷路径（必须是挂载点）")
    volume_reg_parser.add_argument("--volume-id", help="可选的卷ID")
    
    # volume exists
    volume_exists_parser = volume_subparsers.add_parser("exists", help="检查卷是否存在")
    volume_exists_group = volume_exists_parser.add_mutually_exclusive_group(required=True)
    volume_exists_group.add_argument("--volume-path", help="卷路径")
    volume_exists_group.add_argument("--name", help="卷名称")
    
    # volume get-path
    volume_get_path_parser = volume_subparsers.add_parser("get-path", help="获取卷路径")
    volume_get_path_parser.add_argument("device_path", help="设备路径")
    
    # volume get
    volume_get_parser = volume_subparsers.add_parser("get", help="获取卷信息")
    volume_get_parser.add_argument("volume_path", help="卷路径")
    volume_get_parser.add_argument("--strict", action="store_true", help="严格模式")
    
    # volume check
    volume_check_parser = volume_subparsers.add_parser("check", help="检查卷")
    volume_check_parser.add_argument("volume_path", help="卷路径")
    
    args = parser.parse_args()
    
    if not args.category or not args.action:
        parser.print_help()
        sys.exit(1)
    
    tester = APITester(args.url)
    
    # 执行对应的操作
    try:
        if args.category == "device":
            if args.action == "reg":
                tester.device_reg(args.path)
            elif args.action == "replace":
                tester.device_replace(args.path1, args.path2)
            elif args.action == "check":
                tester.device_check(args.path)
            elif args.action == "exists":
                tester.device_exists(args.path)
            elif args.action == "get-path":
                tester.device_get_path(args.serial)
            elif args.action == "get-serial":
                tester.device_get_serial(args.path)
            elif args.action == "get-capacity":
                tester.device_get_capacity(args.path)
        
        elif args.category == "volume":
            if args.action == "reg":
                tester.volume_reg(args.volume_path, args.volume_id)
            elif args.action == "exists":
                tester.volume_exists(args.volume_path, args.name)
            elif args.action == "get-path":
                tester.volume_get_path(args.device_path)
            elif args.action == "get":
                tester.volume_get(args.volume_path, args.strict)
            elif args.action == "check":
                tester.volume_check(args.volume_path)
    
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

