"""
ID 生成器，基于时间戳生成唯一ID
"""

import argparse
import time
import threading
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="Generate a timestamp-based unique ID")
    parser.add_argument("suffix", nargs="?", default="", help="Optional suffix for the ID")
    args = parser.parse_args()
    print(generate_id(args.suffix))


class IDGenerator:
    """ID 生成器，基于时间戳生成唯一ID（静态工具类）"""
    
    # 类变量，用于维护状态
    _lock = threading.Lock()
    _sequence = 0
    _last_timestamp_str = ""
    # 单个时间戳（秒）内可用的序号上限：000~999
    _MAX_SEQUENCE = 999
    
    @classmethod
    def _wait_for_next_second(cls):
        """等待真实时钟越过 _last_timestamp_str，并返回新的时间戳。

        仅在当前时间戳上的序号耗尽（一秒内已发出 1000 个 ID）时调用。
        """
        while True:
            time.sleep(1)
            fresh = cls._get_timestamp()
            if fresh > cls._last_timestamp_str:
                return fresh

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
                # 锚定最后时间戳，序列号递增：既不与历史ID重复，时间戳也不回退
                timestamp_str = cls._last_timestamp_str
                cls._sequence += 1
                # 该时间戳上的序号已用满，等真实时钟追上来再重新计数
                if cls._sequence > cls._MAX_SEQUENCE:
                    timestamp_str = cls._wait_for_next_second()
                    cls._sequence = 0
            # 如果时间戳相同（同一秒内），增加序列号
            elif timestamp_str == cls._last_timestamp_str:
                cls._sequence += 1
                # 序列号溢出处理：如果超过上限，等待下一秒
                if cls._sequence > cls._MAX_SEQUENCE:
                    timestamp_str = cls._wait_for_next_second()
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


if __name__ == "__main__":
    main()


__all__ = [
    "IDGenerator",
    "generate_id",
]

