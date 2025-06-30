import sys
import os
import json
import csv
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from tabulate import tabulate

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QDockWidget, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QFileDialog, QTextEdit, QComboBox, QTabWidget, QGroupBox, QCheckBox,
    QSlider, QSpinBox, QProgressBar, QMenuBar, QMenu, QToolBar, QHeaderView,
    QAbstractItemView, QSizePolicy, QFrame, QScrollArea, QGridLayout
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QRect, QPoint,
    QPropertyAnimation, QEasingCurve, pyqtSlot, QFileSystemWatcher
)
from PyQt6.QtGui import (
    QAction, QIcon, QColor, QPalette, QFont, QLinearGradient,
    QPainter, QBrush, QPen, QPixmap, QDragEnterEvent, QDropEvent
)

import matplotlib

matplotlib.use('QtAgg')  # Fixed: Use QtAgg for PyQt6
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import seaborn as sns

# Set matplotlib style
plt.style.use('dark_background')
sns.set_palette("husl")


class DataProcessor(QThread):
    """Background thread for processing data files."""
    data_ready = pyqtSignal(pd.DataFrame, str)
    error_occurred = pyqtSignal(str)
    progress_update = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.file_path: Optional[str] = None

    def set_file(self, file_path: str) -> None:
        """Set the file path to process."""
        self.file_path = file_path

    def run(self) -> None:
        """Process the data file in background."""
        if not self.file_path:
            return

        try:
            self.progress_update.emit(10)
            df = None
            if self.file_path.endswith('.csv'):
                try:
                    df = pd.read_csv(self.file_path, skip_blank_lines=True, engine='python')
                    df.dropna(how='all', inplace=True)  # Remove any fully empty rows
                except Exception as e:
                    self.error_occurred.emit(f"Failed to load CSV: {e}")
                    self.progress_update.emit(0)
                    return
            elif self.file_path.endswith('.json'):
                try:
                    df = pd.read_json(self.file_path)
                except Exception as e:
                    self.error_occurred.emit(f"Failed to load JSON: {e}")
                    self.progress_update.emit(0)
                    return
            else:
                self.error_occurred.emit(f"Unsupported file type: {self.file_path}")
                self.progress_update.emit(0)
                return

            self.progress_update.emit(50)

            # Infer data types
            for col in df.columns:
                if df[col].dtype == 'object':
                    try:
                        df[col] = pd.to_numeric(df[col])
                    except Exception:
                        pass

            self.progress_update.emit(100)
            self.data_ready.emit(df, self.file_path)

        except Exception as e:
            self.error_occurred.emit(str(e))
            self.progress_update.emit(0)


class StyledButton(QPushButton):
    """Custom styled button with hover effects."""

    def __init__(self, text: str, icon_color: str = "#00ff88"):
        super().__init__(text)
        self.icon_color = icon_color
        self.setStyleSheet(f"""
           QPushButton {{
               background-color: #2a2a2a;
               border: 1px solid #3a3a3a;
               border-radius: 6px;
               padding: 8px 16px;
               color: #ffffff;
               font-weight: bold;
               font-size: 12px;
           }}
           QPushButton:hover {{
               background-color: #3a3a3a;
               border: 1px solid {self.icon_color};
           }}
           QPushButton:pressed {{
               background-color: #1a1a1a;
           }}
       """)


