import os
import logging
import core.component.add_file_data as add_file_data


class get_add_file_data:
    def __init__(self):
        self.add_file=add_file_data.file_data()

    def __call__(self, *args, **kwds):
        self.get_file_path()
        self.get_volume()
        self.get_mount_point()
        return self.add_file

    def get_file_path(self):
        self.add_file.file_path=input("please input file path")
        self.add_file.file_path=os.path.abspath(self.add_file.file_path)
        if not os.path.exists(self.add_file.file_path):
            err="file not exist"
            logging.error(err)
            self.get_file_path()
    
    def get_volume(self):
        self.add_file.storage_volume=input("please input data storage volume, default=0")
        if self.add_file.storage_volume=="":
            self.add_file.storage_volume="0"
        

    def get_mount_point(self):
        self.add_file.mount_point=input("please input mount point of vpolume")
        self.add_file.mount_point=os.path.abspath(self.add_file.mount_point)
        if not os.path.exists(self.add_file.mount_point):
            err="mount point not exists"
            logging.error(err)
            self.get_mount_point()
