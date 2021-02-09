from sqlalchemy import Table, ForeignKey, Column

from fallen_london_chronicler.model.base import Base

areas_storylets = Table(
    "areas_storylets",
    Base.metadata,
    Column("area_id", ForeignKey("areas.id"), primary_key=True),
    Column("storylet_id", ForeignKey("storylets.id"), primary_key=True)
)

areas_settings = Table(
    "areas_settings",
    Base.metadata,
    Column("area_id", ForeignKey("areas.id"), primary_key=True),
    Column("setting_id", ForeignKey("settings.id"), primary_key=True)
)

settings_storylets = Table(
    "settings_storylets",
    Base.metadata,
    Column("setting_id", ForeignKey("settings.id"), primary_key=True),
    Column("storylet_id", ForeignKey("storylets.id"), primary_key=True),
)
