from typing import List, Optional

from pydantic import BaseModel

from fallen_london_chronicler.schema.area import AreaInfo
from fallen_london_chronicler.schema.possessions import CategoryPossessionsInfo
from fallen_london_chronicler.schema.setting import SettingInfo
from fallen_london_chronicler.schema.storylet import StoryletInfo, \
    StoryletBranchOutcomeInfo, StoryletBranchOutcomeMessageInfo, CardInfo


class SubmitRequest(BaseModel):
    apiKey: Optional[str] = None


class PossessionsRequest(SubmitRequest):
    possessions: List[CategoryPossessionsInfo]


class AreaRequest(SubmitRequest):
    area: AreaInfo
    settingId: Optional[int] = None


class OpportunitiesRequest(SubmitRequest):
    displayCards: List[CardInfo]
    areaId: int
    settingId: int


class SettingRequest(SubmitRequest):
    setting: SettingInfo
    areaId: Optional[int] = None


class StoryletListRequest(SubmitRequest):
    areaId: int
    settingId: int
    storylets: List[StoryletInfo]


class StoryletViewRequest(SubmitRequest):
    areaId: int
    settingId: int
    inInventory: bool
    isLinkingFromOutcomeObservation: Optional[int] = None
    storylet: StoryletInfo


class StoryletBranchOutcomeRequest(SubmitRequest):
    areaId: int
    branchId: int
    settingId: int
    endStorylet: Optional[StoryletBranchOutcomeInfo]
    messages: Optional[List[StoryletBranchOutcomeMessageInfo]]
    isLinkingFromOutcomeObservation: Optional[int] = None
    redirect: Optional[StoryletInfo]

