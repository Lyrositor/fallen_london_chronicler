from __future__ import annotations

from typing import Optional, List, Any

from pydantic.main import BaseModel

from fallen_london_chronicler.schema import AreaInfo
from fallen_london_chronicler.schema.misc import ChallengeInfo, QualityRequirementInfo
from fallen_london_chronicler.schema.possessions import PossessionInfo
from fallen_london_chronicler.schema.setting import SettingInfo


class BranchInfo(BaseModel):
    id: int
    actionCost: int
    actionLocked: bool
    buttonText: str
    challenges: List[ChallengeInfo]
    currencyCost: int
    currencyLocked: bool
    description: str
    image: str
    isLocked: bool
    name: str
    ordering: int
    planKey: str
    qualityLocked: bool
    qualityRequirements: List[QualityRequirementInfo]


class StoryletInfo(BaseModel):
    id: int
    canGoBack: Optional[bool] = None
    category: str
    childBranches: Optional[List[BranchInfo]] = None
    description: Optional[str] = None
    distribution: Optional[str] = None
    frequency: Optional[str] = None
    image: str
    isInEventUseTree: Optional[bool] = None
    isLocked: Optional[bool] = None
    name: str
    qualityRequirements: List[QualityRequirementInfo]
    teaser: str
    urgency: Optional[str] = None


class EventInfo(BaseModel):
    id: int
    description: Optional[str] = None
    frequency: Optional[str] = None
    image: str
    isInEventUseTree: Optional[bool] = None
    name: str


class CardInfo(BaseModel):
    category: str
    eventId: int
    image: str
    isAutofire: bool
    name: str
    qualityRequirements: List[QualityRequirementInfo]
    stickiness: str
    teaser: str
    unlockedWithDescription: str


class StoryletBranchOutcomeInfo(BaseModel):
    canGoAgain: bool
    currentActionsRemaining: int
    event: EventInfo
    isDirectLinkingEvent: bool
    isLinkingEvent: bool
    image: str
    maxActionsAllowed: int
    premiumBenefitsApply: bool
    rootEventId: int


class ProgressBarInfo(BaseModel):
    endPercentage: int
    leftScore: int
    rightScore: int
    startPercentage: int


class StoryletBranchOutcomeMessageInfo(BaseModel):
    area: Optional[AreaInfo] = None
    changeType: Optional[str] = None
    image: Optional[str] = None
    isSidebar: Optional[bool] = None
    message: Optional[str] = None
    possession: Optional[PossessionInfo] = None
    priority: Optional[int] = None
    progressBar: Optional[ProgressBarInfo] = None
    setting: Optional[SettingInfo] = None
    tooltip: Optional[str] = None
    type: str
