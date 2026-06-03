import sys
import json
from urllib.parse import urlparse
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QSpinBox, QPushButton, 
                             QTextEdit, QTableWidget, QTableWidgetItem, QTabWidget,
                             QProgressBar, QComboBox, QMessageBox, QSplitter,
                             QGroupBox, QGridLayout, QHeaderView, QFrame, QScrollArea,
                             QSystemTrayIcon, QStyle, QAction, QMenu, QTreeWidget, QTreeWidgetItem,
                             QListWidget, QListWidgetItem, QSizePolicy, QAbstractItemView)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer, QUrl
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = True
    print("PyQtWebEngine successfully imported - Visual preview enabled")
except ImportError as e:
    WEB_ENGINE_AVAILABLE = False
    print(f"PyQtWebEngine not available: {e}")
    print("Visual preview will be disabled. Install with: pip install PyQtWebEngine")
import module
import re
import webbrowser
import os
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
from datetime import datetime
from dotenv import load_dotenv
import markdown

# Load environment variables from .env file
load_dotenv()

class ScrapingThread(QThread):
    """Thread for running web scraping operations"""
    progress_updated = pyqtSignal(str)
    scraping_complete = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, url, max_depth):
        super().__init__()
        self.url = url
        self.max_depth = max_depth
        self.scraper = module.WebScraper()
        self._stop_requested = False
        
    def stop(self):
        """Request graceful stop of the scraping process"""
        self._stop_requested = True
        if hasattr(self.scraper, 'stop_scraping'):
            self.scraper.stop_scraping()
        
    def run(self):
        try:
            self.progress_updated.emit("Starting web scraping...")
            
            # Reset scraper state for new crawl
            self.scraper.reset()
            
            def progress_callback(website):
                if self._stop_requested:
                    return  # Stop processing if requested
                if website:
                    self.progress_updated.emit(f"Scraped: {website.title} (depth {website.depth})")
            
            # Start scraping with progress callback
            websites = self.scraper.crawl_website(self.url, self.max_depth, progress_callback)
            
            # Check if stop was requested
            if self._stop_requested:
                self.progress_updated.emit("Scraping stopped by user.")
                return
            
            # Emit final progress
            self.progress_updated.emit(f"Scraping complete! Found {len(websites)} websites.")
            self.scraping_complete.emit(websites)
            
        except Exception as e:
            if not self._stop_requested:  # Only emit error if not stopped by user
                self.error_occurred.emit(str(e))

class ModernButton(QPushButton):
    """Custom modern button with hover effects"""
    def __init__(self, text, primary=False):
        super().__init__(text)
        self.primary = primary
        self.setMinimumHeight(40)
        self.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_style()
        
    def update_style(self):
        if self.primary:
            self.setStyleSheet("""
                QPushButton {
                    background: #3b82f6;
                    border: none;
                    color: white;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #2563eb;
                }
                QPushButton:pressed {
                    background: #1d4ed8;
                }
                QPushButton:disabled {
                    background: #9ca3af;
                    color: #f3f4f6;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: white;
                    border: 1px solid #d1d5db;
                    color: #374151;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    border-color: #3b82f6;
                    color: #3b82f6;
                    background: #f8fafc;
                }
                QPushButton:pressed {
                    background: #f1f5f9;
                }
                QPushButton:disabled {
                    background: #f9fafb;
                    border-color: #e5e7eb;
                    color: #9ca3af;
                }
            """)

