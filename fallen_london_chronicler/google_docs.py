import os.path
import pickle
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple, List, Iterable

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = (
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive"
)


class NamedStyle(Enum):
    NORMAL_TEXT = "NORMAL_TEXT"
    TITLE = "TITLE"
    SUBTITLE = "SUBTITLE"
    HEADING_1 = "HEADING_1"
    HEADING_2 = "HEADING_2"
    HEADING_3 = "HEADING_3"
    HEADING_4 = "HEADING_4"
    HEADING_5 = "HEADING_5"
    HEADING_6 = "HEADING_6"


class Alignment(Enum):
    START = "START"
    CENTER = "CENTER"
    END = "END"
    JUSTIFIED = "JUSTIFIED"


class BulletStyle(Enum):
    BULLET_GLYPH_PRESET_UNSPECIFIED = "BULLET_GLYPH_PRESET_UNSPECIFIED"
    BULLET_DISC_CIRCLE_SQUARE = "BULLET_DISC_CIRCLE_SQUARE"
    BULLET_DIAMONDX_ARROW3D_SQUARE = "BULLET_DIAMONDX_ARROW3D_SQUARE"
    BULLET_CHECKBOX = "BULLET_CHECKBOX"
    BULLET_ARROW_DIAMOND_DISC = "BULLET_ARROW_DIAMOND_DISC"
    BULLET_STAR_CIRCLE_SQUARE = "BULLET_STAR_CIRCLE_SQUARE"
    BULLET_ARROW3D_CIRCLE_SQUARE = "BULLET_ARROW3D_CIRCLE_SQUARE"
    BULLET_LEFTTRIANGLE_DIAMOND_DISC = "BULLET_LEFTTRIANGLE_DIAMOND_DISC"
    BULLET_DIAMONDX_HOLLOWDIAMOND_SQUARE = \
        "BULLET_DIAMONDX_HOLLOWDIAMOND_SQUARE"
    BULLET_DIAMOND_CIRCLE_SQUARE = "BULLET_DIAMOND_CIRCLE_SQUARE"
    NUMBERED_DECIMAL_ALPHA_ROMAN = "NUMBERED_DECIMAL_ALPHA_ROMAN"
    NUMBERED_DECIMAL_ALPHA_ROMAN_PARENS = "NUMBERED_DECIMAL_ALPHA_ROMAN_PARENS"
    NUMBERED_DECIMAL_NESTED = "NUMBERED_DECIMAL_NESTED"
    NUMBERED_UPPERALPHA_ALPHA_ROMAN = "NUMBERED_UPPERALPHA_ALPHA_ROMAN"
    NUMBERED_UPPERROMAN_UPPERALPHA_DECIMAL = \
        "NUMBERED_UPPERROMAN_UPPERALPHA_DECIMAL"
    NUMBERED_ZERODECIMAL_ALPHA_ROMAN = "NUMBERED_ZERODECIMAL_ALPHA_ROMAN"


@dataclass
class FormattedText:
    text: Optional[str] = None
    image: Optional[str] = None
    font_family: Optional[str] = None
    font_size: Optional[str] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    url_link: Optional[str] = None

    def get_text_request(self, index: int) -> Optional[Dict[str, Any]]:
        if self.text:
            return {
                "insertText": {
                    "text": self.text,
                    "location": {"index": index}
                }
            }
        return None

    def get_image_request(self, index: int) -> Optional[Dict[str, Any]]:
        if self.image:
            return {
                "insertInlineImage": {
                    "uri": self.image,
                    "location": {"index": index}
                }
            }

    def get_format_request(
            self, start_idx: int, end_idx: int
    ) -> Optional[Dict[str, Any]]:
        text_style = {}
        if self.font_family is not None:
            text_style["weightedFontFamily"] = {"fontFamily": self.font_family}
        if self.font_size is not None:
            text_style["fontSize"] = {"magnitude": self.font_size, "unit": "PT"}
        if self.bold is not None:
            text_style["bold"] = self.bold
        if self.italic is not None:
            text_style["italic"] = self.italic
        if self.underline is not None:
            text_style["underline"] = self.underline
        if self.url_link is not None:
            text_style["link"] = {"url": self.url_link}
        if text_style:
            return {
                "updateTextStyle": {
                    "textStyle": text_style,
                    "fields": ",".join(text_style.keys()),
                    "range": {"startIndex": start_idx, "endIndex": end_idx}
                }
            }
        return None

    def get_requests(
            self, idx: int
    ) -> Tuple[int, List[Dict[str, Any]], List[Dict[str, Any]]]:
        start_idx = idx
        image_request = self.get_image_request(idx)
        idx += 1 if self.image else 0
        text_request = self.get_text_request(idx)
        idx += len(self.text) if self.text else 0
        format_request = self.get_format_request(start_idx, idx)

        content_requests = []
        format_requests = []
        if image_request:
            content_requests.append(image_request)
        if text_request:
            content_requests.append(text_request)
        if format_request:
            format_requests.append(format_request)
        return idx, content_requests, format_requests


