"""
设备管理子命令组

提供设备相关的命令行操作，包括：
- 列出所有设备
- 添加设备
- 移除设备
- 查看设备信息
- 更新设备属性
- 检查设备状态
"""

import cmd
from datetime import datetime
from apps.infra.apis.device_manager import (
    list_devices,
    show_device,
    add_device,
    remove_device,
    update_device,
    check_device,
)


class DeviceManager(cmd.Cmd):
    """设备管理命令行界面"""
    
    intro = """
========================================
  设备管理工具
========================================
输入 'help' 查看可用命令
输入 'back' 返回主菜单
"""
    
    prompt = 'filetidy/devicemanager> '
    
    def do_list(self, arg):
        """
        列出所有设备
        
        用法: list
        将提示您依次输入过滤条件，直接敲回车表示不使用该过滤条件
        """
        print("\n开始列出设备...")
        print("（直接敲回车表示不使用该过滤条件）\n")
        
        # 提示输入 kind_filter（可选）
        kind_input = input("请输入设备类型过滤 (HDD, SSD, Tape, TF Card，直接回车不使用): ").strip()
        kind_filter = kind_input if kind_input else None
        
        # 提示输入 state_filter（可选）
        state_input = input("请输入设备状态过滤 (healthy, danger, fault, no_longer_used, removed，直接回车不使用): ").strip()
        state_filter = state_input if state_input else None
        
        # 调用 list_devices 函数
        try:
            devices = list_devices(
                kind_filter=kind_filter,
                state_filter=state_filter,
            )
            
            if not devices:
                print("\n没有找到设备")
                return
            
            print(f"\n找到 {len(devices)} 个设备:\n")
            print(f"{'序列号':<20} {'名称':<20} {'类型':<10} {'状态':<15} {'容量(GB)':<15} {'添加时间':<20}")
            print("-" * 100)
            
            for device in devices:
                print(f"{device['serial']:<20} {device['name']:<20} {device['kind']:<10} "
                      f"{device['state']:<15} {device['capacity_gb']:.2f} GB{'':<8} {device['add_time']:<20}")
            print()
        except Exception as e:
            print(f"\n错误: {str(e)}")
    
    def do_show(self, arg):
        """
        显示指定设备的详细信息
        
        用法: show
        将提示您输入设备序列号或路径
        """
        print("\n开始显示设备信息...")
        print("（可以直接输入序列号或路径）\n")
        
        # 提示输入 serial 或 path（必需参数）
        input_value = input("请输入设备序列号或路径: ").strip()
        if not input_value:
            print("错误: 序列号或路径不能为空")
            return
        
        # 判断输入的是路径还是序列号（简单判断：如果包含 / 或 \ 或 : 则认为是路径）
        is_path = '/' in input_value or '\\' in input_value or ':' in input_value
        
        # 调用 show_device 函数
        try:
            if is_path:
                device = show_device(path=input_value)
            else:
                device = show_device(serial=input_value)
            
            print(f"\n设备详细信息:")
            print(f"  序列号: {device['serial']}")
            print(f"  名称: {device['name']}")
            print(f"  类型: {device['kind']}")
            print(f"  状态: {device['state']}")
            print(f"  容量: {device['capacity_gb']:.2f} GB" if device['capacity_gb'] > 0 else "  容量: N/A")
            print(f"  添加时间: {device['add_time']}")
            print(f"  最后检查时间: {device['last_check_time']}")
            print(f"  其他信息: {device['info']}")
            print()
        except Exception as e:
            print(f"\n错误: {str(e)}")
    
    def do_add(self, arg):
        """
        添加新设备
        
        用法: add
        将提示您依次输入所有参数，直接敲回车表示使用默认值（None）
        """
        print("\n开始添加设备...")
        print("（直接敲回车表示使用默认值 None）\n")
        
        # 提示输入 path（必需参数）
        path = input("请输入设备路径: ").strip()
        if not path:
            print("错误: 路径不能为空")
            return
        
        # 提示输入 name（可选）
        name_input = input("请输入设备名称 (直接回车使用默认值，自动生成): ").strip()
        name = name_input if name_input else None
        
        # 提示输入 kind（可选）
        kind_input = input("请输入设备类型 (HDD, SSD, Tape等，直接回车使用默认值，自动检测): ").strip()
        kind = kind_input if kind_input else None
        
        # 提示输入 capacity（可选）
        capacity_input = input("请输入设备容量（字节，直接回车使用默认值，自动检测）: ").strip()
        capacity = None
        if capacity_input:
            try:
                capacity = int(capacity_input)
            except ValueError:
                print("警告: 容量格式不正确，将使用自动检测")
                capacity = None
        
        # 提示输入 info（可选）
        info_input = input("请输入设备其他信息 (直接回车使用默认值 ''): ").strip()
        info = info_input if info_input else None
        
        # 调用 add_device 函数
        try:
            result = add_device(
                path=path,
                name=name,
                kind=kind,
                capacity=capacity,
                info=info,
            )
            print(f"\n成功添加设备: {result['name']} (序列号: {result['serial']})")
        except Exception as e:
            print(f"\n错误: {str(e)}")
    
    def do_remove(self, arg):
        """
        移除设备
        
        用法: remove
        将提示您输入设备序列号，并确认移除
        """
        print("\n开始移除设备...\n")
        
        # 提示输入 serial（必需参数）
        serial = input("请输入设备序列号: ").strip()
        if not serial:
            print("错误: 序列号不能为空")
            return
        
        # 确认移除
        confirm = input(f"确认移除设备 '{serial}'? (yes/no): ")
        if confirm.lower() != 'yes':
            print("已取消")
            return
        
        # 调用 remove_device 函数
        try:
            remove_device(serial=serial)
            print(f"\n成功移除设备: {serial}")
        except Exception as e:
            print(f"\n错误: {str(e)}")
    
    def do_update(self, arg):
        """
        更新设备属性
        
        用法: update
        将提示您依次输入设备序列号和要更新的属性
        """
        print("\n开始更新设备属性...")
        print("（直接敲回车表示不更新该属性）\n")
        
        # 提示输入 serial（必需参数）
        serial = input("请输入设备序列号: ").strip()
        if not serial:
            print("错误: 序列号不能为空")
            return
        
        # 提示输入 name（可选）
        name_input = input("请输入设备名称 (直接回车不更新): ").strip()
        name = name_input if name_input else None
        
        # 提示输入 state（可选）
        state_input = input("请输入设备状态 (healthy, danger, fault, no_longer_used, removed，直接回车不更新): ").strip()
        state = state_input if state_input else None
        
        # 提示输入 capacity（可选）
        capacity_input = input("请输入设备容量（字节，直接回车不更新）: ").strip()
        capacity = None
        if capacity_input:
            try:
                capacity = int(capacity_input)
            except ValueError:
                print("警告: 容量格式不正确，将跳过此更新")
                capacity = None
        
        # 提示输入 info（可选）
        info_input = input("请输入设备其他信息 (直接回车不更新): ").strip()
        info = info_input if info_input else None
        
        # 调用 update_device 函数
        try:
            update_device(
                serial=serial,
                name=name,
                state=state,
                capacity=capacity,
                info=info,
            )
            print(f"\n成功更新设备 '{serial}' 的属性")
        except Exception as e:
            print(f"\n错误: {str(e)}")
    
    def do_check(self, arg):
        """
        检查设备状态
        
        用法: check
        将提示您输入设备序列号
        """
        print("\n开始检查设备状态...\n")
        
        # 提示输入 serial（必需参数）
        serial = input("请输入设备序列号: ").strip()
        if not serial:
            print("错误: 序列号不能为空")
            return
        
        # 调用 check_device 函数
        try:
            print(f"正在检查设备 '{serial}'...")
            check_device(serial=serial)
            print(f"\n检查完成")
        except Exception as e:
            print(f"\n错误: {str(e)}")
    
    def do_back(self, arg):
        """返回主菜单"""
        return True
    
    def do_quit(self, arg):
        """退出程序"""
        return True
    
    def do_exit(self, arg):
        """退出程序（quit 的别名）"""
        return True
    
    def do_EOF(self, arg):
        """Ctrl+D 返回主菜单"""
        return True
    
    def default(self, line):
        """处理未知命令"""
        print(f"未知命令: {line}")
        print("输入 'help' 查看可用命令")
