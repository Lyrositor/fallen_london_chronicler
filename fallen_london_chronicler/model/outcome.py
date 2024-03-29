from datetime import datetime
from enum import Enum

from sqlalchemy import Column, Enum as EnumType, Integer, DateTime, func, \
    String, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship

from fallen_london_chronicler.model import Base


class OutcomeMessageType(Enum):
    ACTIONS_REFRESHED = "ActionsRefreshedMessage"
    AREA_CHANGE = "AreaChangeMessage"
    DIFFICULTY_ROLL_SUCCESS = "DifficultyRollSuccessMessage"
    DIFFICULTY_ROLL_FAILURE = "DifficultyRollFailureMessage"
    OUTFIT_CHANGEABILITY = "OutfitChangeabilityMessage"
    LIVING_STORY_STARTED = "LivingStoryStartedMessage"
    MAP_SHOULD_UPDATE = "MapShouldUpdateMessage"
    PLAN_COMPLETED_MESSAGE = "PlanCompletedMessage"
    PYRAMID_QUALITY_CHANGE = "PyramidQualityChangeMessage"
    QUALITY_CAP = "QualityCapMessage"
    QUALITY_EXPLICITLY_SET = "QualityExplicitlySetMessage"
    SECOND_CHANCE_RESULT = "SecondChanceResultMessage"
    SETTING_CHANGE = "SettingChangeMessage"
    STANDARD_QUALITY_CHANGE = "StandardQualityChangeMessage"


class OutcomeObservation(Base):
    __tablename__ = "outcome_observations"

    id = Column(Integer, primary_key=True)
    last_modified = Column(
        DateTime, server_default=func.now(), onupdate=datetime.utcnow
    )
    name = Column(String(1023))
    description = Column(Text)
    image = Column(String(1023))
    is_success = Column(Boolean)
    messages = relationship(
        "OutcomeMessage",
        cascade="all, delete, delete-orphan",
        lazy="selectin",
        back_populates="outcome_observation"
    )
    redirect_id = Column(Integer, ForeignKey("storylets.id"))
    redirect = relationship(
        "Storylet", lazy="selectin", back_populates="outcome_redirects"
    )
    redirect_area_id = Column(Integer, ForeignKey("areas.id"))
    redirect_area = relationship(
        "Area", lazy="selectin", back_populates="outcome_redirects"
    )
    redirect_setting_id = Column(Integer, ForeignKey("settings.id"))
    redirect_setting = relationship(
        "Setting", lazy="selectin", back_populates="outcome_redirects"
    )
    redirect_branch_id = Column(Integer, ForeignKey("branches.id"))
    redirect_branch = relationship(
        "Branch",
        lazy="selectin",
        back_populates="outcome_redirects",
        foreign_keys=redirect_branch_id
    )
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    branch = relationship(
        "Branch",
        back_populates="outcome_observations",
        foreign_keys=branch_id
    )

    def __repr__(self) -> str:
        return f"<OutcomeObservation id={self.id} name={self.name}>"


class OutcomeMessage(Base):
    __tablename__ = "outcome_messages"

    id = Column(Integer, primary_key=True)
    type = Column(EnumType(OutcomeMessageType, length=127), nullable=False)
    text = Column(Text, nullable=False)
    image = Column(String(127))
    change = Column(Integer)

    quality_id = Column(Integer, ForeignKey("qualities.id"))
    quality = relationship("Quality", lazy="selectin")
    outcome_observation_id = Column(
        Integer, ForeignKey("outcome_observations.id")
    )
    outcome_observation = relationship(
        "OutcomeObservation", back_populates="messages"
    )

    def __repr__(self) -> str:
        return f"<OutcomeMessage id={self.id} type={self.type.value} text={self.text}>"
