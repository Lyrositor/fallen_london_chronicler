from __future__ import annotations

from enum import Enum

from sqlalchemy import Column, Enum as EnumType, String
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

    name = Column(String)
    description = Column(String)
    image = Column(String)
    type = Column(EnumType(AreaType))
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
    def url(self):
        return f"/area/{self.id}"
