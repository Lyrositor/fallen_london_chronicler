from typing import Optional

from pydantic.main import BaseModel


class SubmitResponse(BaseModel):
    success: bool
    error: Optional[str] = None


class OutcomeSubmitResponse(SubmitResponse):
    outcomeObservationId: Optional[int] = None
    newAreaId: Optional[int] = None
    newSettingId: Optional[int] = None
