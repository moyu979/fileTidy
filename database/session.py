"""
数据库会话/引擎管理与初始化逻辑。
"""

# 本文件未经测试
import logging
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from utils.confs import get_conf_manager
from .models import Base, DeviceModel, VolumeModel, SuperVolumeModel


logger = logging.getLogger(__name__)


_engine = None
_SessionLocal: Optional[sessionmaker] = None


def _build_database_url(path: str) -> str:
    resolved = Path(path).resolve()
    return f"sqlite:///{resolved.as_posix()}"


def _ensure_defaults(session: Session) -> None:
    """根据新抽象写入默认 Device/Volume/SuperVolume。"""
    now = str(int(time.time()))

    default_device_id = "0"
    if session.get(DeviceModel, default_device_id) is None:
        session.add(
            DeviceModel(
                id=default_device_id,
                name="default",
                kind="disk",
                add_time=now,
                last_check_time=now,
                state="healthy",
                capacity=0,
                info="用于默认和缺省的类",
            )
        )

    if session.get(VolumeModel, 0) is None:
        session.add(
            VolumeModel(
                id=0,
                name="default",
                kind="single",
                add_time=now,
                last_check_time=now,
                state="healthy",
                capacity=0,
                info="用于默认和缺省的类",
            )
        )

    if session.get(SuperVolumeModel, 0) is None:
        session.add(
            SuperVolumeModel(
                id=0,
                name="default",
                kind="single",
                add_time=now,
                last_check_time=now,
                state="healthy",
                capacity=0,
                info="用于默认和缺省的类",
            )
        )


def init_database() -> None:
    """初始化数据库并建立 ORM 会话工厂。"""
    global _engine, _SessionLocal

    if _engine is not None and _SessionLocal is not None:
        logger.debug("数据库已初始化，跳过重复初始化")
        return
        
    path = get_conf_manager().get("path")
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


