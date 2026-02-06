"""
文件管理子命令组

提供文件相关的命令行操作，包括：
- 注册文件到数据库
- 导入文件到数据集
"""

import cmd
from datetime import datetime
from apps.infra.apis.file_manager import reg_file, intro_file


class FileManager(cmd.Cmd):
    """文件管理命令行界面"""
    
    intro = """
========================================
  文件管理工具
========================================
输入 'help' 查看可用命令
输入 'back' 返回主菜单
"""
    
    prompt = 'filetidy/filemanager> '
    
    def do_reg_file(self, arg):
        """
        注册文件到数据库
        
        用法: reg_file
        将提示您依次输入所有参数，直接敲回车表示使用默认值（None）
        """
        print("\n开始注册文件...")
        print("（直接敲回车表示使用默认值 None）\n")
        
        # 提示输入 path（必需参数）
        path = input("请输入文件或目录路径: ").strip()
        if not path:
            print("错误: 路径不能为空")
            return
        
        # 提示输入 state（可选）
        state_input = input("请输入文件状态 (直接回车使用默认值 'online'): ").strip()
        state = state_input if state_input else None
        
        # 提示输入 info（可选）
        info_input = input("请输入文件其他信息 (直接回车使用默认值 ''): ").strip()
        info = info_input if info_input else None
        
        # 提示输入 add_time（可选）
        add_time_input = input("请输入文件添加时间 (格式: YYYY-MM-DD HH:MM:SS，直接回车使用当前时间): ").strip()
        add_time = None
        if add_time_input:
            try:
                add_time = datetime.strptime(add_time_input, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print("警告: 时间格式不正确，将使用当前时间")
                add_time = None
        
        # 提示输入 auto_add_to_locations（可选，默认为True）
        auto_add_input = input("是否自动添加到FileLocationsModel (y/n，直接回车使用默认值 'y'): ").strip().lower()
        auto_add_to_locations = True  # 默认值
        if auto_add_input:
            auto_add_to_locations = auto_add_input in ['y', 'yes', 'true', '1']
        
        # 调用 reg_file 函数
        try:
            print(f"\n正在处理路径: {path}")
            count = reg_file(
                path=path,
                state=state,
                info=info,
                add_time=add_time,
                auto_add_to_locations=auto_add_to_locations
            )
            print(f"\n成功注册 {count} 个文件到数据库")
        except Exception as e:
            print(f"\n错误: {str(e)}")
    
    def do_reg(self, arg):
        """reg_file 的简写"""
        self.do_reg_file(arg)

    def do_intro_file(self, arg):
        """
        导入文件到数据集
        
        用法: intro_file
        将提示您依次输入所有参数，直接敲回车表示使用默认值（None）
        """
        print("\n开始导入文件到数据集...")
        print("（直接敲回车表示使用默认值 None）\n")
        
        # 提示输入 path（必需参数）
        path = input("请输入文件或目录路径: ").strip()
        if not path:
            print("错误: 路径不能为空")
            return
        
        # 提示输入 state（可选）
        state_input = input("请输入文件状态 (直接回车使用默认值 'online'): ").strip()
        state = state_input if state_input else None
        
        # 提示输入 info（可选）
        info_input = input("请输入文件其他信息 (直接回车使用默认值 ''): ").strip()
        info = info_input if info_input else None
        
        # 提示输入 add_time（可选）
        add_time_input = input("请输入文件添加时间 (格式: YYYY-MM-DD HH:MM:SS，直接回车使用当前时间): ").strip()
        add_time = None
        if add_time_input:
            try:
                add_time = datetime.strptime(add_time_input, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print("警告: 时间格式不正确，将使用当前时间")
                add_time = None
        
        # 调用 intro_file 函数
        try:
            print(f"\n正在处理路径: {path}")
            count = intro_file(
                path=path,
                state=state,
                info=info,
                add_time=add_time
            )
            print(f"\n成功导入 {count} 个文件到数据集")
        except Exception as e:
            print(f"\n错误: {str(e)}")
    
    def do_intro(self, arg):
        """intro_file 的简写"""
        self.do_intro_file(arg)
    
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
