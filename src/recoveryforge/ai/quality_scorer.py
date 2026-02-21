"""
ML-enhanced quality scoring for recovered files.

Provides confidence scores and recoverability predictions using
heuristic and statistical analysis of file content.
"""

import logging
import math
import os
from collections import Counter
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False


logger = logging.getLogger(__name__)


# File signature magic bytes for format validation
_FILE_SIGNATURES: Dict[str, bytes] = {
    "jpg": b"\xff\xd8\xff",
    "png": b"\x89PNG\r\n\x1a\n",
    "gif": b"GIF8",
    "pdf": b"%PDF",
    "zip": b"PK\x03\x04",
    "docx": b"PK\x03\x04",
    "xlsx": b"PK\x03\x04",
    "mp4": b"\x00\x00\x00",  # partial; ftyp at offset 4
    "avi": b"RIFF",
}


@dataclass
class QualityScore:
    """Quality score for a single file."""
    file_path: str
    score: float  # 0.0 – 1.0
    confidence: float  # Confidence in the score (0.0 – 1.0)
    file_type: str = "unknown"
    details: Dict[str, float] = field(default_factory=dict)


@dataclass
class RecoverabilityPrediction:
    """Prediction of whether a file is worth recovering."""
    file_path: str
    is_recoverable: bool
    probability: float  # 0.0 – 1.0
    reasoning: str = ""


@dataclass
class CorruptionAnalysis:
    """Detailed corruption analysis for a file."""
    file_path: str
    is_corrupt: bool
    corruption_type: str = "none"
    affected_bytes: int = 0
    corruption_percent: float = 0.0
    details: str = ""


@dataclass
class RepairSuggestion:
    """Suggested repair strategy."""
    strategy: str
    priority: int  # 1 = highest
    description: str
    tool: Optional[str] = None


