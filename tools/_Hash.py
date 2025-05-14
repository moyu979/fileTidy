import hashlib
import os
import sys

import init_setting.conf as conf

def getAHash(path,size=conf.get("hash_once")):
    if os.path.isdir(path):
        return None
    else:
        md5=hashlib.md5()
        with open(path,"rb") as fp:
            while True:
                data=fp.read(1024**2*size)
                if not data:
                    break
                md5.update(data)
        file_md5=md5.hexdigest()
        return file_md5

