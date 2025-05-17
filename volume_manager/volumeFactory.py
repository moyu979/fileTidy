import logging
from volume_manager.volume import Volume
from volume_manager.tools import load_upper_volume

import importlib
import os
import sqlite3


import init_setting.conf as conf
class VolumeFactory:
    """
    A factory class for creating volume instances.
    """
    volumes = {}
    no_init_volume=[]

    @classmethod
    def load_volume(cls, name=None, id=None,mount_point=None):
        volume = Volume()
        # 如果id是已知的，那么直接根据id读取即可
        if id is not None:
            logging.debug("load volume by id")
            if id in cls.volumes:
                logging.debug("load volume from cache")
                volume=cls.volumes[id]
            else:
                logging.debug("load volume from database")
                volume.load_info(id=id)
                cls.volumes[id] = volume
        # 如果name是已知的，那么直接根据id读取即可
        elif name is not None:
            logging.debug("load volume by name")
            volume.load_info(name=name)
            if volume.id in cls.volumes:
                volume=cls.volumes[volume.id]
            else:
                cls.volumes[volume.id] = volume
        # 如果挂载点是已知的，那么直接根据id读取即可
        elif mount_point is not None:
            logging.debug("load volume by point")
            volume=cls.load_upper_volume(path=mount_point)
            if volume.id==0:
                logging.error(f"Volume with mount point {mount_point} not found.")
                volume=None
            elif volume.id in cls.volumes:
                volume=cls.volumes[volume.id]
            else:
                cls.volumes[volume.id] = volume
        else:
            logging.error("load volume must has infos")
            volume=None
            raise ValueError("Either id or name must be provided.")
        return volume
        

    def new_volume(cls, info_dict=None, mount_point=None):
        """
        Create a new volume instance and store it in the database.
        :param info_dict: A dictionary containing volume attributes.
        :param mount_point: The mount point of the volume.
        :return: The created Volume instance.
        """
        if info_dict is not None:
            volume = Volume()
            volume.set_volume(info_dict)
        elif mount_point is not None:
            volume = Volume()
            volume.set_volume_interactive()
        else:
            volume = Volume()
            volume.set_volume_interactive()
        return volume
    
    @classmethod
    def load_exist_volumes(cls):
        module_path = f"volume_manager.tools.{conf.get("platform")}.get_all_volume"
        get_all_volume = importlib.import_module(module_path)
        all_volumes=get_all_volume.get_all_mount_points()

        for v in all_volumes:
            mount_point = v[-1]
            test_path=os.path.join(mount_point, "volume_id")
            if os.path.exists(test_path):
                files=os.listdir(test_path)
                id=files[0]
                volume=cls.load_volume(id=id,mount_point=mount_point)
                volume.mount_point=mount_point
            else:
                cls.no_init_volume.append(v)
        cls.load_volume(id=0)

    @classmethod
    def load_upper_volume(cls,path=None):
        if path is None:
            logging.info("using default volume")
            return cls.load_volume(id=0)
        else:
            volume,root=load_upper_volume.load_root_volume_id(path=path)
            volume.mount_point=root
            return volume
        
    @classmethod
    def get_volume_path(cls, volume_id):
        """
        Get the path of the volume.
        :param volume: The Volume instance.
        :return: The path of the volume.
        """
        # 这里需要实现获取卷路径的逻辑,这个逻辑不对，
        if volume_id in cls.volumes:
            volume = cls.volumes[volume_id]
            if volume.mount_point is not None:
                return volume.mount_point
            else:
                logging.error(f"Volume with id {volume_id} does not have a mount point.")
        logging.error("get_volume_path not finished")




        
    
    