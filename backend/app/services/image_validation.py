import hashlib
import io
from dataclasses import dataclass

import numpy as np
from PIL import Image, UnidentifiedImageError

from ..config import settings

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "BMP"}


@dataclass
class ValidatedImage:
    image: Image.Image
    quality_status: str
    reasons: list[str]
    sha256: str
    format: str


def decode_and_assess(data: bytes, declared_type: str | None, task: str) -> ValidatedImage:
    if not data:
        raise ValueError("The uploaded file is empty.")
    if len(data) > settings.max_upload_bytes:
        raise ValueError(f"Image exceeds the {settings.max_upload_bytes // (1024 * 1024)} MB upload limit.")
    try:
        with Image.open(io.BytesIO(data)) as source:
            fmt = source.format
            if fmt not in ALLOWED_FORMATS:
                raise ValueError("Unsupported image format. Upload JPEG, PNG, WebP, or BMP.")
            if declared_type and declared_type not in {"application/octet-stream", "image/jpeg", "image/png", "image/webp", "image/bmp"}:
                raise ValueError("The declared media type is not an accepted image type.")
            mime_formats = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP", "image/bmp": "BMP"}
            if declared_type in mime_formats and mime_formats[declared_type] != fmt:
                raise ValueError("The declared media type does not match the decoded image format.")
            if source.width * source.height > settings.max_image_pixels:
                raise ValueError("Image dimensions exceed the safe pixel limit.")
            source.verify()
        with Image.open(io.BytesIO(data)) as source:
            image = source.convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("The uploaded file is not a valid, decodable image.") from exc
    reasons: list[str] = []
    if min(image.size) < settings.min_image_side:
        reasons.append(f"Resolution is below the minimum {settings.min_image_side}px side length.")
    gray = np.asarray(image.convert("L"), dtype=np.float32)
    if float(gray.std()) < 12:
        reasons.append("Image contrast is very low; recapture or request review.")
    laplacian = (gray[1:-1, :-2] + gray[1:-1, 2:] + gray[:-2, 1:-1] + gray[2:, 1:-1] - 4 * gray[1:-1, 1:-1])
    if laplacian.size and float(laplacian.var()) < 8:
        reasons.append("Image may be blurred; recapture or request review.")
    if task == "dr_grading":
        arr = np.asarray(image)
        channel_spread = float(np.mean(np.max(arr, axis=2).astype(np.float32) - np.min(arr, axis=2).astype(np.float32)))
        if channel_spread < 5:
            reasons.append("Image has little color information; confirm it is a retinal fundus photograph.")
        saturated = np.mean((arr.max(axis=2) < 25) | (arr.min(axis=2) > 245))
        if saturated > 0.92:
            reasons.append("Fundus field of view or illumination is not clearly visible.")
        if image.width < 256 or image.height < 256:
            reasons.append("Fundus image resolution is low for field-of-view assessment.")
    if task == "tb_screening":
        arr = np.asarray(image).astype(np.float32)
        channel_spread = float(np.mean(arr.max(axis=2) - arr.min(axis=2)))
        if channel_spread > 45:
            reasons.append("Image is strongly colorized; confirm it is a chest X-ray.")
    return ValidatedImage(image, "poor" if reasons else "acceptable", reasons, hashlib.sha256(data).hexdigest(), fmt or "unknown")
