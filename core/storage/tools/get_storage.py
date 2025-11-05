# 本文件未经测试
import re
import logging
import os
import sys

# 在导入 core 包之前，确保项目根路径在 sys.path 中，便于独立运行本文件
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.conf import conf

logger = logging.getLogger(__name__)

# 根据平台载入相应的模块
def _get_platform_modules():
    """根据平台获取相应的模块"""
    system = conf.get("system")
    if not system:
        logger.error("配置中未设置system，无法确定系统类型")
        return None, None
        
    system = system.lower()
    
    if system == "linux":
        from core.storage.tools.linux.get_disk import get_disk
        from core.storage.tools.linux.get_tape import get_tape
        return get_disk, get_tape
    else:
        logger.error(f"当前系统({system})不支持，仅支持linux")
        return None, None

def get_storage(path=None):
    """
    获取存储设备信息（磁盘和磁带）
    
    Args:
        path (str, optional): 存储设备路径。如果为空或None，则获取全部存储设备
        
    Returns:
        list: 存储设备信息列表
    """
    try:
        # 获取平台对应的模块
        get_disk, get_tape = _get_platform_modules()
        if get_disk is None or get_tape is None:
            logger.error("获取平台对应的模块失败")
            return None
            
        if path is None or path == "":
            # 获取全部存储设备
            logger.debug("获取全部存储设备信息")
            disk_info = get_disk() or []
            tape_info = get_tape() or []
            
            return disk_info + tape_info
        else:
            # 根据路径获取特定存储设备
            logger.debug(f"根据路径获取存储设备信息: {path}")
            
            # 使用正则表达式判断是磁带还是磁盘
            disk_pattern = re.compile(r'^(/dev/)?(sd[a-z]+|nvme\d+n\d+)$')
            tape_pattern = re.compile(r'^(/dev/)?st\d+$')
            
            if disk_pattern.match(path):
                # 是磁盘设备
                logger.debug(f"识别为磁盘设备: {path}")
                return get_disk(path) or []
            elif tape_pattern.match(path):
                # 是磁带设备
                logger.debug(f"识别为磁带设备: {path}")
                return get_tape(path) or []
            else:
                logger.warning(f"无法识别设备类型: {path}")
                return []
                
    except Exception as e:
        logger.error(f"获取存储设备信息时发生错误: {str(e)}")
        return None

if __name__ == "__main__":
    print(get_storage())
