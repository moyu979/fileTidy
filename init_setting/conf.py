conf={
    "path": "./DataBase",
    "db_path": "./DataBase/files.db",
    "script_path": "./func/init.sql",
    "log_path": "./log",
    "log_file": "initSetting.log",
    "log_level": "DEBUG",
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",

    "hash_once":512
}

def get(key):
    return conf.get(key, None)

def set(key, value):
    if key in conf:
        conf[key] = value
    else:
        raise KeyError(f"Key '{key}' not found in configuration.")