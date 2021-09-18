from __future__ import annotations

import json
from enum import Enum

from sqlalchemy import Integer, Column, Enum as EnumType, ForeignKey, String, \
    Boolean, Text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from fallen_london_chronicler.model.base import Base, GameEntity


class QualityNature(Enum):
    STATUS = "Status"
    THING = "Thing"


class Quality(GameEntity):
    __tablename__ = "qualities"

    name = Column(String(1023), nullable=False)
    description = Column(Text)
    category = Column(String(1023), nullable=False)
    nature = Column(EnumType(QualityNature, length=127), nullable=False)
    storylet_id = Column(Integer, ForeignKey("storylets.id"))
    storylet = relationship("Storylet", back_populates="thing")

    def __repr__(self) -> str:
        return f"<Quality id={self.id} name={self.name}>"


class QualityRequirement(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, nullable=False)
    image = Column(String(127))
    is_cost = Column(Boolean, nullable=False)
    required_quantity_min = Column(Integer)
    required_quantity_max = Column(Integer)
    required_values = Column(Text)
    fallback_text = Column(Text)

    @declared_attr
    def quality_id(self):
        return Column(Integer, ForeignKey("qualities.id"), nullable=False)

    @declared_attr
    def quality(self):
        return relationship("Quality", lazy="selectin")

    @property
    def summary(self):
        min_ = self.required_quantity_min
        max_ = self.required_quantity_max
        if min_ is not None:
            text = f"Unlocked with {self.quality.name}"
            if max_ is not None:
                if min_ == max_:
                    text += f" exactly {min_}"
                else:
                    text += f" {min_} - {max_}"
            elif min_ > 1:
                text += f" {min_}"
        elif max_ is not None:
            text = f"Locked with {self.quality.name}"
            if max_ > 0:
                text += f" higher than {max_}"
        elif self.required_values:
            values = json.loads(self.required_values)
            text = f"{self.quality.name}<ul>"
            for value in values:
                text += f"<li>{value}</li>"
            text += "</ul>"
        else:
            text = self.fallback_text
        return text.replace('"', r'\"')

    def __repr__(self) -> str:
        return \
            f"<{self.__class__.__name__} id={self.id} quality={self.quality}>"


class BranchQualityRequirement(QualityRequirement):
    __tablename__ = "branches_quality_requirements"

    branch_observation_id = Column(
        Integer, ForeignKey("branches_observations.id"), nullable=False
    )
    branch_observation = relationship(
        "BranchObservation", back_populates="quality_requirements"
    )


class StoryletQualityRequirement(QualityRequirement):
    __tablename__ = "storylets_quality_requirements"

    storylet_observation_id = Column(
        Integer, ForeignKey("storylets_observations.id"), nullable=False
    )
    storylet_observation = relationship(
        "StoryletObservation", back_populates="quality_requirements"
    )
