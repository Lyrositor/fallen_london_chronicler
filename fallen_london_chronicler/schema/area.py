from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class AreaInfo(BaseModel):
    id: int
    areaKey: Optional[str]
    canChangeOutfit: bool
    canMoveTo: bool
    childAreas: Optional[List[AreaInfo]] = None
    description: Optional[str] = None
    discovered: bool
    hideName: bool
    image: Optional[str] = None
    name: str
    parentAreaKey: Optional[str] = None
    premiumSubRequired: bool
    showOps: bool
    type: str
    unlocked: bool


AreaInfo.update_forward_refs()
