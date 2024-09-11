import json
import platform

data={
    "db_path":"./",
    "platform":"unknown"
}

kind={
    "disk":["SSD","HDD","NVME"],
    "tape":["lto5","lto6"]
}



def load_datas():
    data["platform"]=platform.system()
    