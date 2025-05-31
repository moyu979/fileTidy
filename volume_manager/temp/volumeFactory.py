import logging
from volume_manager.temp.volume import Volume
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
    no_init_volume={}

    @classmethod
    def load_exist_volumes(cls,force=False):
        """
        Load all existing volumes from the database and cache them.
        """
        module_path = f"volume_manager.tools.{conf.get("platform")}.get_all_volume"
        get_all_volume = importlib.import_module(module_path)
        all_volumes=get_all_volume.get_all_mount_points()

        for v in all_volumes:
            mount_point = v[-1]
            test_path=os.path.join(mount_point, "volume_info")
            if os.path.exists(test_path):
                files=os.listdir(test_path)
                id=files[0]
                if id in cls.volumes and not force:
                    continue
                else:
                    volume=cls.load_volume_from_database(id=id,mount_point=mount_point)

        cls.load_volume_from_database(id=0)

    @classmethod
    def load_volume_from_database(cls, name=None, id=None,mount_point=None,reload=False):
        """
        Load a volume from the database by its name, id, or mount point.
        """
        volume = Volume()
        # 如果id是已知的，那么直接根据id读取即可
        if id is not None or name is not None:
            logging.debug("load volume by id")
            if id in cls.volumes:
                if not reload:
                    logging.debug("load volume from cache")
                    volume=cls.volumes[id]
                else:
                    logging.debug("forced load volume from db")
                    volume.init_from_database(id=id)
            else:
                logging.debug("load volume from database")
                volume.init_from_database(id=id)
                cls.volumes[id] = volume

        # 如果name是已知的，那么直接根据id读取即可
        elif name is not None:
            logging.debug("load volume by name")
            volume.init_from_database(name=name)
            if volume.get_value("id") in cls.volumes:
                if not reload:
                    logging.debug("load volume from cache")
                    volume=cls.volumes[volume.get_value("id")]
                else:
                    logging.debug("force load volume from db")
                    cls.volumes[volume.get_value("id")] = volume
            else:
                logging.debug("load volume from cache")
                cls.volumes[volume.get_value("id")] = volume

        # 如果挂载点是已知的，那么直接根据id读取即可
        elif mount_point is not None:
            logging.debug("load volume by point")
            if not os.path.exists(mount_point):
                logging.error(f"mount point {mount_point} does not exist")
                raise FileNotFoundError(f"Mount point {mount_point} does not exist.")
            else:
                info_path=os.path.join(mount_point, "volume_info")
                if not os.path.exists(info_path):
                    logging.error(f"volume info path {info_path} does not exist")
                    raise FileNotFoundError(f"Volume info path {info_path} does not exist, which means it is not a valid volume.")  
                else:
                    files=os.listdir(info_path)
                    if len(files) == 0:
                        logging.error(f"volume info path {info_path} is empty")
                        raise FileNotFoundError(f"Volume info path {info_path} is empty, which means it is not a valid volume.")
                    else:
                        id=files[0]
                        if id in cls.volumes:
                            if not reload:
                                logging.debug("load volume from cache")
                                volume=cls.volumes[id]
                            else:
                                logging.debug("force load volume from db")
                                volume.init_from_database(id=id)
                                cls.volumes[id] = volume
                        else:
                            logging.debug("load volume from database")
                            volume.init_from_database(id=id)
                            cls.volumes[id] = volume

        return volume
        

    @classmethod
    def new_volume(cls, info_dict=None, mount_point=None):
        """
        Create a new volume instance and store it in the database.
        :param info_dict: A dictionary containing volume attributes.
        :param mount_point: The mount point of the volume.
        :return: The created Volume instance.
        """
        #这个东西得再设计
        module_path = f"volume_manager.tools.{conf.get("platform")}.get_capacity"
        get_all_volume = importlib.import_module(module_path)

        if mount_point is not None:
            info_dict["mount_point"] = mount_point
            info_dict["capacity"]=get_all_volume.get_mount_point_capacity(mount_point=mount_point)[0]
            logging.info("自动获取了部分信息")
        volume=Volume()
        volume.new_volume(info_dict=info_dict)
        cls.volumes[volume.id] = volume
        
    


    @classmethod
    def load_upper_volume(cls,path=None):
        if path is None:
            logging.info("using default volume")
            return cls.load_volume_from_database(id=0)
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




        
    
    