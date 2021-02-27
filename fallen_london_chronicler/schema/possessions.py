from typing import List, Any, Optional

from pydantic.main import BaseModel


class EnhancementInfo(BaseModel):
    category: str
    level: int
    qualityId: int
    qualityName: str


class PossessionInfo(BaseModel):
    id: int
    qualityPossessedId: int

    name: str
    description: str
    image: str
    equippable: bool
    category: str
    nature: str
    availableAt: Optional[str] = None

    level: int
    effectiveLevel: int
    himbleLevel: int
    nameAndLevel: str
    levelDescription: Optional[str] = None
    bonusOrPenaltyDisplay: Optional[str] = None
    progressAsPercentage: int
    cap: Optional[int] = None
    useEventId: Optional[int] = None

    enhancements: List[EnhancementInfo]


class CategoryPossessionsInfo(BaseModel):
    appearance: str
    categories: List[str]
    name: str
    possessions: List[PossessionInfo]
