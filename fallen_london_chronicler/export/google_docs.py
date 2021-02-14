import logging
from collections import defaultdict
from datetime import datetime
from typing import Iterable, List, Dict, Tuple, Optional

from bs4 import BeautifulSoup, Tag
from sqlalchemy.orm import selectinload

from fallen_london_chronicler.db import Session
from fallen_london_chronicler.export.base import Exporter
from fallen_london_chronicler.google_docs import GoogleDocsService, FormattedText, \
    FormattedParagraph, NamedStyle, Alignment, BulletStyle
from fallen_london_chronicler.images import BASE_IMAGE_URL
from fallen_london_chronicler.model import Storylet, Branch, OutcomeObservation, \
    OutcomeMessageType, Area, QualityRequirement


class GoogleDocsExporter(Exporter):
    def __init__(
            self,
            google_credentials_path: str,
            google_credentials_cache_path: str,
            template_document_id: Optional[str],
    ):
        self.service = GoogleDocsService(
            google_credentials_path, google_credentials_cache_path
        )
        self.template_document_id = template_document_id

    def export_all(self, session: Session) -> str:
        date_string = datetime.now().strftime('%Y-%m-%d %H:%M')
        title = f"Fallen London Export {date_string}"
        if self.template_document_id:
            document_id = self.service.copy_document(
                title, self.template_document_id
            )
        else:
            document_id = self.service.create_document(title)
        paragraphs = []
        for area in session.query(Area).options(
                selectinload(Area.storylets).selectinload(Storylet.branches)
        ):
            paragraphs.extend(render_area(area))
            for storylet in area.storylets:
                paragraphs.extend(render_storylet(storylet))
        self.service.insert_text(
            document_id,
            paragraphs,
            1
        )
        return f"https://docs.google.com/document/d/{document_id}/edit"


def render_area(area: Area) -> Iterable[FormattedParagraph]:
    yield FormattedParagraph(
        text_segments=convert_to_formatted_text(
            area.name if area.name else "???"
        ),
        named_style=NamedStyle.HEADING_1,
    )
    if area.description:
        yield FormattedParagraph(
            alignment=Alignment.CENTER,
            text_segments=[FormattedText(area.description, italic=True)],
        )
    if area.image:
        yield FormattedParagraph(
            alignment=Alignment.CENTER,
            text_segments=[
                _get_image(area.image),
                FormattedText("\n")
            ],
        )


def render_storylet(storylet: Storylet) -> Iterable[FormattedParagraph]:
    name = " / ".join(set(so.name for so in storylet.observations if so.name))
    header_segments = []
    if storylet.image:
        header_segments.append(_get_image(storylet.image))
    header_segments.extend(convert_to_formatted_text(name))
    yield FormattedParagraph(
        text_segments=header_segments,
        named_style=NamedStyle.HEADING_2,
    )
    yield FormattedParagraph(
        text_segments=separate_and_format_text(
            (so.teaser for so in storylet.observations if so.teaser),
            italic=True
        )
    )
    yield FormattedParagraph(
        text_segments=separate_and_format_text(
            so.description for so in storylet.observations if so.description
        )
    )
    yield from render_quality_requirements(storylet.quality_requirements)
    for branch in storylet.branches:
        yield from render_branch(branch)


def render_branch(branch: Branch) -> Iterable[FormattedParagraph]:
    name = " / ".join(set(bo.name for bo in branch.observations if bo.name))
    header_segments = []
    if branch.image:
        header_segments.append(_get_image(branch.image))
    header_segments.extend(convert_to_formatted_text(name))
    yield FormattedParagraph(
        text_segments=header_segments,
        named_style=NamedStyle.HEADING_3,
    )
    yield FormattedParagraph(
        text_segments=separate_and_format_text(
            bo.description for bo in branch.observations if bo.description
        )
    )
    yield from render_quality_requirements(branch.quality_requirements)

    successes = [
        outcome for outcome in branch.outcome_observations if outcome.is_success
    ]
    failures = [
        outcome for outcome in branch.outcome_observations
        if not outcome.is_success
    ]
    if successes:
        yield FormattedParagraph(
            text_segments=convert_to_formatted_text("Success"),
            named_style=NamedStyle.HEADING_4
        )
        grouped_successes = group_outcomes(successes)
        for (name, description), messages in grouped_successes.items():
            yield from render_outcome(name, description, messages)
    if failures:
        yield FormattedParagraph(
            text_segments=convert_to_formatted_text("Failure"),
            named_style=NamedStyle.HEADING_4
        )
        grouped_failures = group_outcomes(failures)
        for (name, description), messages in grouped_failures.items():
            yield from render_outcome(name, description, messages)


