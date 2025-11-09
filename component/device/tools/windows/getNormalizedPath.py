# 通过了初步校验

"""
获取磁盘信息
"""

import logging
from utils.runCommand import run_command
from .isHdd import is_hdd
from .isSSD import is_ssd

logger = logging.getLogger(__name__)




def get_normalized_path(dev_path):
    """获取单个设备的完整信息"""    
    # 规范化设备路径
    if dev_path.isdigit():
        device_path = rf'\\.\PhysicalDrive{dev_path}'
    elif dev_path.startswith('PhysicalDrive'):
        device_path = rf'\\.\{dev_path}'
    elif dev_path.startswith(r'\\.\PhysicalDrive'):
        device_path = dev_path
    else:
        device_path = dev_path
    
    return device_path
