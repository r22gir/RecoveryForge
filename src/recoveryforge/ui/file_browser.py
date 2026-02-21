"""
File browser for viewing and selecting recovered files.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QLineEdit, QFileDialog
)
from PyQt6.QtCore import Qt

from ..utils.helpers import format_bytes


logger = logging.getLogger(__name__)


class FileBrowserWidget(QWidget):
    """
    File browser for viewing and managing recovered files.
    """
    
    def __init__(self, recovery_engine, parent=None):
        super().__init__(parent)
        self.recovery_engine = recovery_engine
        self.init_ui()
    
    def init_ui(self):
        """Initialize file browser UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        header = QLabel("File Browser")
        header.setObjectName("header")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_files)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Search/filter bar
        filter_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search files...")
        self.search_input.textChanged.connect(self.filter_files)
        filter_layout.addWidget(self.search_input)
        
        layout.addLayout(filter_layout)
        
        # File table
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(5)
        self.file_table.setHorizontalHeaderLabels([
            "Filename", "Type", "Category", "Size", "Offset"
        ])
        self.file_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.file_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.file_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.file_table)
        
        # Stats
        self.stats_label = QLabel("0 files found")
        layout.addWidget(self.stats_label)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all)
        actions_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        actions_layout.addWidget(self.deselect_all_btn)
        
        actions_layout.addStretch()
        
        self.recover_btn = QPushButton("💾 Recover Selected")
        self.recover_btn.setObjectName("success")
        self.recover_btn.clicked.connect(self.recover_selected)
        actions_layout.addWidget(self.recover_btn)
        
        layout.addLayout(actions_layout)
        
        logger.debug("File browser initialized")
    
    def refresh_files(self):
        """Refresh file list from recovery engine."""
        logger.info("Refreshing file list")
        
        self.file_table.setRowCount(0)
        
        files = self.recovery_engine.get_recovered_files()
        
        for file in files:
            row = self.file_table.rowCount()
            self.file_table.insertRow(row)
            
            # Filename
            filename = f"recovered_{row:06d}.{file.extension}"
            self.file_table.setItem(row, 0, QTableWidgetItem(filename))
            
            # Type
            self.file_table.setItem(row, 1, QTableWidgetItem(file.extension.upper()))
            
            # Category
            category = file.signature.category if file.signature else "unknown"
            self.file_table.setItem(row, 2, QTableWidgetItem(category.title()))
            
            # Size
            size_str = format_bytes(file.size) if file.size > 0 else "Unknown"
            self.file_table.setItem(row, 3, QTableWidgetItem(size_str))
            
            # Offset
            self.file_table.setItem(row, 4, QTableWidgetItem(f"0x{file.offset:08X}"))
        
        self.stats_label.setText(f"{len(files)} files found")
        logger.info(f"Loaded {len(files)} files")
    
    def filter_files(self):
        """Filter files based on search text."""
        search_text = self.search_input.text().lower()
        
        for row in range(self.file_table.rowCount()):
            should_show = True
            
            if search_text:
                # Check if any column matches
                match_found = False
                for col in range(self.file_table.columnCount()):
                    item = self.file_table.item(row, col)
                    if item and search_text in item.text().lower():
                        match_found = True
                        break
                
                should_show = match_found
            
            self.file_table.setRowHidden(row, not should_show)
    
    def select_all(self):
        """Select all visible files."""
        self.file_table.selectAll()
    
    def deselect_all(self):
        """Deselect all files."""
        self.file_table.clearSelection()
    
    def recover_selected(self):
        """Recover selected files."""
        selected_rows = set(item.row() for item in self.file_table.selectedItems())
        
        if not selected_rows:
            logger.warning("No files selected for recovery")
            return
        
        logger.info(f"Recovering {len(selected_rows)} files")
        
        # Get corresponding files
        all_files = self.recovery_engine.get_recovered_files()
        selected_files = [all_files[row] for row in sorted(selected_rows) if row < len(all_files)]
        
        # Get source path from current session
        if not self.recovery_engine.current_session:
            logger.error("No active recovery session")
            return
        
        # TODO: Get actual source path
        # For now, just log the action
        logger.info(f"Would recover {len(selected_files)} files")
