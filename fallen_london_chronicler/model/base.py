from typing import TypeVar, Type, Optional, Any

from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()


T = TypeVar("T", bound="GameEntity")


class GameEntity(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True)

    @classmethod
    def get(
            cls: Type[T], session: Session, entity_id: int
    ) -> Optional[T]:
        return session.query(cls).get(entity_id)

    @classmethod
    def get_or_create(
            cls: Type[T], session: Session, entity_id: int
    ) -> Optional[T]:
        obj = cls.get(session, entity_id)
        if not obj:
            obj = cls(id=entity_id)
            session.add(obj)
        return obj
