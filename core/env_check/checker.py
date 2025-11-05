"""
环境依赖检查器
根据系统类型自动选择并执行对应的依赖检查
"""

import logging
from typing import Tuple, Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


def _load_system_checker() -> Optional[Callable[[], Tuple[bool, Dict[str, Any]]]]:
    """
    根据系统类型载入对应的依赖检查器
    
    Returns:
        Optional[Callable]: 对应的检查函数，如果系统不支持则返回None
    """
    try:
        from core.conf import get
        
        system = get("system")
        if not system:
            logger.warning("无法获取系统类型")
            return None
        
        logger.info(f"检测到系统类型: {system}")
        
        if system.lower() in ["linux", "linux2"]:
            from .linux.dependencies import check_linux_dependencies
            return check_linux_dependencies
        elif system.lower() == "windows":
            # Windows依赖检查（待实现）
            logger.info("Windows依赖检查暂未实现")
            return None
        elif system.lower() == "darwin":
            # macOS依赖检查（待实现）
            logger.info("macOS依赖检查暂未实现")
            return None
        else:
            logger.warning(f"未知系统类型: {system}")
            return None
            
    except ImportError as e:
        logger.error(f"导入配置模块失败: {e}")
        return None
    except Exception as e:
        logger.error(f"载入系统检查器时发生错误: {e}")
        return None


def check_dependencies() -> Tuple[bool, Dict[str, Any]]:
    """
    根据系统类型自动选择并执行对应的依赖检查
    
    Returns:
        Tuple[bool, Dict]: (是否所有依赖都满足, 详细检查结果)
    """
    checker = _load_system_checker()
    
    if checker is None:
        return False, {"error": "unsupported_system", "message": "当前系统不支持依赖检查"}
    
    try:
        return checker()
    except Exception as e:
        logger.error(f"依赖检查过程中发生错误: {e}")
        return False, {"error": "check_failed", "message": str(e)}
