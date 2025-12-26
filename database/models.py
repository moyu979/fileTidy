"""
SQLAlchemy ORM 模型定义。
"""

from __future__ import annotations
import enum
from sqlalchemy import (
    Column,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    Enum,
)
from sqlalchemy.orm import declarative_base


Base = declarative_base()

# 定义枚举类
class DeviceState(enum.Enum):
    HEALTHY = "healthy" # 正常使用的
    DANGER = "danger" # 危险，冗余出现故障，但是暂时可以使用
    FAULT = "fault" # 故障，无法使用
    UNUSED = "unused" # 未使用，指统一淘汰的

# 定义枚举类
class RelationState(enum.Enum):
    USING = "using" # 正在使用
    UNUSED = "unused" # 未使用，一般指代发生替换后之前的设备/卷


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
    __tablename__ = "device"
    # 设备序列号，对于磁盘来说，是磁盘的序列号，对于磁带来说，是一个自动生成的id，需要手记一下
    serial = Column(String, primary_key=True)
    # 设备名称，一个方便记忆的名称
    name = Column(String, unique=True, nullable=False)
    # 设备类型，如硬盘、磁带、TF卡等
    kind = Column(String)
    # 设备添加时间
    add_time = Column(String)
    # 设备最后一次检查时间
    last_check_time = Column(String)
    # 设备状态，如健康、故障等
    state = Column(Enum(DeviceState), default=DeviceState.HEALTHY)
    # 设备容量（字节）
    capacity = Column(Integer)
    # 设备其他信息
    info = Column(Text, default="")


class VolumeStructureModel(Base):
    """
    中间架构抽象，用于描述设备如何组织成文件系统
    """
    __tablename__ = "volume_structures"
    __table_args__ = (
        PrimaryKeyConstraint("volume_id", "device_id"),
    )
    # 卷id
    volume_id = Column(String, nullable=False)
    # 使用哪个设备
    device_id = Column(String, nullable=False)
    # 添加时间
    add_time = Column(String)
    # 状态，指是否还在使用这个映射关系
    state = Column(Enum(RelationState), default=RelationState.USING)
    # 其他信息
    info = Column(Text, default="")


class VolumeModel(Base):
    """
    文件系统级抽象，用于对文件系统的管理
    """
    __tablename__ = "volumes"

    # 卷id  
    id = Column(String, primary_key=True)
    # 卷名称，一个方便记忆的名称
    name = Column(String, unique=True, nullable=False)

    # 卷类型，如单磁带卷、多磁带卷、RAID5卷等，与VolumeStructure一起，构成挂载文件系统时的指南
    # 同一个卷，应当由相同的设备构成，否则可能会造成不可知的问题
    kind = Column(String)

    # 用何技术组成的卷，例如，win存储池，zfs，硬件阵列
    method = Column(String)

    # 添加时间
    add_time = Column(String)

    # 最后一次检查时间
    last_check_time = Column(String)

    # 卷状态，如健康、故障等
    state = Column(Enum(DeviceState), default=DeviceState.HEALTHY)

    # 卷容量（字节）
    capacity = Column(Integer)

    # 卷挂载点，一个唯一的挂载点，用于全局文件索引
    unique_mount_point = Column(String, default="None")

    # 卷文件系统类型，如ext4、xfs、btrfs等
    file_system = Column(String, default="")

    # 卷其他信息
    info = Column(Text, default="")


class SuperVolumeStructureModel(Base):
    __tablename__ = "super_volume_structures"
    __table_args__ = (
        PrimaryKeyConstraint("superVolume_id", "volume_id"),
    )
    # 超级卷id  
    superVolume_id = Column(String, nullable=False)
    # 卷id
    volume_id = Column(String, unique=True, nullable=False)
    # 添加时间
    add_time = Column(String)
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
    id = Column(String, primary_key=True)
    # 超级卷名称，一个方便记忆的名称
    name = Column(String, unique=True, nullable=False)
    # 超级卷类型，如单磁带卷、多磁带卷、RAID5卷等
    kind = Column(String)
    # 用何种方式组合的 eg：snapraid，tape自己完成的……等等
    method = Column(String)
    # 添加时间
    add_time = Column(String)
    # 最后一次检查时间
    last_check_time = Column(String)
    # 超级卷状态，如健康、故障等
    state = Column(Enum(DeviceState), default=DeviceState.HEALTHY)
    # 超级卷其他信息
    info = Column(Text, default="")


class FileModel(Base):
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

    __tablename__ = "files"
    __table_args__ = (
        PrimaryKeyConstraint("md5", "now_path"),
        UniqueConstraint("now_path"),
    )
    # 文件md5值
    md5 = Column(String, nullable=False)
    # 文件大小（字节）
    size = Column(Integer)
    # 文件添加时间
    add_time = Column(String)
    # 文件原始路径
    from_path = Column(Text)
    # 文件当前路径，除去卷路径和**/datas/**过渡路径
    now_path = Column(Text, nullable=False)
    # 文件当前所在的卷
    now_volume = Column(String)
    # 文件当前的名称
    now_name = Column(String)
    # 文件状态，如健康、故障等
    state = Column(String, default="online")
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
    last_visit_time = Column(String)
    # 文件最后一次修改时间
    last_modify_time = Column(String)
    # 文件添加时间
    add_time = Column(String)


