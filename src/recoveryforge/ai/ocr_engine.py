"""
OCR engine using Tesseract for text extraction from images and PDFs.
"""

import logging
import os
import tempfile
from typing import List, Optional
from dataclasses import dataclass, field
from pathlib import Path

try:
    import pytesseract
    from pytesseract import Output
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pdf2image
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    """A block of text with positional information."""
    text: str
    x: int
    y: int
    width: int
    height: int
    confidence: float
    block_num: int = 0
    line_num: int = 0


@dataclass
class Cell:
    """A single cell in a detected table."""
    row: int
    col: int
    text: str


@dataclass
class Table:
    """A table extracted from a document."""
    cells: List[Cell] = field(default_factory=list)
    rows: int = 0
    cols: int = 0

    def to_list(self) -> List[List[str]]:
        """Convert to 2-D list of strings."""
        grid: List[List[str]] = [
            [""] * self.cols for _ in range(self.rows)
        ]
        for cell in self.cells:
            if 0 <= cell.row < self.rows and 0 <= cell.col < self.cols:
                grid[cell.row][cell.col] = cell.text
        return grid


@dataclass
class OCRResult:
    """Full OCR result for a file."""
    text: str
    language: str = "unknown"
    confidence: float = 0.0
    page_count: int = 1
    blocks: List[TextBlock] = field(default_factory=list)
    error: Optional[str] = None


