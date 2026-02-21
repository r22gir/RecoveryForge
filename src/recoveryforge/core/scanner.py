"""
Disk scanner for detecting and scanning storage devices.
"""

import os
import platform
import psutil
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class DriveInfo:
    """Information about a storage drive."""
    device: str
    mountpoint: str
    fstype: str
    total_size: int
    used_size: int
    free_size: int
    is_removable: bool = False
    model: str = "Unknown"
    serial: str = "Unknown"
    
    @property
    def usage_percent(self) -> float:
        """Calculate usage percentage."""
        if self.total_size == 0:
            return 0.0
        return (self.used_size / self.total_size) * 100


class DiskScanner:
    """
    Scanner for detecting and analyzing storage devices.
    """
    
    def __init__(self):
        self.drives: List[DriveInfo] = []
        self.logger = logging.getLogger(__name__)
    
    def scan_drives(self) -> List[DriveInfo]:
        """
        Scan system for available drives.
        
        Returns:
            List of detected drives with information
        """
        self.drives = []
        self.logger.info("Scanning for available drives...")
        
        try:
            # Get all disk partitions
            partitions = psutil.disk_partitions(all=False)
            
            for partition in partitions:
                try:
                    # Get usage statistics
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    # Determine if removable (platform-specific)
                    is_removable = self._is_removable(partition.device)
                    
                    # Get device model if available
                    model = self._get_device_model(partition.device)
                    
                    drive_info = DriveInfo(
                        device=partition.device,
                        mountpoint=partition.mountpoint,
                        fstype=partition.fstype,
                        total_size=usage.total,
                        used_size=usage.used,
                        free_size=usage.free,
                        is_removable=is_removable,
                        model=model
                    )
                    
                    self.drives.append(drive_info)
                    self.logger.debug(f"Found drive: {partition.device} ({partition.mountpoint})")
                    
                except (PermissionError, OSError) as e:
                    self.logger.warning(f"Cannot access {partition.device}: {e}")
                    continue
            
            self.logger.info(f"Found {len(self.drives)} accessible drives")
            return self.drives
            
        except Exception as e:
            self.logger.error(f"Error scanning drives: {e}")
            return []
    
    def _is_removable(self, device: str) -> bool:
        """
        Check if a device is removable.
        
        Args:
            device: Device path
            
        Returns:
            True if removable, False otherwise
        """
        system = platform.system()
        
        if system == "Linux":
            # Check /sys/block for removable flag
            device_name = os.path.basename(device).rstrip('0123456789')
            removable_path = f"/sys/block/{device_name}/removable"
            try:
                if os.path.exists(removable_path):
                    with open(removable_path, 'r') as f:
                        return f.read().strip() == '1'
            except:
                pass
        
        elif system == "Windows":
            # On Windows, check drive type
            import string
            if device and device[0].upper() in string.ascii_uppercase:
                drive_letter = device[0].upper()
                try:
                    import ctypes
                    drive_type = ctypes.windll.kernel32.GetDriveTypeW(f"{drive_letter}:\\")
                    # DRIVE_REMOVABLE = 2, DRIVE_CDROM = 5
                    return drive_type in (2, 5)
                except:
                    pass
        
        return False
    
    def _get_device_model(self, device: str) -> str:
        """
        Get device model name.
        
        Args:
            device: Device path
            
        Returns:
            Model name or "Unknown"
        """
        system = platform.system()
        
        if system == "Linux":
            device_name = os.path.basename(device).rstrip('0123456789')
            model_path = f"/sys/block/{device_name}/device/model"
            try:
                if os.path.exists(model_path):
                    with open(model_path, 'r') as f:
                        return f.read().strip()
            except:
                pass
        
        # TODO: Add Windows WMI support for model detection
        
        return "Unknown"
    
    def get_drive_by_path(self, path: str) -> Optional[DriveInfo]:
        """
        Get drive info for a specific path.
        
        Args:
            path: File or directory path
            
        Returns:
            DriveInfo if found, None otherwise
        """
        try:
            abs_path = os.path.abspath(path)
            
            # Find matching mountpoint
            best_match = None
            best_match_len = 0
            
            for drive in self.drives:
                if abs_path.startswith(drive.mountpoint):
                    if len(drive.mountpoint) > best_match_len:
                        best_match = drive
                        best_match_len = len(drive.mountpoint)
            
            return best_match
            
        except Exception as e:
            self.logger.error(f"Error getting drive for path {path}: {e}")
            return None
    
    def refresh(self):
        """Refresh drive information."""
        self.scan_drives()
