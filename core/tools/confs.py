import hashlib
import json
import logging
import os
import platform
import random

from core.tools.generater import fileTimeSecond

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

conf={
        "data_path":"./datas",
        "db_name":"files.db",
        "load_unit":512,
        "remember_hash":True,
        "platform":"unknown",
        "server_id":None,
        "check_mode":True
    }

bool_mode=["true","false"]

device_kind={
    #机械硬盘
    "01":"2.5寸机械硬盘",
    "02":"3.5寸机械硬盘",
    "03":"其他尺寸机械硬盘",
    #固态硬盘
    "11":"2.5寸固态硬盘",
    "12":"NVME接口固态硬盘",
    "13":"NGFF接口固态硬盘",
    "14":"PCIE接口固态硬盘",
    #磁带
    "25":"lto5磁带",
    "26":"lto6磁带",
    #USB
    "31":"usb2u盘",
    "32":"usb3u盘"
}

# part值得是在原有的目录下划出一个子目录，当作新的part
raid_kind={
    'r0':"raid0",
    'r1':"raid1/mirror",
    'r5':"raid5/raidz1",
    'r6':"raid6",
    'r10':"raid10",

    "2":"stripe",
    "3":"single_disk",
    "4":"Splicing",
    
    "7":"part"

}
tape=[]
disk=[]
need_all=["raid0","raid1","raid5","raidz1","raid6","raid10","stripe"]
device_health={
    "1":"health",
    "2":"degraded",
    "3":"error",
    "4":"broken"
}

capacity={
    "lto5":"1.5T",
    "lto6":"2.5T"
}

file_system={
    "01":"ltfs",
    "02":"ntfs",
    "03":"exfat",
    
    "04":"zfs-raid-z1",
}

hash_storage={}


def save_conf(path="./datas"):
    global conf
    print(conf["server_id"])
    if not os.path.exists(path):
        os.mkdir(path)
    conf_json_path=os.path.join(path,"data.json")
    print(conf_json_path)
    with open(conf_json_path,"w") as f:
        json.dump(conf,f,indent=4)

def load_conf(path="./datas"):
    global conf
    conf_json_path=os.path.join(path,"data.json")
    if os.path.exists(conf_json_path):
        logging.info(f"conf file exists, loading")
        with open(conf_json_path,"r") as f:
            conf=json.load(f)
    else:
        logging.info(f"conf file not exists, using default")
    conf["platform"]=platform.system()
    if conf["server_id"]==None:
        conf["server_id"]=generate_server_id()
    
    for k,v in device_kind.items():
        if k.startswith("0"):
            disk.append(v)
        elif k.startswith("1"):
            tape.append(v)

def generate_server_id():
    now_time,_=fileTimeSecond()
    random_int = random.randint(1, 100)
    int_str=str(random_int)+now_time
    hash_object = hashlib.md5(int_str.encode())
    hash_hex = hash_object.hexdigest()
    return hash_hex


    