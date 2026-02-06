"""
主 CLI 入口

基于 cmd 模块的命令行界面框架，支持多个子命令组。
"""

import cmd
import sys
from .device_manager import DeviceManager
from .file_manager import FileManager


class FileTidyCLI(cmd.Cmd):
    """FileTidy 主命令行界面"""
    
    intro = """
========================================
  FileTidy 命令行工具
  网络 API 失效时的临时工具组
========================================
输入 'help' 查看可用命令
输入 'help <command>' 查看命令详情
输入 'quit' 或 'exit' 退出
"""
    
    prompt = 'filetidy> '
    
    def __init__(self):
        super().__init__()
        # 初始化子命令组
        self.device_manager = DeviceManager()
        self.file_manager = FileManager()
    
    def do_devicemanager(self, arg):
        """
        进入设备管理子命令组
        
        用法: devicemanager
        输入 'help' 查看设备管理相关命令
        """
        self.device_manager.cmdloop()
    
    def do_dm(self, arg):
        """devicemanager 的简写"""
        self.do_devicemanager(arg)
    
    def do_filemanager(self, arg):
        """
        进入文件管理子命令组
        
        用法: filemanager
        输入 'help' 查看文件管理相关命令
        """
        self.file_manager.cmdloop()
    
    def do_fm(self, arg):
        """filemanager 的简写"""
        self.do_filemanager(arg)
    
    def do_quit(self, arg):
        """退出程序"""
        print("再见！")
        return True
    
    def do_exit(self, arg):
        """退出程序（quit 的别名）"""
        return self.do_quit(arg)
    
    def do_EOF(self, arg):
        """Ctrl+D 退出"""
        print("\n再见！")
        return True
    
    def default(self, line):
        """处理未知命令"""
        print(f"未知命令: {line}")
        print("输入 'help' 查看可用命令")


def main():
    """CLI 入口函数"""
    cli = FileTidyCLI()
    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        print("\n\n程序被中断，再见！")
        sys.exit(0)


if __name__ == '__main__':
    main()
