"""
AI-driven file fragment reassembly.

Uses entropy boundary detection and content-based heuristics to
detect file boundaries and predict correct fragment ordering.
"""

import logging
import math
import struct
from collections import Counter
from typing import List, Optional
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


# Known file header signatures (magic bytes)
_FILE_HEADERS: List[tuple] = [
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"GIF8", "gif"),
    (b"%PDF", "pdf"),
    (b"PK\x03\x04", "zip"),
    (b"RIFF", "avi"),
    (b"\x1f\x8b", "gz"),
    (b"BM", "bmp"),
    (b"\x00\x00\x01\xba", "mpg"),
    (b"\x00\x00\x01\xb3", "mpg"),
    (b"ID3", "mp3"),
    (b"fLaC", "flac"),
    (b"OggS", "ogg"),
]

_WINDOW = 512       # Bytes per entropy window
_ENTROPY_JUMP = 1.5  # Minimum entropy change to signal a boundary


@dataclass
class FragmentAnalysis:
    """Analysis of a single binary fragment."""
    index: int
    size: int
    entropy: float
    detected_type: Optional[str] = None
    has_header: bool = False
    has_footer: bool = False


@dataclass
class ValidationResult:
    """Result of assembled file validation."""
    is_valid: bool
    file_type: str = "unknown"
    size: int = 0
    details: str = ""


def _calculate_entropy(data: bytes) -> float:
    """Calculate Shannon entropy of a byte sequence."""
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((c / total) * math.log2(c / total) for c in counts.values() if c > 0)


def _detect_type(data: bytes) -> Optional[str]:
    """Detect file type from magic bytes at the start of data."""
    for magic, ftype in _FILE_HEADERS:
        if data[:len(magic)] == magic:
            return ftype
    return None


class AIFragmentAssembler:
    """
    Reassemble fragmented files using entropy boundary detection
    and content-based heuristics.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def analyze_fragments(self, fragments: List[bytes]) -> List[FragmentAnalysis]:
        """
        Analyze fragment characteristics.

        Args:
            fragments: List of binary fragments.

        Returns:
            List of FragmentAnalysis objects.
        """
        analyses: List[FragmentAnalysis] = []
        for idx, frag in enumerate(fragments):
            entropy = _calculate_entropy(frag)
            detected_type = _detect_type(frag)
            analyses.append(FragmentAnalysis(
                index=idx,
                size=len(frag),
                entropy=entropy,
                detected_type=detected_type,
                has_header=(detected_type is not None),
            ))
        return analyses

    def find_boundaries(self, data: bytes) -> List[int]:
        """
        Find file boundaries in a raw byte stream using entropy changes.

        Significant entropy transitions indicate where one file ends and
        another begins (common in sequential raw disk images).

        Args:
            data: Raw byte data.

        Returns:
            List of byte offsets where boundaries are detected.
        """
        boundaries: List[int] = [0]
        prev_entropy: Optional[float] = None

        for offset in range(0, len(data) - _WINDOW, _WINDOW):
            window = data[offset: offset + _WINDOW]
            ent = _calculate_entropy(window)
            if prev_entropy is not None and abs(ent - prev_entropy) >= _ENTROPY_JUMP:
                boundaries.append(offset)
            prev_entropy = ent

        # Also detect known file headers as explicit boundaries
        for magic, _ in _FILE_HEADERS:
            pos = 0
            while True:
                pos = data.find(magic, pos)
                if pos == -1:
                    break
                if pos not in boundaries:
                    boundaries.append(pos)
                pos += 1

        boundaries.sort()
        return boundaries

    def predict_order(self, fragments: List[bytes]) -> List[int]:
        """
        Predict the correct assembly order for fragments.

        Strategy:
        1. Fragments with known headers go first (sorted by type priority).
        2. Remaining fragments are sorted by entropy similarity to neighbouring
           fragments (greedy nearest-neighbour).

        Args:
            fragments: List of binary fragments in arbitrary order.

        Returns:
            List of indices representing the predicted correct order.
        """
        if not fragments:
            return []

        n = len(fragments)
        analyses = self.analyze_fragments(fragments)

        # Separate header fragments from body fragments
        header_indices = [a.index for a in analyses if a.has_header]
        other_indices = [a.index for a in analyses if not a.has_header]

        # Sort header fragments by type-based priority (jpg first, then others)
        _type_priority = {"jpg": 0, "png": 1, "gif": 2, "pdf": 3, "zip": 4}
        header_indices.sort(
            key=lambda i: _type_priority.get(
                analyses[i].detected_type or "", 99
            )
        )

        # Greedy sort of remaining fragments by entropy proximity
        ordered_others: List[int] = []
        remaining = list(other_indices)
        if remaining:
            current = remaining.pop(0)
            ordered_others.append(current)
            while remaining:
                current_ent = analyses[current].entropy
                closest = min(
                    remaining,
                    key=lambda i: abs(analyses[i].entropy - current_ent),
                )
                remaining.remove(closest)
                ordered_others.append(closest)
                current = closest

        return header_indices + ordered_others

    def reassemble(self, fragments: List[bytes], file_type: str = "") -> bytes:
        """
        Reassemble fragments into a complete file.

        Args:
            fragments: List of binary fragments.
            file_type: Expected output file type (hint only).

        Returns:
            Assembled bytes.
        """
        if not fragments:
            return b""

        order = self.predict_order(fragments)
        return b"".join(fragments[i] for i in order)

    def validate_assembly(
        self, assembled: bytes, file_type: str
    ) -> ValidationResult:
        """
        Validate a reassembled file.

        Args:
            assembled: Assembled bytes to validate.
            file_type: Expected file type (e.g. 'jpg', 'pdf').

        Returns:
            ValidationResult indicating whether the file is structurally valid.
        """
        if not assembled:
            return ValidationResult(is_valid=False, details="Empty data")

        detected = _detect_type(assembled)
        size = len(assembled)

        if file_type and detected and detected != file_type:
            return ValidationResult(
                is_valid=False,
                file_type=detected,
                size=size,
                details=f"Header mismatch: expected {file_type}, got {detected}.",
            )

        is_valid = detected is not None
        return ValidationResult(
            is_valid=is_valid,
            file_type=detected or "unknown",
            size=size,
            details="Header signature valid." if is_valid else "No recognisable file header.",
        )
