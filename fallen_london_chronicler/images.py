import os
import os.path
from enum import Enum
from typing import Optional

import requests

from fallen_london_chronicler.web import CACHED_IMAGES_PATH

BASE_IMAGE_URL = "https://images.fallenlondon.com/images"
HEADERS_URL = f"{BASE_IMAGE_URL}/headers/{{0}}.png"
ICONS_URL = f"{BASE_IMAGE_URL}/icons/{{0}}.png"
ICONS_SMALL_URL = f"{BASE_IMAGE_URL}/icons_small/{{0}}.png"


class ImageType(Enum):
    HEADER = HEADERS_URL
    ICON = ICONS_URL
    ICON_SMALL = ICONS_SMALL_URL


def get_or_cache_image(
        image_type: ImageType, image_id: Optional[str]
) -> Optional[str]:
    if not image_id:
        return None
    path = get_path(image_type, image_id)
    if os.path.exists(path):
        return path
    return cache_image(image_type, image_id)


def cache_image(image_type: ImageType, image_id: str) -> str:
    response = requests.get(image_type.value.format(image_id))
    path = get_path(image_type, image_id)
    full_path = CACHED_IMAGES_PATH + path
    image_dir = os.path.dirname(full_path)
    os.makedirs(image_dir, exist_ok=True)
    with open(full_path, "wb") as f:
        f.write(response.content)
    return path


def get_path(image_type: ImageType, image_id: str) -> str:
    if image_type == ImageType.HEADER:
        path = "/headers/"
    elif image_type == ImageType.ICON:
        path = "/icons/"
    elif image_type == ImageType.ICON_SMALL:
        path = "/icons_small/"
    else:
        raise ValueError(f"Unknown image type: {image_type.value}")
    path += f"{image_id}.png"
    return path
