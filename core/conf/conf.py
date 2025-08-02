import logging
import os
import json
from pathlib import Path
import shutil
import platform

json_path = "./database/conf.json"

conf = None


def load_json():
    global conf
    with open(json_path) as f:
        conf = json.load(f)


def dump_json():
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(conf, f, ensure_ascii=False, indent=4)


def init_conf():
    # 初次运行时进行载入
    logging.info("首次装载conf模块，进行初始化")

    if os.path.exists(json_path):
        logging.info("设置文件已存在，加载即可")
    else:
        logging.info("设置文件不存在，使用默认值")
        base_path = Path(__file__).parent.resolve()
        src = base_path / "default.json"
        dst = json_path
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)

    load_json()

    conf["platform"] = platform.system()  # 主动载入平台

    # todo:根据平台内存尝试调整一次性能够载入的内存大小，不要让设置超限


# 获取指定的数据
def get(key):
    return conf.get(key, None)


def set(key, value):
    if key in conf:
        conf[key] = value
        dump_json()  # 修改时及时写入
    else:
        logging.error("conf中不存在对应的键值，什么都不会被改变")


def map_kind_to_type(kind):
    """
    将细化的kind映射为'hdd'、'ssd'或'tape'。
    """
    kind = kind.lower()
    if kind in conf.get("HDD", []):
        return "hdd"
    elif kind in conf.get("SSD", []):
        return "ssd"
    elif kind in conf.get("TAPE", []):
        return "tape"
    else:
        return kind  # 未知类型原样返回
