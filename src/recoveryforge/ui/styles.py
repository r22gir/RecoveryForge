"""
Styles for RecoveryForge dark theme with glassmorphism.
"""

# Color scheme
COLORS = {
    'background': '#1e1e2e',
    'surface': '#2d2d3d',
    'surface_alt': '#3d3d4d',
    'accent': '#5b9dff',
    'accent_hover': '#7ab5ff',
    'text': '#ffffff',
    'text_secondary': '#b0b0b0',
    'text_disabled': '#606060',
    'success': '#50fa7b',
    'warning': '#ffb86c',
    'error': '#ff5555',
    'border': '#404050',
}

# Main application stylesheet
MAIN_STYLE = f"""
QMainWindow {{
    background-color: {COLORS['background']};
}}

QWidget {{
    color: {COLORS['text']};
    font-family: 'Segoe UI', 'Ubuntu', 'Helvetica', sans-serif;
    font-size: 12px;
}}

/* Panels and containers */
QFrame {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}

QGroupBox {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 8px;
    color: {COLORS['accent']};
}}

/* Buttons */
QPushButton {{
    background-color: {COLORS['accent']};
    color: {COLORS['text']};
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {COLORS['accent_hover']};
}}

QPushButton:pressed {{
    background-color: {COLORS['accent']};
}}

QPushButton:disabled {{
    background-color: {COLORS['surface_alt']};
    color: {COLORS['text_disabled']};
}}

QPushButton#danger {{
    background-color: {COLORS['error']};
}}

QPushButton#success {{
    background-color: {COLORS['success']};
}}

/* Input fields */
QLineEdit, QTextEdit {{
    background-color: {COLORS['surface_alt']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px;
    color: {COLORS['text']};
}}

QLineEdit:focus, QTextEdit:focus {{
    border: 1px solid {COLORS['accent']};
}}

/* Combo boxes */
QComboBox {{
    background-color: {COLORS['surface_alt']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px;
    color: {COLORS['text']};
}}

QComboBox:hover {{
    border: 1px solid {COLORS['accent']};
}}

QComboBox::drop-down {{
    border: none;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['accent']};
}}

/* Progress bars */
QProgressBar {{
    background-color: {COLORS['surface_alt']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    text-align: center;
    color: {COLORS['text']};
}}

QProgressBar::chunk {{
    background-color: {COLORS['accent']};
    border-radius: 5px;
}}

/* Labels */
QLabel {{
    color: {COLORS['text']};
    background: transparent;
}}

QLabel#header {{
    font-size: 18px;
    font-weight: bold;
    color: {COLORS['accent']};
}}

QLabel#subheader {{
    font-size: 14px;
    font-weight: bold;
}}

QLabel#value {{
    font-size: 24px;
    font-weight: bold;
    color: {COLORS['accent']};
}}

/* Tables */
QTableWidget {{
    background-color: {COLORS['surface']};
    alternate-background-color: {COLORS['surface_alt']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    gridline-color: {COLORS['border']};
}}

QTableWidget::item {{
    padding: 4px;
}}

QTableWidget::item:selected {{
    background-color: {COLORS['accent']};
}}

QHeaderView::section {{
    background-color: {COLORS['surface_alt']};
    color: {COLORS['text']};
    padding: 6px;
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    font-weight: bold;
}}

/* Tree views */
QTreeWidget {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}

QTreeWidget::item:selected {{
    background-color: {COLORS['accent']};
}}

QTreeWidget::item:hover {{
    background-color: {COLORS['surface_alt']};
}}

/* Scrollbars */
QScrollBar:vertical {{
    background-color: {COLORS['surface']};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['surface_alt']};
    border-radius: 6px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['accent']};
}}

QScrollBar:horizontal {{
    background-color: {COLORS['surface']};
    height: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['surface_alt']};
    border-radius: 6px;
    min-width: 20px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['accent']};
}}

/* Tab widget */
QTabWidget::pane {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}

QTabBar::tab {{
    background-color: {COLORS['surface_alt']};
    color: {COLORS['text_secondary']};
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['accent']};
    color: {COLORS['text']};
}}

QTabBar::tab:hover {{
    background-color: {COLORS['accent_hover']};
}}

/* Tooltips */
QToolTip {{
    background-color: {COLORS['surface']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 4px;
}}

/* Status bar */
QStatusBar {{
    background-color: {COLORS['surface']};
    color: {COLORS['text_secondary']};
}}

/* Menu bar */
QMenuBar {{
    background-color: {COLORS['surface']};
    color: {COLORS['text']};
}}

QMenuBar::item:selected {{
    background-color: {COLORS['accent']};
}}

QMenu {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
}}

QMenu::item:selected {{
    background-color: {COLORS['accent']};
}}

/* Splitter */
QSplitter::handle {{
    background-color: {COLORS['border']};
}}

QSplitter::handle:hover {{
    background-color: {COLORS['accent']};
}}
"""
