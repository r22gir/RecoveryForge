"""
Dashboard widget showing real-time recovery statistics.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QProgressBar, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ..utils.helpers import format_bytes, format_time


logger = logging.getLogger(__name__)


class StatCard(QFrame):
    """Card widget for displaying a statistic."""
    
    def __init__(self, title: str, value: str = "0", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(100)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        self.title_label = QLabel(title)
        self.title_label.setObjectName("subheader")
        layout.addWidget(self.title_label)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setObjectName("value")
        layout.addWidget(self.value_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
    
    def set_value(self, value: str):
        """Update the displayed value."""
        self.value_label.setText(value)


class DashboardWidget(QWidget):
    """
    Dashboard showing recovery statistics and system status.
    """
    
    def __init__(self, recovery_engine, parent=None):
        super().__init__(parent)
        self.recovery_engine = recovery_engine
        self.init_ui()
    
    def init_ui(self):
        """Initialize dashboard UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Recovery Dashboard")
        header.setObjectName("header")
        layout.addWidget(header)
        
        # Statistics cards
        stats_layout = QGridLayout()
        stats_layout.setSpacing(15)
        
        self.files_found_card = StatCard("Files Found", "0")
        stats_layout.addWidget(self.files_found_card, 0, 0)
        
        self.files_recovered_card = StatCard("Files Recovered", "0")
        stats_layout.addWidget(self.files_recovered_card, 0, 1)
        
        self.bytes_scanned_card = StatCard("Data Scanned", "0 B")
        stats_layout.addWidget(self.bytes_scanned_card, 0, 2)
        
        self.scan_progress_card = StatCard("Scan Progress", "0%")
        stats_layout.addWidget(self.scan_progress_card, 0, 3)
        
        layout.addLayout(stats_layout)
        
        # Active scan progress
        self.scan_group = QGroupBox("Active Scan")
        scan_layout = QVBoxLayout(self.scan_group)
        
        self.scan_status_label = QLabel("No active scan")
        scan_layout.addWidget(self.scan_status_label)
        
        self.scan_progress_bar = QProgressBar()
        self.scan_progress_bar.setTextVisible(True)
        scan_layout.addWidget(self.scan_progress_bar)
        
        layout.addWidget(self.scan_group)
        
        # File type breakdown
        self.types_group = QGroupBox("File Types Discovered")
        types_layout = QVBoxLayout(self.types_group)
        
        self.types_label = QLabel("No files discovered yet")
        self.types_label.setWordWrap(True)
        types_layout.addWidget(self.types_label)
        
        layout.addWidget(self.types_group)
        
        # Recent activity
        self.activity_group = QGroupBox("Recent Activity")
        activity_layout = QVBoxLayout(self.activity_group)
        
        self.activity_label = QLabel("No recent activity")
        self.activity_label.setWordWrap(True)
        activity_layout.addWidget(self.activity_label)
        
        layout.addWidget(self.activity_group)
        
        layout.addStretch()
        
        logger.debug("Dashboard initialized")
    
    def update_stats(self):
        """Update dashboard statistics."""
        session = self.recovery_engine.current_session
        
        if session:
            # Update cards
            self.files_found_card.set_value(str(session.files_found))
            self.files_recovered_card.set_value(str(session.files_recovered))
            self.bytes_scanned_card.set_value(format_bytes(session.bytes_scanned))
            self.scan_progress_card.set_value(f"{session.progress_percent:.1f}%")
            
            # Update progress bar
            self.scan_progress_bar.setValue(int(session.progress_percent))
            
            # Update status
            status_text = f"Status: {session.status.value.title()}"
            if session.total_bytes > 0:
                status_text += f" - {format_bytes(session.bytes_scanned)} / {format_bytes(session.total_bytes)}"
            self.scan_status_label.setText(status_text)
            
            # Update file types
            file_stats = self.recovery_engine.get_file_type_stats()
            if file_stats:
                types_text = "Discovered file types:\n"
                for file_type, count in sorted(file_stats.items(), key=lambda x: x[1], reverse=True):
                    types_text += f"• {file_type.title()}: {count} files\n"
                self.types_label.setText(types_text)
            else:
                self.types_label.setText("No files discovered yet")
        else:
            # No active session
            self.scan_status_label.setText("No active scan")
            self.scan_progress_bar.setValue(0)
