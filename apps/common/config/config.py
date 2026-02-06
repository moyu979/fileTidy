from calendar import c
from functools import cache
import os
import sys
import json
import platform
import threading
import time

from apps.common.config.globalVars import CONFIG_PATH
from apps.common.config import globalVars
from apps.common.log.logger import Logger as logger


class GetUnknownKey(Exception):
    """尝试获取不存在的配置键时抛出的异常"""
    pass

class ConfigManager:
    """配置管理器类"""

    # 全局配置字典
    config_dict = {}
    # 配置字典访问锁
    _config_lock = threading.RLock()
    # 守护线程状态
    _daemon_thread = None
    _running = False
    
    @classmethod
    def init_config(cls):
        """获取配置值"""
        ConfigManager.load_configs()
        ConfigManager.start_daemon()

    @classmethod
    def load_configs(cls):
        """初始化配置函数 - 加载config_path中的所有JSON文件"""
        with cls._config_lock:
            # 清空全局字典
            cls.config_dict.clear()
            # 加载默认配置
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                cls.config_dict = json.load(f)

    @classmethod
    def start_daemon(cls):
        """启动守护线程，定期重载配置"""
        if cls._running:
            return
        cls._running = True
        cls._daemon_thread = threading.Thread(target=cls._daemon_loop, daemon=True)
        cls._daemon_thread.start()
        logger.info("配置守护线程已启动")
        print("配置守护线程已启动")
    
    @classmethod
    def stop_daemon(cls):
        """停止守护线程"""
        cls._running = False
        if cls._daemon_thread is not None:
            cls._daemon_thread.join(timeout=ConfigManager.get("conf_reload_interval")*2)
            cls._daemon_thread = None
    
    @classmethod
    def _daemon_loop(cls):
        """守护线程循环"""
        while cls._running:
            time.sleep(ConfigManager.get("conf_reload_interval"))
            logger.debug("守护线程执行一次配置重载")
            cls.load_configs()
    
    @classmethod
    def get(cls, key):
        """获取配置值"""
        with cls._config_lock:
            # 先检查是否在 globalVars 中
            if hasattr(globalVars, key):
                return getattr(globalVars, key)
            
            # 如果不在 globalVars 中，从 config_dict 中获取
            value = cls.config_dict.get(key, None)
            if value is None:
                logger.error(f"配置值不存在: {key}")
                raise GetUnknownKey(f"配置值不存在: {key}")
            return value
        
    @classmethod
    def set(cls, key, value):
        """设置配置值并保存到文件"""
        with cls._config_lock:
            if key not in cls.config_dict:
                logger.error(f"配置不存在: {key}")
                raise KeyError(f"配置不存在: {key}")
            logger.debug(f"设置配置值: {key}, {value}")
            cls.config_dict[key] = value
            cls._save_config()
    
    @classmethod
    def _save_config(cls):
        """将配置字典保存到文件"""
        with cls._config_lock:
            try:
                # 确保目录存在
                config_dir = os.path.dirname(CONFIG_PATH)
                if config_dir:
                    os.makedirs(config_dir, exist_ok=True)

                # 写入文件（使用临时文件确保原子性）
                temp_file_path = CONFIG_PATH + ".tmp"
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    json.dump(cls.config_dict, f, ensure_ascii=False, indent=4)

                # 原子性替换
                os.replace(temp_file_path, CONFIG_PATH)
                logger.debug(f"配置已保存到文件: {CONFIG_PATH}")
            except Exception as e:
                logger.error(f"保存配置文件失败 {CONFIG_PATH}: {e}")
                # 清理临时文件
                temp_file_path = CONFIG_PATH + ".tmp"
                if os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except:
                        pass
                raise

    
config_manager = ConfigManager()

def _get_system_info():
    """获取操作系统信息"""
    system = platform.system()
    # 标准化系统名称：Windows -> windows, Linux -> linux, Darwin -> macos
    if system == "Windows":
        return "windows"
    elif system == "Linux":
        return "linux"
    elif system == "Darwin":
        return "macos"
    else:
        return system.lower()


def init_config_manager():
    global config_manager
    config_manager.init_config()

    # 将操作系统信息添加到配置中
    system_name = _get_system_info()
    config_manager.config_dict["system"]=system_name
    
    return config_manager


def get_config_manager():
    return config_manager
