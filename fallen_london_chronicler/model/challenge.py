from __future__ import annotations

from enum import Enum

from sqlalchemy import Integer, Column, Enum as EnumType, ForeignKey, String, \
    Text
from sqlalchemy.orm import relationship

from fallen_london_chronicler.model.base import Base


class ChallengeNature(Enum):
    STATUS = "Status"
    THING = "Thing"


class ChallengeType(Enum):
    CHALLENGE = "Challenge"
    LUCK = "Luck"


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, nullable=False)
    category = Column(String(1023), nullable=False)
    name = Column(String(1023), nullable=False)
    description = Column(Text, nullable=False)
    image = Column(String(1023), nullable=False)
    target = Column(Integer, nullable=False)
    nature = Column(EnumType(ChallengeNature, length=127), nullable=False)
    type = Column(EnumType(ChallengeType, length=127), nullable=False)

    branch_observation_id = Column(
        Integer, ForeignKey("branches_observations.id"), nullable=False
    )
    branch_observation = relationship(
        "BranchObservation", back_populates="challenges"
    )

    def __repr__(self) -> str:
        return f"<Challenge id={self.id} name={self.name}>"
