"""
设备管理 API

提供设备相关的业务逻辑函数，包括：
- 列出所有设备
- 添加设备
- 移除设备
- 查看设备信息
- 更新设备属性
- 检查设备状态
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from apps.common.database.models import DeviceModel, DeviceState
from apps.common.database.session import session_scope
from apps.infra.device.device_factory import DeviceFactory
from apps.infra.device.device_manager import device_manager
from apps.infra.device.os_adapter.get_type import get_type


def list_devices(
    kind_filter: Optional[str] = None,
    state_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    列出所有设备
    
    Args:
        kind_filter: 过滤设备类型 (HDD, SSD, Tape, TF Card)
        state_filter: 过滤设备状态 (healthy, danger, fault, no_longer_used, removed)
    
    Returns:
        List[Dict[str, Any]]: 设备信息列表，每个字典包含设备的详细信息
    """
    with session_scope() as session:
        query = session.query(DeviceModel)
        
        if kind_filter:
            query = query.filter(DeviceModel.kind == kind_filter)
        
        if state_filter:
            try:
                state_enum = DeviceState[state_filter.upper()]
                query = query.filter(DeviceModel.state == state_enum)
            except KeyError:
                raise ValueError(f"无效的状态 '{state_filter}'。可用状态: healthy, danger, fault, no_longer_used, removed")
        
        devices = query.all()
        
        result = []
        for device in devices:
            capacity_gb = device.capacity / (1024**3) if device.capacity and device.capacity > 0 else 0
            result.append({
                'serial': device.serial,
                'name': device.name,
                'kind': device.kind or 'N/A',
                'state': device.state.value if device.state else 'N/A',
                'capacity_gb': capacity_gb,
                'add_time': device.add_time.strftime('%Y-%m-%d %H:%M:%S') if device.add_time else 'N/A',
                'last_check_time': device.last_check_time.strftime('%Y-%m-%d %H:%M:%S') if device.last_check_time else 'N/A',
                'info': device.info or 'N/A',
            })
        
        return result


def show_device(serial: Optional[str] = None, path: Optional[str] = None) -> Dict[str, Any]:
    """
    显示指定设备的详细信息
    
    Args:
        serial: 设备序列号（如果提供 path 则不需要）
        path: 设备路径（如果提供 serial 则不需要）
    
    Returns:
        Dict[str, Any]: 设备详细信息字典
    
    Raises:
        ValueError: 设备不存在或参数错误
    """
    # 确保至少提供了一个参数
    if not serial and not path:
        raise ValueError("必须提供 serial 或 path 参数之一")
    
    # 如果只提供了 path，通过 device_manager 获取 serial
    # 如果同时提供了 serial 和 path，优先使用 serial
    if not serial and path:
        serial = device_manager.get_device_id(path)
        if not serial:
            raise ValueError(f"无法从路径 '{path}' 获取设备序列号")
    
    with session_scope() as session:
        device = session.query(DeviceModel).filter(DeviceModel.serial == serial).first()
        
        if not device:
            raise ValueError(f"未找到序列号为 '{serial}' 的设备")
        
        capacity_gb = device.capacity / (1024**3) if device.capacity and device.capacity > 0 else 0
        
        return {
            'serial': device.serial,
            'name': device.name,
            'kind': device.kind or 'N/A',
            'state': device.state.value if device.state else 'N/A',
            'capacity_gb': capacity_gb,
            'add_time': device.add_time.strftime('%Y-%m-%d %H:%M:%S') if device.add_time else 'N/A',
            'last_check_time': device.last_check_time.strftime('%Y-%m-%d %H:%M:%S') if device.last_check_time else 'N/A',
            'info': device.info or 'N/A',
        }


