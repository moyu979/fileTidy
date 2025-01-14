import hashlib
import random

import core.tools.confs as confs
import core.tools.fileTime as fileTime
def get_a_tape_id():
    server_id=confs.conf["server_id"]
    time,_=fileTime.fileTimeSecond()
    random_int = random.randint(1, 100)
    total_str=server_id+time+str(random_int)
    file_hash=hashlib.md5(total_str.encode()).hexdigest()
    return file_hash,None