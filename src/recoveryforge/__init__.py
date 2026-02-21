"""
RecoveryForge - Professional Data Recovery Tool

A comprehensive, open-source data recovery solution with advanced features
including file carving, intelligent tagging, ransomware detection, and a
modern user interface.
"""

__version__ = "1.0.0"
__author__ = "RecoveryForge Team"
__license__ = "MIT"

from .core.scanner import DiskScanner
from .core.recovery_engine import RecoveryEngine
from .core.file_carver import FileCarver

__all__ = [
    "DiskScanner",
    "RecoveryEngine",
    "FileCarver",
]
