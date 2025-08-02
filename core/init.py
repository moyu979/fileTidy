import os
from database.init_database import init_database


def init():
    path = "./database"
    if not os.path.exists(path):
        os.mkdir(path)

    db_path = os.path.join(path, "datas.db")
    init_database(db_path)
