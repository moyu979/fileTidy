# todo 检查正确性
import os
import logging
import sqlite3
import core.tools.confs as confs
from core.tools.db_tools import get_db_path
from core.tools import generater
class volume_data:
    def __init__(self):
        self.id=""
        self.add_time=""
        self.last_check=""
        self.volume_name=""

        self.health=""

        self.info=""
        self.need_all=""
        self.used=""
        self.capacity=""

        self.kind=""
        self.format=""

        self.isBase="-1"
        self.global_point="unknown"

        self.sub_id=[]
        self.sub_dir=[]
        self.state=""
        
    def check(self):
        pass

        

        
