# CHECK: 待检查 - 基础设施 ORM 模型 - 数据库表映射

"""
SQLAlchemy ORM 模型定义。
"""

from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    Enum,
    DateTime,
    Boolean,
)
from sqlalchemy.orm import declarative_base
from domain.storage.device.enum import DeviceState
from domain.storage.super_device.enum import SuperDeviceState, RelationState
from domain.storage.file.enum import FileState
from domain.storage.super_volume.enum import SuperVolumeState
from domain.storage.volume.enum import VolumeState
Base = declarative_base()


class DeviceModel(Base):
    """
    硬件层抽象，用于管理硬件设备
    包括：
    - 硬盘
    - 磁带
    - TF卡
    - 其他硬件设备
    主要用于提供操作硬件设备的抽象
    """
    __tablename__ = "devices"
    # 设备序列号，对于磁盘来说，是磁盘的序列号，对于磁带来说，是一个自动生成的id，需要手记一下
    serial = Column(String, primary_key=True)
    # 设备名称，一个方便记忆的名称，有些磁盘会有friendlyname，但是那个会有重复
    name = Column(String, default="")
    # 设备类型，如硬盘、磁带、TF卡等
    type = Column(String)
    # 设备添加时间
    add_time = Column(DateTime, default=datetime.utcnow)
    # 设备最后一次检查时间
    last_check_time = Column(DateTime, nullable=True)
    # 设备状态，如健康、故障等
    state = Column(Enum(DeviceState), default=DeviceState.UNKNOWN)
    # 设备容量（字节）
    capacity = Column(BigInteger)
    # 设备其他半格式化信息，以json形式存储
    info = Column(Text, default="")

class SuperDeviceStructureModel(Base):
    """
    超级设备与设备之间的关联关系映射表，记录设备如何组成超级设备。
    """
    __tablename__ = "super_device_structures"
    __table_args__ = (
        PrimaryKeyConstraint("super_device_id", "sub_device_id"),
    )
    # 超级设备 id
    super_device_id = Column(String, ForeignKey("super_devices.serial"), nullable=False)
    # 子设备 id（Device 的 serial）
    sub_device_id = Column(String, ForeignKey("devices.serial"), nullable=False)
    # 添加时间
    add_time = Column(DateTime, default=datetime.utcnow)
    # 状态，指是否还在使用这个映射关系
    state = Column(Enum(RelationState), default=RelationState.USING)
    # 其他信息
    info = Column(Text, default="")

class SuperDeviceModel(Base):
    """
    超级设备抽象，用于管理由多个子设备组合而成的逻辑设备。
    例如 RAID、LVM 等由多个物理设备组成的逻辑存储单元。
    """
    __tablename__ = "super_devices"

    # 超级设备id
    serial = Column(String, primary_key=True)
    # 超级设备名称
    name = Column(String, default="")
    # 超级设备类型 如：磁带卷、硬盘卷、RAID5卷等
    type = Column(String)
    # 是否需要全部设备同时上线
    need_all_devices_online = Column(Boolean, default=False)
    # 登记时间
    add_time = Column(DateTime, default=datetime.utcnow)
    # 最后一次检查时间
    last_check_time = Column(DateTime, nullable=True)
    # 超级设备状态，如健康、故障等
    state = Column(Enum(SuperDeviceState), default=SuperDeviceState.HEALTHY)
    # 超级设备容量（字节）
    capacity = Column(BigInteger)
    # 超级设备其他信息
    info = Column(Text, default="")

class VolumeModel(Base):
    """
    文件系统级抽象，用于对文件系统的管理
    """
    __tablename__ = "volumes"

    # 卷id  
    serial = Column(String, primary_key=True)
    # 建立在哪个设备上，可以是设备(device)或者超级设备(super device)
    device_id = Column(String, nullable=False)
    # 卷名称，一个方便记忆的名称
    name = Column(String, default="")
    # 添加时间
    add_time = Column(DateTime, default=datetime.utcnow)
    # 最后一次检查时间
    last_check_time = Column(DateTime, nullable=True)
    # 卷状态，如健康、故障等
    state = Column(Enum(VolumeState), default=VolumeState.UNKNOWN)
    # 卷容量（字节）
    capacity = Column(BigInteger)
    # 卷挂载点，一个唯一的挂载点，用于全局文件索引
    unique_mount_point = Column(String, default="/unknown")
    # 卷文件系统类型，如ext4、xfs、btrfs等
    file_system = Column(String, default="")
    # 卷其他信息
    info = Column(Text, default="")


