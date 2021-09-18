import logging
from typing import Tuple, Optional

from fastapi import APIRouter

from fallen_london_chronicler.aggregator import record_area, \
    record_area_storylets, \
    record_storylet, record_outcome, record_setting, record_opportunities, \
    update_user_possessions
from fallen_london_chronicler.auth import authorize
from fallen_london_chronicler.db import get_session
from fallen_london_chronicler.model import OutcomeObservation, User
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
        logging.info(f"{{{user.name}}} Update possessions")
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
        user = authorize(session, area_request.apiKey)
        if not user:
            return SubmitResponse(success=False, error="Invalid API key")
        logging.info(
            f"{{{user.name}}} Submitting area {area_request.area.name} "
            f"({area_request.area.id})"
        )
        user.current_area = record_area(
            session, area_request.area, area_request.settingId
        )
    return SubmitResponse(success=True)


@router.post("/setting")
async def setting(
        setting_request: SettingRequest
) -> SubmitResponse:
    with get_session() as session:
        user = authorize(session, setting_request.apiKey)
        if not user:
            return SubmitResponse(success=False, error="Invalid API key")
        logging.info(
            f"{{{user.name}}} Submitting setting "
            f"{setting_request.setting.name} ({setting_request.setting.id})"
        )
        user.current_setting = record_setting(
            session, setting_request.setting, setting_request.areaId
        )

    return SubmitResponse(success=True)


@router.post("/opportunities")
async def opportunities(
        opportunities_request: OpportunitiesRequest
) -> SubmitResponse:
    with get_session() as session:
        user = authorize(session, opportunities_request.apiKey)
        if not user:
            return SubmitResponse(success=False, error="Invalid API key")
        logging.info(
            f"{{{user.name}}} Submitting opportunities in "
            f"area {opportunities_request.areaId}/"
            f"setting {opportunities_request.settingId}"
        )
        area_id, setting_id = get_location(user, opportunities_request)
        record_opportunities(
            session,
            opportunities_request.displayCards,
            area_id,
            setting_id,
        )
    return SubmitResponse(success=True)


@router.post("/storylet/list")
async def storylet_list(
        storylet_list_request: StoryletListRequest
) -> SubmitResponse:
    with get_session() as session:
        user = authorize(session, storylet_list_request.apiKey)
        if not user:
            return SubmitResponse(success=False, error="Invalid API key")
        area_id, setting_id = get_location(user, storylet_list_request)
        logging.info(
            f"{{{user.name}}} Submitting storylets in "
            f"area {storylet_list_request.areaId}/"
            f"setting {storylet_list_request.settingId}"
        )
        if area_id is None or setting_id is None:
            return SubmitResponse(
                success=False,
                error="Current area ID or setting ID does not match submitted "
                      "area ID or setting ID, refresh page"
            )
        record_area_storylets(
            session, area_id, setting_id, storylet_list_request.storylets
        )
    return SubmitResponse(success=True)


@router.post("/storylet/view")
async def storylet_view(
        storylet_view_request: StoryletViewRequest
) -> SubmitResponse:
    with get_session() as session:
        user = authorize(session, storylet_view_request.apiKey)
        if not user:
            return SubmitResponse(success=False, error="Invalid API key")
        area_id, setting_id = get_location(user, storylet_view_request)
        logging.info(
            f"{{{user.name}}} Submitting storylet "
            f"{storylet_view_request.storylet.name} "
            f"({storylet_view_request.storylet.id}) in "
            f"area {storylet_view_request.areaId}/"
            f"setting {storylet_view_request.settingId}"
        )
        storylet = record_storylet(
            session, storylet_view_request.storylet, area_id, setting_id,
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
        area_id, setting_id = get_location(user, storylet_outcome_request)
        logging.info(
            f"{{{user.name}}} Submitting storylet outcome in "
            f"area {storylet_outcome_request.areaId}/"
            f"setting {storylet_outcome_request.settingId}"
        )
        outcome = record_outcome(
            user=user,
            session=session,
            branch_id=storylet_outcome_request.branchId,
            outcome_info=storylet_outcome_request.endStorylet,
            messages=storylet_outcome_request.messages,
            redirect=storylet_outcome_request.redirect,
            area_id=area_id,
            setting_id=setting_id,
        )
        if storylet_outcome_request.isLinkingFromOutcomeObservation is not None:
            # TODO Test this, does it have the branch ID?
            observation = session.query(OutcomeObservation).get(
                storylet_outcome_request.isLinkingFromOutcomeObservation
            )
            if observation:
                observation.redirect_outcome = outcome
        if outcome.redirect_area_id is not None:
            user.current_area_id = outcome.redirect_area_id
        if outcome.redirect_setting_id is not None:
            user.current_setting_id = outcome.redirect_setting_id
    return OutcomeSubmitResponse(
        success=True,
        outcomeObservationId=outcome.id,
        newAreaId=outcome.redirect_area_id,
        newSettingId=outcome.redirect_setting_id,
    )


def get_location(
        user: User, submit_request
) -> Tuple[Optional[int], Optional[int]]:
    area_id = submit_request.areaId \
        if user.current_area_id == submit_request.areaId else None
    setting_id = submit_request.settingId \
        if user.current_setting_id == submit_request.settingId \
        else None
    return area_id, setting_id
