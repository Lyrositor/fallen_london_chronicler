import json
import logging
import re
from typing import Iterable, List, Optional, Type, TypeVar

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from fallen_london_chronicler.images import get_or_cache_image, ImageType
from fallen_london_chronicler.model import Area, AreaType, Storylet, \
    StoryletCategory, StoryletObservation, StoryletDistribution, \
    StoryletFrequency, StoryletUrgency, Branch, BranchObservation, Challenge, \
    ChallengeNature, ChallengeType, \
    record_observation, Quality, QualityNature, \
    BranchQualityRequirement, OutcomeObservation, OutcomeMessage, \
    OutcomeMessageType, QualityRequirement, StoryletQualityRequirement, Setting
from fallen_london_chronicler.model.storylet import StoryletStickiness
from fallen_london_chronicler.model.utils import pairwise
from fallen_london_chronicler.recording import RecordingState
from fallen_london_chronicler.schema import StoryletInfo, AreaInfo, BranchInfo, \
    ChallengeInfo, QualityRequirementInfo, StoryletBranchOutcomeInfo, \
    StoryletBranchOutcomeMessageInfo
from fallen_london_chronicler.schema.setting import SettingInfo
from fallen_london_chronicler.schema.storylet import CardInfo
from fallen_london_chronicler.utils import match_any

TOOLTIPS_NONE = (
    re.compile(
        r"^You unlocked this by not having any "
        r"<span class='quality-name'>(?P<quality>.+)</span>$"
    ),
    re.compile(
        r"^You can't do this when you have "
        r"<span class='quality-name'>(?P<quality>.+)</span>$"
    ),
    re.compile(
        r"^Unlocked when you do not have "
        r"<span class='quality-name'>(?P<quality>.+)</span>$"
    ),
    re.compile(
        r"^You unlocked this by having no "
        r"<span class='quality-name'>(?P<quality>.+)</span>$"
    )
)
TOOLTIPS_AT_LEAST_ONE = (
    re.compile(
        r"^You need (?:an? )?<span class='quality-name'>(?P<quality>.+)</span>$"
    ),
    re.compile(
        r"^Unlocked when you have <span class='quality-name'>(?P<quality>.+)"
        r"</span>$"
    ),
    re.compile(
        r"^You need to be <span class='quality-name'>(?P<quality>.+)</span> "
        r"someone$"
    ),
    re.compile(
        r"^You unlocked this with (?:an? )?"
        r"<span class='quality-name'>(?P<quality>.+)</span> "
        r"<em>\(you have (?P<current>\d+) in all\)</em>$"
    ),
    re.compile(
        r"^You can't do this when you have any "
        r"<span class='quality-name'>(?P<quality>.+)</span>$"
    ),
    re.compile(r"^You must be (?P<quality>.+)\.$"),
    re.compile(r"^This is unlocked because you have the (?P<quality>.+)\.$")
)
TOOLTIPS_MINIMUM = (
    re.compile(
        r"^You unlocked this with "
        r"<span class='quality-name'>(?P<quality>.+)</span> (?P<current>\d+) "
        r"<em>\(you needed (?P<quantity_min>\d+)\)</em>$"
    ),
    re.compile(
        r"^You unlocked this with (?P<current>\d+) "
        r"<span class='quality-name'>(?P<quality>.+)</span> "
        r"<em>\(you needed (?P<quantity_min>\d+)\)</em>$"
    ),
    re.compile(
        r"^You need <span class='quality-name'>(?P<quality>.+)</span> "
        r"(?P<quantity_min>\d+)<em> \(you have (?P<current>\d+)\)</em>$"
    ),
    re.compile(
        r"^You need (?P<quantity_min>\d+) "
        r"<span class='quality-name'>(?P<quality>.+)</span> "
        r"<em>\(you have (?P<current>\d+)\)</em>$"
    ),
    re.compile(
        r"^You need (?P<quantity_min>\d+) "
        r"<span class='quality-name'>(?P<quality>.+)</span>$"
    ),
    re.compile(
        r"^You need <span class='quality-name'>(?P<quality>.+)</span> "
        r"(?P<quantity_min>\d+)$"
    ),
)
TOOLTIPS_MAXIMUM = (
    re.compile(
        r"^You can't do this when you have <span class='quality-name'>"
        r"(?P<quality>.+)</span> higher than (?P<quantity_max>\d+)"
        r"<em> \(you have (?P<current>\d+)\)</em>$"
    ),
    re.compile(
        r"^You unlocked this with "
        r"<span class='quality-name'>(?P<quality>.+)</span> (?P<current>\d+) "
        r"<em>\(you needed (?P<quantity_max>\d+) at most\)</em>$"
    ),

    re.compile(
        r"^You unlocked this by not having "
        r"<span class='quality-name'>(?P<quality>.+)</span> "
        r"<em>\(you needed (?P<quantity_max>\d+) at most\)</em>$"
    )
)
TOOLTIPS_EXACTLY = (
    re.compile(
        r"^You unlocked this with "
        r"<span class='quality-name'>(?P<quality>.+)</span> (?P<current>\d+)"
        r"<em> \(you needed exactly (?P<quantity>\d+)\)</em>$"
    ),
    re.compile(
        r"^You need exactly "
        r"<span class='quality-name'>(?P<quality>.+)</span> (?P<quantity>\d+)"
        r"<em> \(you have (?P<current>\d+)\)</em>$"
    ),
    re.compile(
        r"^You need <span class='quality-name'>(?P<quality>.+)</span> "
        r"exactly (?P<quantity>\d+)$"
    )
)
TOOLTIPS_RANGE = (
    re.compile(
        r"^You unlocked this with "
        r"<span class='quality-name'>(?P<quality>.+)</span> (?P<current>\d+)"
        r"<em> \(you needed (?P<quantity_min>\d+)-(?P<quantity_max>\d+)\)</em>$"
    ),
    re.compile(
        r"^You need <span class='quality-name'>(?P<quality>.+)</span> "
        r"(?P<quantity_min>\d+)-(?P<quantity_max>\d+)"
        r"(?:<em> \(you have (?P<current>\d+)\)</em>)?$"
    )
)
TOOLTIPS_WORDY = (
    re.compile(
        r"^Unlocked when <span class='quality-name'>(?P<quality>.+)</span> is:"
        r"<ul class='wordy-list'>(?P<requirements>.+)</ul>$"
    ),
)
TOOLTIPS_WORDY_ITEM = re.compile(
    r"<li(?: class='current')?>(?:<em>)?(.*?)(?:</em>)?</li>"
)

