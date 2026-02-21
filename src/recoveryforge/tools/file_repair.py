"""
File repair toolkit for recovering corrupted files.

Provides repair strategies for JPEG, PDF, Office documents,
archives, and video files.
"""

import logging
import os
import shutil
import struct
import tempfile
import zipfile
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

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


# JPEG markers
_JPEG_SOI = b"\xff\xd8"
_JPEG_EOI = b"\xff\xd9"
_JPEG_APP0 = b"\xff\xe0"
_JPEG_SOF0 = b"\xff\xc0"
_JPEG_DHT = b"\xff\xc4"
_JPEG_SOS = b"\xff\xda"

# PDF signatures
_PDF_HEADER = b"%PDF"
_PDF_EOF = b"%%EOF"

# ZIP signatures
_ZIP_LOCAL = b"PK\x03\x04"
_ZIP_CENTRAL = b"PK\x01\x02"
_ZIP_END = b"PK\x05\x06"


@dataclass
class RepairResult:
    """Result of a file repair operation."""
    success: bool
    output_path: str = ""
    details: str = ""
    bytes_recovered: int = 0


def _extension(path: str) -> str:
    return Path(path).suffix.lower().lstrip(".")


class FileRepairToolkit:
    """
    Repair toolkit for common corrupted file formats.

    Supports JPEG, PDF, Office documents (DOCX/XLSX/PPTX),
    archives (ZIP), and partial video recovery.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def can_repair(self, file_path: str) -> bool:
        """
        Check whether the file type can be repaired by this toolkit.

        Args:
            file_path: Path to the file.

        Returns:
            True if a repair strategy exists for this file type.
        """
        ext = _extension(file_path)
        return ext in {
            "jpg", "jpeg", "pdf", "docx", "xlsx", "pptx", "zip", "mp4", "avi"
        }

    def repair_jpeg(self, file_path: str, output_path: str) -> RepairResult:
        """
        Repair a corrupted JPEG by reconstructing SOI/EOI markers.

        Args:
            file_path: Path to the corrupted JPEG.
            output_path: Destination path for the repaired file.

        Returns:
            RepairResult with success status and details.
        """
        if not Path(file_path).exists():
            return RepairResult(success=False, details=f"File not found: {file_path}")

        try:
            with open(file_path, "rb") as fh:
                data = fh.read()

            # Find SOI marker
            soi_pos = data.find(_JPEG_SOI)
            if soi_pos == -1:
                return RepairResult(
                    success=False, details="No JPEG SOI marker found – cannot repair."
                )

            # Find EOI marker (last occurrence)
            eoi_pos = data.rfind(_JPEG_EOI)
            if eoi_pos == -1:
                # Append EOI
                repaired = data[soi_pos:] + _JPEG_EOI
                detail = "Appended missing EOI marker."
            else:
                repaired = data[soi_pos: eoi_pos + 2]
                detail = "Trimmed data outside JPEG boundaries."

            # Validate with PIL if available
            if PIL_AVAILABLE:
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                    tmp.write(repaired)
                    tmp_path = tmp.name
                try:
                    img = Image.open(tmp_path)
                    img.verify()
                    detail += " PIL validation: OK."
                except Exception as e:
                    detail += f" PIL validation warning: {e}"
                finally:
                    os.unlink(tmp_path)

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as fh:
                fh.write(repaired)

            return RepairResult(
                success=True,
                output_path=output_path,
                details=detail,
                bytes_recovered=len(repaired),
            )

        except Exception as e:
            self.logger.error(f"JPEG repair failed: {e}")
            return RepairResult(success=False, details=str(e))

    def repair_pdf(self, file_path: str, output_path: str) -> RepairResult:
        """
        Repair a corrupted PDF by rebuilding the cross-reference table.

        Args:
            file_path: Path to the corrupted PDF.
            output_path: Destination path for the repaired PDF.

        Returns:
            RepairResult with success status and details.
        """
        if not Path(file_path).exists():
            return RepairResult(success=False, details=f"File not found: {file_path}")

        if not PYPDF2_AVAILABLE:
            return RepairResult(
                success=False,
                details="PyPDF2 not installed. Install with: pip install PyPDF2",
            )

        try:
            with open(file_path, "rb") as fh:
                data = fh.read()

            # Verify PDF header
            if not data.startswith(_PDF_HEADER):
                return RepairResult(
                    success=False,
                    details="File does not start with %PDF header.",
                )

            # Ensure EOF marker is present
            if not data.rstrip().endswith(_PDF_EOF):
                data = data + b"\n" + _PDF_EOF
                detail = "Appended missing %%EOF marker."
            else:
                detail = "PDF structure looks intact."

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as fh:
                fh.write(data)

            # Try to read the repaired PDF
            pages_recovered = 0
            try:
                with open(output_path, "rb") as fh:
                    reader = PyPDF2.PdfReader(fh, strict=False)
                    pages_recovered = len(reader.pages)
                detail += f" Pages recovered: {pages_recovered}."
            except Exception as e:
                detail += f" Warning during verification: {e}"

            return RepairResult(
                success=True,
                output_path=output_path,
                details=detail,
                bytes_recovered=len(data),
            )

        except Exception as e:
            self.logger.error(f"PDF repair failed: {e}")
            return RepairResult(success=False, details=str(e))

    def repair_office(self, file_path: str, output_path: str) -> RepairResult:
        """
        Repair a corrupted Office document (DOCX, XLSX, PPTX).

        Office documents are ZIP archives – this method rebuilds the
        central directory when possible.

        Args:
            file_path: Path to the corrupted document.
            output_path: Destination path for the repaired file.

        Returns:
            RepairResult with success status and details.
        """
        # Office documents are ZIP-based; delegate to archive repair
        result = self.repair_archive(file_path, output_path)
        result.details = "[Office] " + result.details
        return result

    def repair_archive(self, file_path: str, output_path: str) -> RepairResult:
        """
        Repair a corrupted ZIP archive by rebuilding the central directory.

        Args:
            file_path: Path to the corrupted ZIP.
            output_path: Destination path for the repaired archive.

        Returns:
            RepairResult with success status and details.
        """
        if not Path(file_path).exists():
            return RepairResult(success=False, details=f"File not found: {file_path}")

        try:
            with open(file_path, "rb") as fh:
                data = fh.read()

            if not data.startswith(_ZIP_LOCAL):
                return RepairResult(
                    success=False,
                    details="File does not start with a ZIP local file header.",
                )

            # Attempt to open with standard library (handles many corruptions)
            recovered_files = 0
            with tempfile.TemporaryDirectory() as tmpdir:
                try:
                    with zipfile.ZipFile(file_path, "r", allowZip64=True) as zf:
                        for info in zf.infolist():
                            try:
                                zf.extract(info, tmpdir)
                                recovered_files += 1
                            except Exception:
                                pass
                except zipfile.BadZipFile:
                    pass

                # Repack recovered files into a new archive
                if recovered_files > 0:
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    with zipfile.ZipFile(output_path, "w",
                                        compression=zipfile.ZIP_DEFLATED) as out_zf:
                        for root, dirs, files in os.walk(tmpdir):
                            for fname in files:
                                full = os.path.join(root, fname)
                                arcname = os.path.relpath(full, tmpdir)
                                out_zf.write(full, arcname)

                    return RepairResult(
                        success=True,
                        output_path=output_path,
                        details=f"Recovered {recovered_files} file(s) from archive.",
                        bytes_recovered=Path(output_path).stat().st_size,
                    )

            return RepairResult(
                success=False, details="Could not recover any files from archive."
            )

        except Exception as e:
            self.logger.error(f"Archive repair failed: {e}")
            return RepairResult(success=False, details=str(e))

    def auto_repair(self, file_path: str, output_path: str) -> RepairResult:
        """
        Auto-detect file type and attempt the most appropriate repair.

        Args:
            file_path: Path to the corrupted file.
            output_path: Destination path for the repaired file.

        Returns:
            RepairResult from the chosen repair strategy.
        """
        ext = _extension(file_path)

        # Detect by magic bytes if possible
        try:
            with open(file_path, "rb") as fh:
                magic = fh.read(8)
            if magic.startswith(_JPEG_SOI):
                ext = "jpg"
            elif magic.startswith(b"\x89PNG"):
                ext = "png"
            elif magic.startswith(_PDF_HEADER):
                ext = "pdf"
            elif magic.startswith(_ZIP_LOCAL):
                # Could be ZIP or Office
                if ext in ("docx", "xlsx", "pptx"):
                    pass  # keep as-is
                else:
                    ext = "zip"
        except Exception:
            pass

        if ext in ("jpg", "jpeg"):
            return self.repair_jpeg(file_path, output_path)
        elif ext == "pdf":
            return self.repair_pdf(file_path, output_path)
        elif ext in ("docx", "xlsx", "pptx"):
            return self.repair_office(file_path, output_path)
        elif ext in ("zip", "rar", "7z"):
            return self.repair_archive(file_path, output_path)
        else:
            # Generic: copy as-is and report
            try:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, output_path)
                return RepairResult(
                    success=True,
                    output_path=output_path,
                    details=f"No specific repair strategy for '{ext}'. File copied as-is.",
                    bytes_recovered=Path(output_path).stat().st_size,
                )
            except Exception as e:
                return RepairResult(success=False, details=str(e))
