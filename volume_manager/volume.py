from datetime import datetime
import json
import os
import logging
import sqlite3
from pathlib import Path

from init_setting import conf
from volume_manager.tools.id_generate import generate_id
from file_manager.tools.Hash import getAHash
class volume:

    def __init__(self, name=None, id=None, mount_point=None):
        """
        初始化卷对象。

        :param name: 卷的名称
        :param id: 卷的唯一标识符
        :param mount_point: 卷的挂载点
        """

        
        logging.debug("load volume from database")
        
        #如果挂载点不为空，则可以根据挂载点自动解析卷id
        if mount_point is not None:
            logging.info("从mountpoint加载卷信息")
            if not os.path.exists(mount_point):
                logging.error(f"Volume info path {info_path} does not exist.")
                raise FileNotFoundError(f"Mount point {mount_point} does not exist.")
            else:
                info_path = os.path.join(mount_point, "volume_info")
                if not os.path.exists(info_path):
                    logging.error(f"记录 {info_path} 的文件夹不存在，给出的挂载点并非一合法的文件管理卷")
                    raise FileNotFoundError(f"Volume info path {info_path} does not exist.")
                else:
                    files = os.listdir(info_path)
                    temp_id = None
                    for file in files:
                        if file.endswith(".volume_id"):
                            temp_id = file[:-10]
                            logging.debug(f"Found volume id: {id} in {info_path}")
                    if temp_id is None:
                        logging.error(f"在挂载点 {mount_point} 中未找到卷id文件，请检查挂载点是否正确")
                        raise FileNotFoundError(f"No volume id file found in {info_path}. Please check the mount point.")

            #使用根据挂载点解析的卷id刷新id
            if id is not None and id!= temp_id:
                logging.warning(f"提供的卷id {id} 与从挂载点 {mount_point} 解析出的卷id {temp_id} 不一致，可能会导致错误")
                raise ValueError(f"Provided volume id {id} does not match parsed id {temp_id} from mount point {mount_point}.")
            else:
                id = temp_id
        logging.debug(f"id is {id}")
        #根据解析到的信息
        conn=sqlite3.connect(conf.get("db_path"))
        cursor = conn.cursor()
        try:
            if id is not None and name is None:
                logging.debug("load volume from database by id")
                cursor.execute("SELECT * FROM Volume WHERE id=?", (id,))
            elif name is not None and id is None:
                logging.debug("load volume from database by name")
                cursor.execute("SELECT * FROM Volume WHERE name=?", (name,))
            elif id is not None and name is not None:
                logging.warning("load volume from database by name and id, this is not recommended")
                cursor.execute("SELECT * FROM Volume WHERE name=? and id=?", (name,id))
            else:
                logging.error("Neither name nor id is provided, cannot load volume")
                raise ValueError("Either name or id must be provided to load a volume.")
        
            if cursor.rowcount == 0:
                logging.error(f"Volume with id {id} and name {name} does not exist in the database.")
                raise ValueError(f"Volume with id {id} or name {name} does not exist in the database.")
        
            else:
                result = cursor.fetchone()
                if result is None:
                    logging.error("未找到数据库中的卷信息")
                    raise ValueError("No volume information found in the database.")                    
        except sqlite3.Error as e:
            # 捕获数据库错误并记录日志
            logging.error(f"Database error occurred: {e}")
            raise  # 重新抛出异常
        
        except ValueError as ve:
            # 捕获自定义的 ValueError 并记录日志
            logging.error(f"Value error occurred: {ve}")
            raise  # 重新抛出异常
        
        except Exception as ex:
            # 捕获其他未预料的异常并记录日志
            logging.error(f"An unexpected error occurred: {ex}")
            raise  # 重新抛出异常
        
        finally:
            cursor.close()
            conn.close()
        print(result)
        self.values = {}
        self.values["id"] = result[0]
        self.values["name"] = result[1]
        self.values["capacity"] = result[2]
        self.values["used"] = result[3]
        self.values["add_time"] = result[4]
        self.values["last_check"] = result[5]
        self.values["healthy"] = result[6]
        self.values["info"] = result[7]
        self.values["kind"] = result[8]
        
        self.mount_point=mount_point

        self.storages=[]

        conn=sqlite3.connect(conf.get("db_path"))
        cursor = conn.cursor()

        try:
            temp=cursor.execute("SELECT * FROM storageStructure WHERE superid=?", (self.values["id"],)).fetchall()
            if len(temp)==0:
                raise ValueError(f"卷 {self.values["id"]} 的存储结构不合法")
        except sqlite3.Error as e:
            logging.error(f"Database error occurred: {e}")
            raise
        except ValueError as ve:
            logging.error(f"Value error occurred: {ve}")
            raise
        finally:
            cursor.close()
            conn.close()
        
        for item in temp:
            self.storages.append(item[1])

    def update_file(self):
        if self.mount_point==None:
            logging.error("Mount point is not set, cannot update file.")
            raise ValueError("Mount point is not set, cannot update file.")
        elif not os.path.exists(self.mount_point):
            logging.error(f"Mount point {self.mount_point} does not exist.")
            raise FileNotFoundError(f"Mount point {self.mount_point} does not exist.")
        else:
            conn=sqlite3.connect(conf.get("db_path"))
            cursor = conn.cursor()
            in_db_file=cursor.execute("SELECT * FROM File WHERE volume=?", (self.values["id"],)).fetchall()
            cursor.close()
            conn.close()

            matched=[]
            differed=[]
            disappeared=[]
            unexpected=[]

            mp=os.path.join(self.mount_point, "datas")
            for a_file in in_db_file:
                file_path = os.path.join(mp, a_file[4])
                if not os.path.exists(file_path):
                    disappeared.append(file_path)
                else:
                    if conf.get("volume_check")=="relaxed":
                        matched.append(file_path)
                    else:
                        hash=getAHash(file_path)
                        if hash == a_file[3]:
                            matched.append(file_path)
                        else:
                            differed.append(file_path)

            for root,dirs,files in os.walk(mp):
                for file in files:
                    path=os.path.join(root, file)
                    if path not in in_db_file:
                        unexpected.append(path)
            
            logging.info(f"文件扫描完毕，发现{len(matched)}个匹配的文件，{len(differed)}个发生变化的文件，{len(disappeared)}个消失的文件，{len(unexpected)}个不存在于数据库的文件。")
    def to_dict(self):
        return {
            "id": self.values["id"],
            "name": self.values["name"],
            "capacity": self.values["capacity"],
            "used": self.values["used"],

            "add_time": self.values["add_time"],
            "last_check": self.values["last_check"],
            "healthy": self.values["healthy"],
            "info": self.values["info"],
            "kind": self.values["kind"],

            "storages": self.storages,  # 假设子卷是可序列化的

            "mount_point": self.mount_point,
        }
    # 将对象转换为 JSON 字符串
    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=4)
