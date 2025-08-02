import cmd
from volume_manager.temp.volume import Volume
import volume_manager.temp.volumeFactory as volumeFactory


class VolumeCmd(cmd.Cmd):
    intro = "这是卷管理模块，输入 'help' 查看可用命令，输入 'exit' 返回主菜单。"
    prompt = "(VolumeCmd) "

    def do_getVolume(self, arg):
        args = arg.split()
        volume = None
        if len(args) == 0:
            print("请输入卷名，例如: getVolume my_volume")
        elif len(args) == 1:
            volume = volumeFactory.VolumeFactory.load_volume(id=args[0])
        elif len(args) == 2:
            if args[0] not in ["--id", "--name"]:
                print("第一个参数只能是id或者name")
                volume = None
            elif args[0] == "--id":
                volume = volumeFactory.VolumeFactory.load_volume(id=args[1])
            elif args[0] == "--name":
                volume = volumeFactory.VolumeFactory.load_volume(name=args[1])

    def do_newVolume(self, arg):
        prompts = Volume.get_all_fileds()
        print(prompts.keys())

        inputs = {}
        for key, value in prompts.items():
            prompt = value.get("prompt", "not has prompt")
            if value.get("is_list", False):
                inputs[key] = []
                a_val = input(f"{key}({prompt})：")
                while a_val != "q":
                    inputs[key].append(a_val)
                    a_val = input(f"{key}({prompt})：")
            else:
                inputs[key] = input(f"{key}({prompt})：")
        print(inputs)
        volumeFactory.VolumeFactory.new_volume(inputs)

    def do_delete(self, arg):
        """delete [volume_name] - 删除指定的卷"""
        if arg:
            print(f"删除卷: {arg}")
        else:
            print("请输入卷名，例如: delete my_volume")
