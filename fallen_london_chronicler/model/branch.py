from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import Integer, Column, ForeignKey, String, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import InstrumentedList

from fallen_london_chronicler.model.base import Base, GameEntity
from fallen_london_chronicler.model.outcome import OutcomeObservation
from fallen_london_chronicler.model.utils import latest_observation_property


class Branch(GameEntity):
    __tablename__ = "branches"

    action_cost = Column(Integer, default=0)
    button_text = Column(String(1023), default="Go")
    image = Column(String(1023), nullable=False)
    ordering = Column(Integer, default=0)

    observations: InstrumentedList[BranchObservation] = relationship(
        "BranchObservation",
        back_populates="branch",
        lazy="selectin",
        cascade="all, delete, delete-orphan",
        order_by="desc(BranchObservation.last_modified)",
    )
    outcome_observations: InstrumentedList[OutcomeObservation] = relationship(
        "OutcomeObservation",
        back_populates="branch",
        lazy="selectin",
        cascade="all, delete, delete-orphan",
        order_by="desc(OutcomeObservation.last_modified)",
        foreign_keys="OutcomeObservation.branch_id"
    )
    storylet_id = Column(Integer, ForeignKey("storylets.id"))
    storylet = relationship("Storylet", back_populates="branches")
    outcome_redirects = relationship(
        "OutcomeObservation",
        back_populates="redirect_branch",
        foreign_keys="OutcomeObservation.redirect_branch_id"
    )

    def url(self, area_id: int) -> str:
        return f"/branch/{area_id}/{self.id}"

    @property
    def name(self) -> str:
        return latest_observation_property(self.observations, "name")

    @property
    def description(self) -> str:
        return latest_observation_property(self.observations, "description")

    @property
    def challenges(self) -> str:
        return latest_observation_property(self.observations, "challenges")

    @property
    def quality_requirements(self) -> List:
        return latest_observation_property(
            self.observations, "quality_requirements"
        )


class BranchObservation(Base):
    __tablename__ = "branches_observations"

    id = Column(Integer, primary_key=True)
    last_modified = Column(
        DateTime, server_default=func.now(), onupdate=datetime.utcnow
    )
    name = Column(String(1023), nullable=False)
    description = Column(String(65535), nullable=False)
    currency_cost = Column(Integer, nullable=False)

    challenges = relationship(
        "Challenge",
        cascade="all, delete, delete-orphan",
        lazy="selectin",
        back_populates="branch_observation"
    )
    quality_requirements = relationship(
        "BranchQualityRequirement",
        cascade="all, delete, delete-orphan",
        lazy="selectin",
        back_populates="branch_observation"
    )
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    branch = relationship("Branch", back_populates="observations")
