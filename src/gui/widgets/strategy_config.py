#!/usr/bin/env python3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox,
    QGroupBox, QFormLayout, QTabWidget, QPushButton,
    QCheckBox, QScrollArea, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt
import json

class StrategyConfigWidget(QWidget):
    """
    Widget for configuring trading strategies with detailed parameters
    and visualization of the strategy logic.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize UI
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface components"""
        # Main layout
        self.layout = QVBoxLayout(self)
        
        # Strategy configuration tabs
        self.tabs = QTabWidget()
        
        # Pure market making tab
        self.market_making_tab = QWidget()
        self.setup_market_making_tab()
        self.tabs.addTab(self.market_making_tab, "Pure Market Making")
        
        # Cross exchange market making tab
        self.cross_exchange_tab = QWidget()
        self.setup_cross_exchange_tab()
        self.tabs.addTab(self.cross_exchange_tab, "Cross Exchange Market Making")
        
        # Arbitrage tab
        self.arbitrage_tab = QWidget()
        self.setup_arbitrage_tab()
        self.tabs.addTab(self.arbitrage_tab, "Arbitrage")
        
        # TWAP tab
        self.twap_tab = QWidget()
        self.setup_twap_tab()
        self.tabs.addTab(self.twap_tab, "TWAP")
        
        # Avellaneda & Stoikov tab
        self.avellaneda_tab = QWidget()
        self.setup_avellaneda_tab()
        self.tabs.addTab(self.avellaneda_tab, "Avellaneda & Stoikov")
        
        # Action buttons
        self.button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save Configuration")
        self.save_button.clicked.connect(self.save_configuration)
        
        self.load_button = QPushButton("Load Configuration")
        self.load_button.clicked.connect(self.load_configuration)
        
        self.validate_button = QPushButton("Validate Strategy")
        self.validate_button.clicked.connect(self.validate_strategy)
        
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.load_button)
        self.button_layout.addWidget(self.validate_button)
        
        # Add components to main layout
        self.layout.addWidget(self.tabs)
        self.layout.addLayout(self.button_layout)
        
    def setup_market_making_tab(self):
        """Setup the pure market making strategy configuration tab"""
        # Main layout
        layout = QVBoxLayout(self.market_making_tab)
        
        # Create scroll area for many parameters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Scroll content widget
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Market parameters group
        market_group = QGroupBox("Market Parameters")
        market_form = QFormLayout()
        
        # Exchange
        self.mm_exchange = QComboBox()
        self.mm_exchange.addItems(["Binance", "Binance US", "Coinbase Pro", "Kraken", "KuCoin"])
        market_form.addRow("Exchange:", self.mm_exchange)
        
        # Market (trading pair)
        self.mm_market = QComboBox()
        self.mm_market.addItems(["BTC-USDT", "ETH-USDT", "BNB-USDT", "SOL-USDT", "ADA-USDT"])
        market_form.addRow("Market:", self.mm_market)
        
        # Bid/Ask spread
        self.mm_bid_spread = QDoubleSpinBox()
        self.mm_bid_spread.setDecimals(2)
        self.mm_bid_spread.setMinimum(0.01)
        self.mm_bid_spread.setMaximum(5.00)
        self.mm_bid_spread.setValue(0.50)
        self.mm_bid_spread.setSingleStep(0.05)
        self.mm_bid_spread.setSuffix("%")
        market_form.addRow("Bid Spread:", self.mm_bid_spread)
        
        self.mm_ask_spread = QDoubleSpinBox()
        self.mm_ask_spread.setDecimals(2)
        self.mm_ask_spread.setMinimum(0.01)
        self.mm_ask_spread.setMaximum(5.00)
        self.mm_ask_spread.setValue(0.50)
        self.mm_ask_spread.setSingleStep(0.05)
        self.mm_ask_spread.setSuffix("%")
        market_form.addRow("Ask Spread:", self.mm_ask_spread)
        
        # Order refresh time
        self.mm_order_refresh_time = QDoubleSpinBox()
        self.mm_order_refresh_time.setDecimals(1)
        self.mm_order_refresh_time.setMinimum(5.0)
        self.mm_order_refresh_time.setMaximum(300.0)
        self.mm_order_refresh_time.setValue(30.0)
        self.mm_order_refresh_time.setSingleStep(5.0)
        self.mm_order_refresh_time.setSuffix(" sec")
        market_form.addRow("Order Refresh Time:", self.mm_order_refresh_time)
        
        # Apply group layout
        market_group.setLayout(market_form)
        
        # Order parameters group
        order_group = QGroupBox("Order Parameters")
        order_form = QFormLayout()
        
        # Order amount
        self.mm_order_amount = QDoubleSpinBox()
        self.mm_order_amount.setDecimals(6)
        self.mm_order_amount.setMinimum(0.000001)
        self.mm_order_amount.setMaximum(10.0)
        self.mm_order_amount.setValue(0.001)
        self.mm_order_amount.setSingleStep(0.001)
        order_form.addRow("Order Amount:", self.mm_order_amount)
        
        # Order levels
        self.mm_order_levels = QSpinBox()
        self.mm_order_levels.setMinimum(1)
        self.mm_order_levels.setMaximum(5)
        self.mm_order_levels.setValue(1)
        order_form.addRow("Number of Order Levels:", self.mm_order_levels)
        
        # Order level spread
        self.mm_order_level_spread = QDoubleSpinBox()
        self.mm_order_level_spread.setDecimals(2)
        self.mm_order_level_spread.setMinimum(0.01)
        self.mm_order_level_spread.setMaximum(5.00)
        self.mm_order_level_spread.setValue(1.00)
        self.mm_order_level_spread.setSingleStep(0.10)
        self.mm_order_level_spread.setSuffix("%")
        order_form.addRow("Order Level Spread:", self.mm_order_level_spread)
        
        # Order level amount
        self.mm_order_level_amount = QDoubleSpinBox()
        self.mm_order_level_amount.setDecimals(2)
        self.mm_order_level_amount.setMinimum(0.01)
        self.mm_order_level_amount.setMaximum(5.00)
        self.mm_order_level_amount.setValue(1.00)
        self.mm_order_level_amount.setSingleStep(0.10)
        self.mm_order_level_amount.setSuffix("x")
        order_form.addRow("Order Level Amount:", self.mm_order_level_amount)
        
        # Apply group layout
        order_group.setLayout(order_form)
        
        # Advanced parameters group
        advanced_group = QGroupBox("Advanced Parameters")
        advanced_form = QFormLayout()
        
        # Price source
        self.mm_price_source = QComboBox()
        self.mm_price_source.addItems(["current_market", "external_market", "custom_api"])
        advanced_form.addRow("Price Source:", self.mm_price_source)
        
        # Price type
        self.mm_price_type = QComboBox()
        self.mm_price_type.addItems(["mid_price", "last_price", "best_bid", "best_ask"])
        advanced_form.addRow("Price Type:", self.mm_price_type)
        
        # Inventory skew
        self.mm_inventory_skew_enabled = QCheckBox("Enable")
        self.mm_inventory_skew_enabled.setChecked(False)
        advanced_form.addRow("Inventory Skew:", self.mm_inventory_skew_enabled)
        
        # Target base ratio
        self.mm_target_base_ratio = QDoubleSpinBox()
        self.mm_target_base_ratio.setDecimals(2)
        self.mm_target_base_ratio.setMinimum(0.0)
        self.mm_target_base_ratio.setMaximum(100.0)
        self.mm_target_base_ratio.setValue(50.0)
        self.mm_target_base_ratio.setSingleStep(5.0)
        self.mm_target_base_ratio.setSuffix("%")
        advanced_form.addRow("Target Base Ratio:", self.mm_target_base_ratio)
        
        # Apply group layout
        advanced_group.setLayout(advanced_form)
        
        # Risk parameters group
        risk_group = QGroupBox("Risk Parameters")
        risk_form = QFormLayout()
        
        # Max order age
        self.mm_max_order_age = QDoubleSpinBox()
        self.mm_max_order_age.setDecimals(1)
        self.mm_max_order_age.setMinimum(10.0)
        self.mm_max_order_age.setMaximum(3600.0)
        self.mm_max_order_age.setValue(1800.0)
        self.mm_max_order_age.setSingleStep(60.0)
        self.mm_max_order_age.setSuffix(" sec")
        risk_form.addRow("Max Order Age:", self.mm_max_order_age)
        
        # Min order spread
        self.mm_min_spread = QDoubleSpinBox()
        self.mm_min_spread.setDecimals(2)
        self.mm_min_spread.setMinimum(-100.0)
        self.mm_min_spread.setMaximum(100.0)
        self.mm_min_spread.setValue(-0.5)
        self.mm_min_spread.setSingleStep(0.1)
        self.mm_min_spread.setSuffix("%")
        risk_form.addRow("Minimum Spread:", self.mm_min_spread)
        
        # Max spread
        self.mm_max_spread = QDoubleSpinBox()
        self.mm_max_spread.setDecimals(2)
        self.mm_max_spread.setMinimum(0.0)
        self.mm_max_spread.setMaximum(100.0)
        self.mm_max_spread.setValue(5.0)
        self.mm_max_spread.setSingleStep(0.1)
        self.mm_max_spread.setSuffix("%")
        risk_form.addRow("Maximum Spread:", self.mm_max_spread)
        
        # Apply group layout
        risk_group.setLayout(risk_form)
        
        # Add groups to the content layout
        content_layout.addWidget(market_group)
        content_layout.addWidget(order_group)
        content_layout.addWidget(advanced_group)
        content_layout.addWidget(risk_group)
        content_layout.addStretch(1)
        
        # Set the scroll area widget
        scroll.setWidget(content)
        
        # Add scroll area to the tab layout
        layout.addWidget(scroll)
        
    def setup_cross_exchange_tab(self):
        """Setup the cross exchange market making strategy configuration tab"""
        # Main layout
        layout = QVBoxLayout(self.cross_exchange_tab)
        layout.addWidget(QLabel("Cross Exchange Market Making Configuration"))
        
        # Placeholder for now (would be similar to market making but with two exchanges)
        layout.addWidget(QLabel("This strategy creates orders on a secondary exchange (maker) based on the order book of a primary exchange (taker)."))
        
    def setup_arbitrage_tab(self):
        """Setup the arbitrage strategy configuration tab"""
        # Main layout
        layout = QVBoxLayout(self.arbitrage_tab)
        layout.addWidget(QLabel("Arbitrage Strategy Configuration"))
        
        # Placeholder for now
        layout.addWidget(QLabel("This strategy looks for price discrepancies between exchanges and executes trades to capture the difference."))
        
    def setup_twap_tab(self):
        """Setup the TWAP strategy configuration tab"""
        # Main layout
        layout = QVBoxLayout(self.twap_tab)
        layout.addWidget(QLabel("Time-Weighted Average Price (TWAP) Strategy Configuration"))
        
        # Placeholder for now
        layout.addWidget(QLabel("This strategy executes a large order over time to minimize market impact."))
        
    def setup_avellaneda_tab(self):
        """Setup the Avellaneda & Stoikov strategy configuration tab"""
        # Main layout
        layout = QVBoxLayout(self.avellaneda_tab)
        layout.addWidget(QLabel("Avellaneda & Stoikov Strategy Configuration"))
        
        # Placeholder for now
        layout.addWidget(QLabel("This is an advanced market making strategy based on a mathematical model that accounts for inventory risk."))
        
    def save_configuration(self):
        """Save the current strategy configuration"""
        # In a real implementation, we would serialize the configuration and save to a file
        print("Configuration saved")
        
    def load_configuration(self):
        """Load a saved strategy configuration"""
        # In a real implementation, we would load a configuration file and update the UI
        print("Configuration loaded")
        
    def validate_strategy(self):
        """Validate the current strategy configuration"""
        # In a real implementation, we would check if the strategy parameters are valid
        print("Strategy validated")