QUALITY_GAIN = (
    re.compile(
        r"^You've gained (?P<quantity>\d+) x (?P<quality>.+?)"
        r"(?: \(new total (?P<new_state>.+)\))?\.$"
    ),
    re.compile(r"^You now have (?P<quantity>\d+) x (?P<quality>.+)\.$"),
    re.compile(r"^You've gained (?P<quantity>\d+) x (?P<quality>.+)\.$"),
)
QUALITY_LOSS = (
    re.compile(
        r"^You've lost (?P<quantity>\d+) x (?P<quality>.+?)"
        r"(?: \(new total (?P<new_state>.+)\))?\.$"
    ),
)

QUALITY_SET_ZERO = (
    re.compile(r"^Your '(?P<quality>.+)' Quality has gone!$"),
    re.compile(
        r"^'(?P<quality>.+)' has been reset: a conclusion, or a "
        r"new beginning\?$"
    )
)
QUALITY_SET_TO = (
    re.compile(
        r"^An occurrence! Your '(?P<quality>.+)' Quality "
        r"is now (?P<quantity>\d+)!$"
    ),
)

T = TypeVar("T", bound=QualityRequirement)


def record_area(
        session: Session,
        area_info: AreaInfo,
        setting_id: Optional[int] = None
) -> Area:
    area = Area.get_or_create(session, area_info.id)
    area.name = area_info.name
    area.description = fix_html(area_info.description)
    area.image = get_or_cache_image(ImageType.HEADER, area_info.image)
    area.type = AreaType(area_info.type)
    if setting_id is not None:
        setting = Setting.get_or_create(session, setting_id)
        if setting not in area.settings:
            area.settings.append(setting)
    return area


def record_setting(
        session: Session,
        setting_info: SettingInfo,
        area_id: Optional[int] = None
) -> Setting:
    setting = Setting.get_or_create(session, setting_info.id)
    setting.name = setting_info.name
    setting.can_change_outfit = setting_info.canChangeOutfit
    setting.can_travel = setting_info.canTravel
    setting.is_infinite_draw = setting_info.isInfiniteDraw
    setting.items_usable_here = setting_info.itemsUsableHere
    if area_id is not None:
        area = Area.get_or_create(session, area_id)
        if area not in setting.areas:
            setting.areas.append(area)
    return setting


