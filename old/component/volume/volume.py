class Volume:
    def __init__(self, orm_model=None,volume_path=None):
        if orm_model is not None:
            self.orm_model = orm_model
            if volume_path is not None:
                self.volume_path = volume_path
        else:
            self.orm_model = None
            if volume_path is not None:
                self.volume_path = volume_path
            else:
                raise ValueError("volume_path 和 orm_model 不能同时为空")

    def check(self):
        """
        检查卷的介质情况
        """
        pass

    def write(self, src_path, dst_path):
        """
        写入数据
        src_path 是源路径，一般是绝对路径
        dst_path 是目标路径，一般是相对路径，为相对<volume_path>/datas/的路径
        """
        pass

    def get_file(self, path ,dst_path):
        """
        获取文件,path 是源路径，dst_path 是目标路径
        """
        pass