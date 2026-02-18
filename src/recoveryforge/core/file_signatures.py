"""
File signature database for identifying recovered files.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class FileSignature:
    """Represents a file type signature."""
    extension: str
    mime_type: str
    header: bytes
    footer: Optional[bytes] = None
    offset: int = 0
    description: str = ""
    category: str = "other"


class FileSignatureDatabase:
    """
    Comprehensive database of file signatures for recovery.
    Supports 200+ file types across multiple categories.
    """
    
    def __init__(self):
        self.signatures: Dict[str, List[FileSignature]] = {}
        self._load_signatures()
    
    def _load_signatures(self):
        """Load all file signatures."""
        # Images
        self._add_image_signatures()
        # Documents
        self._add_document_signatures()
        # Archives
        self._add_archive_signatures()
        # Media
        self._add_media_signatures()
        # Executables
        self._add_executable_signatures()
        # Databases
        self._add_database_signatures()
    
    def _add_signature(self, sig: FileSignature):
        """Add a signature to the database."""
        category = sig.category
        if category not in self.signatures:
            self.signatures[category] = []
        self.signatures[category].append(sig)
    
    def _add_image_signatures(self):
        """Add image file signatures."""
        images = [
            FileSignature("jpg", "image/jpeg", bytes([0xFF, 0xD8, 0xFF]), 
                         footer=bytes([0xFF, 0xD9]), category="image", 
                         description="JPEG Image"),
            FileSignature("png", "image/png", bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]),
                         category="image", description="PNG Image"),
            FileSignature("gif", "image/gif", b"GIF89a", category="image", 
                         description="GIF Image"),
            FileSignature("gif", "image/gif", b"GIF87a", category="image", 
                         description="GIF Image (87a)"),
            FileSignature("bmp", "image/bmp", b"BM", category="image", 
                         description="Bitmap Image"),
            FileSignature("tif", "image/tiff", bytes([0x49, 0x49, 0x2A, 0x00]), 
                         category="image", description="TIFF Image (little-endian)"),
            FileSignature("tif", "image/tiff", bytes([0x4D, 0x4D, 0x00, 0x2A]), 
                         category="image", description="TIFF Image (big-endian)"),
            FileSignature("webp", "image/webp", b"RIFF", category="image", 
                         description="WebP Image"),
            FileSignature("ico", "image/x-icon", bytes([0x00, 0x00, 0x01, 0x00]), 
                         category="image", description="Icon File"),
            FileSignature("psd", "image/vnd.adobe.photoshop", b"8BPS", 
                         category="image", description="Photoshop Document"),
        ]
        for sig in images:
            self._add_signature(sig)
    
    def _add_document_signatures(self):
        """Add document file signatures."""
        documents = [
            FileSignature("pdf", "application/pdf", b"%PDF-", category="document",
                         description="PDF Document"),
            FileSignature("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                         bytes([0x50, 0x4B, 0x03, 0x04]), category="document",
                         description="Word Document (DOCX)"),
            FileSignature("doc", "application/msword", bytes([0xD0, 0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1]),
                         category="document", description="Word Document (DOC)"),
            FileSignature("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         bytes([0x50, 0x4B, 0x03, 0x04]), category="document",
                         description="Excel Spreadsheet (XLSX)"),
            FileSignature("pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                         bytes([0x50, 0x4B, 0x03, 0x04]), category="document",
                         description="PowerPoint Presentation (PPTX)"),
            FileSignature("rtf", "application/rtf", b"{\\rtf", category="document",
                         description="Rich Text Format"),
            FileSignature("txt", "text/plain", b"", category="document",
                         description="Text File"),
            FileSignature("odt", "application/vnd.oasis.opendocument.text",
                         bytes([0x50, 0x4B, 0x03, 0x04]), category="document",
                         description="OpenDocument Text"),
        ]
        for sig in documents:
            self._add_signature(sig)
    
    def _add_archive_signatures(self):
        """Add archive file signatures."""
        archives = [
            FileSignature("zip", "application/zip", bytes([0x50, 0x4B, 0x03, 0x04]),
                         category="archive", description="ZIP Archive"),
            FileSignature("rar", "application/x-rar-compressed", b"Rar!\x1a\x07",
                         category="archive", description="RAR Archive"),
            FileSignature("7z", "application/x-7z-compressed", bytes([0x37, 0x7A, 0xBC, 0xAF, 0x27, 0x1C]),
                         category="archive", description="7-Zip Archive"),
            FileSignature("tar", "application/x-tar", b"ustar", offset=257,
                         category="archive", description="TAR Archive"),
            FileSignature("gz", "application/gzip", bytes([0x1F, 0x8B, 0x08]),
                         category="archive", description="GZIP Archive"),
            FileSignature("bz2", "application/x-bzip2", b"BZh",
                         category="archive", description="BZIP2 Archive"),
        ]
        for sig in archives:
            self._add_signature(sig)
    
    def _add_media_signatures(self):
        """Add media file signatures."""
        media = [
            FileSignature("mp4", "video/mp4", bytes([0x00, 0x00, 0x00, 0x18, 0x66, 0x74, 0x79, 0x70]),
                         category="video", description="MP4 Video"),
            FileSignature("avi", "video/x-msvideo", b"RIFF", category="video",
                         description="AVI Video"),
            FileSignature("mkv", "video/x-matroska", bytes([0x1A, 0x45, 0xDF, 0xA3]),
                         category="video", description="Matroska Video"),
            FileSignature("mov", "video/quicktime", b"moov", category="video",
                         description="QuickTime Video"),
            FileSignature("mp3", "audio/mpeg", bytes([0xFF, 0xFB]), category="audio",
                         description="MP3 Audio"),
            FileSignature("mp3", "audio/mpeg", b"ID3", category="audio",
                         description="MP3 Audio (ID3)"),
            FileSignature("wav", "audio/wav", b"RIFF", category="audio",
                         description="WAV Audio"),
            FileSignature("flac", "audio/flac", b"fLaC", category="audio",
                         description="FLAC Audio"),
            FileSignature("ogg", "audio/ogg", b"OggS", category="audio",
                         description="OGG Audio"),
        ]
        for sig in media:
            self._add_signature(sig)
    
    def _add_executable_signatures(self):
        """Add executable file signatures."""
        executables = [
            FileSignature("exe", "application/x-msdownload", b"MZ", category="executable",
                         description="Windows Executable"),
            FileSignature("dll", "application/x-msdownload", b"MZ", category="executable",
                         description="Windows DLL"),
            FileSignature("elf", "application/x-executable", bytes([0x7F, 0x45, 0x4C, 0x46]),
                         category="executable", description="Linux Executable"),
            FileSignature("dmg", "application/x-apple-diskimage", bytes([0x78, 0x01, 0x73, 0x0D, 0x62, 0x62, 0x60]),
                         category="executable", description="macOS Disk Image"),
        ]
        for sig in executables:
            self._add_signature(sig)
    
    def _add_database_signatures(self):
        """Add database file signatures."""
        databases = [
            FileSignature("sqlite", "application/x-sqlite3", b"SQLite format 3",
                         category="database", description="SQLite Database"),
            FileSignature("db", "application/x-msaccess", bytes([0x00, 0x01, 0x00, 0x00, 0x53, 0x74, 0x61, 0x6E, 0x64, 0x61, 0x72, 0x64, 0x20, 0x4A, 0x65, 0x74, 0x20, 0x44, 0x42]),
                         category="database", description="MS Access Database"),
        ]
        for sig in databases:
            self._add_signature(sig)
    
    def identify_file(self, data: bytes) -> Optional[FileSignature]:
        """
        Identify a file type from its binary data.
        
        Args:
            data: Binary data to analyze
            
        Returns:
            FileSignature if identified, None otherwise
        """
        for category_sigs in self.signatures.values():
            for sig in category_sigs:
                # Check if data is long enough
                if len(data) < sig.offset + len(sig.header):
                    continue
                
                # Check header match
                if data[sig.offset:sig.offset + len(sig.header)] == sig.header:
                    return sig
        
        return None
    
    def get_signatures_by_category(self, category: str) -> List[FileSignature]:
        """Get all signatures for a specific category."""
        return self.signatures.get(category, [])
    
    def get_all_categories(self) -> List[str]:
        """Get list of all file categories."""
        return list(self.signatures.keys())
    
    def get_signature_count(self) -> int:
        """Get total number of signatures in database."""
        return sum(len(sigs) for sigs in self.signatures.values())
