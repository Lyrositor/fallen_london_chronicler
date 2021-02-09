from contextlib import contextmanager
from typing import ContextManager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as BaseSession

from fallen_london_chronicler.config import config

engine = create_engine(config.db_url)
Session = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def get_session() -> ContextManager[BaseSession]:
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as ex:
        session.rollback()
        raise ex
    finally:
        session.close()
