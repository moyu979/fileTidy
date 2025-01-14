import hashlib
import json
import logging
import os
import platform
import random

from core.tools.fileTime import fileTimeSecond

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

conf={
        "data_path":"./datas",
        "db_name":"files.db",
        "load_unit":512,
        "remember_hash":True,
        "platform":"unknown",
        "port":"50051",
        "server_id":None
    }

tape_kind={
    "5":"lto5",
    "6":"lto6"
}

health={
    "1":"health",
    "2":"in_danger",
    "3":"break_down"
}

disk_kind={
    "1":"HDD",
    "2":"SSD",
    "3":"flash"
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
    print(conf["server_id"])

def generate_server_id():
    now_time,_=fileTimeSecond()
    random_int = random.randint(1, 100)
    int_str=str(random_int)+now_time
    hash_object = hashlib.md5(int_str.encode())
    hash_hex = hash_object.hexdigest()
    return hash_hex


    