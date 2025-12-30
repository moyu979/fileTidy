import os
import logging
import logging.handlers
import inspect
from datetime import datetime
import threading

from apps.common.config.globalVars import LOG_PATH

class Logger:
    """SpiderScheduler 日志管理器 (静态类)"""
    
    name = 'default logger'
    _logger = None
    _log_cache = []
    _logger_initialized = False
    _lock = threading.Lock()

    @classmethod
    def init_log(cls):
        cls._setup_logger()
        cls._flush_cache()
    
    @classmethod
    def _setup_logger(cls):
        """设置日志记录器"""
        try:
            log_path = LOG_PATH
            if not os.path.exists(log_path):
                os.makedirs(log_path, exist_ok=True)
            cls._logger = logging.getLogger(cls.name)
            cls._logger.setLevel(logging.DEBUG)
            cls._logger.propagate = False  # 禁用传播，避免重复输出
            cls._logger.handlers.clear()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(classname)s] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            current_month = datetime.now().strftime('%Y_%m')
            log_file = os.path.join(log_path, f'{current_month}.log')
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(formatter)
            cls._logger.addHandler(file_handler)
            cls._logger.addHandler(console_handler)
            cls._logger_initialized = True
        except Exception as e:
            with cls._lock:
                cls._log_cache.append({
                    'level': 'ERROR',
                    'message': f'日志系统初始化失败: {e}',
                    'classname': 'SpiderLogger'
                })
    
    @classmethod
    def _flush_cache(cls):
        """刷新缓存中的日志"""
        if not cls._logger_initialized:
            return
        with cls._lock:
            if not cls._log_cache:
                return
            pending = cls._log_cache[:]
            cls._log_cache.clear()
        for cached_log in pending:
            level = cached_log.get('level', logging.INFO)
            if isinstance(level, str):
                level = logging._nameToLevel.get(level.upper(), logging.INFO)
            cls._log_with_class(level, "(cached)" + cached_log['message'], cached_log['classname'])
    
    @classmethod
    def _cache_log(cls, level, message, classname='Unknown'):
        """缓存日志消息"""
        normalized_level = level
        if isinstance(normalized_level, str):
            normalized_level = logging._nameToLevel.get(normalized_level.upper(), logging.INFO)
        with cls._lock:
            cls._log_cache.append({
                'level': normalized_level,
                'message': message,
                'classname': classname
            })
    
    @staticmethod
    def _get_calling_class():
        """获取调用日志的类名"""
        try:
            frame = inspect.currentframe()
            while frame:
                frame = frame.f_back
                if frame:
                    if 'self' in frame.f_locals:
                        return frame.f_locals['self'].__class__.__name__
                    elif 'cls' in frame.f_locals:
                        return frame.f_locals['cls'].__name__
                    else:
                        module_name = frame.f_globals.get('__name__', '')
                        if module_name and module_name != '__main__':
                            return module_name.split('.')[-1]
            return 'Unknown'
        except Exception:
            return 'Unknown'
    
    @classmethod
    def _check_month_change(cls):
        """检查是否需要切换到新的月份日志文件"""
        if not cls._logger_initialized:
            return
        current_month = datetime.now().strftime('%Y_%m')
        try:
            log_path = LOG_PATH
            expected_log_file = os.path.join(log_path, f'{current_month}.log')
            for handler in cls._logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    if handler.baseFilename != expected_log_file:
                        cls._setup_logger()
                        break
        except Exception:
            pass
    
    @classmethod
    def _log_with_class(cls, level, message, classname=None):
        """记录带类名的日志"""
        if not cls._logger_initialized:
            if classname is None:
                classname = cls._get_calling_class()
            cls._cache_log(level, message, classname)
            return
        cls._check_month_change()
        if classname is None:
            classname = cls._get_calling_class()
        record = logging.LogRecord(
            name=cls._logger.name,
            level=level,
            pathname='',
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        record.classname = classname
        cls._logger.handle(record)
    
    @classmethod
    def debug(cls, message):
        cls._log_with_class(logging.DEBUG, message)
    
    @classmethod
    def info(cls, message):
        cls._log_with_class(logging.INFO, message)
    
    @classmethod
    def warning(cls, message):
        cls._log_with_class(logging.WARNING, message)
    
    @classmethod
    def error(cls, message):
        cls._log_with_class(logging.ERROR, message)
    
    @classmethod
    def critical(cls, message):
        cls._log_with_class(logging.CRITICAL, message)
    
    @classmethod
    def exception(cls, message):
        if not cls._logger_initialized:
            classname = cls._get_calling_class()
            cls._cache_log('ERROR', message, classname)
            return
        cls._check_month_change()
        classname = cls._get_calling_class()
        record = logging.LogRecord(
            name=cls._logger.name,
            level=logging.ERROR,
            pathname='',
            lineno=0,
            msg=message,
            args=(),
            exc_info=True
        )
        record.classname = classname
        cls._logger.handle(record)
    
    @classmethod
    def log(cls, level, message):
        cls._log_with_class(level, message)
    
    @classmethod
    def setLevel(cls, level):
        if cls._logger_initialized and cls._logger:
            cls._logger.setLevel(level)
    
    @classmethod
    def getLogger(cls):
        return cls._logger

def init_log():
    Logger.init_log()
    print("日志初始化完成")