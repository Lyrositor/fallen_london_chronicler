from __future__ import annotations

import random
import string
from typing import Optional

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Session
from sqlalchemy.orm.collections import InstrumentedList

from fallen_london_chronicler.model import Base, Quality


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(127), nullable=False)
    api_key = Column(String(127), nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    current_area_id = Column(Integer, ForeignKey("areas.id"))
    current_area = relationship("Area")
    current_setting_id = Column(Integer, ForeignKey("settings.id"))
    current_setting = relationship("Setting")
    possessions: InstrumentedList[UserPossession] = relationship(
        "UserPossession",
        lazy="selectin",
        back_populates="user",
        cascade="all, delete, delete-orphan",
    )

    def get_possession(self, quality_id: int) -> Optional[UserPossession]:
        return next(
            (
                possession
                for possession in self.possessions
                if possession.quality_id == quality_id
            ),
            None
        )

    @staticmethod
    def get_by_api_key(session: Session, api_key: str) -> Optional[User]:
        return session.query(User).filter_by(api_key=api_key).one_or_none()

    @classmethod
    def create(cls, session: Session, name: str, is_admin: bool) -> User:
        while True:
            key = "".join(
                random.choices(string.ascii_letters + string.digits, k=32)
            )
            if not cls.get_by_api_key(session, key):
                break
        # noinspection PyArgumentList
        user = cls(
            name=name,
            api_key=key,
            is_admin=is_admin,
        )
        session.add(user)
        return user


class UserPossession(Base):
    __tablename__ = "users_possessions"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship(User, back_populates="possessions")

    quality_id = Column(Integer, ForeignKey("qualities.id"), nullable=False)
    quality = relationship(Quality, lazy="selectin")

    level = Column(Integer, nullable=False)
    progress_as_percentage = Column(Integer, nullable=False)

    @property
    def cp(self):
        total = 0
        cp_cap = 70 if self.quality.category == "BasicAbility" else 50
        for level in range(1, self.level + 1):
            total += min(level, cp_cap)
        total += round(
            self.progress_as_percentage * min(self.level + 1, cp_cap) / 100
        )
        return total
