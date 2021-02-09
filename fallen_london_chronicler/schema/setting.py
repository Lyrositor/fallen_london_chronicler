from pydantic.main import BaseModel


class SettingInfo(BaseModel):
    canChangeOutfit: bool
    canTravel: bool
    id: int
    isInfiniteDraw: bool
    itemsUsableHere: bool
    name: str