def render_quality_requirements(
        quality_requirements: Optional[List[QualityRequirement]]
):
    if not quality_requirements:
        return
    yield FormattedParagraph(
        text_segments=[FormattedText("Requirements:\n", bold=True)]
    )
    yield FormattedParagraph(
        text_segments=convert_to_formatted_text(
            "<br />".join(
                qr.summary for qr in quality_requirements
            )
        ),
        bullets=BulletStyle.BULLET_DISC_CIRCLE_SQUARE
    )


def render_outcome(
        name: Optional[str], description: Optional[str], messages: List[str]
) -> Iterable[FormattedParagraph]:
    if name:
        yield FormattedParagraph(
            text_segments=convert_to_formatted_text(name),
            named_style=NamedStyle.HEADING_5
        )
    if description:
        yield FormattedParagraph(
            text_segments=convert_to_formatted_text(description),
        )
    if messages:
        yield FormattedParagraph(
            text_segments=convert_to_formatted_text("<br />".join(messages)),
            bullets=BulletStyle.BULLET_DISC_CIRCLE_SQUARE
        )


def group_outcomes(
        outcomes: Iterable[OutcomeObservation]
) -> Dict[Tuple[str, str], List[str]]:
    groups = defaultdict(list)
    for outcome in outcomes:
        groups[(outcome.name, outcome.description)].append(outcome)

    grouped_outcomes = {}
    for (name, description), outcomes in groups.items():
        messages_by_type = {}

        # Bundle together messages which seem to be related
        for outcome in outcomes:
            # Ignore second chance failures
            if any(
                    message.type == OutcomeMessageType.SECOND_CHANCE_RESULT
                    for message in outcome.messages
            ):
                continue
            if outcome.redirect:
                if None not in messages_by_type:
                    messages_by_type[None] = set()
                messages_by_type[None].add(
                    f"Redirect to storylet: {outcome.redirect.name}"
                )
            if outcome.redirect_branch:
                pass  # TODO Handle redirect to branch
            for message in outcome.messages:
                if message.type in (
                        OutcomeMessageType.QUALITY_CAP,
                        OutcomeMessageType.OUTFIT_CHANGEABILITY,
                ):
                    messages_by_type[message.type] = message.text
                elif message.type == OutcomeMessageType.AREA_CHANGE:
                    messages_by_type[message.type] = \
                        f"You have moved to a new area " \
                        f"({outcome.redirect_area.name})"
                elif message.type == OutcomeMessageType.SETTING_CHANGE:
                    messages_by_type[message.type] = \
                        f"You have moved to a new setting " \
                        f"({outcome.redirect_setting.name})"
                elif message.type in (
                        OutcomeMessageType.PYRAMID_QUALITY_CHANGE,
                        OutcomeMessageType.STANDARD_QUALITY_CHANGE,
                        OutcomeMessageType.QUALITY_EXPLICITLY_SET
                ):
                    if message.type not in messages_by_type:
                        messages_by_type[message.type] = {}
                    if message.quality in messages_by_type[message.type]:
                        min_change, max_change = \
                            messages_by_type[message.type][message.quality]
                        min_change = min(min_change, message.change)
                        max_change = max(max_change, message.change)
                    else:
                        min_change = max_change = message.change
                    messages_by_type[message.type][message.quality] = (
                        min_change, max_change
                    )

        # Convert to messages
        grouped_messages = []
        for message_type, value in messages_by_type.items():
            if message_type == OutcomeMessageType.PYRAMID_QUALITY_CHANGE:
                for quality, (min_change, max_change) in value.items():
                    change = _format_cp_change(min_change, max_change)
                    if max_change <= 0:
                        text = f"{quality.name} is dropping... {change}"
                    elif min_change >= 0:
                        text = f"{quality.name} is increasing... {change}"
                    else:
                        text = f"{quality.name} is changing... {change}"
                    grouped_messages.append(text)
            elif message_type == OutcomeMessageType.STANDARD_QUALITY_CHANGE:
                for quality, (min_change, max_change) in value.items():
                    change = f"{_format_qty_change(min_change, max_change)}" \
                               f" x {quality.name}"
                    if max_change <= 0:
                        text = f"You've lost {change}"
                    elif min_change >= 0:
                        text = f"You've gained {change}"
                    else:
                        text = f"You've gained/lost {change}"
                    grouped_messages.append(text)
            elif message_type == OutcomeMessageType.QUALITY_EXPLICITLY_SET:
                for quality, (min_change, max_change) in value.items():
                    grouped_messages.append(
                        f"{quality.name} is now "
                        f"{_format_qty_change(min_change, max_change)}"
                    )
            elif message_type is None:
                grouped_messages.extend(value)
            else:
                grouped_messages.append(value)

        grouped_outcomes[(name, description)] = grouped_messages
    return grouped_outcomes


