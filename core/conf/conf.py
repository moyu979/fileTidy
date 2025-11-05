# 本文件未经测试
import logging
import os
import json
from pathlib import Path
import shutil
import platform

conf = None

logger = logging.getLogger(__name__)

def load_json(path=None):
    global conf
    if path is not None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                conf = json.load(f)
        except (FileNotFoundError, PermissionError, json.JSONDecodeError) as exc:
            logging.error("加载配置失败: %s", exc)
            raise
    else:
        try:
            with open(get("json_path"), "r", encoding="utf-8") as f:
                conf = json.load(f)
        except (FileNotFoundError, PermissionError, json.JSONDecodeError) as exc:
            logging.error("加载配置失败: %s", exc)
            raise
        


def dump_json():
    try:
        with open(get("json_path"), "w", encoding="utf-8") as f:
            json.dump(conf, f, ensure_ascii=False, indent=4)
    except (PermissionError, OSError, TypeError, ValueError) as exc:
        logging.error("写入配置失败: %s", exc)
        raise


def init_conf(path=None):
    if path is not None:
        json_path = path
    else:
        json_path = "./data/conf.json"
    # 初次运行时进行载入
    logger.info("首次装载conf模块，进行初始化")
    try:
        if os.path.exists(json_path):
            logger.debug("设置文件已存在，加载即可")
        else:
            logger.info("设置文件不存在，使用默认值")
            base_path = Path(__file__).parent.resolve()
            src = base_path / "default.json"
            dst = json_path
            Path(dst).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)

        load_json(json_path)
    except (FileNotFoundError, PermissionError, OSError) as exc:
        logger.error("初始化配置失败: %s", exc)
        raise
    set("json_path", json_path)
    set("system", platform.system())
    # todo:根据平台内存尝试调整一次性能够载入的内存大小，不要让设置超限


# 获取指定的数据
def get(key):
    return conf.get(key, None)


def set(key, value):
    logging.info(f"设置{key}的值为{value}")
    if key in conf:
        conf[key] = value
        dump_json()  # 修改时及时写入
        return True
    else:
        logging.error(f"conf中不存在对应的键值{key}，什么都不会被改变")
        return False


def map_kind_to_type(kind):
    """
    将细化的kind映射为'hdd'、'ssd'或'tape'。
    """
    if not isinstance(kind, str):
        return kind
    kind_lower = kind.lower()
    if kind_lower in conf.get("HDD", []):
        return "hdd"
    elif kind_lower in conf.get("SSD", []):
        return "ssd"
    elif kind_lower in conf.get("TAPE", []):
        return "tape"
    else:
        return kind  # 未知类型原样返回
