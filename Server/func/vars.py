import json
import platform
import os
from func.tools.decorators import *
from func.tools._fileTime import *
import random
import hashlib

data={
    "db_path":"./",
    "platform":"unknown",
    "port":"50051",
    "serverid":None
}
kind={
    "disk":["SSD","HDD","NVME"],
    "tape":["lto5","lto6"]
}
nowChecking={
    "1":"2",
    "2":"3"
}

import logging

# 设置日志的基本配置
logging.basicConfig(level=logging.DEBUG,  # 日志级别
                    format='%(asctime)s - %(levelname)s - %(message)s',  # 日志输出格式
                    datefmt='%Y-%m-%d %H:%M:%S')  # 日期时间格式

@say_begin_and_end
def load_datas(path="./"):
    logging.info("start loading static datas")
    data_dir=os.path.join(path,"datas")
    if not os.path.exists(data_dir):
        save_datas(path)

    data_json_path=os.path.join(data_dir,"data.json")
    kind_json_path=os.path.join(data_dir,"kind.json")
    nowChecking_json_path=os.path.join(data_dir,"nowChecking.json")

    with open(data_json_path,"r") as f:
        tempdata=json.load(f)
        for k,v in tempdata.items():
            data[k]=v
        print("1",data["db_path"])
    with open(kind_json_path,"r") as f:
        kind=json.load(f)
    with open(nowChecking_json_path,"r") as f:
        nowChecking=json.load(f)
    data["platform"]=platform.system()
    if data["serverid"]==None:
        data["serverid"]=generate_server_id()
def generate_server_id():
    now_time=fileTimeSecond()
    random_int = random.randint(1, 100)
    int_str=str(random_int)+now_time
    hash_object = hashlib.md5(int_str.encode())
    hash_hex = hash_object.hexdigest()
    return hash_hex
@say_begin_and_end
def save_datas(path="./"):
    data_dir=os.path.join(path,"datas")
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)

    data_json_path=os.path.join(data_dir,"data.json")
    kind_json_path=os.path.join(data_dir,"kind.json")
    nowChecking_json_path=os.path.join(data_dir,"nowChecking.json")

    with open(data_json_path,"w") as f:
        json.dump(data,f)
    with open(kind_json_path,"w") as f:
        json.dump(kind,f)
    with open(nowChecking_json_path,"w") as f:
        json.dump(nowChecking,f)