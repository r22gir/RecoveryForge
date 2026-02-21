"""
Main application window for RecoveryForge.
"""

import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QStatusBar, QMenuBar, QMenu, QMessageBox,
    QLabel, QPushButton, QSplitter
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon

from .styles import MAIN_STYLE
from .dashboard import DashboardWidget
from .drive_manager import DriveManagerWidget
from .scanner_panel import ScannerPanel
from .file_browser import FileBrowserWidget
from ..core.recovery_engine import RecoveryEngine


logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window with modern dark theme."""
    
    def __init__(self):
        super().__init__()
        self.recovery_engine = RecoveryEngine()
        self.init_ui()
        
        # Setup status updates
        self.recovery_engine.set_status_callback(self.on_recovery_status_update)
        
        # Periodic UI updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(1000)  # Update every second
    
    def init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle("RecoveryForge - Professional Data Recovery")
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply dark theme
        self.setStyleSheet(MAIN_STYLE)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setMovable(False)
        
        # Dashboard tab
        self.dashboard = DashboardWidget(self.recovery_engine)
        self.tabs.addTab(self.dashboard, "🏠 Dashboard")
        
        # Drive Manager tab
        self.drive_manager = DriveManagerWidget(self.recovery_engine)
        self.tabs.addTab(self.drive_manager, "💾 Drive Manager")
        
        # Scanner tab
        self.scanner_panel = ScannerPanel(self.recovery_engine)
        self.tabs.addTab(self.scanner_panel, "🔍 Scanner")
        
        # File Browser tab
        self.file_browser = FileBrowserWidget(self.recovery_engine)
        self.tabs.addTab(self.file_browser, "📁 File Browser")
        
        # Add tabs to main layout
        main_layout.addWidget(self.tabs)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        logger.info("Main window initialized")
    
    def create_menu_bar(self):
        """Create application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_scan_action = QAction("&New Scan", self)
        new_scan_action.setShortcut("Ctrl+N")
        new_scan_action.triggered.connect(self.new_scan)
        file_menu.addAction(new_scan_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        refresh_drives_action = QAction("&Refresh Drives", self)
        refresh_drives_action.setShortcut("F5")
        refresh_drives_action.triggered.connect(self.refresh_drives)
        tools_menu.addAction(refresh_drives_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        docs_action = QAction("&Documentation", self)
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)
    
    def new_scan(self):
        """Start a new recovery scan."""
        self.tabs.setCurrentIndex(2)  # Switch to scanner tab
        logger.info("New scan initiated")
    
    def refresh_drives(self):
        """Refresh drive information."""
        self.drive_manager.refresh_drives()
        self.status_bar.showMessage("Drives refreshed", 3000)
        logger.info("Drives refreshed")
    
    def show_about(self):
        """Show about dialog."""
        about_text = """
        <h2>RecoveryForge v1.0.0</h2>
        <p><b>Professional Data Recovery Tool</b></p>
        <p>Open-source, free, and powerful data recovery solution.</p>
        <p>© 2024 RecoveryForge Team</p>
        <p>Licensed under MIT License</p>
        <p><a href="https://github.com/r22gir/RecoveryForge">GitHub Repository</a></p>
        """
        QMessageBox.about(self, "About RecoveryForge", about_text)
    
    def show_documentation(self):
        """Show documentation."""
        QMessageBox.information(
            self,
            "Documentation",
            "Documentation is available at:\n\n"
            "• README.md - Getting started\n"
            "• docs/user_manual.md - User guide\n"
            "• docs/api_documentation.md - API reference\n\n"
            "Visit: https://github.com/r22gir/RecoveryForge"
        )
    
    def update_dashboard(self):
        """Periodic dashboard update."""
        if hasattr(self, 'dashboard'):
            self.dashboard.update_stats()
    
    def on_recovery_status_update(self, session):
        """Handle recovery status updates."""
        status_msg = f"Status: {session.status.value.title()}"
        if session.status.value == "scanning":
            status_msg += f" - {session.progress_percent:.1f}% ({session.files_found} files found)"
        self.status_bar.showMessage(status_msg)
        
        # Update dashboard
        if hasattr(self, 'dashboard'):
            self.dashboard.update_stats()
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Check if scan is in progress
        if self.recovery_engine.current_session:
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "A recovery operation is in progress. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.recovery_engine.cancel_recovery()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
