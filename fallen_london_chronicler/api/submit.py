
from fastapi import APIRouter

from fallen_london_chronicler.aggregator import record_area, \
    record_area_storylets, \
    record_storylet, record_outcome, record_setting, record_opportunities, \
    update_user_possessions
from fallen_london_chronicler.auth import authorize
from fallen_london_chronicler.db import get_session
from fallen_london_chronicler.model import OutcomeObservation
from fallen_london_chronicler.schema import SubmitResponse, AreaRequest, \
    StoryletListRequest, StoryletViewRequest, StoryletBranchOutcomeRequest, \
    OutcomeSubmitResponse, PossessionsRequest, SettingRequest
from fallen_london_chronicler.schema.requests import OpportunitiesRequest

router = APIRouter()


@router.post("/possessions")
async def possessions(
        possessions_request: PossessionsRequest
) -> SubmitResponse:
    with get_session() as session:
        user = authorize(session, possessions_request.apiKey)
        if not user:
            return SubmitResponse(success=False, error="Invalid API key")
        update_user_possessions(
            session,
            user,
            (
                p for cpi in possessions_request.possessions
                for p in cpi.possessions
            ))
    return SubmitResponse(success=True)


@router.post("/area")
async def area(area_request: AreaRequest) -> SubmitResponse:
    with get_session() as session:
        if not authorize(session, area_request.apiKey):
            return SubmitResponse(success=False, error="Invalid API key")
        record_area(session, area_request.area, area_request.settingId)
    return SubmitResponse(success=True)


@router.post("/setting")
async def setting(
        setting_request: SettingRequest
) -> SubmitResponse:
    with get_session() as session:
        if not authorize(session, setting_request.apiKey):
            return SubmitResponse(success=False, error="Invalid API key")
        record_setting(session, setting_request.setting, setting_request.areaId)
    return SubmitResponse(success=True)


@router.post("/opportunities")
async def opportunities(
        opportunities_request: OpportunitiesRequest
) -> SubmitResponse:
    with get_session() as session:
        if not authorize(session, opportunities_request.apiKey):
            return SubmitResponse(success=False, error="Invalid API key")
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
    with get_session() as session:
        if not authorize(session, storylet_list_request.apiKey):
            return SubmitResponse(success=False, error="Invalid API key")
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
    with get_session() as session:
        if not authorize(session, storylet_view_request.apiKey):
            return SubmitResponse(success=False, error="Invalid API key")
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
) -> OutcomeSubmitResponse:
    with get_session() as session:
        user = authorize(session, storylet_outcome_request.apiKey)
        if not user:
            return OutcomeSubmitResponse(success=False, error="Invalid API key")
        outcome = record_outcome(
            user=user,
            session=session,
            branch_id=storylet_outcome_request.branchId,
            outcome_info=storylet_outcome_request.endStorylet,
            messages=storylet_outcome_request.messages,
            redirect=storylet_outcome_request.redirect,
            area_id=storylet_outcome_request.areaId,
            setting_id=storylet_outcome_request.settingId,
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
