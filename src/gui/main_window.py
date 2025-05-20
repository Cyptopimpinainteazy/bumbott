#!/usr/bin/env python3
import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QPushButton, QComboBox, 
    QStatusBar, QToolBar, QDockWidget, QTreeView,
    QSplitter, QMessageBox, QGroupBox, QLineEdit
)
from PyQt6.QtCore import Qt, QSize, pyqtSlot, QThread, QObject, pyqtSignal
from PyQt6.QtGui import QIcon, QAction, QFont

# Import custom widgets
from gui.widgets.trading_chart import TradingChartWidget
from gui.widgets.order_book import OrderBookWidget
from gui.widgets.strategy_config import StrategyConfigWidget
from gui.widgets.exchange_connection import ExchangeConnectionWidget
from gui.widgets.trade_history import TradeHistoryWidget
from gui.widgets.performance_metrics import PerformanceMetricsWidget
from gui.widgets.bot_controls import BotControlsWidget
from gui.widgets.portfolio_view import PortfolioViewWidget
from gui.widgets.market_data import MarketDataWidget
from gui.widgets.testing_tab import TestingTabWidget
from gui.widgets.training_tab import TrainingTabWidget


class BotWorker(QObject):
    initialized = pyqtSignal()
    error = pyqtSignal(str)

    def initialize_predictor(self):
        # Initialize neural predictor here
        # For demonstration purposes, assume initialization is successful
        self.initialized.emit()


