from typing import List, Optional

from pydantic import BaseModel

from fallen_london_chronicler.schema.area import AreaInfo
from fallen_london_chronicler.schema.possessions import CategoryPossessionsInfo
from fallen_london_chronicler.schema.setting import SettingInfo
from fallen_london_chronicler.schema.storylet import StoryletInfo, \
    StoryletBranchOutcomeInfo, StoryletBranchOutcomeMessageInfo, CardInfo


class PossessionsRequest(BaseModel):
    possessions: List[CategoryPossessionsInfo]


class AreaRequest(BaseModel):
    area: AreaInfo
    settingId: Optional[int] = None


class OpportunitiesRequest(BaseModel):
    displayCards: List[CardInfo]
    areaId: int
    settingId: int


class SettingRequest(BaseModel):
    setting: SettingInfo
    areaId: Optional[int] = None


class StoryletListRequest(BaseModel):
    areaId: int
    settingId: int
    storylets: List[StoryletInfo]


class StoryletViewRequest(BaseModel):
    areaId: int
    settingId: int
    inInventory: bool
    isLinkingFromOutcomeObservation: Optional[int] = None
    storylet: StoryletInfo


class StoryletBranchOutcomeRequest(BaseModel):
    areaId: int
    branchId: int
    settingId: int
    endStorylet: Optional[StoryletBranchOutcomeInfo]
    messages: Optional[List[StoryletBranchOutcomeMessageInfo]]
    isLinkingFromOutcomeObservation: Optional[int] = None
    redirect: Optional[StoryletInfo]

