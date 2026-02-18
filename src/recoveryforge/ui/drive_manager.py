"""
Drive manager panel for selecting and analyzing drives.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt

from ..utils.helpers import format_bytes


logger = logging.getLogger(__name__)


class DriveCard(QFrame):
    """Card widget for displaying drive information."""
    
    def __init__(self, drive_info, parent=None):
        super().__init__(parent)
        self.drive_info = drive_info
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(150)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Device header
        device_label = QLabel(f"<b>{drive_info.device}</b>")
        layout.addWidget(device_label)
        
        # Model
        model_label = QLabel(f"Model: {drive_info.model}")
        layout.addWidget(model_label)
        
        # Mountpoint
        mount_label = QLabel(f"Mount: {drive_info.mountpoint}")
        layout.addWidget(mount_label)
        
        # Filesystem
        fs_label = QLabel(f"Filesystem: {drive_info.fstype}")
        layout.addWidget(fs_label)
        
        # Size info
        size_label = QLabel(
            f"Size: {format_bytes(drive_info.total_size)} "
            f"({format_bytes(drive_info.used_size)} used, "
            f"{format_bytes(drive_info.free_size)} free)"
        )
        layout.addWidget(size_label)
        
        # Removable status
        if drive_info.is_removable:
            removable_label = QLabel("📱 Removable Drive")
            layout.addWidget(removable_label)
        
        # Select button
        self.select_btn = QPushButton("Select for Scan")
        layout.addWidget(self.select_btn)


class DriveManagerWidget(QWidget):
    """
    Drive manager for viewing and selecting drives for recovery.
    """
    
    def __init__(self, recovery_engine, parent=None):
        super().__init__(parent)
        self.recovery_engine = recovery_engine
        self.init_ui()
        self.refresh_drives()
    
    def init_ui(self):
        """Initialize drive manager UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        header = QLabel("Drive Manager")
        header.setObjectName("header")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_drives)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Info label
        info_label = QLabel(
            "Select a drive to scan for recoverable files. "
            "Be cautious when selecting system drives."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Scroll area for drive cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.drives_container = QWidget()
        self.drives_layout = QVBoxLayout(self.drives_container)
        self.drives_layout.setSpacing(15)
        
        scroll.setWidget(self.drives_container)
        layout.addWidget(scroll)
        
        logger.debug("Drive manager initialized")
    
    def refresh_drives(self):
        """Refresh the list of available drives."""
        logger.info("Refreshing drives")
        
        # Clear existing drive cards
        while self.drives_layout.count():
            item = self.drives_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Scan for drives
        drives = self.recovery_engine.scan_drives()
        
        if not drives:
            no_drives_label = QLabel("No drives detected")
            self.drives_layout.addWidget(no_drives_label)
        else:
            # Create card for each drive
            for drive in drives:
                card = DriveCard(drive)
                card.select_btn.clicked.connect(
                    lambda checked, d=drive: self.select_drive(d)
                )
                self.drives_layout.addWidget(card)
        
        self.drives_layout.addStretch()
        logger.info(f"Found {len(drives)} drives")
    
    def select_drive(self, drive_info):
        """Handle drive selection."""
        logger.info(f"Selected drive: {drive_info.device}")
        # TODO: Signal to scanner panel
        # For now, just log the selection
