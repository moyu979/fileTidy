"""
SQLAlchemy ORM 模型定义。
"""

from __future__ import annotations
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
    false,
    func,
)
from sqlalchemy.orm import declarative_base
from domain.storage.device.enum import DeviceState
from domain.storage.super_device.enum import SuperDeviceRelationState, SuperDeviceState
from domain.storage.file.enum import FileState
from domain.storage.super_volume.enum import SuperVolumeRelationState, SuperVolumeState
from domain.storage.volume.enum import VolumeState
Base = declarative_base()

# NOTE: 每列的 client default 与 server_default 必须保持语义一致：
#   - default=        → SQLAlchemy 客户端默认；走 ORM 的 INSERT 时生效（显式传 None 也兜底），
#                       但**不会**写进 DDL。
#   - server_default= → DDL 里的 DEFAULT 子句；裸 SQL / text() / 迁移脚本写入时生效。
# 例外：`add_time` **故意不写 client default**（2026-10-02 决定）：
#   两边效果只在精度上不同（Python callable 带微秒，CURRENT_TIMESTAMP 只到秒），
#   秒级对本项目够用，且省掉 3.12 已弃用的 datetime.utcnow()。
#   所以它**完全依赖 DDL 的 DEFAULT**：旧库（建表时无 DEFAULT 子句）会写 NULL，重建库才生效。
# 坑：Enum 列在库里存的是**成员名**而非值（见 test_enum_round_trip_stores_member_name），
#     因此 server_default 必须用 `X.NAME.name`（如 DeviceState.UNKNOWN.name → "UNKNOWN"）。
#     时间列用 func.now() 即可：SQLite 方言会渲染成 CURRENT_TIMESTAMP。
#     验证时别看无 dialect 的 `compile()` 输出（那里会显示 `now()`），要真跑 create_all。

# TODO: file 子系统未完成（设计未定稿）：file_sources / file_locations 两张表及 FileState
#       引用为临时设计，后续可能随 file 模块一起重写或删除。


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
    name = Column(String, default="", server_default="")
    # 设备类型，如硬盘、磁带、TF卡等
    dtype = Column(String)
    # 设备添加时间（只由 DDL 的 DEFAULT 提供，见顶部 NOTE）
    add_time = Column(DateTime, server_default=func.now())
    # 设备最后一次检查时间
    last_check_time = Column(DateTime, nullable=True)
    # 设备状态，如健康、故障等
    state = Column(
        Enum(DeviceState),
        default=DeviceState.UNKNOWN,
        server_default=DeviceState.UNKNOWN.name,
    )
    # 设备容量（字节）
    capacity = Column(BigInteger)
    # 设备其他半格式化信息，以json形式存储
    info = Column(Text, default="", server_default="")

class SuperDeviceStructureModel(Base):
    """
    超级设备与子项之间的关联关系映射表，记录子项如何组成超级设备。

    子项（sub_device_id）既可以是物理设备（Device.serial），
    也可以是另一个超级设备（SuperDevice.serial），支持超级设备层叠。
    """
    __tablename__ = "super_device_structures"
    __table_args__ = (
        PrimaryKeyConstraint("super_device_id", "sub_device_id"),
    )
    # 超级设备 id
    super_device_id = Column(String, ForeignKey("super_devices.serial"), nullable=False)
    # 子项 id（Device.serial 或 SuperDevice.serial，支持层叠）
    sub_device_id = Column(String, nullable=False)
    # 添加时间（只由 DDL 的 DEFAULT 提供，见顶部 NOTE）
    add_time = Column(DateTime, server_default=func.now())
    # 状态，指是否还在使用这个映射关系
    state = Column(
        Enum(SuperDeviceRelationState),
        default=SuperDeviceRelationState.USING,
        server_default=SuperDeviceRelationState.USING.name,
    )
    # 其他信息
    info = Column(Text, default="", server_default="")