def record_opportunities(
        session: Session,
        area_id: int,
        setting_id: int,
        cards_info: Iterable[CardInfo]
) -> List[Storylet]:
    return [
        record_card(session, area_id, setting_id, card_info)
        for card_info in cards_info
    ]


def record_area_storylets(
        session: Session,
        area_id: int,
        setting_id: int,
        storylets_info: Iterable[StoryletInfo]
) -> List[Storylet]:
    storylets = [
        record_storylet(session, area_id, setting_id, storylet_info)
        for storylet_info in storylets_info
    ]
    for storylet in storylets:
        storylet.is_top_level = True

    # Create ordered pairs to enable a sorted display - we don't know what the
    # actual, total order is since we don't have access to every storylet that
    # could appear in the area, so let's just create pairwise associations
    for before, after in pairwise(storylets):
        if after in before.before:
            before.before.remove(after)
        if after not in before.after:
            before.after.append(after)

    return storylets


def record_storylet(
        session: Session,
        area_id: int,
        setting_id: int,
        storylet_info: StoryletInfo,
) -> Storylet:
    storylet = Storylet.get_or_create(session, storylet_info.id)
    if storylet_info.canGoBack is not None:
        storylet.can_go_back = storylet_info.canGoBack
    if storylet_info.distribution is not None:
        storylet.distribution = StoryletDistribution(
            str(storylet_info.distribution)
        )
    if storylet_info.frequency is not None:
        storylet.frequency = StoryletFrequency(storylet_info.frequency)
    if storylet_info.urgency is not None:
        storylet.urgency = StoryletUrgency(storylet_info.urgency)
    storylet.category = StoryletCategory(storylet_info.category)
    storylet.image = get_or_cache_image(ImageType.ICON, storylet_info.image)
    record_observation(
        storylet.observations,
        StoryletObservation,
        name=storylet_info.name,
        description=fix_html(storylet_info.description),
        teaser=fix_html(storylet_info.teaser),
        quality_requirements=[
            record_quality_requirement(
                session, StoryletQualityRequirement, quality_requirement_info
            )
            for quality_requirement_info in storylet_info.qualityRequirements
        ],
    )
    if storylet_info.childBranches is not None:
        for branch_info in storylet_info.childBranches:
            storylet.branches.append(record_branch(session, branch_info))

    area = Area.get_or_create(session, area_id)
    area.storylets.append(storylet)
    setting = Setting.get_or_create(session, setting_id)
    setting.storylets.append(storylet)

    return storylet


def record_card(
        session: Session, area_id: int, setting_id: int, card_info: CardInfo
) -> Storylet:
    storylet = Storylet.get_or_create(session, card_info.eventId)
    storylet.category = StoryletCategory(card_info.category)
    storylet.image = get_or_cache_image(ImageType.ICON, card_info.image)
    storylet.is_card = True
    storylet.is_autofire = card_info.isAutofire
    storylet.stickiness = StoryletStickiness(card_info.stickiness)
    record_observation(
        storylet.observations,
        StoryletObservation,
        name=card_info.name,
        teaser=fix_html(card_info.teaser),
        quality_requirements=[
            record_quality_requirement(
                session, StoryletQualityRequirement, quality_requirement_info
            )
            for quality_requirement_info in card_info.qualityRequirements
        ],
    )

    area = Area.get_or_create(session, area_id)
    area.storylets.append(storylet)
    setting = Setting.get_or_create(session, setting_id)
    setting.storylets.append(storylet)
    return storylet


def record_branch(session: Session, branch_info: BranchInfo) -> Branch:
    branch = Branch.get_or_create(session, branch_info.id)
    branch.action_cost = branch_info.actionCost
    branch.button_text = branch_info.buttonText
    branch.image = get_or_cache_image(ImageType.ICON, branch_info.image)
    branch.ordering = branch_info.ordering
    record_observation(
        branch.observations,
        BranchObservation,
        currency_cost=branch_info.currencyCost,
        description=fix_html(branch_info.description),
        name=branch_info.name,
        challenges=[
            record_challenge(challenge_info)
            for challenge_info in branch_info.challenges
        ],
        quality_requirements=[
            record_quality_requirement(
                session, BranchQualityRequirement, quality_requirement_info
            )
            for quality_requirement_info in branch_info.qualityRequirements
        ],
    )
    return branch


