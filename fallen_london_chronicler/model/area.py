from __future__ import annotations

from enum import Enum

from sqlalchemy import Column, Enum as EnumType, String, Text
from sqlalchemy.orm import relationship

from fallen_london_chronicler.model.base import GameEntity
from fallen_london_chronicler.model.secondaries import areas_storylets, areas_settings


class AreaType(Enum):
    DESTINATION = "Destination"
    DISTRICT = "District"
    LANDMARK = "Landmark"
    LODGINGS = "Lodgings"


class Area(GameEntity):
    __tablename__ = "areas"

    name = Column(String(1023))
    description = Column(Text)
    image = Column(String(1023))
    type = Column(EnumType(AreaType, length=127))
    storylets = relationship(
        "Storylet",
        secondary=areas_storylets,
        back_populates="areas"
    )
    settings = relationship(
        "Setting",
        secondary=areas_settings,
        back_populates="areas"
    )
    outcome_redirects = relationship(
        "OutcomeObservation", back_populates="redirect_area"
    )

    @property
    def url(self) -> str:
        return f"/area/{self.id}"

    def __repr__(self) -> str:
        return f"<Area id={self.id} name={self.name}>"
