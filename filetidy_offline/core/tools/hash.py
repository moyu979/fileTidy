import hashlib
import os
import sys

from core.tools.confs import conf
from core.tools.confs import hash_storage
"""
    计算一个文件的哈希值，读取单位是MB
"""
def get_hash(path,size=conf["load_unit"]):

    if os.path.isdir(path):
        return None,"is dir"
    elif conf["remember_hash"] and path in hash_storage.keys():
        return hash_storage[path]
    else:
        md5=hashlib.md5()
        with open(path,"rb") as fp:
            while True:
                data=fp.read(1024**2*size)
                if not data:
                    break
                md5.update(data)
        file_md5=md5.hexdigest()
        if conf["remember_hash"]:
            hash_storage[path]=file_md5
        return file_md5
    
if __name__=="__main__":
    path=""
    if len(sys.argv)!=2:
        path=input("请输入测试路径")
    else:
        path=sys.argv[1]
    path=os.path.abspath(path)
    path=path.replace("\\","/")