class ModernLineEdit(QLineEdit):
    """Custom modern input field"""
    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(40)
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 12px;
                background: white;
                color: #374151;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                outline: none;
            }
            QLineEdit::placeholder {
                color: #9ca3af;
            }
        """)

class ModernSpinBox(QSpinBox):
    """Custom modern spin box"""
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(40)
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet("""
            QSpinBox {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 12px;
                background: white;
                color: #374151;
                font-size: 14px;
            }
            QSpinBox:focus {
                border-color: #3b82f6;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                border: none;
                background: #f9fafb;
                border-radius: 3px;
                margin: 2px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #f3f4f6;
            }
        """)

class ChatBubbleWidget(QWidget):
    def __init__(self, message, timestamp, role):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        # Bubble
        if role == "ai":
            html = markdown.markdown(message)
            bubble = QLabel(html)
            bubble.setTextFormat(Qt.TextFormat.RichText)
        else:
            bubble = QLabel(message)
            bubble.setTextFormat(Qt.TextFormat.PlainText)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        bubble.setFont(QFont("Segoe UI", 11))
        bubble.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        bubble.setMinimumWidth(800)
        bubble.setMaximumWidth(1200)
        bubble.adjustSize()
        # Timestamp
        ts = QLabel(("🤖 " if role == "ai" else "") + timestamp)
        ts.setFont(QFont("Segoe UI", 8))
        ts.setStyleSheet("color: #9ca3af;")
        if role == "user":
            bubble.setStyleSheet("background: #2563eb; color: white; border-radius: 16px; padding: 10px 16px; margin-left: 40px;")
            layout.setAlignment(Qt.AlignmentFlag.AlignRight)
            ts.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            bubble.setStyleSheet("background: #f3f4f6; color: #1e293b; border-radius: 16px; padding: 10px 16px; margin-right: 40px;")
            layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            ts.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(bubble)
        layout.addWidget(ts)

class WebScraperApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.websites = []
        self.scraper = module.WebScraper()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Web Scraper & Data Analyzer")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)  # Set minimum size to prevent geometry issues
        
        # Set clean, minimal styling
        self.setStyleSheet("""
            QMainWindow {
                background: #1e293b;
            }
            QTabWidget::pane {
                border: none;
                background: white;
                border-radius: 8px;
                margin: 8px 8px 8px 8px;
                padding-top: 8px;
            }
            QTabBar::tab {
                background: #475569;
                color: #e2e8f0;
                padding: 12px 20px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                min-width: 120px;
                margin-bottom: 8px;
            }
            QTabBar::tab:selected {
                background: white;
                color: #1e293b;
                border-bottom: none;
                margin-bottom: 8px;
            }
            QTabBar::tab:hover:!selected {
                background: #64748b;
                color: #f1f5f9;
            }
            QTabBar::tab:first {
                margin-left: 8px;
            }
            QTabBar::tab:last {
                margin-right: 8px;
            }
            QGroupBox {
                font-weight: 600;
                font-size: 14px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 16px;
                background: #f8fafc;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                
                color: #1e293b;
                background: #f8fafc;
            }
            QTableWidget {
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                background: white;
                gridline-color: #f1f5f9;
                alternate-background-color: #f8fafc;
                selection-background-color: #dbeafe;
                selection-color: #1e293b;
            }
            QTableWidget::item {
                padding: 8px 4px;
                border: none;
                min-height: 20px;
            }
            QTableWidget::item:selected {
                background: #dbeafe;
                color: #1e293b;
            }
            QHeaderView::section {
                background: #e2e8f0;
                padding: 12px 8px;
                border: none;
                border-right: 1px solid #cbd5e1;
                border-bottom: 1px solid #cbd5e1;
                font-weight: 600;
                color: #1e293b;
            }
            QHeaderView::section:vertical {
                background: #f8fafc;
                padding: 8px 4px;
                border: none;
                border-bottom: 1px solid #e2e8f0;
                font-weight: 500;
                color: #64748b;
                min-width: 40px;
            }
            QProgressBar {
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                text-align: center;
                background: #f1f5f9;
            }
            QProgressBar::chunk {
                background: #3b82f6;
                border-radius: 5px;
            }
            QTextEdit {
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 12px;
                background: white;
                color: #1e293b;
                font-family: 'Segoe UI', sans-serif;
            }
            QComboBox {
                border: 2px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 12px;
                background: white;
                color: #1e293b;
                font-size: 14px;
                min-height: 40px;
            }
            QComboBox:focus {
                border-color: #3b82f6;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #6b7280;
                margin-right: 10px;
            }
            QLabel {
                color: #1e293b;
                font-weight: 500;
                font-size: 14px;
            }
        """)
        
        # System tray icon for notifications

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        self.tray_icon.setVisible(True)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # Create header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Add proper spacing after header
        spacer = QWidget()
        spacer.setFixedHeight(12)
        main_layout.addWidget(spacer)
        
        # Create tab widget with proper margins
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget {
                margin-top: 0px;
                background: transparent;
            }
            QTabWidget::pane {
                border: none;
                background: white;
                border-radius: 8px;
                margin: 4px 8px 8px 8px;
                padding-top: 4px;
            }
            QTabBar {
                background: transparent;
                spacing: 0px;
            }
            QTabBar::tab {
                background: #475569;
                color: #e2e8f0;
                padding: 12px 20px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                min-width: 120px;
                margin-bottom: 4px;
            }
            QTabBar::tab:selected {
                background: white;
                color: #1e293b;
                border-bottom: none;
                margin-bottom: 4px;
            }
            QTabBar::tab:hover:!selected {
                background: #64748b;
                color: #f1f5f9;
            }
            QTabBar::tab:first {
                margin-left: 8px;
            }
            QTabBar::tab:last {
                margin-right: 8px;
            }
        """)
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_scraping_tab()
        self.create_data_tab()
        self.create_analysis_tab()
        self.create_sitemap_tab()
        self.create_ai_tab()
        
    def create_header(self):
        """Create a clean header with help button only (no theme toggle)"""
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: #0f172a;
                border-radius: 12px;
                margin: 4px 4px 8px 4px;
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(24, 20, 24, 20)
        header_layout.setSpacing(16)
        
        # Title
        title_label = QLabel("Web Scraper & Data Analyzer")
        title_label.setStyleSheet("""
            QLabel {
                color: #f8fafc;
                font-size: 28px;
                font-weight: 800;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        
        # Subtitle
        subtitle_label = QLabel("Modern web scraping with intelligent data analysis")
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #cbd5e1;
                font-size: 16px;
                font-weight: 500;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        
        # Help button
        help_button = ModernButton("Help")
        help_button.clicked.connect(self.show_help)
        
        # Right side info
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        info_layout.setSpacing(4)
        
        version_label = QLabel("v2.0")
        version_label.setStyleSheet("""
            QLabel {
                color: #94a3b8;
                font-size: 14px;
                font-weight: 600;
                background: #1e293b;
                padding: 6px 12px;
                border-radius: 6px;
                border: 1px solid #334155;
            }
        """)
        
        info_layout.addWidget(version_label)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(subtitle_label)
        header_layout.addStretch()
        header_layout.addWidget(help_button)
        header_layout.addWidget(info_widget)
        
        return header_widget
        
    def create_scraping_tab(self):
        """Create the web scraping configuration tab"""
        scraping_widget = QWidget()
        main_layout = QVBoxLayout(scraping_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create content widget for scrolling
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Input group
        input_group = QGroupBox("Scraping Configuration")
        input_layout = QGridLayout(input_group)
        input_layout.setSpacing(12)
        
        # URL input
        input_layout.addWidget(QLabel("Website URL:"), 0, 0)
        self.url_input = ModernLineEdit("https://example.com")
        input_layout.addWidget(self.url_input, 0, 1)
        
        # Depth input
        input_layout.addWidget(QLabel("Max Depth (1-100):"), 1, 0)
        self.depth_input = ModernSpinBox()
        self.depth_input.setRange(1, 100)
        self.depth_input.setValue(3)
        input_layout.addWidget(self.depth_input, 1, 1)
        
        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.start_button = ModernButton("Start Scraping", primary=True)
        self.start_button.clicked.connect(self.start_scraping)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = ModernButton("Stop")
        self.stop_button.clicked.connect(self.stop_scraping)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        input_layout.addLayout(button_layout, 2, 0, 1, 2)
        layout.addWidget(input_group)
        
        # Progress group
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setSpacing(8)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(20)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to start scraping...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #374151;
                font-size: 14px;
                padding: 8px;
                background: #f8fafc;
                border-radius: 6px;
                border-left: 3px solid #3b82f6;
            }
        """)
        self.status_label.setWordWrap(True)  # Enable word wrapping
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)
        
        # Results preview
        results_group = QGroupBox("Scraping Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMinimumHeight(80)  # Reduced minimum height for more compact output
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        
        # Set the content widget in the scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(scraping_widget, "Web Scraping")
        
    def create_data_tab(self):
        """Create the data viewing and filtering tab"""
        data_widget = QWidget()
        layout = QVBoxLayout(data_widget)
        layout.setSpacing(16)
        
        # Search and filter controls
        controls_group = QGroupBox("Search & Filter")
        controls_layout = QHBoxLayout(controls_group)
        controls_layout.setSpacing(12)
        
        controls_layout.addWidget(QLabel("Search:"))
        self.search_input = ModernLineEdit("Enter search term...")
        self.search_input.textChanged.connect(self.filter_data)
        controls_layout.addWidget(self.search_input)
        
        controls_layout.addWidget(QLabel("Domain:"))
        self.domain_filter = QComboBox()
        self.domain_filter.currentTextChanged.connect(self.filter_data)
        controls_layout.addWidget(self.domain_filter)
        
        self.export_button = ModernButton("Export Data")
        self.export_button.clicked.connect(self.export_data)
        controls_layout.addWidget(self.export_button)
        
        # Sitemap button
        self.sitemap_button = ModernButton("Generate Sitemap.xml")
        self.sitemap_button.clicked.connect(self.generate_sitemap)
        controls_layout.addWidget(self.sitemap_button)
        
        layout.addWidget(controls_group)
        
        # Data table
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(6)
        self.data_table.setHorizontalHeaderLabels([
            "Title", "URL", "Depth", "Links", "Words", "Load Time"
        ])
        
        # Set table properties to fill available width
        header = self.data_table.horizontalHeader()
        header.setStretchLastSection(False)  # Don't stretch the last section
        
        # Set resize modes to make table fill width properly
        header.setSectionResizeMode(0, QHeaderView.Stretch)      # Title - stretch to fill
        header.setSectionResizeMode(1, QHeaderView.Stretch)      # URL - stretch to fill  
        header.setSectionResizeMode(2, QHeaderView.Fixed)        # Depth - fixed
        header.setSectionResizeMode(3, QHeaderView.Fixed)        # Links - fixed
        header.setSectionResizeMode(4, QHeaderView.Fixed)        # Words - fixed
        header.setSectionResizeMode(5, QHeaderView.Fixed)        # Load Time - fixed
        
        # Set fixed column widths for non-stretching columns
        self.data_table.setColumnWidth(2, 80)   # Depth
        self.data_table.setColumnWidth(3, 80)   # Links
        self.data_table.setColumnWidth(4, 80)   # Words
        self.data_table.setColumnWidth(5, 100)  # Load Time
        
        # Set row height to prevent index cutoff
        self.data_table.verticalHeader().setDefaultSectionSize(40)  # Increased row height
        self.data_table.verticalHeader().setMinimumSectionSize(35)  # Minimum row height
        
        # Enable word wrapping for title and URL columns
        self.data_table.setWordWrap(True)
        
        # Connect double-click signal
        self.data_table.cellDoubleClicked.connect(self.show_content_preview)
        
        layout.addWidget(self.data_table)
        
        self.tab_widget.addTab(data_widget, "Data View")
        
    def create_analysis_tab(self):
        """Create the data analysis tab"""
        analysis_widget = QWidget()
        layout = QVBoxLayout(analysis_widget)
        layout.setSpacing(16)
        
        # Create scroll area for better layout
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)
        
        # Statistics group
        stats_group = QGroupBox("Statistics")
        stats_layout = QGridLayout(stats_group)
        stats_layout.setSpacing(12)
        
        self.stats_labels = {}
        stats_fields = [
            ("Total Pages", "Total Pages"),
            ("Total Links", "Total Links"), 
            ("Total Words", "Total Words"),
            ("Average Load Time", "Average Load Time"),
            ("Max Depth Reached", "Max Depth Reached")
        ]
        
        for i, (label_text, field) in enumerate(stats_fields):
            stats_layout.addWidget(QLabel(f"{label_text}:"), i, 0)
            label = QLabel("0")
            label.setStyleSheet("""
                QLabel {
                    font-weight: 700;
                    color: #3b82f6;
                    font-size: 16px;
                    padding: 8px 12px;
                    background: #eff6ff;
                    border-radius: 6px;
                    border-left: 3px solid #3b82f6;
                }
            """)
            self.stats_labels[field] = label
            stats_layout.addWidget(label, i, 1)
        
        content_layout.addWidget(stats_group)
        
        # Domain breakdown
        domain_group = QGroupBox("Domain Breakdown")
        domain_layout = QVBoxLayout(domain_group)
        
        self.domain_text = QTextEdit()
        self.domain_text.setReadOnly(True)
        self.domain_text.setMaximumHeight(150)
        domain_layout.addWidget(self.domain_text)
        
        content_layout.addWidget(domain_group)
        
        # Content preview
        content_preview_group = QGroupBox("Content Preview")
        content_preview_layout = QVBoxLayout(content_preview_group)
        
        # Create splitter for text and visual preview
        preview_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Text preview
        text_preview_widget = QWidget()
        text_preview_layout = QVBoxLayout(text_preview_widget)
        text_preview_layout.setContentsMargins(0, 0, 0, 0)
        
        text_label = QLabel("Text Content:")
        text_label.setStyleSheet("font-weight: 600; margin-bottom: 8px;")
        text_preview_layout.addWidget(text_label)
        
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setMaximumHeight(400)
        self.content_text.setFont(QFont("Segoe UI", 12))
        self.content_text.setStyleSheet("""
            QTextEdit {
                font-size: 12px;
                line-height: 1.4;
                padding: 16px;
            }
        """)
        text_preview_layout.addWidget(self.content_text)
        
        # Visual HTML preview
        visual_preview_widget = QWidget()
        visual_preview_layout = QVBoxLayout(visual_preview_widget)
        visual_preview_layout.setContentsMargins(0, 0, 0, 0)
        
        visual_label = QLabel("Visual Preview:")
        visual_label.setStyleSheet("font-weight: 600; margin-bottom: 8px;")
        visual_preview_layout.addWidget(visual_label)
        
        if WEB_ENGINE_AVAILABLE:
            self.web_view = QWebEngineView()
            self.web_view.setMinimumHeight(400)
            self.web_view.setMaximumHeight(400)
            visual_preview_layout.addWidget(self.web_view)
        else:
            self.web_view = QLabel("Visual preview not available\nInstall PyQtWebEngine for HTML rendering")
            self.web_view.setStyleSheet("color: #6b7280; padding: 20px; text-align: center;")
            self.web_view.setMinimumHeight(400)
            self.web_view.setMaximumHeight(400)
            visual_preview_layout.addWidget(self.web_view)
        
        # Add widgets to splitter
        preview_splitter.addWidget(text_preview_widget)
        preview_splitter.addWidget(visual_preview_widget)
        preview_splitter.setSizes([400, 600])  # Set initial split ratio
        
        content_preview_layout.addWidget(preview_splitter)
        
        content_layout.addWidget(content_preview_group)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(analysis_widget, "Analysis")
        
    def create_sitemap_tab(self):
        """Create the visual sitemap tab with a tree widget and export button"""
        sitemap_widget = QWidget()
        layout = QVBoxLayout(sitemap_widget)
        layout.setSpacing(16)
        
        # Export button
        self.export_sitemap_button = ModernButton("Export Sitemap (JSON)")
        self.export_sitemap_button.clicked.connect(self.export_sitemap_json)
        layout.addWidget(self.export_sitemap_button)
        
        self.sitemap_tree = QTreeWidget()
        self.sitemap_tree.setHeaderLabels(["Page Title", "URL"])
        self.sitemap_tree.setColumnWidth(0, 350)
        self.sitemap_tree.setColumnWidth(1, 600)
        self.sitemap_tree.itemDoubleClicked.connect(self.open_url_in_browser)
        layout.addWidget(self.sitemap_tree)
        
        self.tab_widget.addTab(sitemap_widget, "Sitemap")

    def create_ai_tab(self):
        """Create a simplified, modern AI Analysis tab with a chat interface and compact quick actions, using more curves to match the app style."""
        ai_widget = QWidget()
        layout = QVBoxLayout(ai_widget)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        hint_label = QLabel("💡 Ask questions about your scraped websites below.")
        hint_label.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-size: 13px;
                padding: 4px 0 8px 0;
            }
        """)
        layout.addWidget(hint_label)

        # --- Chat area ---
        self.ai_chat_history = QListWidget()
        self.ai_chat_history.setStyleSheet("""
            QListWidget {
                background: #f8fafc;
                border: 1.5px solid #e2e8f0;
                border-radius: 22px;
                font-size: 15px;
                color: #1e293b;
                padding: 12px;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        self.ai_chat_history.setSpacing(6)
        self.ai_chat_history.setMinimumHeight(300)
        self.ai_chat_history.setResizeMode(QListWidget.Adjust)
        self.ai_chat_history.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        layout.addWidget(self.ai_chat_history, stretch=1)
        self.chat_messages = []  # Store (role, message, timestamp) tuples
        self.render_chat_history()

        # --- Quick action buttons ---
        quick_actions_widget = QWidget()
        quick_actions_layout = QHBoxLayout(quick_actions_widget)
        quick_actions_layout.setSpacing(8)
        quick_actions_layout.setContentsMargins(0, 0, 0, 0)
        quick_questions = [
            "Analyze the website structure",
            "Find key content themes",
            "Suggest SEO improvements",
            "Compare page performance"
        ]
        for question in quick_questions:
            quick_btn = QPushButton(question)
            quick_btn.setFont(QFont("Segoe UI", 10))
            quick_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            quick_btn.clicked.connect(lambda _, q=question: self.quick_question(q))
            quick_btn.setStyleSheet("""
                QPushButton {
                    background: #e0e7ef;
                    border: none;
                    color: #374151;
                    padding: 8px 22px;
                    border-radius: 22px;
                    font-weight: 500;
                    font-size: 13px;
                    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.04);
                }
                QPushButton:hover {
                    background: #3b82f6;
                    color: white;
                }
                QPushButton:pressed {
                    background: #2563eb;
                    color: white;
                }
            """)
            quick_actions_layout.addWidget(quick_btn)
        layout.addWidget(quick_actions_widget)

        # --- Input area ---
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("Type your question and press Enter...")
        self.ai_input.setMinimumHeight(44)
        self.ai_input.setFont(QFont("Segoe UI", 12))
        self.ai_input.returnPressed.connect(self.send_ai_message)
        self.ai_input.setStyleSheet("""
            QLineEdit {
                border: 1.5px solid #e2e8f0;
                border-radius: 22px;
                padding: 10px 20px;
                background: white;
                color: #1e293b;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                outline: none;
            }
            QLineEdit::placeholder {
                color: #9ca3af;
            }
        """)
        self.ai_send_button = QPushButton("Send")
        self.ai_send_button.setMinimumHeight(44)
        self.ai_send_button.setMinimumWidth(80)
        self.ai_send_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        self.ai_send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ai_send_button.clicked.connect(self.send_ai_message)
        self.ai_send_button.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                border: none;
                color: white;
                padding: 10px 28px;
                border-radius: 22px;
                font-weight: 600;
                font-size: 15px;
                box-shadow: 0 2px 8px rgba(59, 130, 246, 0.08);
            }
            QPushButton:hover {
                background: #2563eb;
            }
            QPushButton:pressed {
                background: #1d4ed8;
            }
            QPushButton:disabled {
                background: #9ca3af;
                color: #f3f4f6;
            }
        """)
        input_layout.addWidget(self.ai_input, stretch=1)
        input_layout.addWidget(self.ai_send_button)
        layout.addWidget(input_container)

        self.tab_widget.addTab(ai_widget, "AI Analysis")
        ai_tab_index = self.tab_widget.count() - 1
        self.set_ai_tab_gradient(ai_tab_index)

    def render_chat_history(self):
        self.ai_chat_history.clear()
        for role, msg, timestamp in self.chat_messages:
            item = QListWidgetItem()
            bubble = ChatBubbleWidget(msg, timestamp, role)
            bubble.adjustSize()
            item.setSizeHint(bubble.sizeHint())
            self.ai_chat_history.addItem(item)
            self.ai_chat_history.setItemWidget(item, bubble)
        self.ai_chat_history.scrollToBottom()

    def send_ai_message(self):
        user_msg = self.ai_input.text().strip()
        if not user_msg:
            return
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_messages.append(("user", user_msg, timestamp))
        self.render_chat_history()
        self.ai_input.clear()
        # Show thinking indicator as AI message
        self.chat_messages.append(("ai", "<i>🤔 Analyzing your question...</i>", timestamp))
        self.render_chat_history()
        ai_context = self.get_ai_context(user_msg)
        QTimer.singleShot(100, lambda: self._do_ai_response_openrouter(user_msg, ai_context))

    def _do_ai_response_openrouter(self, user_msg, ai_context):
        if OPENAI_AVAILABLE:
            try:
                client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=os.environ.get("OPENROUTER_API_KEY"),
                )
                system_prompt = """You are an expert website analyst and AI assistant specializing in web scraping analysis. Your role is to:\n\n1. **Analyze website content** - Provide insights about the scraped websites\n2. **Identify patterns** - Find common themes, structures, and content types\n3. **Offer recommendations** - Suggest improvements for SEO, content, or structure\n4. **Answer questions** - Respond to specific queries about the websites\n5. **Provide actionable insights** - Give practical advice based on the data\n\n**Response Guidelines:**\n- Be professional yet conversational\n- Use clear, structured responses with bullet points when appropriate\n- Reference specific websites by title when relevant\n- Provide specific examples from the content\n- Suggest actionable next steps when possible\n- Use markdown formatting for better readability\n\n**Context:** You have access to scraped website data including titles, URLs, content previews, and metadata."""
                user_prompt = f"""# Website Analysis Request\n\n## User Question\n{user_msg}\n\n## Available Website Data\n{ai_context}\n\n## Instructions\nPlease provide a comprehensive analysis based on the user's question. Use the website data above to support your response. If the question is about specific aspects (SEO, content, structure, etc.), focus your analysis accordingly.\n\n**Format your response with:**\n- Clear headings and structure\n- Specific examples from the websites\n- Actionable insights and recommendations\n- Professional, helpful tone"""
                completion = client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": "http://localhost:8000",
                        "X-Title": "Web Scraper & Data Analyzer - AI Analysis",
                    },
                    extra_body={},
                    model="deepseek/deepseek-r1-0528-qwen3-8b:free",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                try:
                    answer = completion.choices[0].message.content
                    if answer is not None:
                        answer = answer.strip()
                    else:
                        answer = "❌ **AI Analysis Error**\n\nNo response content received from the AI model."
                except (AttributeError, IndexError, KeyError):
                    answer = "❌ **AI Analysis Error**\n\nUnexpected response format from the AI model."
                if hasattr(self, "ai_stats_label"):
                    self.ai_stats_label.setText(f"Analyzed {len(self.websites)} websites")
            except Exception as e:
                answer = f"❌ **AI Analysis Error**\n\nI encountered an error while analyzing your request: `{str(e)}`\n\nPlease try again or check your internet connection."
        else:
            if ai_context == "No data available. Please scrape some websites first.":
                answer = "📊 **No Data Available**\n\nPlease scrape some websites first to enable AI analysis."
            else:
                answer = f"🤖 **AI Analysis Preview**\n\nI have analyzed {len(self.websites)} websites. Your question: '{user_msg}'\n\n*(This is a placeholder response. Install the 'openai' package for real AI analysis.)*"
        # Remove the last AI thinking message
        if self.chat_messages and self.chat_messages[-1][1].startswith("<i>🤔"):
            self.chat_messages.pop()
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_messages.append(("ai", answer, timestamp))
        self.render_chat_history()

    def open_url_in_browser(self, item, column):
        url = item.data(1, Qt.ItemDataRole.DisplayRole)
        if url:
            webbrowser.open(url)

    def get_icon(self, is_root=False):

        if is_root:
            return self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)
        else:
            return self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        """Build and display the sitemap tree from crawled data, with icons and tooltips"""
        self.sitemap_tree.clear()
        if not self.websites:
            return
        url_to_website = {w.url: w for w in self.websites}
        children_map = {w.url: [] for w in self.websites}
        for w in self.websites:
            for link in w.links:
                if link in url_to_website:
                    children_map[w.url].append(link)
        root_url = self.websites[0].url
        def add_items(parent_item, url, visited, depth):
            if url in visited:
                return
            visited.add(url)
            website = url_to_website[url]
            item = QTreeWidgetItem([website.title, website.url])
            item.setIcon(0, self.get_icon(is_root=False))
            tooltip = f"<b>Title:</b> {website.title}<br>"
            tooltip += f"<b>URL:</b> {website.url}<br>"
            tooltip += f"<b>Depth:</b> {website.depth}<br>"
            tooltip += f"<b>Outgoing Links:</b> {len(website.links)}"
            item.setToolTip(0, tooltip)
            item.setToolTip(1, tooltip)
            parent_item.addChild(item)
            for child_url in children_map[url]:
                add_items(item, child_url, visited, depth+1)
        root_website = url_to_website[root_url]
        root_item = QTreeWidgetItem([root_website.title, root_website.url])
        root_item.setIcon(0, self.get_icon(is_root=True))
        tooltip = f"<b>Title:</b> {root_website.title}<br>"
        tooltip += f"<b>URL:</b> {root_website.url}<br>"
        tooltip += f"<b>Depth:</b> {root_website.depth}<br>"
        tooltip += f"<b>Outgoing Links:</b> {len(root_website.links)}"
        root_item.setToolTip(0, tooltip)
        root_item.setToolTip(1, tooltip)
        self.sitemap_tree.addTopLevelItem(root_item)
        visited = set([root_url])
        for child_url in children_map[root_url]:
            add_items(root_item, child_url, visited, 1)
        self.sitemap_tree.expandToDepth(1)

    def export_sitemap_json(self):
        """Export the sitemap tree as a JSON file (preserving hierarchy)"""
        if not self.websites:
            QMessageBox.warning(self, "Error", "No sitemap data to export.")
            return
        def build_tree(item):
            data = {
                'title': item.text(0),
                'url': item.text(1),
                'children': [build_tree(item.child(i)) for i in range(item.childCount())]
            }
            return data
        root = self.sitemap_tree.topLevelItem(0)
        if not root:
            QMessageBox.warning(self, "Error", "No sitemap data to export.")
            return
        sitemap_data = build_tree(root)
        try:
            with open('sitemap_tree.json', 'w', encoding='utf-8') as f:
                json.dump(sitemap_data, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Success", "Sitemap exported to 'sitemap_tree.json'")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export sitemap: {e}")

    def is_valid_url(self, url):
        """Check if the URL is valid (basic check for scheme and domain)"""
        try:
            parsed = urlparse(url)
            return all([parsed.scheme in ("http", "https"), parsed.netloc])
        except Exception:
            return False

    def start_scraping(self):
        """Start the web scraping process"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a valid URL")
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Validate URL format
        if not self.is_valid_url(url):
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid website URL (e.g. https://example.com)")
            return
        
        max_depth = self.depth_input.value()
        
        # Update UI
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Scraping in progress...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #1e40af;
                font-size: 14px;
                padding: 8px;
                background: #eff6ff;
                border-radius: 6px;
                border-left: 3px solid #3b82f6;
            }
        """)
        
        # Start scraping thread
        self.scraping_thread = ScrapingThread(url, max_depth)
        self.scraping_thread.progress_updated.connect(self.update_progress)
        self.scraping_thread.scraping_complete.connect(self.scraping_finished)
        self.scraping_thread.error_occurred.connect(self.scraping_error)
        self.scraping_thread.start()
        
    def stop_scraping(self):
        """Stop the scraping process"""
        if hasattr(self, 'scraping_thread') and self.scraping_thread.isRunning():
            # Use graceful stop instead of forceful termination
            self.scraping_thread.stop()
            
            # Wait for the thread to finish gracefully (with timeout)
            if not self.scraping_thread.wait(5000):  # Wait up to 5 seconds
                # If it doesn't stop gracefully, then force terminate
                self.scraping_thread.terminate()
                self.scraping_thread.wait(2000)  # Wait up to 2 more seconds
            
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Scraping stopped.")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #92400e;
                font-size: 14px;
                padding: 8px;
                background: #fffbeb;
                border-radius: 6px;
                border-left: 3px solid #f59e0b;
            }
        """)
        
    def update_progress(self, message):
        """Update progress message"""
        self.status_label.setText(message)
        self.results_text.append(message)
        
    def show_help(self):
        """Show a help/info dialog with usage instructions (no theme switch info)"""
        help_text = (
            "<h2>Web Scraper & Data Analyzer - Help</h2>"
            "<ul>"
            "<li><b>Enter a valid website URL</b> and set the max depth, then click <b>Start Scraping</b>.</li>"
            "<li>View and filter scraped data in the <b>Data View</b> tab.</li>"
            "<li>Analyze statistics and preview content in the <b>Analysis</b> tab.</li>"
            "<li>Export data to JSON or generate a <b>sitemap.xml</b> from the Data View tab.</li>"
            "<li>Get desktop notifications when scraping completes or on errors.</li>"
            "</ul>"
            "<p>For more info, see the README or contact support.</p>"
        )
        QMessageBox.information(self, "Help / Info", help_text)

    def scraping_finished(self, websites):
        """Handle scraping completion"""
        self.websites = websites
        self.scraper.websites = websites
        
        # Update UI
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Scraping complete! Found {len(websites)} websites.")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #166534;
                font-size: 14px;
                padding: 8px;
                background: #f0fdf4;
                border-radius: 6px;
                border-left: 3px solid #22c55e;
            }
        """)
        
        # Update data view
        self.update_data_table()
        self.update_analysis()
        self.update_sitemap_tree()
        
        # Switch to data tab
        self.tab_widget.setCurrentIndex(1)
        
        # Show desktop notification
        self.tray_icon.showMessage(
            "Web Scraper",
            f"Scraping complete! Found {len(websites)} websites.",
            QSystemTrayIcon.MessageIcon(1),  # 1 = Information
            5000
        )
        
    def scraping_error(self, error_message):
        """Handle scraping errors"""
        QMessageBox.critical(self, "Error", f"Scraping failed: {error_message}")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Scraping failed.")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #991b1b;
                font-size: 14px;
                padding: 8px;
                background: #fef2f2;
                border-radius: 6px;
                border-left: 3px solid #ef4444;
            }
        """)
        
        # Show desktop notification
        self.tray_icon.showMessage(
            "Web Scraper",
            f"Scraping failed: {error_message}",
            QSystemTrayIcon.MessageIcon(3),
            5000
        )
        
    def update_data_table(self):
        """Update the data table with scraped websites"""
        self.data_table.setRowCount(len(self.websites))
        for row, website in enumerate(self.websites):
            self.data_table.setRowHeight(row, 40)
            title_item = QTableWidgetItem(website.title)
            title_item.setTextAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            url_item = QTableWidgetItem(website.url)
            url_item.setTextAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            depth_item = QTableWidgetItem(str(website.depth))
            depth_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            links_item = QTableWidgetItem(str(len(website.links)))
            links_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            words_item = QTableWidgetItem(str(website.get_word_count()))
            words_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            load_time = f"{website.load_time:.2f}s" if website.load_time else "N/A"
            load_time_item = QTableWidgetItem(load_time)
            load_time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.data_table.setItem(row, 0, title_item)
            self.data_table.setItem(row, 1, url_item)
            self.data_table.setItem(row, 2, depth_item)
            self.data_table.setItem(row, 3, links_item)
            self.data_table.setItem(row, 4, words_item)
            self.data_table.setItem(row, 5, load_time_item)
        # Update domain filter
        domains = list(set(w.get_normalized_domain() for w in self.websites))
        self.domain_filter.clear()
        self.domain_filter.addItem("All Domains")
        self.domain_filter.addItems(domains)
        # Update content preview with first website
        if self.websites:
            first_website = self.websites[0]
            content_preview = first_website.get_text_preview(800)
            self.content_text.setText(content_preview)
            
            # Also update visual preview for first website
            if WEB_ENGINE_AVAILABLE and hasattr(self, 'web_view'):
                try:
                    html_content = first_website.content
                    if html_content and html_content.strip():
                        full_html = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="utf-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>{first_website.title}</title>
                            <style>
                                body {{ 
                                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                                    line-height: 1.6;
                                    margin: 20px;
                                    color: #333;
                                }}
                                img {{ max-width: 100%; height: auto; }}
                                a {{ color: #3b82f6; text-decoration: none; }}
                                a:hover {{ text-decoration: underline; }}
                            </style>
                        </head>
                        <body>
                            {html_content}
                        </body>
                        </html>
                        """
                        self.web_view.setHtml(full_html, QUrl(first_website.url))
                    else:
                        self.web_view.setHtml("""
                        <html>
                        <body style="font-family: Arial, sans-serif; padding: 20px; color: #666;">
                            <h3>No HTML Content Available</h3>
                            <p>This page doesn't have HTML content to display in the visual preview.</p>
                        </body>
                        </html>
                        """)
                except Exception as e:
                    self.web_view.setHtml(f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; padding: 20px; color: #dc2626;">
                        <h3>Error Loading Preview</h3>
                        <p>Failed to load the visual preview:</p>
                        <p><strong>{str(e)}</strong></p>
                        <p>This might be due to:</p>
                        <ul>
                            <li>Invalid HTML content</li>
                            <li>Missing resources (images, CSS, etc.)</li>
                            <li>Security restrictions</li>
                        </ul>
                    </body>
                    </html>
                    """)
            
    def filter_data(self):
        """Filter the data table based on search and domain filters"""
        search_term = self.search_input.text().lower()
        selected_domain = self.domain_filter.currentText()
        
        for row in range(self.data_table.rowCount()):
            website = self.websites[row]
            
            # Check search term
            matches_search = (search_term in website.title.lower() or 
                            search_term in website.url.lower() or
                            website.search_content(search_term))
            
            # Check domain filter
            matches_domain = (selected_domain == "All Domains" or 
                            website.get_normalized_domain() == selected_domain)
            
            # Show/hide row
            self.data_table.setRowHidden(row, not (matches_search and matches_domain))
            
    def update_analysis(self):
        """Update the analysis tab with enhanced statistics"""
        if not self.websites:
            return
            
        stats = self.scraper.get_statistics()
        
        # Update statistics labels
        self.stats_labels["Total Pages"].setText(str(stats['total_pages']))
        self.stats_labels["Total Links"].setText(str(stats['total_links']))
        self.stats_labels["Total Words"].setText(str(stats['total_words']))
        self.stats_labels["Average Load Time"].setText(f"{stats['avg_load_time']:.2f}s")
        self.stats_labels["Max Depth Reached"].setText(str(stats['max_depth_reached']))
        
        # Update domain breakdown with enhanced information
        domain_text = "Domain Breakdown:\n\n"
        
        # Show visited URLs count
        domain_text += f"📊 Total URLs Checked: {stats.get('visited_urls_count', 0)}\n"
        domain_text += f"🎯 Starting Domain: {stats.get('start_domain', 'N/A')}\n\n"
        
        # Show domain page counts
        if stats.get('domain_page_counts'):
            domain_text += "📈 Pages per Domain:\n"
            for domain, count in stats['domain_page_counts'].items():
                domain_text += f"  • {domain}: {count} pages\n"
            domain_text += "\n"
        
        # Show final domain breakdown
        domain_text += "🏠 Final Domain Distribution:\n"
        for domain, count in stats['domains'].items():
            domain_text += f"  • {domain}: {count} pages\n"
        
        self.domain_text.setText(domain_text)
        
    def export_data(self):
        """Export scraped data to JSON file"""
        if not self.websites:
            QMessageBox.warning(self, "Error", "No data to export")
            return
            
        try:
            data = []
            for website in self.websites:
                website_data = {
                    'title': website.title,
                    'url': website.url,
                    'depth': website.depth,
                    'links': website.links,
                    'word_count': website.get_word_count(),
                    'load_time': website.load_time,
                    'domain': website.get_domain(),
                    'normalized_domain': website.get_normalized_domain(),
                    'timestamp': website.timestamp.isoformat()
                }
                data.append(website_data)
                
            with open('scraped_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            QMessageBox.information(self, "Success", "Data exported to 'scraped_data.json'")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export data: {e}")

    def show_content_preview(self, row, column):
        """Show content preview for the selected website"""
        if row < len(self.websites):
            website = self.websites[row]
            
            # Update text preview with more content
            content_preview = website.get_text_preview(1000)  # Increased from 500
            self.content_text.setText(content_preview)
            
            # Update visual HTML preview
            if WEB_ENGINE_AVAILABLE and hasattr(self, 'web_view'):
                try:
                    # Get the HTML content
                    html_content = website.content
                    if html_content and html_content.strip():
                        # Create a complete HTML document with proper encoding
                        full_html = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="utf-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>{website.title}</title>
                            <style>
                                body {{ 
                                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                                    line-height: 1.6;
                                    margin: 20px;
                                    color: #333;
                                }}
                                img {{ max-width: 100%; height: auto; }}
                                a {{ color: #3b82f6; text-decoration: none; }}
                                a:hover {{ text-decoration: underline; }}
                            </style>
                        </head>
                        <body>
                            {html_content}
                        </body>
                        </html>
                        """
                        
                        # Load the HTML content
                        self.web_view.setHtml(full_html, QUrl(website.url))
                    else:
                        # Show a message if no HTML content
                        self.web_view.setHtml("""
                        <html>
                        <body style="font-family: Arial, sans-serif; padding: 20px; color: #666;">
                            <h3>No HTML Content Available</h3>
                            <p>This page doesn't have HTML content to display in the visual preview.</p>
                            <p>Check the text preview tab for the extracted content.</p>
                        </body>
                        </html>
                        """)
                except Exception as e:
                    # Show error message in the web view
                    error_html = f"""
                    <html>
                    <body style="font-family: Arial, sans-serif; padding: 20px; color: #dc2626;">
                        <h3>Error Loading Preview</h3>
                        <p>Failed to load the visual preview:</p>
                        <p><strong>{str(e)}</strong></p>
                        <p>This might be due to:</p>
                        <ul>
                            <li>Invalid HTML content</li>
                            <li>Missing resources (images, CSS, etc.)</li>
                            <li>Security restrictions</li>
                        </ul>
                    </body>
                    </html>
                    """
                    self.web_view.setHtml(error_html)
            else:
                # Fallback for when PyQtWebEngine is not available
                if hasattr(self, 'web_view'):
                    self.web_view.setText("Visual preview not available\nInstall PyQtWebEngine for HTML rendering")

    def generate_sitemap(self):
        """Generate sitemap.xml from crawled URLs"""
        if not self.websites:
            QMessageBox.warning(self, "Error", "No data to generate sitemap.")
            return
        try:
            urls = [w.url for w in self.websites]
            sitemap = [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            ]
            for url in urls:
                sitemap.append("  <url>")
                sitemap.append(f"    <loc>{url}</loc>")
                sitemap.append("  </url>")
            sitemap.append("</urlset>")
            with open("sitemap.xml", "w", encoding="utf-8") as f:
                f.write("\n".join(sitemap))
            QMessageBox.information(self, "Sitemap Generated", "sitemap.xml has been created in the current directory.")
            self.tray_icon.showMessage(
                "Web Scraper",
                "sitemap.xml has been generated.",
                QSystemTrayIcon.MessageIcon(1),
                4000
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate sitemap: {e}")
            self.tray_icon.showMessage(
                "Web Scraper",
                f"Failed to generate sitemap: {e}",
                QSystemTrayIcon.MessageIcon(3),
                4000
            )

    def update_sitemap_tree(self):
        """Build and display the sitemap tree from crawled data, with icons and tooltips."""
        self.sitemap_tree.clear()
        if not self.websites:
            return
        url_to_website = {w.url: w for w in self.websites}
        children_map = {w.url: [] for w in self.websites}
        for w in self.websites:
            for link in w.links:
                if link in url_to_website:
                    children_map[w.url].append(link)
        root_url = self.websites[0].url
        def add_items(parent_item, url, visited, depth):
            if url in visited:
                return
            visited.add(url)
            website = url_to_website[url]
            item = QTreeWidgetItem([website.title, website.url])
            item.setIcon(0, self.get_icon(is_root=False))
            tooltip = f"<b>Title:</b> {website.title}<br>"
            tooltip += f"<b>URL:</b> {website.url}<br>"
            tooltip += f"<b>Depth:</b> {website.depth}<br>"
            tooltip += f"<b>Outgoing Links:</b> {len(website.links)}"
            item.setToolTip(0, tooltip)
            item.setToolTip(1, tooltip)
            parent_item.addChild(item)
            for child_url in children_map[url]:
                add_items(item, child_url, visited, depth+1)
        root_website = url_to_website[root_url]
        root_item = QTreeWidgetItem([root_website.title, root_website.url])
        root_item.setIcon(0, self.get_icon(is_root=True))
        tooltip = f"<b>Title:</b> {root_website.title}<br>"
        tooltip += f"<b>URL:</b> {root_website.url}<br>"
        tooltip += f"<b>Depth:</b> {root_website.depth}<br>"
        tooltip += f"<b>Outgoing Links:</b> {len(root_website.links)}"
        root_item.setToolTip(0, tooltip)
        root_item.setToolTip(1, tooltip)
        self.sitemap_tree.addTopLevelItem(root_item)
        visited = set([root_url])
        for child_url in children_map[root_url]:
            add_items(root_item, child_url, visited, 1)
        self.sitemap_tree.expandToDepth(1)

    def set_ai_tab_gradient(self, tab_index):
        """Apply premium gradient styling to the AI tab header"""
        gradient_css = """
        QTabBar::tab:nth-child({}) {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
            color: white;
            font-weight: 700;
            border: 2px solid #667eea;
            border-bottom: none;
            padding: 14px 24px;
            font-size: 15px;
        }}
        QTabBar::tab:nth-child({}):selected {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #f093fb, stop:0.5 #764ba2, stop:1 #667eea);
            color: white;
            font-weight: 800;
            border-bottom: none;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }}
        QTabBar::tab:nth-child({}):hover:!selected {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #5a67d8, stop:0.5 #6b46c1, stop:1 #e879f9);
        }}
        """.format(tab_index+1, tab_index+1, tab_index+1)
        self.tab_widget.tabBar().setStyleSheet(self.tab_widget.tabBar().styleSheet() + gradient_css)

    def quick_question(self, question):
        """Handle quick question button clicks by sending the question as if typed by the user."""
        self.ai_input.setText(question)
        self.send_ai_message()

    def get_ai_context(self, user_msg=None):
        """Return a string summary of the scraped websites for AI analysis. If no data, return a message indicating no data is available."""
        if not self.websites:
            return "No data available. Please scrape some websites first."
        # Summarize up to 5 websites for context
        context_lines = []
        for i, w in enumerate(self.websites[:5]):
            context_lines.append(f"{i+1}. Title: {w.title}\n   URL: {w.url}\n   Preview: {w.get_text_preview(120)}")
        context = "\n".join(context_lines)
        return context

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for modern look
    
    # Set application icon and properties
    app.setApplicationName("Web Scraper & Data Analyzer")
    app.setApplicationVersion("2.0")
    
    window = WebScraperApp()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 