import uuid

from fastapi import APIRouter
from starlette.requests import Request

from fallen_london_chronicler.aggregator import record_area, \
    record_area_storylets, \
    record_storylet, record_outcome, record_setting, record_opportunities
from fallen_london_chronicler.config import config
from fallen_london_chronicler.db import get_session
from fallen_london_chronicler.model import OutcomeObservation
from fallen_london_chronicler.model.api_key import APIKey
from fallen_london_chronicler.recording import recording_states, RecordingState
from fallen_london_chronicler.schema import SubmitResponse, AreaRequest, \
    StoryletListRequest, StoryletViewRequest, StoryletBranchOutcomeRequest, \
    OutcomeSubmitResponse, PossessionsRequest, SettingRequest
from fallen_london_chronicler.schema.requests import OpportunitiesRequest, \
    SubmitRequest

router = APIRouter()


def authorize(request: SubmitRequest) -> bool:
    if not config.require_api_key:
        return True
    with get_session() as session:
        return bool(session.query(APIKey).get(request.apiKey))


def get_recording_state(request: Request) -> RecordingState:
    recording_id = request.session.get("recording_id", str(uuid.uuid1()))
    request.session["recording_id"] = recording_id
    return recording_states[recording_id]


@router.post("/possessions")
async def possessions(
        possessions_request: PossessionsRequest, request: Request
) -> SubmitResponse:
    if not authorize(possessions_request):
        return SubmitResponse(success=False, error="Invalid API key")
    recording_state = get_recording_state(request)
    recording_state.active = True
    recording_state.update_possessions(
        (
            p for cpi in possessions_request.possessions
            for p in cpi.possessions
        )
    )
    return SubmitResponse(success=True)


@router.post("/area")
async def area(area_request: AreaRequest) -> SubmitResponse:
    if not authorize(area_request):
        return SubmitResponse(success=False, error="Invalid API key")
    with get_session() as session:
        record_area(session, area_request.area, area_request.settingId)
    return SubmitResponse(success=True)


@router.post("/setting")
async def setting(
        setting_request: SettingRequest
) -> SubmitResponse:
    if not authorize(setting_request):
        return SubmitResponse(success=False, error="Invalid API key")
    with get_session() as session:
        record_setting(session, setting_request.setting, setting_request.areaId)
    return SubmitResponse(success=True)


@router.post("/opportunities")
async def opportunities(
        opportunities_request: OpportunitiesRequest
) -> SubmitResponse:
    if not authorize(opportunities_request):
        return SubmitResponse(success=False, error="Invalid API key")
    with get_session() as session:
        record_opportunities(
            session,
            opportunities_request.areaId,
            opportunities_request.settingId,
            opportunities_request.displayCards
        )
    return SubmitResponse(success=True)


@router.post("/storylet/list")
async def storylet_list(
        storylet_list_request: StoryletListRequest
) -> SubmitResponse:
    if not authorize(storylet_list_request):
        return SubmitResponse(success=False, error="Invalid API key")
    with get_session() as session:
        record_area_storylets(
            session,
            storylet_list_request.areaId,
            storylet_list_request.settingId,
            storylet_list_request.storylets
        )
    return SubmitResponse(success=True)


@router.post("/storylet/view")
async def storylet_view(
        storylet_view_request: StoryletViewRequest
) -> SubmitResponse:
    if not authorize(storylet_view_request):
        return SubmitResponse(success=False, error="Invalid API key")
    with get_session() as session:
        storylet = record_storylet(
            session,
            storylet_view_request.areaId,
            storylet_view_request.settingId,
            storylet_view_request.storylet,
        )
        if storylet_view_request.isLinkingFromOutcomeObservation is not None:
            observation = session.query(OutcomeObservation).get(
                storylet_view_request.isLinkingFromOutcomeObservation
            )
            if observation:
                observation.redirect = storylet
    return SubmitResponse(success=True)


@router.post("/storylet/outcome")
async def storylet_outcome(
        storylet_outcome_request: StoryletBranchOutcomeRequest,
        request: Request,
) -> OutcomeSubmitResponse:
    if not authorize(storylet_outcome_request):
        return OutcomeSubmitResponse(success=False, error="Invalid API key")
    with get_session() as session:
        recording_state = get_recording_state(request)
        if not recording_state.active:
            return OutcomeSubmitResponse(
                success=False,
                error="Recording is not active",
            )
        outcome = record_outcome(
            recording_state=recording_state,
            session=session,
            branch_id=storylet_outcome_request.branchId,
            outcome_info=storylet_outcome_request.endStorylet,
            messages=storylet_outcome_request.messages,
            redirect=storylet_outcome_request.redirect,
            area_id=storylet_outcome_request.areaId,
            setting_id=storylet_outcome_request.settingId,
        )
        if not outcome:
            return OutcomeSubmitResponse(
                success=False,
                error="Unknown branch, cannot submit outcome"
            )
        if storylet_outcome_request.isLinkingFromOutcomeObservation is not None:
            # TODO Test this, does it have the branch ID?
            observation = session.query(OutcomeObservation).get(
                storylet_outcome_request.isLinkingFromOutcomeObservation
            )
            if observation:
                observation.redirect_outcome = outcome
    return OutcomeSubmitResponse(
        success=True,
        outcomeObservationId=outcome.id,
        newAreaId=outcome.redirect_area_id,
        newSettingId=outcome.redirect_setting_id,
    )
