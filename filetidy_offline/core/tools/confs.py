import json
import logging
import os
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

conf={
    "data_path":"./datas",
    "db_name":"files.db",
    "load_unit":512,
    "remember_hash":True,
}

hash_storage={}

def save_conf(path="./data_path"):
    pass