def record_challenge(challenge_info: ChallengeInfo) -> Challenge:
    challenge = Challenge()
    challenge.game_id = challenge_info.id
    challenge.category = challenge_info.category
    challenge.name = challenge_info.name
    challenge.description = fix_html(challenge_info.description)
    challenge.image = get_or_cache_image(
        ImageType.ICON_SMALL, challenge_info.image
    )
    challenge.target = challenge_info.targetNumber
    challenge.nature = ChallengeNature(challenge_info.nature)
    challenge.type = ChallengeType(challenge_info.type)
    return challenge


def record_quality_requirement(
        session: Session,
        cls: Type[T],
        quality_requirement_info: QualityRequirementInfo
) -> T:
    quality_requirement = cls()
    quality_requirement.game_id = quality_requirement_info.id
    quality_requirement.image = get_or_cache_image(
        ImageType.ICON_SMALL, quality_requirement_info.image
    )
    quality_requirement.is_cost = quality_requirement_info.isCost

    # Copy the quality ID for diffing purposes
    quality_requirement.quality = record_quality(
        session,
        game_id=quality_requirement_info.qualityId,
        name=quality_requirement_info.qualityName,
        category=quality_requirement_info.category,
        nature=quality_requirement_info.nature
    )
    quality_requirement.quality_id = quality_requirement.quality.id

    quantity_min = quantity_max = required_values = None
    tooltip = quality_requirement_info.tooltip
    if match_any(TOOLTIPS_NONE, quality_requirement_info.tooltip):
        quantity_max = 0
    elif match_any(TOOLTIPS_AT_LEAST_ONE, quality_requirement_info.tooltip):
        quantity_min = 1
    elif match := match_any(TOOLTIPS_MINIMUM, quality_requirement_info.tooltip):
        quantity_min = int(match.group("quantity_min"))
    elif match := match_any(TOOLTIPS_MAXIMUM, quality_requirement_info.tooltip):
        quantity_max = int(match.group("quantity_max"))
    elif match := match_any(TOOLTIPS_EXACTLY, quality_requirement_info.tooltip):
        quantity_min = quantity_max = int(match.group("quantity"))
    elif match := match_any(TOOLTIPS_RANGE, quality_requirement_info.tooltip):
        quantity_min = int(match.group("quantity_min"))
        quantity_max = int(match.group("quantity_max"))
    elif match := match_any(TOOLTIPS_WORDY, quality_requirement_info.tooltip):
        required_values = [
            req.replace(r'\"', '"')
            for req in TOOLTIPS_WORDY_ITEM.findall(match.group("requirements"))
        ]
    else:
        logging.error(f"Unknown tooltip: {tooltip}")
        quality_requirement.fallback_text = fix_html(tooltip)

    quality_requirement.required_quantity_min = quantity_min
    quality_requirement.required_quantity_max = quantity_max
    quality_requirement.required_values = json.dumps(required_values) \
        if required_values else None

    return quality_requirement


def record_quality(
        session: Session, game_id: int, name: str, category: str, nature: str
) -> Quality:
    quality = Quality.get_or_create(session, game_id)
    quality.name = name
    quality.category = category
    quality.nature = QualityNature(nature)
    return quality


