"""
ok
ID 生成器，基于时间戳生成唯一ID
"""

import time
import threading
from datetime import datetime


class IDGenerator:
    """ID 生成器，基于时间戳生成唯一ID（静态工具类）"""
    
    # 类变量，用于维护状态
    _lock = threading.Lock()
    _sequence = 0
    _last_timestamp_str = ""
    
    @staticmethod
    def _get_timestamp():
        """获取当前年月日时分秒格式的时间戳（YYYYMMDDHHmmss）"""
        return datetime.now().strftime("%Y%m%d%H%M%S")
    
    @classmethod
    def generate(cls, suffix=""):
        """
        生成基于时间戳的唯一ID
        
        Args:
            suffix: ID 后缀（如 "device", "volume" 等）
        
        Returns:
            str: 生成的ID，格式为 {timestamp}_{sequence}_{suffix}
        """
        with cls._lock:
            timestamp_str = cls._get_timestamp()
            
            # 时钟回拨检测：如果时间戳小于上次时间戳，说明时钟回拨了
            if timestamp_str < cls._last_timestamp_str:
                # 使用最后时间戳，序列号递增，避免ID冲突
                cls._sequence += 1
            # 如果时间戳相同（同一秒内），增加序列号
            elif timestamp_str == cls._last_timestamp_str:
                cls._sequence += 1
                # 序列号溢出处理：如果超过999，等待下一秒
                if cls._sequence > 999:
                    # 等待下一秒
                    time.sleep(1)
                    timestamp_str = cls._get_timestamp()
                    # 如果时间戳还是相同（理论上不应该），继续等待
                    while timestamp_str <= cls._last_timestamp_str:
                        time.sleep(1)
                        timestamp_str = cls._get_timestamp()
                    cls._sequence = 0
            else:
                # 时间戳不同（新的秒），重置序列号
                cls._sequence = 0
            
            cls._last_timestamp_str = timestamp_str
            
            # 构建ID各部分
            # 序列号部分（固定3位），支持每秒1000次
            sequence_str = str(cls._sequence).zfill(3)
            
            # 组合ID，使用下划线分隔各部分
            # 格式：YYYYMMDDHHmmss_sequence 或 YYYYMMDDHHmmss_sequence_suffix
            if suffix:
                id_str = f"{timestamp_str}_{sequence_str}_{suffix}"
            else:
                id_str = f"{timestamp_str}_{sequence_str}"
            
            return id_str


def generate_id(suffix=""):
    """
    生成含时的序列号（使用静态工具类）
    
    Args:
        suffix: ID 后缀（如 "device", "volume" 等）
    
    Returns:
        str: 生成的ID，格式：YYYYMMDDHHmmss_sequence 或 YYYYMMDDHHmmss_sequence_suffix
    """
    return IDGenerator.generate(suffix=suffix)


__all__ = [
    "IDGenerator",
    "generate_id",
]

