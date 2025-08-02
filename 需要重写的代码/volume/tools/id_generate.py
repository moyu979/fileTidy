from datetime import time
import hashlib
import random


def generate_id():
    now_time = str(int(time.time()))
    random_int = random.randint(1, 100)
    int_str = str(random_int) + now_time
    hash_object = hashlib.md5(int_str.encode())
    hash_hex = "volume:" + hash_object.hexdigest()[:16]
    return hash_hex
