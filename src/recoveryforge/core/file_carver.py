"""
File carver for recovering deleted files using signature-based detection.
"""

import os
import hashlib
from typing import List, Optional, Callable, Dict
from dataclasses import dataclass
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import mmap

from .file_signatures import FileSignatureDatabase, FileSignature

logger = logging.getLogger(__name__)


@dataclass
class RecoveredFile:
    """Represents a recovered file."""
    offset: int
    size: int
    signature: FileSignature
    data: Optional[bytes] = None
    hash: Optional[str] = None
    quality_score: float = 0.0
    
    def calculate_hash(self):
        """Calculate SHA-256 hash of file data."""
        if self.data:
            self.hash = hashlib.sha256(self.data).hexdigest()
    
    @property
    def extension(self) -> str:
        """Get file extension."""
        return self.signature.extension if self.signature else "bin"


class FileCarver:
    """
    File carver for signature-based file recovery.
    Supports multi-threaded scanning and custom file types.
    """
    
    def __init__(self, signature_db: Optional[FileSignatureDatabase] = None):
        self.signature_db = signature_db or FileSignatureDatabase()
        self.logger = logging.getLogger(__name__)
        self.recovered_files: List[RecoveredFile] = []
        self.progress_callback: Optional[Callable[[int, int], None]] = None
        self.cancel_flag = False
        
    def set_progress_callback(self, callback: Callable[[int, int], None]):
        """
        Set progress callback function.
        
        Args:
            callback: Function(bytes_scanned, total_bytes)
        """
        self.progress_callback = callback
    
    def cancel_scan(self):
        """Cancel ongoing scan."""
        self.cancel_flag = True
    
    def scan_file(
        self,
        file_path: str,
        chunk_size: int = 1024 * 1024,  # 1MB chunks
        categories: Optional[List[str]] = None
    ) -> List[RecoveredFile]:
        """
        Scan a file or disk image for recoverable files.
        
        Args:
            file_path: Path to file/disk to scan
            chunk_size: Size of chunks to read
            categories: File categories to search for (None = all)
            
        Returns:
            List of recovered files
        """
        self.recovered_files = []
        self.cancel_flag = False
        
        try:
            file_size = os.path.getsize(file_path)
            self.logger.info(f"Scanning {file_path} ({file_size} bytes)")
            
            # Filter signatures by category
            signatures = self._get_filtered_signatures(categories)
            
            with open(file_path, 'rb') as f:
                bytes_scanned = 0
                
                while bytes_scanned < file_size:
                    if self.cancel_flag:
                        self.logger.info("Scan cancelled by user")
                        break
                    
                    # Read chunk
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    # Scan chunk for signatures
                    self._scan_chunk(chunk, bytes_scanned, signatures)
                    
                    bytes_scanned += len(chunk)
                    
                    # Report progress
                    if self.progress_callback:
                        self.progress_callback(bytes_scanned, file_size)
            
            self.logger.info(f"Scan complete. Found {len(self.recovered_files)} files")
            return self.recovered_files
            
        except Exception as e:
            self.logger.error(f"Error scanning file: {e}")
            return []
    
    def scan_device(
        self,
        device_path: str,
        max_size: Optional[int] = None,
        categories: Optional[List[str]] = None
    ) -> List[RecoveredFile]:
        """
        Scan a raw device for recoverable files.
        
        Args:
            device_path: Path to device (e.g., /dev/sda1)
            max_size: Maximum bytes to scan (None = entire device)
            categories: File categories to search for
            
        Returns:
            List of recovered files
        """
        # TODO: Add raw device scanning support
        # This requires elevated privileges and platform-specific handling
        self.logger.warning("Raw device scanning not yet implemented")
        return []
    
    def _get_filtered_signatures(self, categories: Optional[List[str]]) -> List[FileSignature]:
        """Get filtered list of signatures to search for."""
        if categories is None:
            # Return all signatures
            all_sigs = []
            for cat_sigs in self.signature_db.signatures.values():
                all_sigs.extend(cat_sigs)
            return all_sigs
        else:
            # Return only requested categories
            filtered = []
            for category in categories:
                filtered.extend(self.signature_db.get_signatures_by_category(category))
            return filtered
    
    def _scan_chunk(self, chunk: bytes, offset: int, signatures: List[FileSignature]):
        """
        Scan a chunk of data for file signatures.
        
        Args:
            chunk: Data to scan
            offset: Offset in original file
            signatures: Signatures to search for
        """
        for i in range(len(chunk)):
            for sig in signatures:
                # Check if we have enough data
                if i + len(sig.header) > len(chunk):
                    continue
                
                # Check for signature match
                if chunk[i:i + len(sig.header)] == sig.header:
                    # Found potential file
                    self._extract_file(chunk, i, offset + i, sig)
    
    def _extract_file(self, chunk: bytes, chunk_offset: int, file_offset: int, sig: FileSignature):
        """
        Extract a file from the chunk.
        
        Args:
            chunk: Data chunk
            chunk_offset: Offset within chunk
            file_offset: Absolute offset
            sig: File signature
        """
        # For now, just record the location
        # Full extraction with footer detection would happen in a second pass
        recovered = RecoveredFile(
            offset=file_offset,
            size=0,  # Unknown until footer found
            signature=sig,
            quality_score=0.5  # Default score
        )
        
        self.recovered_files.append(recovered)
        self.logger.debug(f"Found {sig.extension} at offset {file_offset}")
    
    def extract_files(
        self,
        source_path: str,
        output_dir: str,
        files: Optional[List[RecoveredFile]] = None
    ) -> Dict[str, str]:
        """
        Extract recovered files to output directory.
        
        Args:
            source_path: Source file/device path
            output_dir: Output directory
            files: Files to extract (None = all)
            
        Returns:
            Dict mapping offset to output path
        """
        if files is None:
            files = self.recovered_files
        
        extracted = {}
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create category subdirectories
        categories = set(f.signature.category for f in files)
        for category in categories:
            (output_path / category).mkdir(exist_ok=True)
        
        # Extract each file
        with open(source_path, 'rb') as source:
            for i, recovered in enumerate(files):
                try:
                    # Seek to file location
                    source.seek(recovered.offset)
                    
                    # For now, extract a fixed size
                    # TODO: Implement proper footer detection
                    max_size = 10 * 1024 * 1024  # 10MB max
                    data = source.read(max_size)
                    
                    # Detect actual size using footer if available
                    if recovered.signature.footer:
                        footer_pos = data.find(recovered.signature.footer)
                        if footer_pos != -1:
                            data = data[:footer_pos + len(recovered.signature.footer)]
                    
                    # Save file
                    output_file = output_path / recovered.signature.category / f"recovered_{i:06d}.{recovered.extension}"
                    with open(output_file, 'wb') as out:
                        out.write(data)
                    
                    extracted[str(recovered.offset)] = str(output_file)
                    self.logger.debug(f"Extracted {output_file}")
                    
                except Exception as e:
                    self.logger.error(f"Error extracting file at offset {recovered.offset}: {e}")
        
        self.logger.info(f"Extracted {len(extracted)} files to {output_dir}")
        return extracted