class OCREngine:
    """
    Full OCR capabilities using Tesseract.

    Supports text extraction, language detection, table detection,
    and creation of searchable PDFs from images.
    """

    def __init__(self, languages: List[str] = None):
        """
        Initialize Tesseract with language support.

        Args:
            languages: List of Tesseract language codes (e.g. ['eng', 'fra']).
                       Defaults to ['eng'].
        """
        self.logger = logging.getLogger(__name__)
        self.languages = languages or ["eng"]
        self._lang_string = "+".join(self.languages)

        if not TESSERACT_AVAILABLE:
            self.logger.warning(
                "pytesseract not installed. OCR features unavailable. "
                "Install with: pip install pytesseract"
            )
        if not PIL_AVAILABLE:
            self.logger.warning(
                "Pillow not installed. OCR features unavailable. "
                "Install with: pip install Pillow"
            )

    def _open_image(self, file_path: str) -> Optional["Image.Image"]:
        """Open an image from a path (PIL Image)."""
        if not PIL_AVAILABLE:
            return None
        try:
            return Image.open(file_path)
        except Exception as e:
            self.logger.error(f"Cannot open image {file_path}: {e}")
            return None

    def _pdf_to_images(self, file_path: str) -> List["Image.Image"]:
        """Convert PDF pages to PIL images."""
        if not PDF2IMAGE_AVAILABLE:
            self.logger.warning(
                "pdf2image not installed. PDF OCR unavailable. "
                "Install with: pip install pdf2image"
            )
            return []
        try:
            pages = pdf2image.convert_from_path(file_path)
            return pages
        except Exception as e:
            self.logger.error(f"PDF conversion failed for {file_path}: {e}")
            return []

    def _get_images(self, file_path: str) -> List["Image.Image"]:
        """Return a list of PIL images for any supported file type."""
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return self._pdf_to_images(file_path)
        img = self._open_image(file_path)
        return [img] if img is not None else []

    def extract_text(self, file_path: str) -> OCRResult:
        """
        Extract all text from an image or PDF.

        Args:
            file_path: Path to the image or PDF file.

        Returns:
            OCRResult containing extracted text and metadata.
        """
        if not TESSERACT_AVAILABLE or not PIL_AVAILABLE:
            return OCRResult(text="", error="Tesseract or Pillow not available")

        if not Path(file_path).exists():
            return OCRResult(text="", error=f"File not found: {file_path}")

        images = self._get_images(file_path)
        if not images:
            return OCRResult(text="", error="No images to process")

        all_text: List[str] = []
        total_conf = 0.0
        page_count = len(images)

        for img in images:
            try:
                data = pytesseract.image_to_data(
                    img, lang=self._lang_string, output_type=Output.DICT
                )
                page_text = pytesseract.image_to_string(img, lang=self._lang_string)
                all_text.append(page_text.strip())

                # Average confidence from non-empty words
                confs = [
                    int(c) for c, t in zip(data["conf"], data["text"])
                    if str(c).lstrip("-").isdigit() and int(c) >= 0 and t.strip()
                ]
                if confs:
                    total_conf += sum(confs) / len(confs)
            except Exception as e:
                self.logger.error(f"OCR failed on page: {e}")

        confidence = total_conf / page_count if page_count > 0 else 0.0
        combined_text = "\n\n".join(all_text)

        return OCRResult(
            text=combined_text,
            language=self._lang_string,
            confidence=confidence,
            page_count=page_count,
        )

    def extract_with_positions(self, file_path: str) -> List[TextBlock]:
        """
        Extract text with bounding box positions.

        Args:
            file_path: Path to the image or PDF.

        Returns:
            List of TextBlock objects with position data.
        """
        if not TESSERACT_AVAILABLE or not PIL_AVAILABLE:
            return []

        if not Path(file_path).exists():
            return []

        images = self._get_images(file_path)
        if not images:
            return []

        blocks: List[TextBlock] = []
        # Process first page only for positional data
        img = images[0]
        try:
            data = pytesseract.image_to_data(
                img, lang=self._lang_string, output_type=Output.DICT
            )
            n = len(data["text"])
            for i in range(n):
                word = data["text"][i].strip()
                if not word:
                    continue
                conf_raw = data["conf"][i]
                conf = float(conf_raw) if str(conf_raw).lstrip("-").isdigit() else -1.0
                if conf < 0:
                    continue
                blocks.append(TextBlock(
                    text=word,
                    x=int(data["left"][i]),
                    y=int(data["top"][i]),
                    width=int(data["width"][i]),
                    height=int(data["height"][i]),
                    confidence=conf / 100.0,
                    block_num=int(data["block_num"][i]),
                    line_num=int(data["line_num"][i]),
                ))
        except Exception as e:
            self.logger.error(f"Positional OCR failed: {e}")

        return blocks

    def detect_language(self, file_path: str) -> str:
        """
        Auto-detect the language of a document.

        Args:
            file_path: Path to the image or PDF.

        Returns:
            Detected language code (e.g. 'eng', 'fra').
        """
        if not TESSERACT_AVAILABLE or not PIL_AVAILABLE:
            return "unknown"

        images = self._get_images(file_path)
        if not images:
            return "unknown"

        try:
            # Use OSD (orientation and script detection) to get language hints
            osd = pytesseract.image_to_osd(images[0], output_type=Output.DICT)
            script = osd.get("script", "")
            script_to_lang = {
                "Latin": "eng",
                "Arabic": "ara",
                "Cyrillic": "rus",
                "Han": "chi_sim",
                "Devanagari": "hin",
                "Japanese": "jpn",
                "Korean": "kor",
            }
            return script_to_lang.get(script, "eng")
        except Exception as e:
            self.logger.debug(f"Language detection failed: {e}")
            return "eng"

    def extract_tables(self, file_path: str) -> List[Table]:
        """
        Extract tabular data from a document using heuristic line grouping.

        Args:
            file_path: Path to the image or PDF.

        Returns:
            List of Table objects.
        """
        blocks = self.extract_with_positions(file_path)
        if not blocks:
            return []

        # Group blocks by approximate row (y-coordinate proximity)
        row_tolerance = 10
        rows: dict = {}
        for block in blocks:
            row_key = round(block.y / row_tolerance) * row_tolerance
            rows.setdefault(row_key, []).append(block)

        sorted_row_keys = sorted(rows.keys())
        if len(sorted_row_keys) < 2:
            return []

        # Sort each row by x position to determine columns
        row_lists = [
            sorted(rows[k], key=lambda b: b.x) for k in sorted_row_keys
        ]
        max_cols = max(len(r) for r in row_lists)
        if max_cols < 2:
            return []

        table = Table(rows=len(row_lists), cols=max_cols)
        for r_idx, row in enumerate(row_lists):
            for c_idx, block in enumerate(row):
                table.cells.append(Cell(row=r_idx, col=c_idx, text=block.text))

        return [table]

    def make_searchable_pdf(self, image_path: str, output_path: str) -> bool:
        """
        Convert an image to a searchable PDF using Tesseract.

        Args:
            image_path: Path to the source image.
            output_path: Destination path for the searchable PDF.

        Returns:
            True if successful, False otherwise.
        """
        if not TESSERACT_AVAILABLE or not PIL_AVAILABLE:
            self.logger.error("Tesseract or Pillow not available")
            return False

        if not Path(image_path).exists():
            self.logger.error(f"Image not found: {image_path}")
            return False

        try:
            img = self._open_image(image_path)
            if img is None:
                return False

            # Tesseract can generate a PDF directly via the pdf config
            out_stem = str(Path(output_path).with_suffix(""))
            pytesseract.pytesseract.run_tesseract(
                image_path,
                out_stem,
                lang=self._lang_string,
                config="pdf",
                nice=0,
                timeout=60,
            )
            return Path(output_path).exists()
        except Exception as e:
            self.logger.error(f"Searchable PDF creation failed: {e}")
            return False
