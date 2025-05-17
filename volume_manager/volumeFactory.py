import logging
from volume_manager.volume import Volume

import importlib
import os
import sqlite3


import init_setting.conf as conf
class VolumeFactory:
    """
    A factory class for creating volume instances.
    """
    volumes = {}

    @classmethod
    def load_volume(cls, name=None, id=None,mount_point=None):
        if id is not None:
            conn=sqlite3.connect(conf.get("db_path"))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Volume WHERE id=?", (id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            if result is None:
                logging.error(f"Volume with id {id} not found.")
                raise ValueError(f"Volume with id {id} not found.")
            
            volume = Volume()
            volume.set_volume(result,mount_point=mount_point)
            #载入子卷
            conn=sqlite3.connect(conf.get("db_path"))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM storageStructure WHERE superid=?", (id,))
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            volume.set_sub_volume(result)

            cls.volumes[id] = volume

            return volume
        
        elif name is not None:
            logging.error("load volume by name not finished")
        else:
            logging.error("load volume by mount_point not finished")

    def new_volume(cls, info_dict=None, mount_point=None):
        """
        Create a new volume instance and store it in the database.
        :param info_dict: A dictionary containing volume attributes.
        :param mount_point: The mount point of the volume.
        :return: The created Volume instance.
        """
        if info_dict is not None:
            volume = Volume()
            volume.set_volume(info_dict, mount_point=mount_point)
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
                cls.load_volume(id=id,mount_point=mount_point)
            else:
                continue

            
        
    
    