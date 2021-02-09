from __future__ import annotations

from enum import Enum

from sqlalchemy import Integer, Column, Enum as EnumType, ForeignKey, String
from sqlalchemy.orm import relationship

from fallen_london_chronicler.model.base import Base


class ChallengeNature(Enum):
    STATUS = "Status"


class ChallengeType(Enum):
    CHALLENGE = "Challenge"
    LUCK = "Luck"


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    image = Column(String, nullable=False)
    target = Column(Integer, nullable=False)
    nature = Column(EnumType(ChallengeNature), nullable=False)
    type = Column(EnumType(ChallengeType), nullable=False)

    branch_observation_id = Column(
        Integer, ForeignKey("branches_observations.id"), nullable=False
    )
    branch_observation = relationship(
        "BranchObservation", back_populates="challenges"
    )
