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
MAX_PROCESSING_DIMENSION = 960  # Capped at 960px to maintain sub-512MB RAM and sub-second OCR on cloud instances
THUMBNAIL_MAX_DIMENSION = 320   # Fast lightweight thumbnail for dashboard preview


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


def generate_thumbnail(
    image_bytes: bytes,
    max_dim: int = THUMBNAIL_MAX_DIMENSION,
    quality: int = 75,
) -> bytes:
    """
    Generates a fast, low-memory JPEG thumbnail (~15-25KB) from raw image bytes.
    Saves bandwidth and client render memory on dashboard history views.
    """
    try:
        with Image.open(io.BytesIO(image_bytes)) as pil_img:
            upright = fix_orientation(pil_img)
            if upright.mode != "RGB":
                upright = upright.convert("RGB")
            upright.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            out_buf = io.BytesIO()
            upright.save(out_buf, format="JPEG", quality=quality, optimize=True)
            return out_buf.getvalue()
    except Exception as e:
        logger.warning(f"Failed to generate thumbnail: {e}")
        return image_bytes[:1024]  # Return dummy fallback if thumbnail fails


def assess_image_quality(img_cv: np.ndarray) -> Dict[str, Any]:
    """
    Evaluates image blur via Laplacian variance and overall brightness.
    Uses CV_32F (half the RAM of CV_64F) and downsamples oversized images before blur check.
    """
    h, w = img_cv.shape[:2]
    # Downsample for blur calculation if over 800px to cap blur computation memory to <1MB
    if max(h, w) > 800:
        scale = 800.0 / max(h, w)
        sample = cv2.resize(img_cv, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    else:
        sample = img_cv

    if len(sample.shape) == 3:
        gray = cv2.cvtColor(sample, cv2.COLOR_BGR2GRAY)
    else:
        gray = sample

    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_32F).var())
    brightness = float(np.mean(gray))

    # Free sample memory if created
    if sample is not img_cv:
        del sample
    del gray

    # A variance below 50 indicates substantial blur on typical document/label captures
    is_blurry = laplacian_var < 50.0
    is_too_dark = brightness < 40.0
    is_too_bright = brightness > 230.0

    warning = None
    if is_blurry:
        warning = "Image appears blurry or out of focus. Text extraction may be incomplete."
    elif is_too_dark:
        warning = "Image is very dark. Please capture the label in better lighting."
    elif is_too_bright:
        warning = "Image is overexposed or washed out with glare."

    return {
        "is_blurry": is_blurry,
        "blur_score": round(laplacian_var, 2),
        "brightness": round(brightness, 2),
        "is_too_dark": is_too_dark,
        "is_too_bright": is_too_bright,
        "quality_warning": warning,
    }


def preprocess_image(
    image_bytes: bytes,
    enhance_for_ocr: bool = True,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Decodes image, fixes orientation, checks resolution, runs quality assessment,
    and applies OpenCV enhancement:
    - Downsamples images whose dimension exceeds MAX_PROCESSING_DIMENSION (1600px)
      to avoid memory exhaustion in OpenCV & PaddleOCR feature maps
    - Orientation correction via EXIF
    - Blur & lighting assessment
    - Grayscale conversion & CLAHE adaptive contrast
    - Noise reduction via bilateral filter
    
    Returns:
        (processed_image_ndarray, metadata_dict)
    """
    # Load using PIL first to handle EXIF rotation and downsampling reliably
    with Image.open(io.BytesIO(image_bytes)) as pil_img:
        upright_img = fix_orientation(pil_img)
        # Convert to RGB (in case of RGBA, P or CMYK)
        if upright_img.mode != "RGB":
            upright_img = upright_img.convert("RGB")
        
        orig_width, orig_height = upright_img.size

        # Downsample oversized camera images to prevent memory spikes
        max_side = max(orig_width, orig_height)
        if max_side > MAX_PROCESSING_DIMENSION:
            scale = MAX_PROCESSING_DIMENSION / float(max_side)
            proc_w = int(orig_width * scale)
            proc_h = int(orig_height * scale)
            upright_img = upright_img.resize((proc_w, proc_h), Image.Resampling.LANCZOS)
        else:
            proc_w, proc_h = orig_width, orig_height

        # Convert PIL image to OpenCV BGR format
        rgb_array = np.array(upright_img)
        bgr_img = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
        del rgb_array

    quality = assess_image_quality(bgr_img)

    metadata: Dict[str, Any] = {
        "original_width": orig_width,
        "original_height": orig_height,
        "processed_width": proc_w,
        "processed_height": proc_h,
        "quality": quality,
        "enhanced": False,
    }

    if not enhance_for_ocr:
        return bgr_img, metadata

    # Enhancement for OCR:
    # 1. Convert to grayscale
    gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
    del bgr_img

    # 2. Adaptive contrast enhancement using CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray)
    del gray

    # 3. Fast bilateral filter to smooth noise while preserving sharp text edges (d=3 for sub-50ms execution)
    denoised = cv2.bilateralFilter(enhanced_gray, d=3, sigmaColor=35, sigmaSpace=35)
    del enhanced_gray

    metadata["enhanced"] = True

    return denoised, metadata
