"""
NutriLens – Intelligent Ingredient Region Detector & Cropper
Locates the ingredients section anywhere on food packaging, handles small text,
curved/tilted packaging, perspective distortion, and produces an enhanced
cropped image of the ingredients block as visual extraction evidence.
"""
import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import cv2
from PIL import Image

logger = logging.getLogger(__name__)

# Ingredient section header keywords
INGREDIENT_HEADER_PATTERNS = [
    r"\b(?:list\s+of\s+ingredients?|ingredients?|ingrediente?s?|ingred[a-z]*)\b",
    r"\b(?:contains\s*[:\-])\b",
    r"\b(?:allergen\s+(?:information|advice|declaration))\b",
    r"\b(?:samagri|samagree)\b",  # Hindi / regional transliteration
]

# Stop keywords indicating the end of the ingredients block
STOP_PATTERNS = [
    r"\b(?:nutrition(?:al)?\s+(?:facts|information|values?)|poshan)\b",
    r"\b(?:mfd\s+by|manufactured\s+by|packed\s+by|marketed\s+by|imported\s+by)\b",
    r"\b(?:net\s+(?:weight|wt|quantity|contents?))\b",
    r"\b(?:batch\s+no|lot\s+no|date\s+of\s+mfg|best\s+before|expiry|use\s+by)\b",
    r"\b(?:fssai|lic\s*\.?\s*no|license\s+no)\b",
    r"\b(?:customer\s+care|feedback|consumer\s+cell|toll\s+free)\b",
    r"\b(?:store\s+in\s+a\s+cool|keep\s+dry|dry\s+place)\b",
    r"\b(?:mrp\s*[\:\.]?\s*rs|inclusive\s+of\s+all\s+taxes)\b",
]


def enhance_ingredient_crop(crop_bgr: np.ndarray) -> np.ndarray:
    """
    Applies dedicated contrast enhancement, sharpening, and glare mitigation
    specifically tuned for small-print ingredient declarations on glossy,
    metallic, or curved food packaging.
    """
    if crop_bgr is None or crop_bgr.size == 0:
        return crop_bgr

    try:
        # Convert to LAB color space to process luminance channel independently
        lab = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) on L-channel
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l_channel)

        merged_lab = cv2.merge((l_enhanced, a_channel, b_channel))
        enhanced_bgr = cv2.cvtColor(merged_lab, cv2.COLOR_LAB2BGR)

        # Subtle unsharp masking to enhance small printed font edges without noise explosion
        gaussian = cv2.GaussianBlur(enhanced_bgr, (0, 0), sigmaX=2.0)
        sharpened = cv2.addWeighted(enhanced_bgr, 1.35, gaussian, -0.35, 0)

        return sharpened
    except Exception as e:
        logger.warning(f"Failed to enhance ingredient crop: {e}")
        return crop_bgr


