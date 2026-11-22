"""
NutriLens – OCR Engine Adapter (Day 4)
Provides an abstracted OCR interface supporting PaddleOCR, a graceful manual-entry fallback,
and a mock engine for automated testing.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
import logging
import numpy as np
import cv2

logger = logging.getLogger(__name__)


import os
import gc

# Configure lightweight single-threaded CPU execution to reduce memory overhead on constrained cloud hosts
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")


@dataclass
class OCRLine:
    text: str
    confidence: float
    box: Optional[List[List[int]]] = None


@dataclass
class OCRResult:
    raw_text: str
    confidence: float
    lines: List[OCRLine] = field(default_factory=list)
    engine: str = "fallback"
    ocr_available: bool = True
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "confidence": round(self.confidence, 4),
            "lines": [
                {
                    "text": line.text,
                    "confidence": round(line.confidence, 4),
                    "box": line.box,
                }
                for line in self.lines
            ],
            "engine": self.engine,
            "ocr_available": self.ocr_available,
            "notes": self.notes,
        }


class BaseOCREngine(ABC):
    """Abstract OCR engine interface."""

    def is_initialized(self) -> bool:
        """Returns True if the engine model is loaded and ready."""
        return True

    @abstractmethod
    def extract_text(self, image: Union[np.ndarray, bytes]) -> OCRResult:
        """
        Extract text from an image (OpenCV numpy array or raw bytes).
        Returns a structured OCRResult.
        """
        pass


class PaddleOCREngine(BaseOCREngine):
    """
    PaddleOCR implementation for multi-language text recognition.
    Optimized for low-RAM cloud hosting:
    - use_angle_cls=False avoids loading the ~70MB angle classifier neural net
    - enable_mkldnn=False avoids massive memory-mapped cache allocations
    - show_log=False suppresses unnecessary stdout buffers
    - Downscales oversized images before OCR to prevent feature map memory spikes
    """

    def __init__(self, lang: str = "en", use_angle_cls: bool = False):
        self.lang = lang
        self.use_angle_cls = use_angle_cls
        self._ocr = None
        self._initialized = False
        self._init_error = None
        self._paddle_version = "unknown"  # set after import in _ensure_initialized

    def is_initialized(self) -> bool:
        return self._initialized and self._ocr is not None

    def _ensure_initialized(self) -> bool:
        if self._initialized:
            return self._ocr is not None
        try:
            from paddleocr import PaddleOCR
            import paddleocr as _poc_module
            self._paddle_version = getattr(_poc_module, "__version__", "2.x")
            is_v3 = self._paddle_version.startswith("3.")

            if is_v3:
                # PaddleOCR 3.x API: use_doc_orientation_classify replaces use_angle_cls
                # show_log=False suppresses heavy paddle framework output
                self._ocr = PaddleOCR(
                    lang=self.lang,
                    use_doc_orientation_classify=False,
                    show_log=False,
                )
                logger.info(
                    f"PaddleOCR {self._paddle_version} (3.x) engine initialized "
                    f"(use_doc_orientation_classify=False, predict() API)."
                )
            else:
                # PaddleOCR 2.x legacy API
                self._ocr = PaddleOCR(
                    use_angle_cls=self.use_angle_cls,
                    lang=self.lang,
                    enable_mkldnn=False,
                    show_log=False,
                )
                logger.info(
                    f"PaddleOCR {self._paddle_version} (2.x) engine initialized "
                    f"(use_angle_cls={self.use_angle_cls}, ocr() API)."
                )
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            self._initialized = True
            self._ocr = None
            self._init_error = str(e)
            self._paddle_version = "unknown"
            return False

    def _extract_lines_v3(self, result_iterable) -> List[OCRLine]:
        """Parse PaddleOCR 3.x predict() result objects into OCRLine list."""
        ocr_lines: List[OCRLine] = []
        try:
            for res in result_iterable:
                # res.json has: dt_polys, rec_texts, rec_scores
                res_dict = None
                if hasattr(res, "json"):
                    res_dict = res.json
                elif hasattr(res, "res"):
                    res_dict = res.res
                elif isinstance(res, dict):
                    res_dict = res

                if not res_dict:
                    logger.warning("[OCR_V3] Result object has no .json/.res attribute; skipping.")
                    continue

                rec_texts = res_dict.get("rec_texts", [])
                rec_scores = res_dict.get("rec_scores", [])
                dt_polys = res_dict.get("dt_polys", [])

                logger.info(
                    f"[OCR_V3] Detected {len(rec_texts)} text regions from predict()."
                )

                for idx, (text, score) in enumerate(zip(rec_texts, rec_scores)):
                    if not str(text).strip():
                        continue
                    box = None
                    if idx < len(dt_polys):
                        poly = dt_polys[idx]
                        # Convert numpy polygon to list of [x, y] pairs
                        try:
                            box = [[int(p[0]), int(p[1])] for p in poly]
                        except Exception:
                            box = None
                    ocr_lines.append(
                        OCRLine(
                            text=str(text).strip(),
                            confidence=float(score),
                            box=box,
                        )
                    )
        except Exception as e:
            logger.error(f"[OCR_V3] Failed to parse 3.x predict() result: {e}")
        return ocr_lines

    def _extract_lines_v2(self, result) -> List[OCRLine]:
        """Parse PaddleOCR 2.x ocr() result into OCRLine list."""
        ocr_lines: List[OCRLine] = []
        logger.info(
            f"[OCR_V2] result type={type(result)} "
            f"len0={len(result[0]) if result and result[0] is not None else 'N/A'}"
        )
        if result and len(result) > 0 and result[0] is not None and len(result[0]) > 0:
            for item in result[0]:
                try:
                    box = item[0]
                    text, conf = item[1]
                    if not str(text).strip():
                        continue
                    ocr_lines.append(
                        OCRLine(text=str(text).strip(), confidence=float(conf), box=box)
                    )
                except (IndexError, TypeError, ValueError) as e:
                    logger.warning(f"[OCR_V2] Skipping malformed item: {e}")
        return ocr_lines

    def extract_text(self, image: Union[np.ndarray, bytes]) -> OCRResult:
        if not self._ensure_initialized() or self._ocr is None:
            err_msg = self._init_error or "PaddleOCR engine is not available"
            logger.warning(f"PaddleOCR fallback triggered: {err_msg}")
            return OCRResult(
                raw_text="",
                confidence=0.0,
                lines=[],
                engine="fallback",
                ocr_available=False,
                notes=f"OCR Engine Unavailable: {err_msg}. Please verify image or enter manually.",
            )

        is_v3 = getattr(self, "_paddle_version", "2.x").startswith("3.")

        # If bytes passed, decode to OpenCV BGR
        if isinstance(image, bytes):
            nparr = np.frombuffer(image, np.uint8)
            img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            img_cv = image

        if img_cv is None:
            return OCRResult(
                raw_text="",
                confidence=0.0,
                lines=[],
                engine="paddleocr",
                ocr_available=True,
                notes="Failed to decode image input.",
            )

        # Ensure max dimension does not exceed 1600px.
        # Food labels with small-text nutrition tables need higher resolution than 960px for
        # accurate OCR — 960px was causing missed characters on dense Indian label text.
        h, w = img_cv.shape[:2]
        max_dim = max(h, w)
        if max_dim > 1600:
            scale = 1600.0 / max_dim
            new_w, new_h = int(w * scale), int(h * scale)
            img_cv = cv2.resize(img_cv, (new_w, new_h), interpolation=cv2.INTER_AREA)
            logger.debug(f"[OCR] Resized image to {new_w}x{new_h} for OCR.")

        # Ensure 3-channel BGR for PaddleOCR
        if len(img_cv.shape) == 2:
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_GRAY2BGR)

        ocr_lines: List[OCRLine] = []

        # ── PaddleOCR 3.x path ──────────────────────────────────────────────
        if is_v3:
            try:
                result_iter = self._ocr.predict(img_cv)
                ocr_lines = self._extract_lines_v3(result_iter)
            except Exception as e:
                logger.error(f"[OCR_V3] predict() failed: {e}")
                # Graceful fallback: attempt legacy .ocr() in case wrapper still works
                try:
                    result_legacy = self._ocr.ocr(img_cv, cls=False)
                    ocr_lines = self._extract_lines_v2(result_legacy)
                    logger.info("[OCR_V3→V2] Fell back to .ocr() after predict() failure.")
                except Exception as e2:
                    logger.error(f"[OCR_V3→V2] .ocr() fallback also failed: {e2}")
                    return OCRResult(
                        raw_text="",
                        confidence=0.0,
                        lines=[],
                        engine="fallback",
                        ocr_available=False,
                        notes=f"OCR Inference Error (v3): {e}; fallback also failed: {e2}",
                    )
        # ── PaddleOCR 2.x path ──────────────────────────────────────────────
        else:
            try:
                result = self._ocr.ocr(img_cv, cls=self.use_angle_cls)
                ocr_lines = self._extract_lines_v2(result)
                del result
            except Exception as e:
                logger.error(f"[OCR_V2] .ocr() failed: {e}")
                return OCRResult(
                    raw_text="",
                    confidence=0.0,
                    lines=[],
                    engine="fallback",
                    ocr_available=False,
                    notes=f"OCR Inference Error: {e}",
                )

        raw_text = "\n".join(line.text for line in ocr_lines)
        confidences = [line.confidence for line in ocr_lines]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

        logger.info(
            f"[OCR] Extracted {len(ocr_lines)} lines, avg_conf={avg_conf:.4f}, "
            f"chars={len(raw_text)}, paddle_ver={getattr(self, '_paddle_version', '?')}"
        )

        gc.collect()

        return OCRResult(
            raw_text=raw_text,
            confidence=avg_conf,
            lines=ocr_lines,
            engine="paddleocr",
            ocr_available=True,
        )


class FallbackOCREngine(BaseOCREngine):
    """
    Clearly labelled manual-entry fallback when PaddleOCR is not installed or configured.
    Does NOT fabricate extraction results.
    """

    def __init__(self, reason: str = "PaddleOCR engine is not configured in this environment."):
        self.reason = reason

    def is_initialized(self) -> bool:
        return False

    def extract_text(self, image: Union[np.ndarray, bytes]) -> OCRResult:
        return OCRResult(
            raw_text="",
            confidence=0.0,
            lines=[],
            engine="fallback",
            ocr_available=False,
            notes=f"OCR Engine Unavailable: {self.reason}. Please input product details manually.",
        )


class MockOCREngine(BaseOCREngine):
    """
    Test-only engine supporting deterministic OCR simulation
    for unit tests and controlled fixtures.
    """

    def __init__(self, predefined_text: Optional[str] = None, confidence: float = 0.95):
        self.predefined_text = predefined_text
        self.confidence = confidence

    def is_initialized(self) -> bool:
        return True

    def set_text(self, text: str, confidence: float = 0.95):
        self.predefined_text = text
        self.confidence = confidence

    def extract_text(self, image: Union[np.ndarray, bytes]) -> OCRResult:
        text = self.predefined_text or ""
        lines = [
            OCRLine(text=line.strip(), confidence=self.confidence)
            for line in text.split("\n")
            if line.strip()
        ]
        return OCRResult(
            raw_text=text,
            confidence=self.confidence,
            lines=lines,
            engine="mock",
            ocr_available=True,
        )


# Global singleton or active engine
_ACTIVE_ENGINE: Optional[BaseOCREngine] = None


def set_active_engine(engine: BaseOCREngine) -> None:
    """Override active OCR engine (e.g. for testing)."""
    global _ACTIVE_ENGINE
    _ACTIVE_ENGINE = engine


def get_ocr_engine() -> BaseOCREngine:
    """
    Returns the active OCR engine.
    Attempts PaddleOCR first; falls back cleanly to FallbackOCREngine if unavailable.
    """
    global _ACTIVE_ENGINE
    if _ACTIVE_ENGINE is not None:
        return _ACTIVE_ENGINE

    try:
        import paddleocr  # check if importable
        engine = PaddleOCREngine()
        _ACTIVE_ENGINE = engine
        return engine
    except Exception as e:
        logger.warning(
            f"PaddleOCR is not available ({e}). Using FallbackOCREngine with manual entry."
        )
        engine = FallbackOCREngine(
            reason=f"PaddleOCR package not importable: {e}"
        )
        _ACTIVE_ENGINE = engine
        return engine
