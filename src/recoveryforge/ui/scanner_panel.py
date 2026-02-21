"""
Scanner panel for configuring and running recovery scans.
"""

import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QFileDialog,
    QGroupBox, QCheckBox, QProgressBar, QTextEdit
)
from PyQt6.QtCore import Qt

from ..utils.helpers import format_bytes


logger = logging.getLogger(__name__)


class ScannerPanel(QWidget):
    """
    Scanner panel for configuring and running recovery scans.
    """
    
    def __init__(self, recovery_engine, parent=None):
        super().__init__(parent)
        self.recovery_engine = recovery_engine
        self.init_ui()
    
    def init_ui(self):
        """Initialize scanner panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Recovery Scanner")
        header.setObjectName("header")
        layout.addWidget(header)
        
        # Source selection
        source_group = QGroupBox("Scan Source")
        source_layout = QVBoxLayout(source_group)
        
        source_input_layout = QHBoxLayout()
        
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Select file or device to scan...")
        source_input_layout.addWidget(self.source_input)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_source)
        source_input_layout.addWidget(self.browse_btn)
        
        source_layout.addLayout(source_input_layout)
        layout.addWidget(source_group)
        
        # Output selection
        output_group = QGroupBox("Output Directory")
        output_layout = QVBoxLayout(output_group)
        
        output_input_layout = QHBoxLayout()
        
        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText("Select output directory for recovered files...")
        self.output_input.setText(str(Path.home() / "RecoveredFiles"))
        output_input_layout.addWidget(self.output_input)
        
        self.browse_output_btn = QPushButton("Browse...")
        self.browse_output_btn.clicked.connect(self.browse_output)
        output_input_layout.addWidget(self.browse_output_btn)
        
        output_layout.addLayout(output_input_layout)
        layout.addWidget(output_group)
        
        # File type selection
        types_group = QGroupBox("File Types to Recover")
        types_layout = QGridLayout(types_group)
        
        self.type_checkboxes = {}
        file_types = [
            ("Images", "image"),
            ("Documents", "document"),
            ("Videos", "video"),
            ("Audio", "audio"),
            ("Archives", "archive"),
            ("Executables", "executable"),
            ("Databases", "database"),
            ("All Types", "all")
        ]
        
        for i, (label, type_id) in enumerate(file_types):
            checkbox = QCheckBox(label)
            checkbox.setChecked(type_id in ["image", "document", "video"])
            self.type_checkboxes[type_id] = checkbox
            types_layout.addWidget(checkbox, i // 4, i % 4)
        
        layout.addWidget(types_group)
        
        # Scan controls
        controls_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶ Start Scan")
        self.start_btn.setObjectName("success")
        self.start_btn.clicked.connect(self.start_scan)
        controls_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_scan)
        controls_layout.addWidget(self.stop_btn)
        
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Progress display
        progress_group = QGroupBox("Scan Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to scan")
        progress_layout.addWidget(self.status_label)
        
        self.stats_label = QLabel("")
        progress_layout.addWidget(self.stats_label)
        
        layout.addWidget(progress_group)
        
        # Log output
        log_group = QGroupBox("Scan Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        layout.addStretch()
        
        logger.debug("Scanner panel initialized")
    
    def browse_source(self):
        """Browse for source file/device."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File or Disk Image",
            str(Path.home()),
            "All Files (*.*)"
        )
        
        if file_path:
            self.source_input.setText(file_path)
            self.add_log(f"Selected source: {file_path}")
    
    def browse_output(self):
        """Browse for output directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            str(Path.home())
        )
        
        if dir_path:
            self.output_input.setText(dir_path)
            self.add_log(f"Selected output: {dir_path}")
    
    def start_scan(self):
        """Start recovery scan."""
        source = self.source_input.text().strip()
        output = self.output_input.text().strip()
        
        if not source:
            self.add_log("ERROR: No source selected")
            return
        
        if not output:
            self.add_log("ERROR: No output directory selected")
            return
        
        # Get selected file types
        categories = []
        for type_id, checkbox in self.type_checkboxes.items():
            if checkbox.isChecked() and type_id != "all":
                categories.append(type_id)
        
        if self.type_checkboxes["all"].isChecked():
            categories = None  # Scan all types
        
        self.add_log(f"Starting scan of {source}")
        self.add_log(f"Output directory: {output}")
        if categories:
            self.add_log(f"File types: {', '.join(categories)}")
        else:
            self.add_log("File types: All")
        
        # Update UI state
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # Start recovery
        success = self.recovery_engine.start_recovery(source, output, categories)
        
        if not success:
            self.add_log("ERROR: Failed to start recovery")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
    
    def stop_scan(self):
        """Stop ongoing scan."""
        self.add_log("Stopping scan...")
        self.recovery_engine.cancel_recovery()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
    
    def add_log(self, message: str):
        """Add message to scan log."""
        self.log_text.append(message)
        logger.info(message)
