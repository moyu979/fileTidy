conf={
    "platform":"Darwin",  # 运行脚本的平台

    "path": "./DataBase",
    "db_path": "./DataBase/files.db",
    "script_path": "./func/init.sql",
    "log_path": "./log",
    "log_file": "initSetting.log",
    "log_level": "DEBUG",
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",

    "hash_once":512,

    #执行文件插入的规则，
    # relaxed表示当同路径文件存在时，默认是相同的，直接返回，不校验哈希值
    # strict表示当同路径文件存在时，校验哈希值，如果相同，则保持，如果不同，将原本的的文件状态变为“covered”
    "insert_node":"relaxed"
    
}

def get(key):
    return conf.get(key, None)

def set(key, value):
    if key in conf:
        conf[key] = value
    else:
        raise KeyError(f"Key '{key}' not found in configuration.")
    
