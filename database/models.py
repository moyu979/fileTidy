"""SQLAlchemy ORM 模型定义。"""

from __future__ import annotations

from sqlalchemy import (
    Column,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base


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
    __tablename__ = "device"

    serial = Column(String, primary_key=True)  # device_ 开头的唯一 ID
    name = Column(String, unique=True, nullable=False)
    kind = Column(String)
    add_time = Column(String)
    last_check_time = Column(String)
    state = Column(String, default="healthy")
    capacity = Column(Integer)
    info = Column(Text, default="")


class VolumeStructureModel(Base):
    """
    中间架构抽象，用于描述设备如何组织成文件系统
    """
    __tablename__ = "volume_structures"
    __table_args__ = (
        PrimaryKeyConstraint("volume_id", "device_id"),
    )

    volume_id = Column(String, nullable=False)
    device_id = Column(String, nullable=False)
    add_time = Column(String)
    info = Column(Text, default="")


class VolumeModel(Base):
    """
    文件系统级抽象，用于对文件系统的管理
    """
    __tablename__ = "volumes"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    kind = Column(String)
    add_time = Column(String)
    last_check_time = Column(String)
    state = Column(String, default="healthy")
    capacity = Column(Integer)
    info = Column(Text, default="")
    unique_mount_point = Column(String, default="")
    file_system = Column(String, default="")


class SuperVolumeStructureModel(Base):
    __tablename__ = "super_volume_structures"
    __table_args__ = (
        PrimaryKeyConstraint("superVolume_id", "volume_id"),
    )

    superVolume_id = Column(String, nullable=False)
    volume_id = Column(String, unique=True, nullable=False)
    add_time = Column(String)
    info = Column(Text, default="")


class SuperVolumeModel(Base):
    """
    超文件系统级抽象，用于对超级文件系统的管理，用来管理多个文件系统的校验关系
    """
    __tablename__ = "super_volumes"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    kind = Column(String)
    add_time = Column(String)
    last_check_time = Column(String)
    state = Column(String, default="healthy")
    capacity = Column(Integer)
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

    md5 = Column(String, nullable=False)
    size = Column(Integer)
    add_time = Column(String)
    from_path = Column(Text)
    now_path = Column(Text, nullable=False)
    now_volume = Column(String)
    now_name = Column(String)
    state = Column(String, default="online")
    info = Column(Text, default="")


class CacheModel(Base):
    """
    缓存级抽象，用于对缓存的管理
    """
    __tablename__ = "cache"
    __table_args__ = (
        PrimaryKeyConstraint("md5", "now_path"),
    )

    md5 = Column(String, nullable=False)
    size = Column(Integer)
    now_path = Column(Text, nullable=False)
    now_name = Column(String)
    last_visit_time = Column(String)
    last_modify_time = Column(String)
    add_time = Column(String)


