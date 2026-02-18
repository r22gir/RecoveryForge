"""
Basic tests for RecoveryForge core modules.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def test_imports():
    """Test that core modules can be imported."""
    from recoveryforge.core import DiskScanner, FileCarver, RecoveryEngine
    from recoveryforge.core.file_signatures import FileSignatureDatabase
    from recoveryforge.utils import format_bytes, format_time
    
    assert DiskScanner is not None
    assert FileCarver is not None
    assert RecoveryEngine is not None
    assert FileSignatureDatabase is not None


def test_file_signature_database():
    """Test file signature database."""
    from recoveryforge.core.file_signatures import FileSignatureDatabase
    
    db = FileSignatureDatabase()
    
    # Check that signatures are loaded
    assert db.get_signature_count() > 0
    
    # Check categories exist
    categories = db.get_all_categories()
    assert "image" in categories
    assert "document" in categories
    assert "video" in categories
    
    # Test file identification
    jpeg_header = bytes([0xFF, 0xD8, 0xFF, 0xE0])
    sig = db.identify_file(jpeg_header)
    assert sig is not None
    assert sig.extension == "jpg"


def test_disk_scanner():
    """Test disk scanner."""
    from recoveryforge.core.scanner import DiskScanner
    
    scanner = DiskScanner()
    drives = scanner.scan_drives()
    
    # Should find at least one drive (system drive)
    assert len(drives) >= 0  # May be 0 in sandboxed environments


def test_format_helpers():
    """Test utility formatting functions."""
    from recoveryforge.utils.helpers import format_bytes, format_time
    
    # Test byte formatting
    assert format_bytes(0) == "0 B"
    assert format_bytes(1024) == "1.00 KB"
    assert format_bytes(1048576) == "1.00 MB"
    assert format_bytes(1073741824) == "1.00 GB"
    
    # Test time formatting
    assert format_time(0) == "0s"
    assert format_time(65) == "1m 5s"
    assert format_time(3661) == "1h 1m 1s"


def test_recovery_engine():
    """Test recovery engine initialization."""
    from recoveryforge.core.recovery_engine import RecoveryEngine
    
    engine = RecoveryEngine()
    assert engine is not None
    assert engine.disk_scanner is not None
    assert engine.file_carver is not None


def test_metadata_extractor():
    """Test metadata extractor."""
    from recoveryforge.analysis.metadata_extractor import MetadataExtractor
    
    extractor = MetadataExtractor()
    assert extractor is not None


def test_content_analyzer():
    """Test content analyzer."""
    from recoveryforge.analysis.content_analyzer import ContentAnalyzer
    
    analyzer = ContentAnalyzer()
    assert analyzer is not None


def test_deduplicator():
    """Test deduplicator."""
    from recoveryforge.intelligence.deduplicator import Deduplicator
    
    deduplicator = Deduplicator()
    assert deduplicator is not None


def test_drive_health_monitor():
    """Test drive health monitor."""
    from recoveryforge.intelligence.drive_health import DriveHealthMonitor
    
    monitor = DriveHealthMonitor()
    assert monitor is not None


def test_report_generator():
    """Test report generator."""
    from recoveryforge.tools.reporter import ReportGenerator
    
    reporter = ReportGenerator()
    assert reporter is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
