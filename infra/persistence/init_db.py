# CHECK: 待检查 - 基础设施数据库初始化 - 建表与初始设置

# infrastructure/persistence/init_db.py

from .models import Base
from .defaults import ensure_defaults


def init_database(engine, session_factory=None):
    """
    初始化数据库（建表 + 填充默认数据）。

    Args:
        engine: SQLAlchemy 引擎实例
        session_factory: 可选，用于创建会话以执行默认数据填充

    Raises:
        Exception: 默认数据填充过程中发生的异常，会自动回滚
    """
    Base.metadata.create_all(bind=engine)

    if session_factory:
        session = session_factory()
        try:
            ensure_defaults(session)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()