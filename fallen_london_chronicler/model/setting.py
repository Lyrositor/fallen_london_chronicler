from sqlalchemy import String, Column, Boolean
from sqlalchemy.orm import relationship

from fallen_london_chronicler.model.base import GameEntity
from fallen_london_chronicler.model.secondaries import areas_settings, \
    settings_storylets


class Setting(GameEntity):
    __tablename__ = "settings"

    name = Column(String(1023))
    can_change_outfit = Column(Boolean)
    can_travel = Column(Boolean)
    is_infinite_draw = Column(Boolean)
    items_usable_here = Column(Boolean)

    areas = relationship(
        "Area",
        secondary=areas_settings,
        back_populates="settings"
    )
    storylets = relationship(
        "Storylet",
        secondary=settings_storylets,
        back_populates="settings"
    )
    outcome_redirects = relationship(
        "OutcomeObservation", back_populates="redirect_setting"
    )

    def __repr__(self) -> str:
        return f"<Setting id={self.id} name={self.name}>"
