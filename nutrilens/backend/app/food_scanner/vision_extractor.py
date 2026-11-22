"""
NutriLens – Multimodal Vision Extraction Service
Uses configured vision LLMs (Gemini / OpenAI) as an intelligent fallback or complementary source
when OCR output is incomplete, low-confidence, or requires complex visual layout reasoning.
Adheres strictly to the structured nutrition facts and ingredient schema.
"""
import os
import io
import json
import base64
import logging
from typing import Dict, Any, Optional, List, Tuple
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """
You are an expert food label OCR and packaging analyst.
Analyze the provided image of a packaged food label carefully.
Extract the structured information into the exact JSON schema provided below.

Strict Requirements:
1. Use null for any field that is NOT clearly visible or declared on the label. Never fabricate, guess, or assume missing values.
2. Never treat a missing nutrient as zero (0). Only output 0 if the label explicitly declares 0 (e.g., '0g', '0mg').
3. For nutrition_facts, extract values per 100g or per 100ml whenever available. If only per-serving values are given, extract them and indicate "per_serving" in nutrition_basis.
4. Extract exact nutrient numbers without units in the float fields. Pay attention to g vs mg vs kcal.
5. In ingredients, provide the exact list of individual ingredients extracted, preserving original names and INS codes (e.g., 'INS 500(ii)').
6. Extract declared allergens (e.g. 'Contains Wheat, Milk') separately from precautionary allergen statements (e.g. 'May contain traces of Peanuts').
7. List any fields you are uncertain about in 'uncertain_fields'.
8. If the image is blurry, corrupted, or does not show a food label, include a clear message in 'warnings'.

Respond ONLY with valid JSON conforming to this schema:
{
  "product_name": null,
  "brand": null,
  "category": null,
  "serving_size": null,
  "nutrition_basis": "per_100g",
  "ingredients": [],
  "raw_ingredients_text": null,
  "nutrition_facts": {
    "energy_kcal": null,
    "total_fat_g": null,
    "saturated_fat_g": null,
    "trans_fat_g": null,
    "carbohydrates_g": null,
    "total_sugar_g": null,
    "added_sugar_g": null,
    "dietary_fibre_g": null,
    "protein_g": null,
    "sodium_mg": null
  },
  "declared_allergens": [],
  "precautionary_allergens": [],
  "uncertain_fields": [],
  "warnings": []
}
"""


def _clean_json_response(raw_text: str) -> Optional[Dict[str, Any]]:
    """Strips markdown code fences and parses JSON safely."""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception as e:
        logger.error(f"Failed to parse LLM vision response as JSON: {e}")
    return None


def prepare_vision_image_bytes(
    image_bytes: bytes,
    max_dim: int = 1024,
    quality: int = 78,
) -> Tuple[bytes, str]:
    """
    Downsamples and compresses image bytes to a lightweight JPEG (~80-150KB)
    specifically for Vision LLM upload. Ensures lightning-fast upload & API response.
    """
    try:
        with Image.open(io.BytesIO(image_bytes)) as pil_img:
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGB")
            w, h = pil_img.size
            if max(w, h) > max_dim:
                scale = float(max_dim) / max(w, h)
                pil_img = pil_img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

            out_buf = io.BytesIO()
            pil_img.save(out_buf, format="JPEG", quality=quality, optimize=True)
            return out_buf.getvalue(), "image/jpeg"
    except Exception as e:
        logger.warning(f"Vision image optimization fallback to original: {e}")
        return image_bytes, "image/jpeg"


class MultimodalVisionExtractor:
    """Orchestrates vision extraction using Gemini or OpenAI with client caching and image compression."""

    def __init__(self):
        self.gemini_api_key = (
            getattr(settings, "GEMINI_API_KEY", None)
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
        )
        self.openai_api_key = (
            getattr(settings, "OPENAI_API_KEY", None)
            or os.getenv("OPENAI_API_KEY")
        )
        self._gemini_client = None
        self._openai_client = None

    def is_available(self) -> bool:
        return bool(self.gemini_api_key or self.openai_api_key)

    def extract_from_image_bytes(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
    ) -> Optional[Dict[str, Any]]:
        """Tries Gemini first, falls back to OpenAI if configured."""
        if not self.is_available():
            logger.info("No vision LLM API key configured (GEMINI_API_KEY / OPENAI_API_KEY).")
            return None

        # Compress and downsample image before sending over network
        comp_bytes, comp_mime = prepare_vision_image_bytes(image_bytes)

        if self.gemini_api_key:
            try:
                res = self._extract_with_gemini(comp_bytes, comp_mime)
                if res:
                    return res
            except Exception as e:
                logger.warning(f"Gemini vision extraction failed: {e}")

        if self.openai_api_key:
            try:
                res = self._extract_with_openai(comp_bytes, comp_mime)
                if res:
                    return res
            except Exception as e:
                logger.warning(f"OpenAI vision extraction failed: {e}")

        return None

    def _extract_with_gemini(
        self,
        image_bytes: bytes,
        mime_type: str,
    ) -> Optional[Dict[str, Any]]:
        from google import genai
        from google.genai import types

        if self._gemini_client is None:
            self._gemini_client = genai.Client(api_key=self.gemini_api_key)

        # Try fast modern production Gemini flash models with fallbacks
        candidate_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest"]
        last_exc = None

        for model_name in candidate_models:
            try:
                response = self._gemini_client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=mime_type,
                        ),
                        EXTRACTION_PROMPT,
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1,
                    ),
                )
                if response and response.text:
                    parsed = _clean_json_response(response.text)
                    if parsed:
                        return parsed
            except Exception as e:
                last_exc = e
                logger.info(f"Gemini model {model_name} attempted: {e}")
                continue

        if last_exc:
            logger.warning(f"All Gemini models exhausted: {last_exc}")
        return None

    def _extract_with_openai(
        self,
        image_bytes: bytes,
        mime_type: str,
    ) -> Optional[Dict[str, Any]]:
        from openai import OpenAI

        if self._openai_client is None:
            self._openai_client = OpenAI(api_key=self.openai_api_key, timeout=8.0)

        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{b64_image}"

        response = self._openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": EXTRACTION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url, "detail": "low"},
                        },
                    ],
                }
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if content:
            return _clean_json_response(content)
        return None
