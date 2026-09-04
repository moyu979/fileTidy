# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 基础设施数据库模块 - 数据库连接与会话管理

# infrastructure/persistence/database.py

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """SQLite 连接后自动开启外键约束。"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


def build_session_factory(database_url: str):
    """
    根据数据库 URL 创建 SQLAlchemy 引擎和会话工厂。

    SQLite 数据库会自动设置 check_same_thread=False。

    Args:
        database_url: 数据库连接 URL

    Returns:
        (SessionLocal, engine) — 会话工厂和引擎实例
    """
    connect_args = {}

    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    engine = create_engine(
        database_url,
        connect_args=connect_args,
    )

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    return SessionLocal, engine

@contextmanager
def session_scope(session_factory):
    """
    提供数据库会话的上下文管理器，自动提交或回滚。

    Args:
        session_factory: 用于创建 SQLAlchemy 会话的工厂函数

    Yields:
        SQLAlchemy 会话对象

    Raises:
        Exception: 会话中发生的异常，会自动触发回滚
    """
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()