class SuperDeviceModel(Base):
    """
    超级设备抽象，用于管理由多个子设备组合而成的逻辑设备。
    例如 RAID、LVM 等由多个物理设备组成的逻辑存储单元。
    """
    __tablename__ = "super_devices"

    # 超级设备id
    serial = Column(String, primary_key=True)
    # 超级设备名称
    name = Column(String, default="", server_default="")
    # 超级设备类型 如：磁带卷、硬盘卷、RAID5卷等
    sdtype = Column(String)
    # 是否需要全部设备同时上线
    need_all_devices_online = Column(Boolean, default=False, server_default=false())
    # 登记时间（只由 DDL 的 DEFAULT 提供，见顶部 NOTE）
    add_time = Column(DateTime, server_default=func.now())
    # 最后一次检查时间
    last_check_time = Column(DateTime, nullable=True)
    # 超级设备状态，如健康、故障等
    state = Column(
        Enum(SuperDeviceState),
        default=SuperDeviceState.HEALTHY,
        server_default=SuperDeviceState.HEALTHY.name,
    )
    # 超级设备容量（字节）
    capacity = Column(BigInteger)
    # 超级设备其他信息
    info = Column(Text, default="", server_default="")

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
    name = Column(String, default="", server_default="")
    # 添加时间（只由 DDL 的 DEFAULT 提供，见顶部 NOTE）
    add_time = Column(DateTime, server_default=func.now())
    # 最后一次检查时间
    last_check_time = Column(DateTime, nullable=True)
    # 卷状态，如健康、故障等
    state = Column(
        Enum(VolumeState),
        default=VolumeState.UNKNOWN,
        server_default=VolumeState.UNKNOWN.name,
    )
    # 卷容量（字节）
    capacity = Column(BigInteger)
    # 卷挂载点，一个唯一的挂载点，用于全局文件索引
    unique_mount_point = Column(String, default="/unknown", server_default="/unknown")
    # 卷文件系统类型，如ext4、xfs、btrfs等
    file_system = Column(String, default="", server_default="")
    # 卷其他信息
    info = Column(Text, default="", server_default="")


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
    # TODO(P2): `unique=True` 是**不分状态**的硬约束，语义过强：卷只要进过任何超级卷，
    #   哪怕关联已变 UNUSED（替换/移除后），该行仍占着唯一的 volume_id 位，于是这个卷
    #   永远不能再编入别的超级卷（见 super_volume_repository.add_volumes 的校验，
    #   以及 test_add_volumes_rejects_existing_unused_membership 的如实断言）。
    #   正解是「部分唯一索引」——只对 state == USING 的行唯一：
    #     Index("uq_sv_structure_volume_using", "volume_id",
    #           unique=True, sqlite_where=text("state = 'USING'"))
    #   注意枚举列在库里存的是**成员名**，where 里要用 'USING' 而非 'using'。
    #   改的时候需同步放宽 add_volumes 的校验与两条相关测试。先放着，未定稿。
    volume_id = Column(String, ForeignKey("volumes.serial"), unique=True, nullable=False)
    # 添加时间（只由 DDL 的 DEFAULT 提供，见顶部 NOTE）
    add_time = Column(DateTime, server_default=func.now())
    # 状态，指是否还在使用这个映射关系
    state = Column(
        Enum(SuperVolumeRelationState),
        default=SuperVolumeRelationState.USING,
        server_default=SuperVolumeRelationState.USING.name,
    )
    # 其他信息
    info = Column(Text, default="", server_default="")


class SuperVolumeModel(Base):
    """
    超文件系统级抽象，用于对超级文件系统的管理，用来管理多个文件系统的校验关系
    """
    __tablename__ = "super_volumes"

    # 超级卷id
    serial = Column(String, primary_key=True)
    # 超级卷名称，一个方便记忆的名称
    # **不设唯一约束**（2026-10-02）：名字只是给人看的标签，查重一律用 serial（主键）；
    # 而软删除（state=REMOVED）的行会永久保留，带唯一约束就会永久霸占该名字，
    # 导致同名超级卷无法重建。
    name = Column(String, nullable=False)
    # 超级卷类型，如单磁带卷、多磁带卷、RAID5卷等
    svtype = Column(String)
    # 用何种方式组合的 eg：snapraid，tape自己完成的……等等
    method = Column(String)
    # 添加时间（只由 DDL 的 DEFAULT 提供，见顶部 NOTE）
    add_time = Column(DateTime, server_default=func.now())
    # 最后一次检查时间
    last_check_time = Column(DateTime, nullable=True)
    # 超级卷状态，如健康、故障等
    state = Column(
        Enum(SuperVolumeState),
        default=SuperVolumeState.HEALTHY,
        server_default=SuperVolumeState.HEALTHY.name,
    )
    # 超级卷其他信息
    info = Column(Text, default="", server_default="")

class FileSourcesModel(Base):
    """
    文件级抽象，用于对文件的管理，本结构用于记录文件的原始来源。
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
    # 文件sha512值
    sha512 = Column(String, nullable=False)
    # 文件md5值
    md5 = Column(String, nullable=False)
    # 文件大小（字节）
    size = Column(Integer)
    # 文件添加时间（只由 DDL 的 DEFAULT 提供，见顶部 NOTE）
    add_time = Column(DateTime, server_default=func.now())
    # 文件原始路径（绝对路径）
    from_path = Column(Text)
    # 文件状态，如健康、故障，密码丢失等，
    state = Column(
        Enum(FileState),
        default=FileState.ONLINE,
        server_default=FileState.ONLINE.name,
    )
    # 文件其他信息
    info = Column(Text, default="", server_default="")

class FileLocationsModel(Base):
    """
    文件级抽象，用于对文件的管理，本结构用于记录文件的现在状态
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
    # 文件sha512值
    sha512 = Column(String, nullable=False)
    # 文件md5值
    md5 = Column(String, nullable=False)
    # 文件大小（字节）
    size = Column(Integer)
    # 文件添加时间（只由 DDL 的 DEFAULT 提供，见顶部 NOTE）
    add_time = Column(DateTime, server_default=func.now())
    # 文件当前路径，除去卷路径和**/datas/**过渡路径
    now_path = Column(Text, nullable=False)
    # 文件当前所在的卷
    now_volume = Column(String, ForeignKey("volumes.serial"))
    # 文件状态，如在线、丢失、损坏等
    state = Column(
        Enum(FileState),
        default=FileState.ONLINE,
        server_default=FileState.ONLINE.name,
    )
    # 文件其他信息
    info = Column(Text, default="", server_default="")

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
    # 文件sha512值
    sha512 = Column(String, nullable=False)
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
    # 文件添加时间（只由 DDL 的 DEFAULT 提供，见顶部 NOTE）
    add_time = Column(DateTime, server_default=func.now())

