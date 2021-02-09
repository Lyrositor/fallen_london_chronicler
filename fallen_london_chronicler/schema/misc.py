from pydantic import BaseModel


class QualityRequirementInfo(BaseModel):
    id: int
    category: str
    image: str
    isCost: bool
    nature: str
    qualityId: int
    qualityName: str
    status: str
    tooltip: str


class ChallengeInfo(BaseModel):
    id: int
    canAffordSecondChance: bool
    category: str
    description: str
    image: str
    name: str
    nature: str
    secondChanceId: int
    secondChanceLevel: int
    targetNumber: int
    type: str
