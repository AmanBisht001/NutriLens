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

    @abstractmethod
    def extract_text(self, image: Union[np.ndarray, bytes]) -> OCRResult:
        """
        Extract text from an image (OpenCV numpy array or raw bytes).
        Returns a structured OCRResult.
        """
        pass


class PaddleOCREngine(BaseOCREngine):
    """
    PaddleOCR implementation for multi-language text recognition
    and text orientation angle classification.
    """

    def __init__(self, lang: str = "en", use_angle_cls: bool = True):
        self.lang = lang
        self.use_angle_cls = use_angle_cls
        self._ocr = None
        self._initialized = False

    def _ensure_initialized(self):
        if self._initialized:
            return
        try:
            from paddleocr import PaddleOCR
            # Initialize PaddleOCR engine
            self._ocr = PaddleOCR(use_angle_cls=self.use_angle_cls, lang=self.lang)
            self._initialized = True
            logger.info("PaddleOCR engine initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            raise RuntimeError(
                f"PaddleOCR is not installed or could not be initialized: {e}"
            )

    def extract_text(self, image: Union[np.ndarray, bytes]) -> OCRResult:
        self._ensure_initialized()

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

        # Run PaddleOCR
        result = self._ocr.ocr(img_cv, cls=self.use_angle_cls)

        ocr_lines: List[OCRLine] = []
        confidences: List[float] = []

        if result and len(result) > 0 and result[0] is not None:
            for item in result[0]:
                box = item[0]
                text, conf = item[1]
                ocr_lines.append(OCRLine(text=str(text), confidence=float(conf), box=box))
                confidences.append(float(conf))

        raw_text = "\n".join(l.text for l in ocr_lines)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

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
