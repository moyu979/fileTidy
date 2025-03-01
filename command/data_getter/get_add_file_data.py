import os
import logging
import core.component.add_file_data as add_file_data


class get_add_file_data:
    def __init__(self):
        self.add_file=add_file_data.file_data()

    def __call__(self, *args, **kwds):
        self.get_file_path()
        self.get_volume()
        self.get_root_path()
        self.get_volume_point()
        self.get_show_path()
        return self.add_file

    def get_file_path(self):
        self.add_file.file_path=input("please input file path:")
        self.add_file.file_path=os.path.abspath(self.add_file.file_path).replace("\\\\","/").replace("\\","/")
        if not os.path.exists(self.add_file.file_path):
            err="file not exist"
            logging.error(err)
            self.get_file_path()

    def get_root_path(self):
        self.add_file.root_point="/"+self.add_file.file_path.split("/")[-1]
        root_point=input(f"please tell us where your file mount at, we guess is {self.add_file.root_point},you can keep it with an empty input:")
        if root_point!="":
            self.add_file.root_point=root_point

    def get_volume_point(self):
        self.add_file.volume_point=input("please tell this point store in which path of volume, i guess is \"/\"")
        if self.add_file.volume_point=="":
            self.add_file.volume_point="/"

    def get_volume(self):
        self.add_file.volume=input("please tell us which volume store those file,default is 0:")
        if self.add_file.volume=="":
            self.add_file.volume="0"

    def get_show_path(self):
        self.add_file.mount_point=input("please tell us point in showm, i guess is \"/\"")
        if self.add_file.mount_point=="":
            self.add_file.mount_point="0"