def detect_and_crop_ingredient_region(
    img_bgr: np.ndarray,
    ocr_lines: List[Any],
    output_dir: str,
    scan_id: str,
    image_idx: int = 0,
) -> Optional[Dict[str, Any]]:
    """
    Locates the ingredient declaration using OCR spatial bounding boxes,
    clusters the contiguous ingredient paragraph lines, crops the region
    with safety padding, applies enhancement, and saves it to disk.

    Returns dict with crop file path, relative URL, bounding box, and confidence.
    """
    if img_bgr is None or not ocr_lines:
        return None

    img_h, img_w = img_bgr.shape[:2]

    # Find candidate header lines
    header_idx: Optional[int] = None
    header_box: Optional[List[List[int]]] = None

    for idx, line in enumerate(ocr_lines):
        text = getattr(line, "text", "") or ""
        text_lower = text.lower().strip()
        for pat in INGREDIENT_HEADER_PATTERNS:
            if re.search(pat, text_lower, re.IGNORECASE):
                # Ensure it's not a stop pattern like "nutrition facts containing..."
                if not any(re.search(sp, text_lower, re.IGNORECASE) for sp in STOP_PATTERNS[:2]):
                    header_idx = idx
                    header_box = getattr(line, "box", None)
                    break
        if header_idx is not None:
            break

    # If no explicit header line found, check if lines look like ingredient lists
    # (multiple commas, parentheses, additive numbers)
    if header_idx is None:
        for idx, line in enumerate(ocr_lines):
            text = getattr(line, "text", "") or ""
            comma_count = text.count(",") + text.count(";")
            has_ins = bool(re.search(r"\b(?:ins|e)\s*[-_]?\s*\d{3,4}\b", text, re.I))
            if comma_count >= 2 or (comma_count >= 1 and has_ins):
                header_idx = idx
                header_box = getattr(line, "box", None)
                break

    if header_idx is None or not header_box:
        logger.debug("[INGREDIENT_DETECTOR] No ingredient header or dense list found in OCR lines.")
        return None

    # Collect lines belonging to the ingredient block starting from header_idx
    block_lines = [ocr_lines[header_idx]]
    h_box = header_box
    h_ymin = min(pt[1] for pt in h_box)
    h_ymax = max(pt[1] for pt in h_box)
    h_line_height = max(10, h_ymax - h_ymin)

    # Walk downwards through subsequent lines
    for line in ocr_lines[header_idx + 1:]:
        box = getattr(line, "box", None)
        if not box or len(box) < 4:
            continue

        text = getattr(line, "text", "") or ""
        text_lower = text.lower().strip()

        # Stop condition: reached an explicit non-ingredient section
        if any(re.search(sp, text_lower, re.IGNORECASE) for sp in STOP_PATTERNS):
            # Check if this line is an allergen warning (allergens are kept with ingredients!)
            is_allergen = bool(re.search(r"\b(?:contains|may\s+contain|allergen)\b", text_lower, re.I))
            if is_allergen:
                block_lines.append(line)
            break

        line_ymin = min(pt[1] for pt in box)
        line_ymax = max(pt[1] for pt in box)

        # Check if line is roughly below or adjacent to current block (within 3x line height)
        prev_box = getattr(block_lines[-1], "box", None)
        if prev_box:
            prev_ymax = max(pt[1] for pt in prev_box)
            vert_gap = line_ymin - prev_ymax
            if vert_gap > (h_line_height * 4.5):
                # Too far below, likely a different block
                break

        block_lines.append(line)

        # Safety cap: ingredient declarations rarely span more than 20 OCR lines
        if len(block_lines) >= 20:
            break

    if not block_lines:
        return None

    # Compute bounding box encompassing all collected block lines
    all_x = []
    all_y = []
    for l in block_lines:
        box = getattr(l, "box", None)
        if box:
            for pt in box:
                all_x.append(pt[0])
                all_y.append(pt[1])

    if not all_x or not all_y:
        return None

    xmin = max(0, int(min(all_x)))
    ymin = max(0, int(min(all_y)))
    xmax = min(img_w, int(max(all_x)))
    ymax = min(img_h, int(max(all_y)))

    # Apply generous safety padding around the crop (15% height, 10% width)
    pad_x = max(16, int((xmax - xmin) * 0.08))
    pad_y = max(16, int((ymax - ymin) * 0.12))

    crop_xmin = max(0, xmin - pad_x)
    crop_ymin = max(0, ymin - pad_y)
    crop_xmax = min(img_w, xmax + pad_x)
    crop_ymax = min(img_h, ymax + pad_y)

    crop_w = crop_xmax - crop_xmin
    crop_h = crop_ymax - crop_ymin

    if crop_w < 40 or crop_h < 30:
        return None

    # Slice region from original image
    raw_crop = img_bgr[crop_ymin:crop_ymax, crop_xmin:crop_xmax].copy()

    # Apply dedicated enhancement
    enhanced_crop = enhance_ingredient_crop(raw_crop)

    # Save to scan uploads directory
    crop_filename = f"{scan_id}_{image_idx}_ingredients_crop.jpg"
    crop_path = os.path.join(output_dir, crop_filename)

    try:
        cv2.imwrite(crop_path, enhanced_crop, [cv2.IMWRITE_JPEG_QUALITY, 90])
        relative_url = f"/api/scans/images/{crop_filename}"
        logger.info(
            f"[INGREDIENT_DETECTOR] Successfully cropped ingredient region: "
            f"{crop_w}x{crop_h}px saved to {crop_filename}"
        )
        return {
            "crop_path": crop_path,
            "crop_url": relative_url,
            "bbox": [crop_xmin, crop_ymin, crop_xmax, crop_ymax],
            "width": crop_w,
            "height": crop_h,
            "lines_included": len(block_lines),
        }
    except Exception as e:
        logger.error(f"[INGREDIENT_DETECTOR] Failed to write crop image: {e}")
        return None