class PlotCanvas(FigureCanvas):
    """Matplotlib canvas for displaying plots."""

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(8, 6), facecolor='#1e1e1e')
        super().__init__(self.figure)
        self.setParent(parent)
        self.setStyleSheet("background-color: #1e1e1e;")

    def clear_plot(self) -> None:
        """Clear all plots from the canvas."""
        self.figure.clear()
        self.draw()

    def create_bar_chart(self, data: pd.DataFrame, x_col: str, y_col: str) -> None:
        """Create a bar chart from the data."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#1e1e1e')

        colors = ['#00ff88', '#ff0088', '#0088ff', '#ff8800', '#8800ff']
        ax.bar(data[x_col], data[y_col], color=colors[0], alpha=0.8, edgecolor='white', linewidth=0.5)

        ax.set_xlabel(x_col, color='white', fontsize=12)
        ax.set_ylabel(y_col, color='white', fontsize=12)
        ax.set_title(f'{y_col} by {x_col}', color='white', fontsize=14, fontweight='bold')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.2, linestyle='--')

        for spine in ax.spines.values():
            spine.set_edgecolor('#3a3a3a')

        self.figure.tight_layout()
        self.draw()

    def create_pie_chart(self, data: pd.DataFrame, col: str) -> None:
        """Create a pie chart from the data."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        value_counts = data[col].value_counts()
        colors = list(plt.cm.Set3(np.linspace(0, 1, len(value_counts))))

        wedges, texts, autotexts = ax.pie(
            value_counts.values,
            labels=value_counts.index,
            autopct='%1.1f%%',
            colors=colors,
            explode=[0.05] * len(value_counts),
            shadow=True,
            startangle=90
        )

        for text in texts:
            text.set_color('white')
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontweight('bold')

        ax.set_title(f'Distribution of {col}', color='white', fontsize=14, fontweight='bold')
        self.figure.tight_layout()
        self.draw()

    def create_line_chart(self, data: pd.DataFrame, x_col: str, y_col: str) -> None:
        """Create a line chart from the data."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#1e1e1e')

        ax.plot(data[x_col], data[y_col], color='#00ff88', linewidth=2, marker='o', markersize=6,
                markerfacecolor='#ff0088', markeredgecolor='white')

        ax.set_xlabel(x_col, color='white', fontsize=12)
        ax.set_ylabel(y_col, color='white', fontsize=12)
        ax.set_title(f'{y_col} over {x_col}', color='white', fontsize=14, fontweight='bold')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.2, linestyle='--')

        for spine in ax.spines.values():
            spine.set_edgecolor('#3a3a3a')

        self.figure.tight_layout()
        self.draw()


class AutoVizApp(QMainWindow):
    """Main application window for automated visualization and analytics."""

    def __init__(self):
        super().__init__()
        # Initialize instance attributes
        self.current_df: Optional[pd.DataFrame] = None
        self.current_file: Optional[str] = None
        self.watch_folder: Optional[str] = None
        self.processed_files: set = set()
        self.dark_mode: bool = True

        # Initialize UI components (will be set in init_ui)
        self.main_splitter: Optional[QSplitter] = None
        self.file_label: Optional[QLabel] = None
        self.data_table: Optional[QTableWidget] = None
        self.refresh_btn: Optional[QPushButton] = None
        self.clear_btn: Optional[QPushButton] = None
        self.viz_tabs: Optional[QTabWidget] = None
        self.plot_canvas: Optional[PlotCanvas] = None
        self.chart_type: Optional[QComboBox] = None
        self.x_column: Optional[QComboBox] = None
        self.y_column: Optional[QComboBox] = None
        self.plot_btn: Optional[QPushButton] = None
        self.stats_widget: Optional[QTextEdit] = None
        self.metrics_text: Optional[QTextEdit] = None
        self.run_regression_btn: Optional[QPushButton] = None
        self.regression_text: Optional[QTextEdit] = None
        self.log_widget: Optional[QTextEdit] = None
        self.progress_bar: Optional[QProgressBar] = None
        self.file_watcher: Optional[QFileSystemWatcher] = None
        self.watch_timer: Optional[QTimer] = None

        # Initialize UI
        self.init_ui()
        self.apply_theme()

        # Setup data processor thread
        self.data_processor = DataProcessor()
        self.data_processor.data_ready.connect(self.on_data_loaded)
        self.data_processor.error_occurred.connect(self.on_error)
        self.data_processor.progress_update.connect(self.update_progress)

    def init_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle("AutoViz Analytics Dashboard")
        self.setGeometry(100, 100, 1400, 900)

        # Central widget setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create menu bar
        self.create_menu_bar()

        # Create toolbar
        self.create_toolbar()

        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)

        # Left dock - Data panel
        self.create_data_dock()

        # Center - Visualization area
        self.create_viz_area()

        # Right dock - Insights panel
        self.create_insights_dock()

        # Bottom dock - Log panel
        self.create_log_dock()

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
           QProgressBar {
               background-color: #2a2a2a;
               border: none;
           }
           QProgressBar::chunk {
               background-color: #00ff88;
           }
       """)
        main_layout.addWidget(self.progress_bar)

        # Enable drag and drop
        self.setAcceptDrops(True)

    def create_menu_bar(self) -> None:
        """Create the application menu bar."""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
           QMenuBar {
               background-color: #2a2a2a;
               color: white;
               padding: 5px;
           }
           QMenuBar::item:selected {
               background-color: #3a3a3a;
           }
       """)

        # File menu
        file_menu = menubar.addMenu("File")

        open_action = QAction("Open File", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        watch_action = QAction("Watch Folder", self)
        watch_action.setShortcut("Ctrl+W")
        watch_action.triggered.connect(self.setup_watch_folder)
        file_menu.addAction(watch_action)

        file_menu.addSeparator()

        export_action = QAction("Export Plot", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_plot)
        file_menu.addAction(export_action)

        # View menu
        view_menu = menubar.addMenu("View")

        theme_action = QAction("Toggle Theme", self)
        theme_action.setShortcut("Ctrl+T")
        theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_action)

    def create_toolbar(self) -> None:
        """Create the main toolbar."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
           QToolBar {
               background-color: #2a2a2a;
               border: none;
               padding: 5px;
           }
       """)
        self.addToolBar(toolbar)

        # Add actions with proper connections
        open_btn = StyledButton("📁 Open", "#00ff88")
        open_btn.clicked.connect(self.open_file)
        toolbar.addWidget(open_btn)

        watch_btn = StyledButton("👁️ Watch", "#0088ff")
        watch_btn.clicked.connect(self.setup_watch_folder)
        toolbar.addWidget(watch_btn)

        bar_btn = StyledButton("📊 Bar Chart", "#ff0088")
        bar_btn.clicked.connect(lambda: self.quick_plot("Bar Chart"))
        toolbar.addWidget(bar_btn)

        pie_btn = StyledButton("🥧 Pie Chart", "#ff8800")
        pie_btn.clicked.connect(lambda: self.quick_plot("Pie Chart"))
        toolbar.addWidget(pie_btn)

        line_btn = StyledButton("📈 Line Chart", "#8800ff")
        line_btn.clicked.connect(lambda: self.quick_plot("Line Chart"))
        toolbar.addWidget(line_btn)

        toolbar.addSeparator()

        export_btn = StyledButton("💾 Export", "#00ffff")
        export_btn.clicked.connect(self.export_plot)
        toolbar.addWidget(export_btn)

    def create_data_dock(self) -> None:
        """Create the data panel dock widget."""
        data_dock = QDockWidget("Data Explorer", self)
        data_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable)

        data_widget = QWidget()
        data_layout = QVBoxLayout(data_widget)

        # File info
        self.file_label = QLabel("No file loaded")
        self.file_label.setStyleSheet("color: #888; padding: 10px; font-size: 12px;")
        data_layout.addWidget(self.file_label)

        # Data table
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.data_table.horizontalHeader().setStretchLastSection(True)
        self.data_table.setStyleSheet("""
           QTableWidget {
               background-color: #1e1e1e;
               alternate-background-color: #2a2a2a;
               color: white;
               gridline-color: #3a3a3a;
               selection-background-color: #00ff88;
               selection-color: black;
           }
           QHeaderView::section {
               background-color: #3a3a3a;
               color: white;
               padding: 5px;
               border: 1px solid #2a2a2a;
           }
       """)
        data_layout.addWidget(self.data_table)

        # Control buttons
        button_layout = QHBoxLayout()

        self.refresh_btn = StyledButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_data)
        button_layout.addWidget(self.refresh_btn)

        self.clear_btn = StyledButton("Clear")
        self.clear_btn.clicked.connect(self.clear_data)
        button_layout.addWidget(self.clear_btn)

        data_layout.addLayout(button_layout)

        data_dock.setWidget(data_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, data_dock)

    def create_viz_area(self) -> None:
        """Create the central visualization area."""
        viz_widget = QWidget()
        viz_layout = QVBoxLayout(viz_widget)
        viz_layout.setContentsMargins(10, 10, 10, 10)

        # Tab widget for multiple views
        self.viz_tabs = QTabWidget()
        self.viz_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.viz_tabs.setStyleSheet("""
           QTabWidget::pane {
               border: 1px solid #3a3a3a;
               background-color: #1e1e1e;
           }
           QTabBar::tab {
               background-color: #2a2a2a;
               color: white;
               padding: 8px 16px;
               margin-right: 2px;
           }
           QTabBar::tab:selected {
               background-color: #3a3a3a;
               border-bottom: 2px solid #00ff88;
           }
           QTabBar::tab:hover {
               background-color: #3a3a3a;
           }
       """)

        # Plot tab
        self.plot_canvas = PlotCanvas()
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)

        # Chart controls
        controls_layout = QHBoxLayout()

        self.chart_type = QComboBox()
        self.chart_type.addItems(["Bar Chart", "Pie Chart", "Line Chart"])
        self.chart_type.setStyleSheet("""
           QComboBox {
               background-color: #2a2a2a;
               color: white;
               padding: 5px;
               border: 1px solid #3a3a3a;
               border-radius: 4px;
           }
           QComboBox::drop-down {
               border: none;
           }
           QComboBox::down-arrow {
               image: none;
               border-left: 5px solid transparent;
               border-right: 5px solid transparent;
               border-top: 5px solid white;
               margin-right: 5px;
           }
       """)
        controls_layout.addWidget(QLabel("Chart Type:"))
        controls_layout.addWidget(self.chart_type)

        self.x_column = QComboBox()
        self.x_column.setStyleSheet(self.chart_type.styleSheet())
        controls_layout.addWidget(QLabel("X Axis:"))
        controls_layout.addWidget(self.x_column)

        self.y_column = QComboBox()
        self.y_column.setStyleSheet(self.chart_type.styleSheet())
        controls_layout.addWidget(QLabel("Y Axis:"))
        controls_layout.addWidget(self.y_column)

        self.plot_btn = StyledButton("Generate Plot")
        self.plot_btn.clicked.connect(self.generate_plot)
        controls_layout.addWidget(self.plot_btn)

        controls_layout.addStretch()

        plot_layout.addLayout(controls_layout)
        plot_layout.addWidget(self.plot_canvas)

        self.viz_tabs.addTab(plot_container, "Visualization")

        # Statistics tab
        self.stats_widget = QTextEdit()
        self.stats_widget.setReadOnly(True)
        self.stats_widget.setStyleSheet("""
           QTextEdit {
               background-color: #1e1e1e;
               color: white;
               font-family: 'Consolas', 'Monaco', monospace;
               font-size: 12px;
               border: none;
           }
       """)
        self.viz_tabs.addTab(self.stats_widget, "Statistics")

        viz_layout.addWidget(self.viz_tabs)
        self.main_splitter.addWidget(viz_widget)

    def create_insights_dock(self) -> None:
        """Create the insights panel dock widget."""
        insights_dock = QDockWidget("Insights & Analysis", self)
        insights_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable)

        insights_widget = QWidget()
        insights_layout = QVBoxLayout(insights_widget)

        # Metrics group
        metrics_group = QGroupBox("Key Metrics")
        metrics_group.setStyleSheet("""
           QGroupBox {
               background-color: transparent;
               border: none;
           }
           QGroupBox::title {
               subcontrol-origin: margin;
               subcontrol-position: top center;
               color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,
                   stop:0 #ff8800, stop:1 #00ffff);
               border: 2px solid black;
               border-radius: 4px;
               padding: 4px 8px;
               font-family: 'Consolas', monospace;
               font-size: 14px;
           }
        """)
        metrics_layout = QVBoxLayout()

        self.metrics_text = QTextEdit()
        self.metrics_text.setReadOnly(True)
        self.metrics_text.setMaximumHeight(150)
        self.metrics_text.setStyleSheet("""
           QTextEdit {
               background-color: #ffffff;
               color: #000000;
               font-family: 'Consolas', 'Monaco', monospace;
               font-size: 14px;
               border: 1px solid #3a3a3a;
               padding: 5px;
           }
       """)
        metrics_layout.addWidget(self.metrics_text)
        metrics_group.setLayout(metrics_layout)
        insights_layout.addWidget(metrics_group)

        # Regression analysis group
        regression_group = QGroupBox("Regression Analysis")
        regression_group.setStyleSheet("""
           QGroupBox {
               background-color: transparent;
               border: none;
           }
           QGroupBox::title {
               subcontrol-origin: margin;
               subcontrol-position: top center;
               color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,
                   stop:0 #ff8800, stop:1 #00ffff);
               border: 2px solid black;
               border-radius: 4px;
               padding: 4px 8px;
               font-family: 'Consolas', monospace;
               font-size: 14px;
           }
        """)
        regression_layout = QVBoxLayout()

        reg_controls = QHBoxLayout()
        self.run_regression_btn = StyledButton("Run OLS")
        self.run_regression_btn.clicked.connect(self.run_regression)
        reg_controls.addWidget(self.run_regression_btn)
        reg_controls.addStretch()
        regression_layout.addLayout(reg_controls)

        self.regression_text = QTextEdit()
        self.regression_text.setReadOnly(True)
        # Improved styling for regression output
        self.regression_text.setStyleSheet("""
           QTextEdit {
               background-color: #1e1e1e;
               color: white;
               font-family: 'Consolas', 'Monaco', monospace;
               font-size: 12px;
               line-height: 1.4em;
               border: 1px solid #3a3a3a;
               padding: 5px;
           }
        """)
        self.regression_text.setFont(QFont("Consolas", 12))
        regression_layout.addWidget(self.regression_text)

        regression_group.setLayout(regression_layout)
        insights_layout.addWidget(regression_group)

        insights_dock.setWidget(insights_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, insights_dock)

    def create_log_dock(self) -> None:
        """Create the log panel dock widget."""
        log_dock = QDockWidget("Activity Log", self)
        log_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable)

        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setMaximumHeight(150)
        self.log_widget.setStyleSheet("""
           QTextEdit {
               background-color: #1a1a1a;
               color: #00ff88;
               font-family: 'Consolas', 'Monaco', monospace;
               font-size: 11px;
               border: 1px solid #3a3a3a;
           }
       """)

        log_dock.setWidget(self.log_widget)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, log_dock)

        self.log("AutoViz Analytics Dashboard initialized")

    def apply_theme(self) -> None:
        """Apply the current theme to the application."""
        if self.dark_mode:
            self.setStyleSheet("""
               QMainWindow {
                   background-color: #1a1a1a;
               }
               QWidget {
                   background-color: #1e1e1e;
                   color: white;
                   font-family: 'Segoe UI', Arial, sans-serif;
               }
               QDockWidget {
                   color: white;
                   titlebar-close-icon: none;
                   titlebar-normal-icon: none;
               }
               QDockWidget::title {
                   background-color: #2a2a2a;
                   padding: 8px;
                   border-bottom: 2px solid #00ff88;
                   color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,
                       stop:0 #ff8800, stop:1 #00ffff);
                   border: 2px solid black;
                   border-radius: 4px;
                   font-family: 'Consolas', monospace;
                   font-size: 14px;
               }
               QSplitter::handle {
                   background-color: #3a3a3a;
               }
               QLabel {
                   color: white;
               }
           """)
        else:
            self.setStyleSheet("")

    def log(self, message: str) -> None:
        """Add a message to the activity log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_widget.append(f"[{timestamp}] {message}")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop events for file loading."""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith(('.csv', '.json')):
                self.load_file(file_path)
                break

    @pyqtSlot()
    def open_file(self) -> None:
        """Open a file dialog to select a data file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Data File",
            "",
            "Data Files (*.csv *.json);;All Files (*)"
        )
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path: str) -> None:
        """Load a data file for processing."""
        self.log(f"Loading file: {file_path}")
        self.current_file = file_path
        self.file_label.setText(f"File: {os.path.basename(file_path)}")

        # Try robust CSV and JSON loading here for instant feedback in log
        self.dataframe = None
        if file_path.endswith('.csv'):
            try:
                df = pd.read_csv(file_path, skip_blank_lines=True, engine='python')
                df.dropna(how='all', inplace=True)  # Remove any fully empty rows
                self.dataframe = df
                self.log(f"Data loaded: {len(df)} rows, {len(df.columns)} columns")
            except Exception as e:
                self.log(f"Failed to load CSV: {e}")
                self.dataframe = None
        elif file_path.endswith('.json'):
            try:
                self.dataframe = pd.read_json(file_path)
            except Exception as e:
                self.log(f"Failed to load JSON: {e}")
                self.dataframe = None

        # Always use the background thread for processing & UI update
        self.data_processor.set_file(file_path)
        self.data_processor.start()

    @pyqtSlot(pd.DataFrame, str)
    def on_data_loaded(self, df: pd.DataFrame, file_path: str) -> None:
        """Handle successfully loaded data."""
        self.current_df = df
        self.log(f"Data loaded successfully: {df.shape[0]} rows, {df.shape[1]} columns")

        # Update data table
        self.update_data_table()

        # Update column dropdowns
        self.update_column_dropdowns()

        # Calculate metrics
        self.calculate_metrics()

        # Update statistics
        self.update_statistics()

    @pyqtSlot(str)
    def on_error(self, error_msg: str) -> None:
        """Handle data loading errors."""
        self.log(f"Error: {error_msg}")

    @pyqtSlot(int)
    def update_progress(self, value: int) -> None:
        """Update the progress bar."""
        self.progress_bar.setValue(value)

    def update_data_table(self) -> None:
        """Update the data table with current dataframe."""
        if self.current_df is None:
            return

        self.data_table.clear()
        self.data_table.setRowCount(min(100, len(self.current_df)))
        self.data_table.setColumnCount(len(self.current_df.columns))
        self.data_table.setHorizontalHeaderLabels(self.current_df.columns.tolist())

        for i in range(min(100, len(self.current_df))):
            for j, col in enumerate(self.current_df.columns):
                item = QTableWidgetItem(str(self.current_df.iloc[i, j]))
                self.data_table.setItem(i, j, item)

    def update_column_dropdowns(self) -> None:
        """Update the column selection dropdowns."""
        if self.current_df is None:
            return

        columns = self.current_df.columns.tolist()

        self.x_column.clear()
        self.x_column.addItems(columns)

        self.y_column.clear()
        numeric_columns = self.current_df.select_dtypes(include=[np.number]).columns.tolist()
        self.y_column.addItems(numeric_columns)

    def calculate_metrics(self) -> None:
        """Calculate and display key metrics."""
        if self.current_df is None:
            return

        metrics_lines = []

        # Basic info
        metrics_lines.append(f"Total Rows: {len(self.current_df):,}")
        metrics_lines.append(f"Total Columns: {len(self.current_df.columns)}")
        metrics_lines.append(f"Memory Usage: {self.current_df.memory_usage(deep=True).sum() / 1024 ** 2:.2f} MB")
        metrics_lines.append("")

        # Numeric columns stats
        numeric_cols = self.current_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            metrics_lines.append("Numeric Columns:")
            for col in numeric_cols[:5]:  # Show first 5
                mean_val = self.current_df[col].mean()
                std_val = self.current_df[col].std()
                metrics_lines.append(f"  {col}: μ={mean_val:.2f}, σ={std_val:.2f}")

        self.metrics_text.setText("\n".join(metrics_lines))

    def update_statistics(self) -> None:
        """Update the statistics view."""
        if self.current_df is None:
            return

        # Generate descriptive statistics
        desc_stats = self.current_df.describe(include='all')

        # Convert to formatted table
        stats_table = tabulate(
            desc_stats.reset_index(),
            headers='keys',
            tablefmt='fancy_grid',
            floatfmt='.2f'
        )

        self.stats_widget.setText(stats_table)

    @pyqtSlot()
    def generate_plot(self) -> None:
        """Generate the selected plot type."""
        if self.current_df is None:
            self.log("No data loaded")
            return

        chart_type = self.chart_type.currentText()
        x_col = self.x_column.currentText()
        y_col = self.y_column.currentText()

        if chart_type == "Bar Chart" and x_col and y_col:
            try:
                # Create fresh DataFrame to avoid index name collisions
                plot_data = self.current_df[[x_col, y_col]].copy()
                # Group and compute mean with as_index=False to directly get DataFrame
                plot_data = plot_data.groupby(x_col, as_index=False)[y_col].mean()
                self.plot_canvas.create_bar_chart(plot_data, x_col, y_col)
            except Exception as e:
                self.log(f"Bar Chart error: {e}")
                return
            self.log(f"Generated {chart_type}")
            return
        try:
            if chart_type == "Pie Chart" and x_col:
                self.plot_canvas.create_pie_chart(self.current_df, x_col)

            elif chart_type == "Line Chart" and x_col and y_col:
                # Sort by x column for line chart
                plot_data = self.current_df.sort_values(x_col)
                self.plot_canvas.create_line_chart(plot_data, x_col, y_col)

            self.log(f"Generated {chart_type}")
        except Exception as e:
            self.log(f"Plot generation error: {str(e)}")

    def quick_plot(self, chart_type: str) -> None:
        """Quick plot generation from toolbar buttons."""
        if self.current_df is None:
            self.log("No data loaded for quick plot")
            return

        # Set the chart type and generate
        self.chart_type.setCurrentText(chart_type)
        self.generate_plot()

    @pyqtSlot()
    def run_regression(self) -> None:
        """Run OLS regression analysis."""
        if self.current_df is None:
            self.log("No data loaded for regression")
            return

        try:
            # Get numeric columns
            numeric_cols = self.current_df.select_dtypes(include=[np.number]).columns.tolist()

            if len(numeric_cols) < 2:
                self.regression_text.setText("Need at least 2 numeric columns for regression")
                return

            # Use first numeric column as dependent variable, others as independent
            y = self.current_df[numeric_cols[0]]
            X = self.current_df[numeric_cols[1:]]

            # Add constant
            X = sm.add_constant(X)

            # Fit model
            model = sm.OLS(y, X).fit()

            # Display results
            summary_text = str(model.summary())
            self.regression_text.setText(summary_text)

            self.log(f"Regression completed: R² = {model.rsquared:.4f}")

        except Exception as e:
            self.regression_text.setText(f"Regression error: {str(e)}")
            self.log(f"Regression error: {str(e)}")

    @pyqtSlot()
    def export_plot(self) -> None:
        """Export the current plot to file."""
        if not hasattr(self.plot_canvas, 'figure'):
            self.log("No plot to export")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Plot",
            "",
            "PNG Files (*.png);;PDF Files (*.pdf);;All Files (*)"
        )

        if file_path:
            try:
                self.plot_canvas.figure.savefig(
                    file_path,
                    dpi=300,
                    bbox_inches='tight',
                    facecolor='#1e1e1e',
                    edgecolor='none'
                )
                self.log(f"Plot exported to: {file_path}")
            except Exception as e:
                self.log(f"Export error: {str(e)}")

    @pyqtSlot()
    def setup_watch_folder(self) -> None:
        """Setup folder watching for automatic file import."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Watch"
        )

        if folder_path:
            self.watch_folder = folder_path

            # Setup file system watcher
            if self.file_watcher:
                self.file_watcher.deleteLater()

            self.file_watcher = QFileSystemWatcher([folder_path])
            self.file_watcher.directoryChanged.connect(self.on_folder_changed)

            # Setup timer for periodic checks
            if self.watch_timer:
                self.watch_timer.stop()

            self.watch_timer = QTimer()
            self.watch_timer.timeout.connect(self.check_new_files)
            self.watch_timer.start(10000)  # Check every 10 seconds

            self.log(f"Watching folder: {folder_path}")

            # Initial scan
            self.check_new_files()

    @pyqtSlot(str)
    def on_folder_changed(self, path: str) -> None:
        """Handle folder change events."""
        self.log(f"Folder changed: {path}")
        self.check_new_files()

    def check_new_files(self) -> None:
        """Check for new files in the watched folder."""
        if not self.watch_folder:
            return

        try:
            # Get all CSV and JSON files in the folder
            csv_files = list(Path(self.watch_folder).glob("*.csv"))
            json_files = list(Path(self.watch_folder).glob("*.json"))
            all_files = csv_files + json_files

            for file_path in all_files:
                # Check if file hasn't been processed yet
                if str(file_path) not in self.processed_files:
                    # Add to processed files set
                    self.processed_files.add(str(file_path))
                    self.log(f"New file detected: {file_path.name}")
                    # Load the new file
                    self.load_file(str(file_path))
                    break  # Process one file at a time

        except Exception as e:
            self.log(f"Watch folder error: {str(e)}")

    @pyqtSlot()
    def refresh_data(self) -> None:
        """Refresh the current data view."""
        if self.current_file:
            self.load_file(self.current_file)

    @pyqtSlot()
    def clear_data(self) -> None:
        """Clear all loaded data."""
        self.current_df = None
        self.current_file = None
        self.data_table.clear()
        self.plot_canvas.clear_plot()
        self.metrics_text.clear()
        self.stats_widget.clear()
        self.regression_text.clear()
        self.file_label.setText("No file loaded")
        self.x_column.clear()
        self.y_column.clear()
        self.log("Data cleared")

    @pyqtSlot()
    def toggle_theme(self) -> None:
        """Toggle between dark and light themes."""
        self.dark_mode = not self.dark_mode
        self.apply_theme()

        # Update plot style
        if self.dark_mode:
            plt.style.use('dark_background')
            self.plot_canvas.figure.patch.set_facecolor('#1e1e1e')
        else:
            plt.style.use('default')
            self.plot_canvas.figure.patch.set_facecolor('white')

        self.plot_canvas.draw()
        self.log(f"Theme changed to: {'Dark' if self.dark_mode else 'Light'}")

    def closeEvent(self, event) -> None:
        """Handle application close event."""
        # Stop the watch timer if running
        if self.watch_timer and self.watch_timer.isActive():
            self.watch_timer.stop()

        # Clean up file watcher
        if self.file_watcher:
            self.file_watcher.deleteLater()

        # Ensure data processor thread is properly terminated
        if self.data_processor.isRunning():
            self.data_processor.quit()
            self.data_processor.wait()

        event.accept()




def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    # Create and show main window
    window = AutoVizApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()