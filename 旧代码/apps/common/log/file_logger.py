import os
import threading
from datetime import datetime
from pathlib import Path

from apps.common.config.globalVars import FILE_LOG_PATH


class FileLogger:
    """文件操作日志管理器 (静态类)
    
    用于记录文件操作，使用自定义标记（如 add, move, delete 等）
    每月自动创建一个新的日志文件
    """
    
    name = 'file logger'
    _log_path = None
    _current_log_file = None
    _current_month = None
    _lock = threading.Lock()
    _initialized = False

    @classmethod
    def init_log(cls):
        """初始化文件日志系统"""
        cls._setup_log_path()
        cls._initialized = True
    
    @classmethod
    def _setup_log_path(cls):
        """设置日志路径"""
        try:
            log_path = FILE_LOG_PATH
            if not os.path.exists(log_path):
                os.makedirs(log_path, exist_ok=True)
            cls._log_path = Path(log_path)
            cls._check_month_change()
        except Exception as e:
            print(f"文件日志系统初始化失败: {e}")
    
    @classmethod
    def _check_month_change(cls):
        """检查是否需要切换到新的月份日志文件"""
        if cls._log_path is None:
            return
        
        current_month = datetime.now().strftime('%Y_%m')
        
        # 如果月份改变了，更新日志文件路径
        if cls._current_month != current_month:
            cls._current_month = current_month
            cls._current_log_file = cls._log_path / f'{current_month}.log'
    
    @classmethod
    def _write_log(cls, action: str, message: str):
        """写入日志到文件"""
        if not cls._initialized:
            cls.init_log()
        
        cls._check_month_change()
        
        if cls._current_log_file is None:
            return
        
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # 精确到毫秒
            log_line = f"[{timestamp}] [{action.upper()}] {message}\n"
            
            with cls._lock:
                with open(cls._current_log_file, 'a', encoding='utf-8') as f:
                    f.write(log_line)
        except Exception as e:
            print(f"写入文件日志失败: {e}")
    
    @classmethod
    def _format_fields(cls, **kwargs) -> str:
        """格式化字段为键值对字符串"""
        parts = []
        for key, value in kwargs.items():
            if value is not None:
                parts.append(f"{key}={value}")
        return " | ".join(parts)
    
    @classmethod
    def reg(cls, path: str, md5: str, sha512: str):
        """
        记录标记文件到源的操作
        Args:
            path: 文件路径
            md5: 文件的MD5值
            sha512: 文件的SHA512值
        """
        message = cls._format_fields(path=path, md5=md5, sha512=sha512)
        cls._write_log('REG', message)
    
    @classmethod
    def intro(cls, path: str, md5: str, sha512: str, dst: str):
        """
        记录从源将文件导入数据库内卷的操作
        
        Args:
            path: 源文件路径
            md5: 文件的MD5值
            sha512: 文件的SHA512值
            dst: 目标路径（卷内路径）
        """
        message = cls._format_fields(path=path, md5=md5, sha512=sha512, dst=dst)
        cls._write_log('INTRO', message)
    
    @classmethod
    def skip_duplicate(cls, path: str, md5: str, sha512: str):
        """
        记录跳过已存在记录的操作（增加了已存在记录）
        
        Args:
            path: 文件路径
            md5: 文件的MD5值
            sha512: 文件的SHA512值
        """
        message = cls._format_fields(path=path, md5=md5, sha512=sha512)
        cls._write_log('SKIP_DUPLICATE', message)
    
    @classmethod
    def move(cls, path: str, md5: str, sha512: str, dst: str):
        """
        记录移动操作
        
        Args:
            path: 源文件路径
            md5: 文件的MD5值
            sha512: 文件的SHA512值
            dst: 目标路径
        """
        message = cls._format_fields(path=path, md5=md5, sha512=sha512, dst=dst)
        cls._write_log('MOVE', message)
    
    @classmethod
    def delete(cls, message: str):
        """记录删除操作"""
        cls._write_log('DELETE', message)
    
    @classmethod
    def update(cls, message: str):
        """记录更新操作"""
        cls._write_log('UPDATE', message)
    
    @classmethod
    def copy(cls, message: str):
        """记录复制操作"""
        cls._write_log('COPY', message)
    
    @classmethod
    def log(cls, action: str, message: str):
        """通用日志方法，可以自定义操作标记"""
        cls._write_log(action, message)


def init_file_log():
    """初始化文件日志系统"""
    FileLogger.init_log()
    print("文件日志初始化完成")
