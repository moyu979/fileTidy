import cmd
import core.storage.storageFactory as storage


class StorageCmd(cmd.Cmd):
    intro = "这是卷管理模块，输入 'help' 查看可用命令，输入 'exit' 返回主菜单。"
    prompt = "(VolumeCmd) "

    def __init__(self):
        self.storages = {}

    def do_showStorage(self, arg):
        storages = storage.StorageFactory.get_all_mounted_storage
        for storage in storages:
            print(f"{storage.get_value("id")}")
