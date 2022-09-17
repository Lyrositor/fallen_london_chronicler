from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List

from sqlalchemy import Integer, Column, Enum as EnumType, ForeignKey, Boolean, \
    String, DateTime, func, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import InstrumentedList

from fallen_london_chronicler.model.base import Base, GameEntity
from fallen_london_chronicler.model.secondaries import areas_storylets, \
    settings_storylets
from fallen_london_chronicler.model.utils import latest_observation_property

storylets_order = Table(
    "storylets_order",
    Base.metadata,
    Column("before_id", ForeignKey("storylets.id"), primary_key=True),
    Column("after_id", ForeignKey("storylets.id"), primary_key=True)
)


class StoryletCategory(Enum):
    AMBITION = "Ambition"
    BLUE = "Blue"
    EPISODIC = "Episodic"
    FANCY = "Fancy"
    GOLD = "Gold"
    ITEM_USE = "ItemUse"
    LIVING_WORLD = "LivingWorld"
    ONGOING = "Ongoing"
    QUESTICLE_START = "QuesticleStart"
    QUESTICLE_STEP = "QuesticleStep"
    PREMIUM = "Premium"
    SEASONAL = "Seasonal"
    SINISTER = "Sinister"
    TRAVEL = "Travel"
    UNSPECIALIZED = "Unspecialised"


class StoryletDistribution(Enum):
    ABUNDANT = "Abundant"
    FREQUENT = "Frequent"
    INFREQUENT = "Infrequent"
    RARE = "Rare"
    STANDARD = "Standard"
    UBIQUITOUS = "Ubiquitous"
    UNUSUAL = "Unusual"
    VERY_INFREQUENT = "VeryInfrequent"
    ZERO = "0"


class StoryletFrequency(Enum):
    ALWAYS = "Always"
    SOMETIMES = "Sometimes"


class StoryletUrgency(Enum):
    NORMAL = "Normal"
    HIGH = "High"
    MUST = "Must"


class StoryletStickiness(Enum):
    DISCARDABLE = "Discardable"
    STICKY = "Sticky"


class Storylet(GameEntity):
    __tablename__ = "storylets"

    can_go_back = Column(Boolean)
    category = Column(EnumType(StoryletCategory, length=127))
    distribution = Column(EnumType(StoryletDistribution, length=127))
    frequency = Column(EnumType(StoryletFrequency, length=127))
    stickiness = Column(EnumType(StoryletStickiness, length=127))
    image = Column(String(1023))
    urgency = Column(EnumType(StoryletUrgency, length=127))
    is_autofire = Column(Boolean, default=False)
    is_card = Column(Boolean, default=False)
    is_top_level = Column(Boolean, default=False)

    observations: InstrumentedList[StoryletObservation] = relationship(
        "StoryletObservation",
        back_populates="storylet",
        cascade="all, delete, delete-orphan",
        lazy="selectin",
        order_by="desc(StoryletObservation.last_modified)"
    )
    outcome_redirects = relationship(
        "OutcomeObservation", back_populates="redirect"
    )
    areas = relationship(
        "Area", secondary=areas_storylets, back_populates="storylets"
    )
    settings = relationship(
        "Setting", secondary=settings_storylets, back_populates="storylets"
    )
    branches = relationship(
        "Branch", back_populates="storylet", order_by="desc(Branch.ordering)"
    )
    thing = relationship(
        "Quality", back_populates="storylet", uselist=False
    )

    before = relationship(
        "Storylet",
        secondary=storylets_order,
        primaryjoin="storylets_order.c.after_id == Storylet.id",
        secondaryjoin="storylets_order.c.before_id == Storylet.id",
        backref="after"
    )

    def url(self, area_id: int) -> str:
        return f"/storylet/{area_id}/{self.id}"

    @property
    def color(self) -> str:
        if self.category == StoryletCategory.SINISTER:
            return "black"
        elif self.category in (
                StoryletCategory.GOLD,
                StoryletCategory.PREMIUM
        ):
            return "gold"
        elif self.category in (
                StoryletCategory.AMBITION, StoryletCategory.SEASONAL
        ):
            return "silver"
        elif self.category in (
                StoryletCategory.QUESTICLE_START,
                StoryletCategory.QUESTICLE_STEP,
                StoryletCategory.EPISODIC,
                StoryletCategory.ONGOING
        ):
            return "bronze"
        elif self.category in (StoryletCategory.LIVING_WORLD,):
            return "green"
        elif self.category in (StoryletCategory.BLUE,):
            return "blue"
        elif self.category == StoryletCategory.FANCY:
            return "purple"
        return "white"

    @property
    def name(self) -> str:
        return latest_observation_property(self.observations, "name")

    @property
    def teaser(self) -> str:
        return latest_observation_property(self.observations, "teaser")

    @property
    def description(self) -> str:
        return latest_observation_property(self.observations, "description")

    @property
    def quality_requirements(self) -> List:
        return latest_observation_property(
            self.observations, "quality_requirements"
        )

    def __repr__(self) -> str:
        return f"<Storylet id={self.id} name={self.name}>"


class StoryletObservation(Base):
    __tablename__ = "storylets_observations"

    id = Column(Integer, primary_key=True)
    last_modified = Column(
        DateTime, server_default=func.now(), onupdate=datetime.utcnow
    )
    name = Column(String(1023))
    description = Column(Text)
    teaser = Column(Text)

    quality_requirements = relationship(
        "StoryletQualityRequirement",
        cascade="all, delete, delete-orphan",
        lazy="selectin",
        back_populates="storylet_observation"
    )
    storylet_id = Column(Integer, ForeignKey("storylets.id"))
    storylet = relationship("Storylet", back_populates="observations")

    def __repr__(self) -> str:
        quality_requirements = ", ".join(
            str(qr) for qr in self.quality_requirements
        )
        return (
            f"<StoryletObservation id={self.id} name={self.name} "
            f"quality_requirements=[{quality_requirements}]>")