def record_outcome(
        recording_state: RecordingState,
        session: Session,
        branch_id: int,
        outcome_info: Optional[StoryletBranchOutcomeInfo],
        messages: Optional[List[StoryletBranchOutcomeMessageInfo]],
        redirect: Optional[StoryletInfo],
        area_id: int,
        setting_id: int,
) -> Optional[OutcomeObservation]:
    if messages is None:
        messages = []
    branch = Branch.get_or_create(session, branch_id)
    if not branch:
        return None
    redirect_area = redirect_setting = None
    outcome_messages = []
    for message_info in messages:
        if message_info.message is None:
            continue
        outcome_message = record_outcome_message(
            recording_state, session, message_info
        )
        outcome_messages.append(outcome_message)
        if message_info.area:
            redirect_area = record_area(session, message_info.area)
        elif message_info.setting:
            redirect_setting = record_setting(session, message_info.setting)

    # Create associations between areas and settings
    # If the player is redirected to both a new area and a setting, the two will
    # be linked; otherwise, the old area/setting will be associated with the
    # redirect
    if redirect_area and redirect_setting:
        if redirect_setting not in redirect_area.settings:
            redirect_area.settings.append(redirect_setting)
    elif redirect_area:
        setting = Setting.get_or_create(session, setting_id)
        if setting not in redirect_area.settings:
            redirect_area.settings.append(setting)
    elif redirect_setting:
        area = Area.get_or_create(session, area_id)
        if area not in redirect_setting.areas:
            redirect_setting.areas.append(area)

    return record_observation(
        branch.outcome_observations,
        OutcomeObservation,
        name=outcome_info.event.name if outcome_info else None,
        description=fix_html(
            outcome_info.event.description if outcome_info else None
        ),
        image=get_or_cache_image(ImageType.ICON, outcome_info.event.image)
        if outcome_info else branch.image,
        is_success=not any(
            om.type == OutcomeMessageType.DIFFICULTY_ROLL_FAILURE
            for om in outcome_messages
        ),
        messages=outcome_messages,
        redirect=record_storylet(
            session,
            redirect_area.id if redirect_area else area_id,
            redirect_setting.id if redirect_setting else setting_id,
            redirect
        ) if redirect else None,
        redirect_area=redirect_area,
        redirect_setting=redirect_setting
    )


def record_outcome_message(
        recording_state: RecordingState,
        session: Session,
        info: StoryletBranchOutcomeMessageInfo
) -> OutcomeMessage:
    message = OutcomeMessage()
    message.type = OutcomeMessageType(info.type)
    message.text = info.message.strip()
    message.image = get_or_cache_image(ImageType.ICON_SMALL, info.image)

    if info.possession:
        message.quality = record_quality(
            session,
            game_id=info.possession.id,
            name=info.possession.name,
            category=info.possession.category,
            nature=info.possession.nature
        )
        message.quality_id = message.quality.id
        old_state = recording_state.get_possession(message.quality_id)
        new_state = recording_state.update_possession(info.possession)

        if message.type == OutcomeMessageType.STANDARD_QUALITY_CHANGE:
            message.change = (
                new_state.level - old_state.level
                if old_state else new_state.level
            )
        elif message.type == OutcomeMessageType.QUALITY_EXPLICITLY_SET:
            message.change = new_state.level
        elif message.type == OutcomeMessageType.PYRAMID_QUALITY_CHANGE:
            message.change = (
                new_state.cp - old_state.cp if old_state else new_state.cp
            )

    # Verify the change if possible, in case state went out of sync, and also
    # clean up any messages which need to be cleaned up
    change = None
    if message.type == OutcomeMessageType.STANDARD_QUALITY_CHANGE:
        if match := match_any(QUALITY_GAIN, message.text):
            change = int(match.group("quantity"))
            quality = match.group("quality")
            message.text = f"You've gained {change} x {quality}."
        elif match := match_any(QUALITY_LOSS, message.text):
            change = -int(match.group("quantity"))
            quality = match.group("quality")
            message.text = f"You've lost {-change} x {quality}."
        else:
            logging.warning(
                f"Unexpected quality change message: {message.text}"
            )
    elif message.type == OutcomeMessageType.QUALITY_EXPLICITLY_SET:
        if match_any(QUALITY_SET_ZERO, message.text):
            change = 0
        elif match := match_any(QUALITY_SET_TO, message.text):
            change = int(match.group("quantity"))
    elif message.type == OutcomeMessageType.PYRAMID_QUALITY_CHANGE:
        change_txt = f"+{message.change}" \
            if message.change > 0 else str(message.change)
        msg = "increasing..." if message.change > 0 else "decreasing..."
        message.text = f"{message.quality.name} is {msg} ({change_txt})"
    elif message.type in (
            OutcomeMessageType.DIFFICULTY_ROLL_SUCCESS,
            OutcomeMessageType.DIFFICULTY_ROLL_FAILURE
    ):
        message.text = message.text.replace(
            " (Simple challenges mean you don't learn so much.)", ""
        )

    message.text = fix_html(message.text)

    if change is not None and change != message.change:
        logging.warning(
            f"Calculated change ({message.change}) does not match parsed "
            f"change ({change}), using parsed change"
        )
        message.change = change

    return message


def fix_html(text: Optional[str]) -> Optional[str]:
    return str(BeautifulSoup(text, "html.parser")) if text is not None else None