def convert_to_formatted_text(
        text: str, bold: Optional[bool] = None, italic: Optional[bool] = None
) -> List[FormattedText]:
    segments = []
    text = text.replace("\r", "").replace("\n", "")
    soup = BeautifulSoup(text, "html.parser")
    segments.extend(_format_soup(soup, bold, italic))
    if segments and not segments[-1].text.endswith("\n"):
        segments.append(FormattedText("\n"))
    return segments


def separate_and_format_text(
        items: Iterable[str],
        bold: Optional[bool] = None,
        italic: Optional[bool] = None
) -> List[FormattedText]:
    segments = []
    for item in set(items):
        if segments:
            segments.append(FormattedText("----------\n"))
        segments.extend(
            convert_to_formatted_text(item, bold=bold, italic=italic)
        )
    return segments


def _format_soup(
        tags: Iterable[Tag],
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
        url_link: Optional[str] = None,
        prefix: str = ""
) -> Iterable[FormattedText]:
    for tag in tags:
        if tag.name == "p":
            sub = list(_format_soup(
                tag, bold=bold, italic=italic, url_link=url_link, prefix=prefix
            ))
            yield from sub
            if sub and not sub[-1].text.endswith("\n"):
                yield FormattedText("\n")
        elif tag.name in ("em", "i"):
            yield from _format_soup(
                tag, bold=bold, italic=True, url_link=url_link, prefix=prefix
            )
        elif tag.name == "strong":
            yield from _format_soup(
                tag, bold=True, italic=italic, url_link=url_link, prefix=prefix
            )
        elif tag.name == "span" and "descriptive" in tag["class"]:
            yield from _format_soup(
                tag, bold=True, italic=True, url_link=url_link, prefix=prefix
            )
        elif tag.name == "br":
            yield FormattedText("\n")
        elif tag.name == "a":
            yield from _format_soup(
                tag,
                bold=bold,
                italic=italic,
                url_link=tag.attrs.get("href"),
                prefix=prefix
            )
        elif tag.name == "ul":
            yield from _format_soup(
                tag,
                bold=bold,
                italic=italic,
                url_link=url_link,
                prefix=prefix + "\t"
            )
        elif tag.name == "li":
            yield FormattedText("\n")
            yield from _format_soup(
                tag, bold=bold, italic=italic, url_link=url_link, prefix=prefix
            )
        elif tag.name == "span":
            yield from _format_soup(
                tag, bold=bold, italic=italic, url_link=url_link, prefix=prefix
            )
        else:
            if tag.name is not None:
                logging.warning(f"Unexpected tag {tag.name}")
            yield FormattedText(
                prefix + str(tag.string),
                bold=bold,
                italic=italic,
                url_link=url_link
            )


def _format_cp_change(min_change: int, max_change: int) -> str:
    text = "("
    if min_change == max_change:
        text += str(min_change)
    else:
        text += f"{min_change} to {max_change}"
    text += " CP)"
    return text


def _format_qty_change(min_change: int, max_change: int) -> str:
    if max_change < 0:
        old_min_change = abs(min_change)
        min_change = abs(max_change)
        max_change = old_min_change
    if min_change == max_change:
        return str(min_change)
    else:
        return f"{min_change} - {max_change}"


def _get_image(image_str: str) -> FormattedText:
    return FormattedText(image=BASE_IMAGE_URL + image_str)
