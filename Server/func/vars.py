import json
import platform
import os
data={
    "db_path":"./",
    "platform":"unknown",
    "port":"50051"
}

kind={
    "disk":["SSD","HDD","NVME"],
    "tape":["lto5","lto6"]
}

nowChecking={
    "1":"2",
    "2":"3"

}

def load_datas(path="./"):
    data_dir=os.path.join(path,"datas")
    if not os.path.exists(data_dir):
        save_datas(path)
    data_json_path=os.path.join(data_dir,"data.json")
    kind_json_path=os.path.join(data_dir,"kind.json")
    nowChecking_json_path=os.path.join(data_dir,"nowChecking.json")

    with open(data_json_path,"r") as f:
        data=json.load(f)
    with open(kind_json_path,"r") as f:
        kind=json.load(f)
    with open(nowChecking_json_path,"r") as f:
        nowChecking=json.load(f)
    data["platform"]=platform.system()
    
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