class MainWindow(QMainWindow):
    """
    Main window for the BumBot trading application.
    Provides access to all features through a modern, tabbed interface.
    """
    
    def __init__(self):
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("BumBot - Advanced Crypto Trading Platform")
        self.setMinimumSize(1200, 800)
        
        # Setup UI components
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_status_bar()
        self.setup_signals()
        
        # Apply stylesheet
        self.apply_stylesheet()
        
    def setup_ui(self):
        """Initialize the main UI components"""
        
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Create control panel for left side
        self.control_panel = QWidget()
        self.control_layout = QVBoxLayout(self.control_panel)
        self.control_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add exchange connection widget
        self.exchange_connection = ExchangeConnectionWidget()
        self.control_layout.addWidget(self.exchange_connection)
        
        # Add bot controls
        self.bot_controls = BotControlsWidget()
        self.control_layout.addWidget(self.bot_controls)
        
        # Add portfolio view
        self.portfolio_view = PortfolioViewWidget()
        self.control_layout.addWidget(self.portfolio_view)
        
        # Add vertical spacer
        self.control_layout.addStretch(1)
        
        # Create main content tabs for right side
        self.main_tabs = QTabWidget()
        
        # Trading tab
        self.trading_tab = QWidget()
        self.trading_layout = QVBoxLayout(self.trading_tab)
        
        # Create trading chart and order book section
        self.trading_chart = TradingChartWidget()
        self.order_book = OrderBookWidget()
        
        # Create trading layout
        trading_chart_layout = QHBoxLayout()
        trading_chart_layout.addWidget(self.trading_chart, 7)
        trading_chart_layout.addWidget(self.order_book, 3)
        
        self.trading_layout.addLayout(trading_chart_layout)
        
        # Add trade history
        self.trade_history = TradeHistoryWidget()
        self.trading_layout.addWidget(self.trade_history, 1)
        
        # Add trading tab to main tabs
        self.main_tabs.addTab(self.trading_tab, "Trading")
        
        # Strategy tab
        self.strategy_tab = QWidget()
        self.strategy_layout = QVBoxLayout(self.strategy_tab)
        
        # Add strategy configuration widget
        self.strategy_config = StrategyConfigWidget()
        self.strategy_layout.addWidget(self.strategy_config)
        
        # Add strategy tab to main tabs
        self.main_tabs.addTab(self.strategy_tab, "Strategy")
        
        # Create testing tab
        self.testing_tab = QWidget()
        self.testing_layout = QVBoxLayout(self.testing_tab)
        
        # Add neural predictor diagnostics widget
        self.testing_panel = TestingTabWidget()
        self.testing_layout.addWidget(self.testing_panel)
        
        # Add testing tab to main tabs
        self.main_tabs.addTab(self.testing_tab, "AI Testing")
        
        # Create training tab
        self.training_tab = QWidget()
        self.training_layout = QVBoxLayout(self.training_tab)
        
        # Add neural network training controls
        self.training_panel = TrainingTabWidget()
        self.training_layout.addWidget(self.training_panel)
        
        # Add training tab to main tabs
        self.main_tabs.addTab(self.training_tab, "AI Training")
        
        # Analytics tab
        self.analytics_tab = QWidget()
        self.analytics_layout = QVBoxLayout(self.analytics_tab)
        
        # Add performance metrics widget
        self.performance_metrics = PerformanceMetricsWidget()
        self.analytics_layout.addWidget(self.performance_metrics)
        
        # Add analytics tab to main tabs
        self.main_tabs.addTab(self.analytics_tab, "Analytics")
        
        # Market Data tab
        self.market_data_tab = QWidget()
        self.market_data_layout = QVBoxLayout(self.market_data_tab)
        
        # Add market data widget
        self.market_data = MarketDataWidget()
        self.market_data_layout.addWidget(self.market_data)
        
        # Add market data tab to main tabs
        self.main_tabs.addTab(self.market_data_tab, "Market Data")
        
        # Add components to splitter
        self.main_splitter.addWidget(self.control_panel)
        self.main_splitter.addWidget(self.main_tabs)
        
        # Set initial splitter sizes (30% left, 70% right)
        self.main_splitter.setSizes([300, 700])
        
        # Add splitter to main layout
        self.main_layout.addWidget(self.main_splitter)
        
    def setup_menu_bar(self):
        """Setup the main menu bar"""
        
        # Create menu bar
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        # Connect to Exchange action
        connect_action = QAction("Connect to Exchange", self)
        connect_action.triggered.connect(self.on_connect_exchange)
        file_menu.addAction(connect_action)
        
        # Import/Export configuration
        import_config_action = QAction("Import Configuration", self)
        import_config_action.triggered.connect(self.on_import_config)
        file_menu.addAction(import_config_action)
        
        export_config_action = QAction("Export Configuration", self)
        export_config_action.triggered.connect(self.on_export_config)
        file_menu.addAction(export_config_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Trading menu
        trading_menu = menu_bar.addMenu("&Trading")
        
        start_bot_action = QAction("Start Bot", self)
        start_bot_action.triggered.connect(self.on_start_bot)
        trading_menu.addAction(start_bot_action)
        
        stop_bot_action = QAction("Stop Bot", self)
        stop_bot_action.triggered.connect(self.on_stop_bot)
        trading_menu.addAction(stop_bot_action)
        
        trading_menu.addSeparator()
        
        test_strategy_action = QAction("Backtest Strategy", self)
        test_strategy_action.triggered.connect(self.on_test_strategy)
        trading_menu.addAction(test_strategy_action)
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        
        toggle_control_panel_action = QAction("Toggle Control Panel", self)
        toggle_control_panel_action.triggered.connect(self.on_toggle_control_panel)
        view_menu.addAction(toggle_control_panel_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        about_action = QAction("About BumBot", self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)
        
        docs_action = QAction("Documentation", self)
        docs_action.triggered.connect(self.on_documentation)
        help_menu.addAction(docs_action)
        
    def setup_status_bar(self):
        """Setup the status bar"""
        
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # Add status message
        self.status_message = QLabel("Ready")
        status_bar.addWidget(self.status_message, 1)
        
        # Add connection status
        self.connection_status = QLabel("Not Connected")
        self.connection_status.setStyleSheet("color: red;")
        status_bar.addPermanentWidget(self.connection_status)
        
        # Add bot status
        self.bot_status = QLabel("Bot: Inactive")
        self.bot_status.setStyleSheet("color: gray;")
        status_bar.addPermanentWidget(self.bot_status)
        
    def setup_signals(self):
        """Connect signals between UI components"""
        
        # Connect exchange connection signals
        self.exchange_connection.connection_changed.connect(self.on_connection_changed)
        
        # Connect bot control signals
        self.bot_controls.bot_started.connect(self.on_bot_started)
        self.bot_controls.bot_stopped.connect(self.on_bot_stopped)
        
    def apply_stylesheet(self):
        """Apply custom stylesheet to the application"""
        
        # Set application font
        app_font = QFont("Segoe UI", 9)
        # Use the current application instance instead of QApplication directly
        self.font = app_font
        
        # Add a modern theme to the application
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #2D2D30;
                color: #E0E0E0;
            }
            
            QTabWidget::pane {
                border: 1px solid #3F3F46;
                background-color: #2D2D30;
            }
            
            QTabBar::tab {
                background-color: #252526;
                color: #E0E0E0;
                padding: 8px 16px;
                border: 1px solid #3F3F46;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: #007ACC;
                color: white;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #3E3E40;
            }
            
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            
            QPushButton:hover {
                background-color: #1C97EA;
            }
            
            QPushButton:pressed {
                background-color: #0062A3;
            }
            
            QPushButton:disabled {
                background-color: #4D4D4D;
                color: #9D9D9D;
            }
            
            QComboBox {
                background-color: #3E3E42;
                color: #E0E0E0;
                border: 1px solid #3F3F46;
                padding: 4px;
                border-radius: 4px;
            }
            
            QLineEdit {
                background-color: #3E3E42;
                color: #E0E0E0;
                border: 1px solid #3F3F46;
                padding: 4px;
                border-radius: 4px;
            }
            
            QGroupBox {
                border: 1px solid #3F3F46;
                border-radius: 4px;
                margin-top: 8px;
                font-weight: bold;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
            }
            
            QSplitter::handle {
                background-color: #3F3F46;
            }
            
            QStatusBar {
                background-color: #007ACC;
                color: white;
            }
            
            QMenuBar {
                background-color: #2D2D30;
                color: #E0E0E0;
            }
            
            QMenuBar::item:selected {
                background-color: #3E3E40;
            }
            
            QMenu {
                background-color: #2D2D30;
                color: #E0E0E0;
                border: 1px solid #3F3F46;
            }
            
            QMenu::item:selected {
                background-color: #3E3E40;
            }
        """)
    
    # Slot methods
    
    @pyqtSlot()
    def on_connect_exchange(self):
        """Handle connect to exchange action"""
        self.exchange_connection.connect_exchange()
    
    @pyqtSlot()
    def on_import_config(self):
        """Handle import configuration action"""
        QMessageBox.information(self, "Import Configuration", 
                               "Configuration import feature will be implemented.")
    
    @pyqtSlot()
    def on_export_config(self):
        """Handle export configuration action"""
        QMessageBox.information(self, "Export Configuration", 
                               "Configuration export feature will be implemented.")
    
    @pyqtSlot()
    def on_start_bot(self):
        """Handle start bot action"""
        # Create and start worker thread
        self.bot_thread = QThread()
        self.bot_worker = BotWorker()
        self.bot_worker.moveToThread(self.bot_thread)
        
        # Connect signals
        self.bot_thread.started.connect(self.bot_worker.initialize_predictor)
        self.bot_worker.initialized.connect(self.bot_controls.on_bot_started)
        self.bot_worker.error.connect(self.handle_bot_error)
        self.bot_thread.finished.connect(self.bot_thread.deleteLater)
        
        self.bot_thread.start()
        
        # Disable start button during initialization
        self.bot_controls.start_btn.setEnabled(False)
    
    @pyqtSlot()
    def on_stop_bot(self):
        """Handle stop bot action"""
        self.bot_controls.stop_bot()
    
    @pyqtSlot()
    def on_test_strategy(self):
        """Handle test strategy action"""
        QMessageBox.information(self, "Backtest Strategy", 
                               "Strategy backtesting feature will be implemented.")
    
    @pyqtSlot()
    def on_toggle_control_panel(self):
        """Handle toggle control panel action"""
        if self.control_panel.isVisible():
            self.control_panel.hide()
        else:
            self.control_panel.show()
    
    @pyqtSlot()
    def on_about(self):
        """Handle about action"""
        QMessageBox.about(self, "About BumBot", 
                         """<h2>BumBot</h2>
                         <p>Advanced Cryptocurrency Trading Platform</p>
                         <p>Based on HummingBot with enhanced GUI and visualization features.</p>
                         <p>Version 1.0.0</p>""")
    
    @pyqtSlot()
    def on_documentation(self):
        """Handle documentation action"""
        QMessageBox.information(self, "Documentation", 
                               "Documentation will be available soon.")
    
    @pyqtSlot(bool)
    def on_connection_changed(self, connected):
        """Handle connection status changes"""
        if connected:
            self.connection_status.setText("Connected")
            self.connection_status.setStyleSheet("color: green;")
            self.status_message.setText("Connected to exchange")
        else:
            self.connection_status.setText("Not Connected")
            self.connection_status.setStyleSheet("color: red;")
            self.status_message.setText("Disconnected from exchange")
    
    @pyqtSlot()
    def on_bot_started(self):
        """Handle bot started event"""
        self.bot_status.setText("Bot: Active")
        self.bot_status.setStyleSheet("color: green;")
        self.status_message.setText("Trading bot started")
    
    @pyqtSlot()
    def on_bot_stopped(self):
        """Handle bot stopped event"""
        self.bot_status.setText("Bot: Inactive")
        self.bot_status.setStyleSheet("color: gray;")
        self.status_message.setText("Trading bot stopped")
    
    @pyqtSlot(str)
    def handle_bot_error(self, error_message):
        """Handle bot error"""
        QMessageBox.critical(self, "Bot Error", error_message)
