"""
设备管理子命令组

提供设备相关的命令行操作，包括：
- 列出所有设备
- 添加设备
- 删除设备
- 查看设备信息
- 更新设备属性
- 检查设备状态
"""

import cmd
from datetime import datetime
from apps.common.database.models import DeviceModel, DeviceState
from apps.common.database.session import session_scope
from apps.infra.device.device_factory import DeviceFactory


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
    
    def __init__(self):
        super().__init__()
        self.device_factory = DeviceFactory()
    
    def do_list(self, arg):
        """
        列出所有设备
        
        用法: list [--kind <类型>] [--state <状态>]
        
        参数:
          --kind <类型>    过滤设备类型 (HDD, SSD, Tape, TF Card)
          --state <状态>   过滤设备状态 (healthy, danger, fault, no_longer_used, removed)
        
        示例:
          list
          list --kind HDD
          list --state healthy
        """
        args = self._parse_args(arg)
        kind_filter = args.get('--kind')
        state_filter = args.get('--state')
        
        with session_scope() as session:
            query = session.query(DeviceModel)
            
            if kind_filter:
                query = query.filter(DeviceModel.kind == kind_filter)
            
            if state_filter:
                try:
                    state_enum = DeviceState[state_filter.upper()]
                    query = query.filter(DeviceModel.state == state_enum)
                except KeyError:
                    print(f"错误: 无效的状态 '{state_filter}'")
                    print("可用状态: healthy, danger, fault, no_longer_used, removed")
                    return
            
            devices = query.all()
            
            if not devices:
                print("没有找到设备")
                return
            
            print(f"\n找到 {len(devices)} 个设备:\n")
            print(f"{'序列号':<20} {'名称':<20} {'类型':<10} {'状态':<15} {'容量(GB)':<15} {'添加时间':<20}")
            print("-" * 100)
            
            for device in devices:
                capacity_gb = device.capacity / (1024**3) if device.capacity and device.capacity > 0 else 0
                add_time_str = device.add_time.strftime('%Y-%m-%d %H:%M:%S') if device.add_time else 'N/A'
                print(f"{device.serial:<20} {device.name:<20} {device.kind or 'N/A':<10} "
                      f"{device.state.value if device.state else 'N/A':<15} "
                      f"{capacity_gb:.2f} GB{'':<8} {add_time_str:<20}")
            print()
    
    def do_show(self, arg):
        """
        显示指定设备的详细信息
        
        用法: show <序列号>
        
        示例:
          show S123456789
        """
        if not arg:
            print("错误: 请提供设备序列号")
            print("用法: show <序列号>")
            return
        
        serial = arg.strip()
        
        with session_scope() as session:
            device = session.query(DeviceModel).filter(DeviceModel.serial == serial).first()
            
            if not device:
                print(f"错误: 未找到序列号为 '{serial}' 的设备")
                return
            
            print(f"\n设备详细信息:")
            print(f"  序列号: {device.serial}")
            print(f"  名称: {device.name}")
            print(f"  类型: {device.kind or 'N/A'}")
            print(f"  状态: {device.state.value if device.state else 'N/A'}")
            print(f"  容量: {device.capacity / (1024**3):.2f} GB" if device.capacity and device.capacity > 0 else "  容量: N/A")
            print(f"  添加时间: {device.add_time.strftime('%Y-%m-%d %H:%M:%S') if device.add_time else 'N/A'}")
            print(f"  最后检查时间: {device.last_check_time.strftime('%Y-%m-%d %H:%M:%S') if device.last_check_time else 'N/A'}")
            print(f"  其他信息: {device.info or 'N/A'}")
            print()
    
    def do_add(self, arg):
        """
        添加新设备
        
        用法: add --path <设备路径> [--name <名称>] [--kind <类型>] [--capacity <容量(字节)>] [--info <信息>]
        
        参数:
          --path <路径>      设备路径 (必需)
          --name <名称>      设备名称 (可选，默认自动生成)
          --kind <类型>      设备类型 (可选，默认自动检测)
          --capacity <容量>  设备容量，单位字节 (可选，默认自动检测)
          --info <信息>      其他信息 (可选)
        
        示例:
          add --path /dev/disk0
          add --path /dev/sda --name "主硬盘"
          add --path /dev/sdb --kind HDD --capacity 1000000000000
        
        args = self._parse_args(arg)
        
        path = args.get('--path')
        if not path:
            print("错误: 必须提供设备路径")
            print("用法: add --path <设备路径> [选项...]")
            return
        
        try:
            kwargs = {'path': path}
            
            if '--name' in args:
                kwargs['name'] = args['--name']
            
            if '--kind' in args:
                kwargs['kind'] = args['--kind']
            
            if '--capacity' in args:
                try:
                    kwargs['capacity'] = int(args['--capacity'])
                except ValueError:
                    print("错误: 容量必须是整数（字节）")
                    return
            
            if '--info' in args:
                kwargs['info'] = args['--info']
            
            # 根据类型创建设备
            from apps.infra.device.os_adapter.get_type import get_type
            
            device = None
            if 'kind' in kwargs:
                kind = kwargs['kind'].upper()
                if kind == 'HDD':
                    from apps.infra.device.impl.hdd_device import HddDevice
                    device = HddDevice.new_device(**kwargs)
                elif kind == 'SSD':
                    from apps.infra.device.impl.ssd_device import SsdDevice
                    device = SsdDevice.new_device(**kwargs)
                elif kind.startswith('TAPE'):
                    from apps.infra.device.impl.tape_device import TapeDevice
                    device = TapeDevice.new_device(**kwargs)
                else:
                    print(f"错误: 不支持的类型 '{kind}'")
                    return
            else:
                # 自动检测类型
                detected_kind = get_type(kwargs['path'])
                if detected_kind is None:
                    print("错误: 无法自动检测设备类型，请使用 --kind 参数指定")
                    return
                
                detected_kind = detected_kind.upper()
                if detected_kind == 'HDD':
                    from apps.infra.device.impl.hdd_device import HddDevice
                    device = HddDevice.new_device(**kwargs)
                elif detected_kind == 'SSD':
                    from apps.infra.device.impl.ssd_device import SsdDevice
                    device = SsdDevice.new_device(**kwargs)
                elif detected_kind.startswith('TAPE'):
                    from apps.infra.device.impl.tape_device import TapeDevice
                    device = TapeDevice.new_device(**kwargs)
                else:
                    print(f"错误: 不支持检测到的类型 '{detected_kind}'")
                    return
            
            print(f"成功添加设备: {device.orm_model.name} (序列号: {device.orm_model.serial})")
            
        except Exception as e:
            print(f"错误: {str(e)}")
        """
        print("not implemented")
    def do_delete(self, arg):
        """
        删除设备
        
        用法: delete <序列号>
        
        警告: 此操作不可恢复！
        
        示例:
          delete S123456789
        """
        if not arg:
            print("错误: 请提供设备序列号")
            print("用法: delete <序列号>")
            return
        
        serial = arg.strip()
        
        # 确认删除
        confirm = input(f"确认删除设备 '{serial}'? (yes/no): ")
        if confirm.lower() != 'yes':
            print("已取消")
            return
        
        with session_scope() as session:
            device = session.query(DeviceModel).filter(DeviceModel.serial == serial).first()
            
            if not device:
                print(f"错误: 未找到序列号为 '{serial}' 的设备")
                return
            
            session.delete(device)
            session.commit()
            print(f"成功删除设备: {serial}")
    
    def do_update(self, arg):
        """
        更新设备属性
        
        用法: update <序列号> --<属性名> <值>
        
        可用属性:
          --name <名称>          设备名称
          --state <状态>          设备状态 (healthy, danger, fault, no_longer_used, removed)
          --capacity <容量(字节)>  设备容量
          --info <信息>           其他信息
        
        示例:
          update S123456789 --name "新名称"
          update S123456789 --state danger
          update S123456789 --capacity 2000000000000
        """
        args = arg.split()
        if len(args) < 3:
            print("错误: 参数不足")
            print("用法: update <序列号> --<属性名> <值>")
            return
        
        serial = args[0]
        attr_name = args[1].lstrip('-')
        attr_value = ' '.join(args[2:])
        
        with session_scope() as session:
            device = session.query(DeviceModel).filter(DeviceModel.serial == serial).first()
            
            if not device:
                print(f"错误: 未找到序列号为 '{serial}' 的设备")
                return
            
            try:
                # 获取设备实例
                device_obj = self.device_factory.get_device(serial)
                if not device_obj:
                    print(f"错误: 无法创建设备实例")
                    return
                
                # 处理状态枚举
                if attr_name == 'state':
                    try:
                        attr_value = DeviceState[attr_value.upper()]
                    except KeyError:
                        print(f"错误: 无效的状态 '{attr_value}'")
                        print("可用状态: healthy, danger, fault, no_longer_used, removed")
                        return
                
                # 处理容量
                if attr_name == 'capacity':
                    try:
                        attr_value = int(attr_value)
                    except ValueError:
                        print("错误: 容量必须是整数（字节）")
                        return
                
                device_obj.set(attr_name, attr_value)
                print(f"成功更新设备 '{serial}' 的 {attr_name} 为 {attr_value}")
                
            except Exception as e:
                print(f"错误: {str(e)}")
    
    def do_check(self, arg):
        """
        检查设备状态
        
        用法: check <序列号>
        
        示例:
          check S123456789
        """
        if not arg:
            print("错误: 请提供设备序列号")
            print("用法: check <序列号>")
            return
        
        serial = arg.strip()
        
        try:
            device = self.device_factory.get_device(serial)
            if not device:
                print(f"错误: 未找到序列号为 '{serial}' 的设备")
                return
            
            print(f"正在检查设备 '{serial}'...")
            # 调用设备的 check 方法
            device.check()
            
            # 更新最后检查时间
            with session_scope() as session:
                db_device = session.query(DeviceModel).filter(DeviceModel.serial == serial).first()
                if db_device:
                    db_device.last_check_time = datetime.utcnow()
                    session.commit()
            
            print(f"检查完成")
            
        except Exception as e:
            print(f"错误: {str(e)}")
    
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
    
    def _parse_args(self, arg):
        """解析命令行参数"""
        args = {}
        parts = arg.split()
        i = 0
        while i < len(parts):
            if parts[i].startswith('--'):
                key = parts[i]
                if i + 1 < len(parts) and not parts[i + 1].startswith('--'):
                    args[key] = parts[i + 1]
                    i += 2
                else:
                    args[key] = True
                    i += 1
            else:
                i += 1
        return args
    
    def default(self, line):
        """处理未知命令"""
        print(f"未知命令: {line}")
        print("输入 'help' 查看可用命令")
