"""
ID 生成器，生成含时的序列号
"""

import time
import threading
import random

# 模块级别的默认机器ID，在程序启动时随机生成一次
# TODO: 后续需要改进，应该基于实际的设备标识（如MAC地址、机器名等）
_default_machine_id = None


def _get_default_machine_id():
    """获取默认机器ID（程序启动时随机生成，运行期间保持不变）"""
    global _default_machine_id
    if _default_machine_id is None:
        _default_machine_id = random.randint(0, 1023)  # 4位，支持1024台机器
    return _default_machine_id


class IDGenerator:
    """ID 生成器，生成含时的唯一序列号"""
    
    def __init__(self, machine_id=None, use_milliseconds=True):
        """
        初始化 ID 生成器
        
        Args:
            machine_id: 机器标识符（可选），用于多机器环境区分
            use_milliseconds: 是否使用毫秒级时间戳（默认 True，精度更高）
        """
        self.machine_id = machine_id or _get_default_machine_id()
        self.use_milliseconds = use_milliseconds
        self._lock = threading.Lock()
        self._sequence = 0
        self._last_timestamp = 0
    
    
    def _get_timestamp(self):
        """获取当前时间戳"""
        if self.use_milliseconds:
            return int(time.time() * 1000)  # 毫秒时间戳
        else:
            return int(time.time())  # 秒时间戳
    
    def generate(self, prefix="", length=None):
        """
        生成含时的序列号
        
        Args:
            prefix: ID 前缀（如 "device_", "volume_" 等）
            length: 指定ID总长度（可选），如果指定，会在序列号部分补零
        
        Returns:
            str: 生成的ID，格式为 {prefix}{timestamp}{machine_id}{sequence}
        """
        with self._lock:
            timestamp = self._get_timestamp()
            
            # 如果时间戳相同，增加序列号
            if timestamp == self._last_timestamp:
                self._sequence += 1
            else:
                self._sequence = 0
                self._last_timestamp = timestamp
            
            # 构建ID各部分
            # 时间戳部分
            timestamp_str = str(timestamp)
            
            # 机器ID部分（固定长度）
            machine_id_str = str(self.machine_id).zfill(4)  # 4位机器ID
            
            # 序列号部分（固定长度）
            sequence_str = str(self._sequence).zfill(6)  # 6位序列号，支持每毫秒100万次
            
            # 组合ID
            id_str = f"{timestamp_str}{machine_id_str}{sequence_str}"
            
            # 如果指定了长度，进行填充或截断
            if length:
                if len(id_str) < length:
                    # 如果太短，在序列号部分补零
                    padding = length - len(id_str) - len(prefix)
                    if padding > 0:
                        id_str = id_str + "0" * padding
                elif len(id_str) > length - len(prefix):
                    # 如果太长，截断序列号部分
                    max_id_len = length - len(prefix)
                    id_str = id_str[:max_id_len]
            
            return f"{prefix}{id_str}"
    
    def generate_numeric(self):
        """
        生成纯数字的含时序列号
        
        Returns:
            int: 生成的数字ID
        """
        with self._lock:
            timestamp = self._get_timestamp()
            
            # 如果时间戳相同，增加序列号
            if timestamp == self._last_timestamp:
                self._sequence += 1
            else:
                self._sequence = 0
                self._last_timestamp = timestamp
            
            # 组合：时间戳 + 机器ID(4位) + 序列号(6位)
            if self.use_milliseconds:
                # 毫秒时间戳是13位，机器ID占4位，序列号占6位
                # 格式：timestamp(13位) + machine_id(4位) + sequence(6位) = 23位
                numeric_id = timestamp * 10000000000 + self.machine_id * 1000000 + self._sequence
            else:
                # 秒时间戳是10位，机器ID占4位，序列号占6位
                # 格式：timestamp(10位) + machine_id(4位) + sequence(6位) = 20位
                numeric_id = timestamp * 10000000000 + self.machine_id * 1000000 + self._sequence
            
            return numeric_id


# 全局单例实例
_default_generator = IDGenerator()


def generate_id(prefix="", length=None):
    """
    生成含时的序列号（使用默认生成器）
    
    Args:
        prefix: ID 前缀（如 "device_", "volume_" 等）
        length: 指定ID总长度（可选）
    
    Returns:
        str: 生成的ID
    """
    return _default_generator.generate(prefix=prefix, length=length)


def generate_numeric_id():
    """
    生成纯数字的含时序列号（使用默认生成器）
    
    Returns:
        int: 生成的数字ID
    """
    return _default_generator.generate_numeric()


__all__ = [
    "IDGenerator",
    "generate_id",
    "generate_numeric_id",
]

