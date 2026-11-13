"""
NutriLens – Food Scanner Image Preprocessor (Day 4)
Handles image validation, file size restrictions, orientation handling,
and OpenCV-based image enhancement for OCR.
"""
import io
import os
import logging
from typing import Tuple, Dict, Any, Optional
import numpy as np
import cv2
from PIL import Image, ExifTags
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# Constants
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB per image
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MIN_IMAGE_DIMENSION = 50  # Minimum 50x50 pixels


class ImageValidationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


def validate_image_bytes(
    content: bytes,
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
) -> None:
    """
    Validates uploaded file size, extension, MIME type, and decodability.
    Raises ImageValidationError if invalid.
    """
    # 1. Size check
    if not content or len(content) == 0:
        raise ImageValidationError("Uploaded image file is empty.")

    if len(content) > MAX_IMAGE_SIZE_BYTES:
        max_mb = MAX_IMAGE_SIZE_BYTES // (1024 * 1024)
        size_mb = len(content) / (1024 * 1024)
        raise ImageValidationError(
            f"File size ({size_mb:.2f} MB) exceeds maximum allowed limit of {max_mb} MB."
        )

    # 2. Extension check
    if filename:
        ext = os.path.splitext(filename)[1].lower()
        if ext and ext not in ALLOWED_EXTENSIONS:
            allowed_str = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise ImageValidationError(
                f"Unsupported file extension '{ext}'. Allowed extensions: {allowed_str}."
            )

    # 3. Content-Type check (if provided)
    if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
        allowed_types_str = ", ".join(sorted(ALLOWED_MIME_TYPES))
        raise ImageValidationError(
            f"Unsupported image type '{content_type}'. Allowed types: {allowed_types_str}."
        )

    # 4. Decodability check using PIL
    try:
        with Image.open(io.BytesIO(content)) as img:
            img.verify()
            width, height = img.size
            if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
                raise ImageValidationError(
                    f"Image dimensions ({width}x{height}) are too small. Minimum required: {MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION}px."
                )
    except ImageValidationError:
        raise
    except Exception as e:
        raise ImageValidationError(f"Invalid or corrupted image file: {str(e)}")


def fix_orientation(pil_image: Image.Image) -> Image.Image:
    """
    Checks EXIF orientation tag and rotates/transposes image to upright orientation.
    """
    try:
        exif = pil_image.getexif()
        if not exif:
            return pil_image

        orientation_key = None
        for key in ExifTags.TAGS.keys():
            if ExifTags.TAGS[key] == "Orientation":
                orientation_key = key
                break

        if orientation_key and orientation_key in exif:
            orientation = exif[orientation_key]
            if orientation == 3:
                return pil_image.rotate(180, expand=True)
            elif orientation == 6:
                return pil_image.rotate(270, expand=True)
            elif orientation == 8:
                return pil_image.rotate(90, expand=True)
            elif orientation == 2:
                return pil_image.transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 4:
                return pil_image.transpose(Image.FLIP_TOP_BOTTOM)
            elif orientation == 5:
                return pil_image.rotate(270, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 7:
                return pil_image.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
    except Exception as e:
        logger.warning(f"Could not process EXIF orientation: {e}")

    return pil_image


def preprocess_image(
    image_bytes: bytes,
    enhance_for_ocr: bool = True,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Decodes image, fixes orientation, and optionally applies OpenCV enhancement:
    - Grayscale conversion
    - Noise reduction / bilateral filtering
    - Contrast enhancement (CLAHE)
    
    Returns:
        (processed_image_ndarray, metadata_dict)
    """
    # Load using PIL first to handle EXIF rotation reliably
    with Image.open(io.BytesIO(image_bytes)) as pil_img:
        upright_img = fix_orientation(pil_img)
        # Convert to RGB (in case of RGBA or CMYK)
        if upright_img.mode != "RGB":
            upright_img = upright_img.convert("RGB")
        
        orig_width, orig_height = upright_img.size
        # Convert PIL image to OpenCV BGR format
        rgb_array = np.array(upright_img)
        bgr_img = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)

    metadata: Dict[str, Any] = {
        "original_width": orig_width,
        "original_height": orig_height,
        "enhanced": False,
    }

    if not enhance_for_ocr:
        return bgr_img, metadata

    # Enhancement for OCR:
    # 1. Convert to grayscale
    gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)

    # 2. Adaptive contrast enhancement using CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray)

    # 3. Mild bilateral filter to smooth background noise while preserving sharp text edges
    denoised = cv2.bilateralFilter(enhanced_gray, d=5, sigmaColor=50, sigmaSpace=50)

    metadata["enhanced"] = True
    metadata["processed_width"] = orig_width
    metadata["processed_height"] = orig_height

    return denoised, metadata