@dataclass
class FormattedParagraph:
    text_segments: List[FormattedText]
    named_style: Optional[NamedStyle] = None
    alignment: Optional[Alignment] = None
    bullets: Optional[BulletStyle] = None

    def get_format_requests(
            self, start_idx: int, end_idx: int
    ) -> Iterable[Dict[str, Any]]:
        idx_range = {"startIndex": start_idx, "endIndex": end_idx}
        paragraph_style = {}
        if self.named_style is not None:
            paragraph_style["namedStyleType"] = self.named_style.value
        if self.alignment is not None:
            paragraph_style["alignment"] = self.alignment.value
        if paragraph_style:
            yield {
                "updateParagraphStyle": {
                    "paragraphStyle": paragraph_style,
                    "fields": ",".join(paragraph_style.keys()),
                    "range": idx_range
                }
            }
        if self.bullets is not None:
            yield {
                "createParagraphBullets": {
                    "bulletPreset": self.bullets.value,
                    "range": idx_range
                }
            }


class GoogleDocsService:
    def __init__(self, client_secrets_path: str, credentials_cache_path: str):
        credentials = self._get_credentials(
            client_secrets_path, credentials_cache_path
        )
        self.documents = build(
            "docs", "v1", credentials=credentials, cache_discovery=False
        ).documents()

        self.files = build(
            "drive", "v3", credentials=credentials, cache_discovery=False
        ).files()

    def create_document(self, title: str) -> str:
        return self.documents.create(
            body={"title": title}
        ).execute()["documentId"]

    def copy_document(self, title: str, source_document_id: str) -> str:
        return self.files.copy(
            fileId=source_document_id, body={"name": title}
        ).execute()["id"]

    def insert_text(
            self,
            document_id: str,
            paragraphs: Iterable[FormattedParagraph],
            starting_idx: int
    ) -> None:
        all_content_requests = []
        all_format_requests = []
        idx = starting_idx
        for paragraph in paragraphs:
            paragraph_start_idx = idx
            for text_segment in paragraph.text_segments:
                idx, content_requests, format_requests = \
                    text_segment.get_requests(idx)
                all_content_requests.extend(content_requests)
                all_format_requests.extend(format_requests)
            all_format_requests.extend(paragraph.get_format_requests(
                paragraph_start_idx, idx
            ))
        self._batch_update(
            document_id, [*all_content_requests, *all_format_requests]
        )

    def set_document_properties(
            self,
            document_id: str,
            background_color: Optional[Tuple[float, float, float]] = None,
            margin: Optional[float] = None,
    ) -> None:
        document_style = {}
        fields = []

        if background_color is not None:
            red, green, blue = background_color
            document_style["background"] = {
                "color": {
                    "color": {
                        "rgbColor": {"red": red, "green": green, "blue": blue}
                    }
                }
            }
            fields.append("background")

        if margin is not None:
            margin_info = {"magnitude": margin, "unit": "PT"}
            document_style["marginTop"] = margin_info
            document_style["marginBottom"] = margin_info
            document_style["marginRight"] = margin_info
            document_style["marginLeft"] = margin_info
            fields.extend(
                ("marginTop", "marginBottom", "marginRight", "marginLeft")
            )

        request = {
            "updateDocumentStyle": {
                "documentStyle": document_style,
                "fields": ",".join(fields),
            }
        }
        self._batch_update(document_id, [request])

    def _batch_update(
            self, document_id: str, requests: List[Dict[str, Any]]
    ) -> None:
        self.documents.batchUpdate(
            documentId=document_id, body={"requests": requests}
        ).execute()

    @staticmethod
    def _get_credentials(
            client_secrets_path: str, credentials_cache_path: str
    ):
        credentials = None
        if os.path.exists(credentials_cache_path):
            with open(credentials_cache_path, "rb") as token:
                credentials = pickle.load(token)
        if not credentials or not credentials.valid:
            if credentials and credentials.expired \
                    and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secrets_path, SCOPES
                )
                credentials = flow.run_local_server(port=0)
            with open(credentials_cache_path, "wb") as token:
                pickle.dump(credentials, token)
        return credentials