def add_device(
    path: str,
    name: Optional[str] = None,
    kind: Optional[str] = None,
    capacity: Optional[int] = None,
    info: Optional[str] = None,
) -> Dict[str, str]:
    """
    添加新设备
    
    Args:
        path: 设备路径 (必需)
        name: 设备名称 (可选，默认自动生成)
        kind: 设备类型 (可选，默认自动检测)
        capacity: 设备容量，单位字节 (可选，默认自动检测)
        info: 其他信息 (可选)
    
    Returns:
        Dict[str, str]: 包含设备名称和序列号的字典
    
    Raises:
        ValueError: 参数错误或不支持的类型
        Exception: 创建设备时的其他错误
    """
    kwargs = {'path': path}
    
    if name is not None:
        kwargs['name'] = name
    
    if kind is not None:
        kwargs['kind'] = kind
    
    if capacity is not None:
        kwargs['capacity'] = capacity
    
    if info is not None:
        kwargs['info'] = info
    
    # 根据类型创建设备
    device = None
    if 'kind' in kwargs:
        kind_upper = kwargs['kind'].upper()
        if kind_upper == 'HDD':
            from apps.infra.device.impl.hdd_device import HddDevice
            device = HddDevice.new_device(**kwargs)
        elif kind_upper == 'SSD':
            from apps.infra.device.impl.ssd_device import SsdDevice
            device = SsdDevice.new_device(**kwargs)
        elif kind_upper.startswith('TAPE'):
            from apps.infra.device.impl.tape_device import TapeDevice
            device = TapeDevice.new_device(**kwargs)
        else:
            raise ValueError(f"不支持的类型 '{kind_upper}'")
    else:
        # 自动检测类型
        detected_kind = get_type(kwargs['path'])
        if detected_kind is None:
            raise ValueError("无法自动检测设备类型，请使用 kind 参数指定")
        
        detected_kind = detected_kind.upper()
        if detected_kind == 'HDD':
            from apps.infra.device.impl.hdd_device import HddDevice
            device = HddDevice.new_device(**kwargs)
        elif detected_kind == 'SSD':
            from apps.infra.device.impl.ssd_device import SsdDevice
            device = SsdDevice.new_device(**kwargs)
        elif detected_kind.startswith('TAPE'):
            from apps.infra.device.impl.tape_device import TapeDevice
            device = TapeDevice.new_device(**kwargs)
        else:
            raise ValueError(f"不支持检测到的类型 '{detected_kind}'")
    
    return {
        'name': device.orm_model.name,
        'serial': device.orm_model.serial,
    }


def remove_device(serial: str) -> None:
    """
    移除设备（软删除：将状态设置为 removed）
    
    Args:
        serial: 设备序列号
    
    Raises:
        ValueError: 设备不存在
    """
    device_factory = DeviceFactory()
    
    device_obj = device_factory.get_device(serial)
    if not device_obj:
        raise ValueError(f"未找到序列号为 '{serial}' 的设备或无法创建设备实例")
    
    # 将设备状态设置为 REMOVED（软删除）
    device_obj.set('state', DeviceState.REMOVED)


def update_device(
    serial: str,
    name: Optional[str] = None,
    state: Optional[str] = None,
    capacity: Optional[int] = None,
    info: Optional[str] = None,
) -> None:
    """
    更新设备属性
    
    Args:
        serial: 设备序列号
        name: 设备名称
        state: 设备状态 (healthy, danger, fault, no_longer_used, removed)
        capacity: 设备容量，单位字节
        info: 其他信息
    
    Raises:
        ValueError: 设备不存在或参数错误
        Exception: 更新设备时的其他错误
    """
    device_factory = DeviceFactory()
    
    device_obj = device_factory.get_device(serial)
    if not device_obj:
        raise ValueError(f"未找到序列号为 '{serial}' 的设备或无法创建设备实例")
    
    # 处理状态枚举
    if state is not None:
        try:
            state_enum = DeviceState[state.upper()]
            device_obj.set('state', state_enum)
        except KeyError:
            raise ValueError(f"无效的状态 '{state}'。可用状态: healthy, danger, fault, no_longer_used, removed")
    
    # 处理其他属性
    if name is not None:
        device_obj.set('name', name)
    
    if capacity is not None:
        device_obj.set('capacity', capacity)
    
    if info is not None:
        device_obj.set('info', info)


def check_device(serial: str) -> None:
    """
    检查设备状态
    
    Args:
        serial: 设备序列号
    
    Raises:
        ValueError: 设备不存在
        Exception: 检查设备时的其他错误
    """
    device_factory = DeviceFactory()
    
    device = device_factory.get_device(serial)
    if not device:
        raise ValueError(f"未找到序列号为 '{serial}' 的设备")
    
    # 调用设备的 check 方法
    device.check()
    
    # 更新最后检查时间
    with session_scope() as session:
        db_device = session.query(DeviceModel).filter(DeviceModel.serial == serial).first()
        if db_device:
            db_device.last_check_time = datetime.utcnow()
            session.commit()
