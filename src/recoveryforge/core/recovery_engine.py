"""
Main recovery engine coordinating all recovery operations.
"""

import logging
from typing import List, Optional, Dict, Callable
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
import threading

from .scanner import DiskScanner, DriveInfo
from .file_carver import FileCarver, RecoveredFile
from .file_signatures import FileSignatureDatabase


class RecoveryStatus(Enum):
    """Recovery operation status."""
    IDLE = "idle"
    SCANNING = "scanning"
    ANALYZING = "analyzing"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class RecoverySession:
    """Represents a recovery session."""
    session_id: str
    source_drive: DriveInfo
    output_directory: str
    status: RecoveryStatus = RecoveryStatus.IDLE
    files_found: int = 0
    files_recovered: int = 0
    bytes_scanned: int = 0
    total_bytes: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        if self.total_bytes == 0:
            return 0.0
        return (self.bytes_scanned / self.total_bytes) * 100


class RecoveryEngine:
    """
    Main recovery engine coordinating all recovery operations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.disk_scanner = DiskScanner()
        self.file_carver = FileCarver()
        self.signature_db = FileSignatureDatabase()
        
        self.current_session: Optional[RecoverySession] = None
        self.recovered_files: List[RecoveredFile] = []
        
        self.status_callback: Optional[Callable[[RecoverySession], None]] = None
        self.progress_callback: Optional[Callable[[int, int], None]] = None
        
        self._scan_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    def set_status_callback(self, callback: Callable[[RecoverySession], None]):
        """Set callback for status updates."""
        self.status_callback = callback
    
    def set_progress_callback(self, callback: Callable[[int, int], None]):
        """Set callback for progress updates."""
        self.progress_callback = callback
    
    def scan_drives(self) -> List[DriveInfo]:
        """Scan system for available drives."""
        return self.disk_scanner.scan_drives()
    
    def start_recovery(
        self,
        source_path: str,
        output_dir: str,
        file_categories: Optional[List[str]] = None
    ) -> bool:
        """
        Start a recovery session.
        
        Args:
            source_path: Path to scan (file or device)
            output_dir: Output directory for recovered files
            file_categories: Categories of files to recover
            
        Returns:
            True if started successfully, False otherwise
        """
        with self._lock:
            if self.current_session and self.current_session.status == RecoveryStatus.SCANNING:
                self.logger.warning("Recovery already in progress")
                return False
            
            # Get drive info if available
            drive = self.disk_scanner.get_drive_by_path(source_path)
            
            # Create session
            import uuid
            self.current_session = RecoverySession(
                session_id=str(uuid.uuid4()),
                source_drive=drive,
                output_directory=output_dir,
                status=RecoveryStatus.SCANNING
            )
            
            # Start scan in background thread
            self._scan_thread = threading.Thread(
                target=self._scan_worker,
                args=(source_path, output_dir, file_categories),
                daemon=True
            )
            self._scan_thread.start()
            
            return True
    
    def _scan_worker(
        self,
        source_path: str,
        output_dir: str,
        file_categories: Optional[List[str]]
    ):
        """Worker thread for scanning."""
        try:
            self.logger.info(f"Starting recovery scan: {source_path}")
            
            # Set up progress callback
            def progress_update(bytes_scanned: int, total_bytes: int):
                if self.current_session:
                    self.current_session.bytes_scanned = bytes_scanned
                    self.current_session.total_bytes = total_bytes
                    
                    if self.status_callback:
                        self.status_callback(self.current_session)
            
            self.file_carver.set_progress_callback(progress_update)
            
            # Scan for files
            self.recovered_files = self.file_carver.scan_file(
                source_path,
                categories=file_categories
            )
            
            if self.current_session:
                self.current_session.files_found = len(self.recovered_files)
                self.current_session.status = RecoveryStatus.COMPLETED
                
                if self.status_callback:
                    self.status_callback(self.current_session)
            
            self.logger.info(f"Recovery scan completed. Found {len(self.recovered_files)} files")
            
        except Exception as e:
            self.logger.error(f"Error during recovery scan: {e}")
            if self.current_session:
                self.current_session.status = RecoveryStatus.ERROR
                self.current_session.errors.append(str(e))
                
                if self.status_callback:
                    self.status_callback(self.current_session)
    
    def recover_files(
        self,
        source_path: str,
        files: Optional[List[RecoveredFile]] = None
    ) -> Dict[str, str]:
        """
        Recover selected files to output directory.
        
        Args:
            source_path: Source path to recover from
            files: Specific files to recover (None = all)
            
        Returns:
            Dict mapping offsets to output paths
        """
        if not self.current_session:
            self.logger.error("No active recovery session")
            return {}
        
        self.current_session.status = RecoveryStatus.RECOVERING
        
        try:
            extracted = self.file_carver.extract_files(
                source_path,
                self.current_session.output_directory,
                files
            )
            
            self.current_session.files_recovered = len(extracted)
            self.current_session.status = RecoveryStatus.COMPLETED
            
            return extracted
            
        except Exception as e:
            self.logger.error(f"Error recovering files: {e}")
            self.current_session.status = RecoveryStatus.ERROR
            self.current_session.errors.append(str(e))
            return {}
    
    def cancel_recovery(self):
        """Cancel ongoing recovery operation."""
        if self.current_session:
            self.file_carver.cancel_scan()
            self.current_session.status = RecoveryStatus.CANCELLED
            self.logger.info("Recovery cancelled")
    
    def get_recovered_files(self) -> List[RecoveredFile]:
        """Get list of recovered files from current session."""
        return self.recovered_files
    
    def get_file_type_stats(self) -> Dict[str, int]:
        """Get statistics of recovered files by type."""
        stats = {}
        for file in self.recovered_files:
            category = file.signature.category
            stats[category] = stats.get(category, 0) + 1
        return stats
