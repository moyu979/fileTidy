import os


class VolumeManager:
    def __init__(self):
        self.volumes = []

    def get_volume(self, volume_id):
        return self.volumes[volume_id]

    def add_volume(self, volume):
        self.volumes.append(volume)

    def get_volume_id(self, path):
        """
        根据路径获取卷id
        遍历路径的上级目录，查找datas目录，如果找到则检查同级是否有meta_data目录
        如果meta_data目录存在且只有一个文件，该文件名就是volume_id
        
        Args:
            path: 文件或目录路径
        
        Returns:
            str: 卷id，如果未找到则返回None
        """
        # 转换为绝对路径
        abs_path = os.path.abspath(path)
        
        # 如果是文件，从父目录开始遍历
        if os.path.isfile(abs_path):
            current_dir = os.path.dirname(abs_path)
        else:
            current_dir = abs_path
        
        # 向上遍历目录
        while True:
            # 检查当前目录的父目录
            parent_dir = os.path.dirname(current_dir)
            
            # 如果到达根目录，返回None
            if parent_dir == current_dir:
                return None
            
            # 检查当前目录是否是datas目录
            dir_name = os.path.basename(current_dir)
            if dir_name == "datas":
                # 检查同级是否有meta_data目录
                meta_data_dir = os.path.join(parent_dir, "meta_data")
                if os.path.isdir(meta_data_dir):
                    # 列出meta_data目录下的所有文件
                    try:
                        files = [f for f in os.listdir(meta_data_dir) 
                                if os.path.isfile(os.path.join(meta_data_dir, f))]
                        
                        # 检查是否只有一个文件
                        if len(files) == 1:
                            # 文件名就是volume_id
                            volume_id = files[0]
                            return volume_id
                        else:
                            # 文件数量不符合要求，继续向上查找
                            pass
                    except (PermissionError, OSError):
                        # 无法访问目录，继续向上查找
                        pass
            
            # 继续向上遍历
            current_dir = parent_dir

    def get_data_path(self, volume_id):
        """
        根据卷id获取路径
        """
        path = input("暂时没想好怎么实现，请直接手动输入路径: ").strip()
        if path == "":
            return None
        path = os.path.abspath(path)
        # 在用户输入的基础上拼接 /datas/
        path = os.path.join(path, "datas")
        return path

volume_manager = VolumeManager()