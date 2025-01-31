import hashlib
import random
import time
import core.tools.confs as confs
def get_a_device_id():
    server_id=confs.conf["server_id"]
    time=fileTimeSecond()
    random_int = random.randint(1, 100)
    total_str=server_id+time+str(random_int)
    file_hash=hashlib.md5(total_str.encode()).hexdigest()
    return file_hash[:16]

def fileTimeSecond():
    time_tuple = time.localtime(time.time())
    name=f"{time_tuple[0]:0>4}:{time_tuple[1]:0>2}:{time_tuple[2]:0>2} {time_tuple[3]:0>2}:{time_tuple[4]:0>2}:{time_tuple[5]:0>2}"
    return name