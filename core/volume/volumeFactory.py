from volume.volume import Volume
import volume.volume_creater as creater
import volume.volume_checker as checker
import logging
class VolumeFactory:

    volumes:dict[str,Volume]={}

    @classmethod
    def load_volume_from_database(cls,volume_id=None,volume_name=None,mount_point=None):
        volume=Volume(volume_id,volume_name,mount_point)
        if volume is not None:
            cls.volumes[volume.values["id"]]=volume
    #信息获取模块
    @classmethod
    def get_volume_fields():
        pass
    @classmethod
    def new_volume(cls,infos):
        pass
    @classmethod
    def get_mount_point(cls,volume_id):
        """
            根据卷的特征（id）获得卷的挂载点
        """
        #因为计划在起始的时候就将所有已挂载的卷载入，所以如果不存在，大概是没挂载，
        logging.debug(f"正在查找id为{volume_id}的卷")
        if volume_id in cls.volumes.keys():
            return cls.volumes[volume_id].mount_point
        else:
            logging.error("未发现该卷，该卷未挂载")
            return None
    #新建卷模块
    @classmethod
    def get_volume_fields(cls)->dict[str,str]:
        data={}
        for k,v in checker.checker.fields.items():
            data[k]=v.get("prompt","no prompt given")
        return data
    @classmethod
    def new_volume(cls,dict:dict):
        creat=creater.volume_creater()
        volume=creat(dict)
        cls.volumes[volume.values["id"]]=volume
    #   
    
    
    @classmethod
    def show_all_volumes(cls):
        logging.info("全部已经使用的卷如下")
        for k,v in cls.volumes.items():
            print(v.to_json())

    @classmethod
    def get_volume(cls,volume_id)->Volume:
        volume_id=str(volume_id)
        print(cls.volumes["0"])
        return cls.volumes.get(volume_id,None)



