import cmd

class VolumeCmd(cmd.Cmd):
    intro = "这是卷管理模块，输入 'help' 查看可用命令，输入 'exit' 返回主菜单。"
    prompt = "(VolumeCmd) "

    def do_getVolume(self, arg):
        args=arg.split()
    
    def do_newVolume(self, arg):
        pass

    def do_delete(self, arg):
        """delete [volume_name] - 删除指定的卷"""
        if arg:
            print(f"删除卷: {arg}")
        else:
            print("请输入卷名，例如: delete my_volume")