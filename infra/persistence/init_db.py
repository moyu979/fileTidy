# infrastructure/persistence/init_db.py

from .models import Base
from .seed import seed_defaults


def init_database(engine, session_factory=None):
    """
    初始化数据库（建表 + seed）
    """
    Base.metadata.create_all(bind=engine)

    if session_factory:
        session = session_factory()
        try:
            seed_defaults(session)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()