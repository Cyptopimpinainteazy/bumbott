#!/usr/bin/env python3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGroupBox, QSlider, QSpinBox,
    QFormLayout, QComboBox, QCheckBox, QMessageBox,
    QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon

class BotControlsWidget(QWidget):
    """
    Widget for controlling the trading bot.
    Provides controls to start/stop the bot and adjust trading parameters.
    """
    # Signals for bot state changes
    bot_started = pyqtSignal()
    bot_stopped = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Bot state
        self.is_running = False
        
        # Initialize UI
        self.init_ui()
        
        # Don't use timer for now to prevent crashes
        
    def init_ui(self):
        """Initialize the user interface components"""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Bot controls group box
        self.controls_group = QGroupBox("Bot Controls")
        self.controls_layout = QVBoxLayout()
        
        # Strategy selection form
        self.form_layout = QFormLayout()
        
        # Strategy selector
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "Pure Market Making", "Cross Exchange Market Making", 
            "TWAP", "Arbitrage", "Avellaneda & Stoikov", "Spot Perpetual Arbitrage"
        ])
        self.form_layout.addRow("Strategy:", self.strategy_combo)
        
        # Trading pair selector
        self.pair_combo = QComboBox()
        self.pair_combo.addItems([
            "BTC/USDT", "ETH/USDT", "BNB/USDT", 
            "SOL/USDT", "XRP/USDT", "ADA/USDT"
        ])
        self.form_layout.addRow("Trading Pair:", self.pair_combo)
        
        # Order amount
        self.amount_spinbox = QDoubleSpinBox()
        self.amount_spinbox.setDecimals(6)
        self.amount_spinbox.setMinimum(0.000001)
        self.amount_spinbox.setMaximum(100.0)
        self.amount_spinbox.setValue(0.01)
        self.amount_spinbox.setSingleStep(0.001)
        self.form_layout.addRow("Order Amount:", self.amount_spinbox)
        
        # Order spread
        self.spread_spinbox = QDoubleSpinBox()
        self.spread_spinbox.setDecimals(2)
        self.spread_spinbox.setMinimum(0.01)
        self.spread_spinbox.setMaximum(5.0)
        self.spread_spinbox.setValue(1.0)
        self.spread_spinbox.setSingleStep(0.1)
        self.spread_spinbox.setSuffix("%")
        self.form_layout.addRow("Spread:", self.spread_spinbox)
        
        # Risk controls - stop loss
        self.stop_loss = QDoubleSpinBox()
        self.stop_loss.setDecimals(2)
        self.stop_loss.setMinimum(0.5)
        self.stop_loss.setMaximum(10.0)
        self.stop_loss.setValue(3.0)
        self.stop_loss.setSingleStep(0.5)
        self.stop_loss.setSuffix("%")
        self.form_layout.addRow("Stop Loss:", self.stop_loss)
        
        # Risk controls - take profit
        self.take_profit = QDoubleSpinBox()
        self.take_profit.setDecimals(2)
        self.take_profit.setMinimum(0.5)
        self.take_profit.setMaximum(20.0)
        self.take_profit.setValue(5.0)
        self.take_profit.setSingleStep(0.5)
        self.take_profit.setSuffix("%")
        self.form_layout.addRow("Take Profit:", self.take_profit)
        
        # Advanced settings checkbox
        self.advanced_settings = QCheckBox("Use AI-powered order sizing")
        self.advanced_settings.setToolTip("Enable AI-assisted dynamic order sizing based on market conditions")
        self.form_layout.addRow("", self.advanced_settings)
        
        # Status frame
        self.status_frame = QGroupBox("Bot Status")
        self.status_layout = QVBoxLayout(self.status_frame)
        
        # Status indicators
        self.status_indicator = QLabel("Status: Not Running")
        self.status_indicator.setStyleSheet("color: gray; font-weight: bold;")
        self.runtime_indicator = QLabel("Runtime: 00:00:00")
        self.trades_indicator = QLabel("Trades: 0")
        self.pnl_indicator = QLabel("P&L: 0.00 USDT (0.00%)")
        
        self.status_layout.addWidget(self.status_indicator)
        self.status_layout.addWidget(self.runtime_indicator)
        self.status_layout.addWidget(self.trades_indicator)
        self.status_layout.addWidget(self.pnl_indicator)
        
        # Buttons
        self.button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Bot")
        self.start_button.clicked.connect(self.start_bot)
        self.start_button.setMinimumHeight(40)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #26A69A;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2EB9A9;
            }
            QPushButton:pressed {
                background-color: #1F8A80;
            }
        """)
        
        self.stop_button = QPushButton("Stop Bot")
        self.stop_button.clicked.connect(self.stop_bot)
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #EF5350;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F47270;
            }
            QPushButton:pressed {
                background-color: #D43F3C;
            }
            QPushButton:disabled {
                background-color: #4D4D4D;
                color: #9D9D9D;
            }
        """)
        
        self.button_layout.addWidget(self.start_button)
        self.button_layout.addWidget(self.stop_button)
        
        # Assemble the layouts
        self.controls_layout.addLayout(self.form_layout)
        self.controls_group.setLayout(self.controls_layout)
        
        self.layout.addWidget(self.controls_group)
        self.layout.addWidget(self.status_frame)
        self.layout.addLayout(self.button_layout)
        self.layout.addStretch(1)
        
    def start_bot(self):
        """Start the trading bot with current settings"""
        # Get current settings
        strategy = self.strategy_combo.currentText()
        trading_pair = self.pair_combo.currentText()
        
        # In a real implementation, we would initialize the bot with these settings
        # and start the trading process
        
        # For demonstration, simulate successful start
        self.is_running = True
        
        # Update UI
        self.status_indicator.setText("Status: Running")
        self.status_indicator.setStyleSheet("color: green; font-weight: bold;")
        
        # Enable/disable buttons
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # Disable settings while running
        self.strategy_combo.setEnabled(False)
        self.pair_combo.setEnabled(False)
        self.amount_spinbox.setEnabled(False)
        self.spread_spinbox.setEnabled(False)
        self.stop_loss.setEnabled(False)
        self.take_profit.setEnabled(False)
        self.advanced_settings.setEnabled(False)
        
        # Update stats immediately instead of using timer
        self.update_stats()
        
        # Emit signal
        self.bot_started.emit()
        
        QMessageBox.information(
            self, 
            "Bot Started", 
            f"Trading bot started with {strategy} strategy on {trading_pair}."
        )
        
    def stop_bot(self):
        """Stop the trading bot"""
        # In a real implementation, we would stop the bot's operations
        
        # For demonstration, simulate successful stop
        self.is_running = False
        
        # Update UI
        self.status_indicator.setText("Status: Stopped")
        self.status_indicator.setStyleSheet("color: red; font-weight: bold;")
        
        # Enable/disable buttons
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        # Enable settings after stopping
        self.strategy_combo.setEnabled(True)
        self.pair_combo.setEnabled(True)
        self.amount_spinbox.setEnabled(True)
        self.spread_spinbox.setEnabled(True)
        self.stop_loss.setEnabled(True)
        self.take_profit.setEnabled(True)
        self.advanced_settings.setEnabled(True)
        
        # No timer to stop now
        
        # Emit signal
        self.bot_stopped.emit()
        
        QMessageBox.information(
            self, 
            "Bot Stopped", 
            "Trading bot has been stopped."
        )
    
    def update_stats(self):
        """Update the bot statistics display"""
        if not self.is_running:
            return
        
        # In a real implementation, we would fetch actual stats from the bot
        
        # For demonstration, update the runtime counter
        current_text = self.runtime_indicator.text()
        hours, minutes, seconds = map(int, current_text.split(": ")[1].split(":"))
        
        seconds += 1
        if seconds >= 60:
            seconds = 0
            minutes += 1
            if minutes >= 60:
                minutes = 0
                hours += 1
        
        runtime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.runtime_indicator.setText(f"Runtime: {runtime_str}")
        
        # Simulate random trade activity
        if seconds % 10 == 0:  # Simulate a new trade every 10 seconds
            current_trades = int(self.trades_indicator.text().split(": ")[1])
            self.trades_indicator.setText(f"Trades: {current_trades + 1}")
            
            # Simulate P&L changes
            import random
            pnl_amount = random.uniform(-2, 3)
            pnl_percent = random.uniform(-0.5, 0.7)
            
            pnl_color = "green" if pnl_amount >= 0 else "red"
            self.pnl_indicator.setText(f"P&L: {pnl_amount:.2f} USDT ({pnl_percent:.2f}%)")
            self.pnl_indicator.setStyleSheet(f"color: {pnl_color}; font-weight: bold;")
