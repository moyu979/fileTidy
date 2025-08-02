import cmd


class FileTidyCmd(cmd.Cmd):
    intro = "欢迎使用 FileTidy 命令行工具！输入 'help' 查看可用命令，输入 'exit' 退出。"
    prompt = "(FileTidy) "

    def do_volume(self, arg):
        """进入卷管理模式"""
        if arg:
            print(f"你好, {arg}!")
        else:
            print("你好!")

    def do_add(self, arg):
        """add [x] [y] - 计算两个数字的和"""
        try:
            x, y = map(float, arg.split())
            print(f"{x} + {y} = {x + y}")
        except ValueError:
            print("请输入两个数字，例如: add 2 3")

    def do_subcommand(self, arg):
        """subcommand - 进入二级命令模式"""
        print("进入二级命令模式，输入 'exit' 返回主菜单。")
        SubCommand().cmdloop()

    def do_exit(self, arg):
        """exit - 退出程序"""
        print("再见！")
        return True


class SubCommand(cmd.Cmd):
    intro = "这是二级命令模式，输入 'help' 查看可用命令，输入 'exit' 返回主菜单。"
    prompt = "(SubCommand) "

    def do_hello(self, arg):
        """hello [name] - 在二级命令模式中打招呼"""
        if arg:
            print(f"你好, {arg}!")
        else:
            print("你好，二级命令模式！")

    def do_exit(self, arg):
        """exit - 返回主菜单"""
        print("返回主菜单。")
        return True


if __name__ == "__main__":
    FileTidyCmd().cmdloop()
