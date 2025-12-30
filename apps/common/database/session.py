"""
数据库会话/引擎管理与初始化逻辑。

关于 SQLite 和 DateTime 类型的说明：
SQLite 本身不支持原生的 DATETIME 类型，但 SQLAlchemy 会自动处理：
1. SQLAlchemy 会将 DateTime 类型映射到 SQLite 的 TEXT 类型
2. 存储时自动将 Python datetime 对象转换为 ISO 8601 格式字符串（如 '2024-01-01 12:00:00.000000'）
3. 读取时自动将字符串转换回 Python datetime 对象
4. 这种转换对应用层是透明的，无需手动处理

如果数据库中已有旧格式的时间数据（如时间戳字符串），需要运行数据迁移函数。
"""

# 本文件未经测试
import logging
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from apps.common.config.globalVars import DATABASE_PATH
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from .models import (
    Base,
    DeviceModel,
    VolumeModel,
    SuperVolumeModel,
    DeviceState,
    FileModel,
    CacheModel,
    VolumeStructureModel,
    SuperVolumeStructureModel,
)


logger = logging.getLogger(__name__)

_engine = None
_SessionLocal: Optional[sessionmaker] = None


def _build_database_url(path: str) -> str:
    resolved = Path(path).resolve()
    return f"sqlite:///{resolved.as_posix()}"


def _ensure_defaults(session: Session) -> None:
    """根据新抽象写入默认 Device/Volume/SuperVolume。"""
    now = datetime.utcnow()

    if session.get(DeviceModel, "EXTERNAL_DEVICE") is None:
        session.add(
            DeviceModel(
                serial="EXTERNAL_DEVICE",
                name="EXTERNAL_DEVICE",
                kind="disk",
                add_time=now,
                last_check_time=now,
                state=DeviceState.HEALTHY,
                capacity=0,
                info="用于默认和缺省的类",
            )
        )

    if session.get(VolumeModel, "EXTERNAL_VOLUME") is None:
        session.add(
            VolumeModel(
                id="EXTERNAL_VOLUME",
                name="EXTERNAL_VOLUME",
                kind="single_disk",
                add_time=now,
                last_check_time=now,
                state=DeviceState.HEALTHY,
                capacity=0,
                info="用于默认和缺省的类",
            )
        )

    if session.get(SuperVolumeModel, "EXTERNAL_SUPERVOLUME") is None:
        session.add(
            SuperVolumeModel(
                id="EXTERNAL_SUPERVOLUME",
                name="EXTERNAL_SUPERVOLUME",
                kind="single",
                add_time=now,
                last_check_time=now,
                state=DeviceState.HEALTHY,
                info="用于默认和缺省的类",
            )
        )


def init_database() -> None:
    """初始化数据库并建立 ORM 会话工厂。"""
    global _engine, _SessionLocal

    if _engine is not None and _SessionLocal is not None:
        logger.debug("数据库已初始化，跳过重复初始化")
        return
        
    path = DATABASE_PATH
    logger.info("初始化数据库，路径为%s", path)
    if not path:
        raise ValueError("初始化数据库的路径不能为空")

    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    database_url = _build_database_url(str(db_path))
    _engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)

    Base.metadata.create_all(bind=_engine)


    with session_scope() as session:
        try:
            _ensure_defaults(session)
        except IntegrityError as exc:
            session.rollback()
            logger.error("插入默认数据失败: %s", exc)
            raise


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """提供事务范围的 Session 上下文管理器。"""
    if _SessionLocal is None:
        init_database()

    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Session:
    """获取一个新的 Session 实例，调用方负责关闭。"""
    if _SessionLocal is None:
        init_database()
    return _SessionLocal()


def get_engine():
    if _engine is None:
        init_database()
    return _engine