class MLQualityScorer:
    """
    ML-enhanced quality scoring for recovered files.

    Uses statistical analysis and format validation heuristics
    to produce confidence-weighted quality scores.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score_file(self, file_path: str) -> QualityScore:
        """
        Score file quality.

        Args:
            file_path: Path to the file.

        Returns:
            QualityScore with normalized score and confidence.
        """
        path = Path(file_path)
        if not path.exists():
            return QualityScore(file_path=file_path, score=0.0, confidence=0.0,
                                details={"error": 1.0})

        file_type = self._detect_type(file_path)
        details: Dict[str, float] = {}

        size_score = self._score_size(path, details)
        header_score = self._score_header(file_path, file_type, details)
        entropy_score = self._score_entropy(file_path, details)
        format_score = self._score_format(file_path, file_type, details)

        raw_score = (
            size_score * 0.15
            + header_score * 0.35
            + entropy_score * 0.20
            + format_score * 0.30
        )
        score = max(0.0, min(1.0, raw_score))
        confidence = 0.85 if file_type != "unknown" else 0.50

        return QualityScore(
            file_path=file_path,
            score=score,
            confidence=confidence,
            file_type=file_type,
            details=details,
        )

    def predict_recoverability(self, file_path: str) -> RecoverabilityPrediction:
        """
        Predict whether a file is recoverable.

        Args:
            file_path: Path to the file.

        Returns:
            RecoverabilityPrediction with probability and reasoning.
        """
        qs = self.score_file(file_path)
        is_recoverable = qs.score >= 0.4
        reasoning = (
            f"Quality score {qs.score:.2f} "
            f"({'above' if is_recoverable else 'below'} recovery threshold 0.40). "
            f"File type: {qs.file_type}."
        )
        return RecoverabilityPrediction(
            file_path=file_path,
            is_recoverable=is_recoverable,
            probability=qs.score,
            reasoning=reasoning,
        )

    def analyze_corruption(self, file_path: str) -> CorruptionAnalysis:
        """
        Detailed corruption analysis.

        Args:
            file_path: Path to the file.

        Returns:
            CorruptionAnalysis describing the nature and extent of corruption.
        """
        path = Path(file_path)
        if not path.exists():
            return CorruptionAnalysis(
                file_path=file_path, is_corrupt=True,
                corruption_type="missing", details="File not found"
            )

        file_type = self._detect_type(file_path)
        size = path.stat().st_size

        # Check header validity
        header_ok = self._validate_header(file_path, file_type)
        # Check for null-byte regions (sign of corruption)
        null_bytes = self._count_null_regions(file_path)
        null_pct = (null_bytes / size * 100.0) if size > 0 else 0.0

        is_corrupt = not header_ok or null_pct > 20.0

        corruption_type = "none"
        details_parts = []

        if not header_ok:
            corruption_type = "header_corrupt"
            details_parts.append("File header does not match expected signature.")
        if null_pct > 20.0:
            corruption_type = "data_loss" if not header_ok else "partial_data_loss"
            details_parts.append(f"Null-byte regions: {null_pct:.1f}% of file.")

        return CorruptionAnalysis(
            file_path=file_path,
            is_corrupt=is_corrupt,
            corruption_type=corruption_type,
            affected_bytes=null_bytes,
            corruption_percent=null_pct,
            details=" ".join(details_parts) or "No corruption detected.",
        )

    def suggest_repair(self, file_path: str) -> List[RepairSuggestion]:
        """
        Suggest repair strategies for a corrupted file.

        Args:
            file_path: Path to the file.

        Returns:
            List of RepairSuggestion ordered by priority.
        """
        ca = self.analyze_corruption(file_path)
        suggestions: List[RepairSuggestion] = []
        file_type = self._detect_type(file_path)

        if not ca.is_corrupt:
            suggestions.append(RepairSuggestion(
                strategy="no_repair_needed",
                priority=1,
                description="File appears intact. No repair required.",
            ))
            return suggestions

        if file_type in ("jpg", "jpeg"):
            suggestions.append(RepairSuggestion(
                strategy="jpeg_repair",
                priority=1,
                description="Rebuild JPEG markers and reconstruct scan data.",
                tool="FileRepairToolkit.repair_jpeg",
            ))
        elif file_type == "pdf":
            suggestions.append(RepairSuggestion(
                strategy="pdf_repair",
                priority=1,
                description="Rebuild PDF cross-reference table and reconstruct structure.",
                tool="FileRepairToolkit.repair_pdf",
            ))
        elif file_type in ("zip", "docx", "xlsx", "pptx"):
            suggestions.append(RepairSuggestion(
                strategy="archive_repair",
                priority=1,
                description="Attempt to recover ZIP central directory.",
                tool="FileRepairToolkit.repair_archive",
            ))
        else:
            suggestions.append(RepairSuggestion(
                strategy="hex_recovery",
                priority=2,
                description="Hex-level carving to recover partial content.",
            ))

        if ca.corruption_percent > 50.0:
            suggestions.append(RepairSuggestion(
                strategy="partial_extraction",
                priority=3,
                description="Extract any readable content from the damaged file.",
            ))

        return suggestions

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_type(self, file_path: str) -> str:
        """Detect file type from magic bytes."""
        try:
            with open(file_path, "rb") as fh:
                header = fh.read(16)
            for ext, magic in _FILE_SIGNATURES.items():
                if header.startswith(magic):
                    return ext
        except Exception:
            pass
        suffix = Path(file_path).suffix.lower().lstrip(".")
        return suffix if suffix else "unknown"

    def _validate_header(self, file_path: str, file_type: str) -> bool:
        """Validate file header against known signatures."""
        if file_type not in _FILE_SIGNATURES:
            return True  # Cannot validate unknown types
        try:
            with open(file_path, "rb") as fh:
                header = fh.read(16)
            return header.startswith(_FILE_SIGNATURES[file_type])
        except Exception:
            return False

    def _score_size(self, path: Path, details: Dict[str, float]) -> float:
        """Score file based on size (empty files score 0)."""
        size = path.stat().st_size
        if size == 0:
            details["size"] = 0.0
            return 0.0
        score = min(1.0, math.log10(size + 1) / 6.0)  # ~1 MB = 1.0
        details["size"] = round(score, 3)
        return score

    def _score_header(
        self, file_path: str, file_type: str, details: Dict[str, float]
    ) -> float:
        """Score file based on header validity."""
        valid = self._validate_header(file_path, file_type)
        score = 1.0 if valid else 0.0
        details["header"] = score
        return score

    def _score_entropy(self, file_path: str, details: Dict[str, float]) -> float:
        """
        Score based on entropy. Very low or very high entropy is suspicious.
        Normal files: 5–7.5 bits/byte.
        """
        try:
            with open(file_path, "rb") as fh:
                data = fh.read(65536)
            if not data:
                details["entropy"] = 0.0
                return 0.0
            counts = Counter(data)
            total = len(data)
            entropy = -sum(
                (c / total) * math.log2(c / total)
                for c in counts.values() if c > 0
            )
            # Score peaks at ~6.5 bits/byte (typical compressed data)
            score = 1.0 - abs(entropy - 6.5) / 6.5
            score = max(0.0, min(1.0, score))
            details["entropy"] = round(score, 3)
            return score
        except Exception:
            details["entropy"] = 0.0
            return 0.0

    def _score_format(
        self, file_path: str, file_type: str, details: Dict[str, float]
    ) -> float:
        """Format-specific validation scoring."""
        score = 0.8  # Default if we can't do format-specific checks
        try:
            if file_type in ("jpg", "jpeg") and PIL_AVAILABLE:
                img = Image.open(file_path)
                img.verify()
                score = 1.0
            elif file_type == "pdf" and PYPDF2_AVAILABLE:
                with open(file_path, "rb") as fh:
                    reader = PyPDF2.PdfReader(fh, strict=False)
                    _ = len(reader.pages)
                score = 1.0
            elif file_type == "png" and PIL_AVAILABLE:
                img = Image.open(file_path)
                img.verify()
                score = 1.0
        except Exception:
            score = 0.2
        details["format"] = round(score, 3)
        return score

    def _count_null_regions(self, file_path: str, chunk_size: int = 4096) -> int:
        """Count bytes in null-filled chunks (indicates missing data)."""
        null_bytes = 0
        try:
            with open(file_path, "rb") as fh:
                while True:
                    chunk = fh.read(chunk_size)
                    if not chunk:
                        break
                    if chunk == b"\x00" * len(chunk):
                        null_bytes += len(chunk)
        except Exception:
            pass
        return null_bytes