class SuperVolumeStructureModel(Base):
    """
    超级卷与卷之间的关联关系映射表，记录卷如何组成超级卷。
    """
    __tablename__ = "super_volume_structures"
    __table_args__ = (
        PrimaryKeyConstraint("super_volume_id", "volume_id"),
    )
    # 超级卷 id
    super_volume_id = Column(String, ForeignKey("super_volumes.serial"), nullable=False)
    # 卷 id
    volume_id = Column(String, ForeignKey("volumes.serial"), unique=True, nullable=False)
    # 添加时间
    add_time = Column(DateTime, default=datetime.utcnow)
    # 状态，指是否还在使用这个映射关系
    state = Column(Enum(RelationState), default=RelationState.USING)
    # 其他信息
    info = Column(Text, default="")


class SuperVolumeModel(Base):
    """
    超文件系统级抽象，用于对超级文件系统的管理，用来管理多个文件系统的校验关系
    """
    __tablename__ = "super_volumes"

    # 超级卷id
    serial = Column(String, primary_key=True)
    # 超级卷名称，一个方便记忆的名称
    name = Column(String, unique=True, nullable=False)
    # 超级卷类型，如单磁带卷、多磁带卷、RAID5卷等
    type = Column(String)
    # 用何种方式组合的 eg：snapraid，tape自己完成的……等等
    method = Column(String)
    # 添加时间
    add_time = Column(DateTime, default=datetime.utcnow)
    # 最后一次检查时间
    last_check_time = Column(DateTime, nullable=True)
    # 超级卷状态，如健康、故障等
    state = Column(Enum(SuperVolumeState), default=SuperVolumeState.HEALTHY)
    # 超级卷其他信息
    info = Column(Text, default="")

class FileSourcesModel(Base):
    """
    文件级抽象，用于对文件的管理
    包括：
    - 文件的id值
    - 文件的sha512值
    - 文件的MD5值
    - 文件的大小
    - 文件的添加时间
    - 文件的原始路径
    - 文件的状态
    - 文件的其他信息
    """
    __tablename__ = "file_sources"
    #自增主键
    id = Column(Integer, primary_key=True)
    # 文件md5值
    sha512 = Column(String, nullable=False)
    # 文件md5值
    md5 = Column(String, nullable=False)
    # 文件大小（字节）
    size = Column(Integer)
    # 文件添加时间
    add_time = Column(DateTime, default=datetime.utcnow)
    # 文件原始路径
    from_path = Column(Text)
    # 文件状态，如健康、故障，密码丢失等
    state = Column(Enum(FileState), default=FileState.ONLINE)
    # 文件其他信息
    info = Column(Text, default="")

class FileLocationsModel(Base):
    """
    文件级抽象，用于对文件的管理
    包括：
    - 文件的MD5值
    - 文件的大小
    - 文件的添加时间
    - 文件的原始路径
    - 文件当前的路径
    - 文件当前所在的卷
    - 文件当前的名称
    - 文件的状态
    - 文件的其他信息
    """
    __tablename__ = "file_locations"
    __table_args__ = (
        PrimaryKeyConstraint("now_volume", "now_path"),
    )
    # 文件md5值
    sha512 = Column(String, nullable=False)
    # 文件md5值
    md5 = Column(String, nullable=False)
    # 文件大小（字节）
    size = Column(Integer)
    # 文件添加时间
    add_time = Column(DateTime, default=datetime.utcnow)
    # 文件当前路径，除去卷路径和**/datas/**过渡路径
    now_path = Column(Text, nullable=False)
    # 文件当前所在的卷
    now_volume = Column(String, ForeignKey("volumes.serial"))
    # 文件状态，如在线、丢失、损坏等
    state = Column(Enum(FileState), default=FileState.ONLINE)
    # 文件其他信息
    info = Column(Text, default="")

class CacheModel(Base):
    """
    缓存级抽象，用于对缓存的管理
    """
    __tablename__ = "cache"
    __table_args__ = (
        PrimaryKeyConstraint("md5", "now_path"),
    )

    # 文件md5值
    md5 = Column(String, nullable=False)
    # 文件大小（字节）
    size = Column(Integer)
    # 文件当前路径，除去卷路径和**/datas/**过渡路径
    now_path = Column(Text, nullable=False)
    # 文件当前的名称
    now_name = Column(String)
    # 文件最后一次访问时间
    last_visit_time = Column(DateTime, nullable=True)
    # 文件最后一次修改时间
    last_modify_time = Column(DateTime, nullable=True)
    # 文件添加时间
    add_time = Column(DateTime, default=datetime.utcnow)


