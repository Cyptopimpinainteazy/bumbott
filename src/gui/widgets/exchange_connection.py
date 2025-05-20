#!/usr/bin/env python3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QLineEdit, QGroupBox,
    QFormLayout, QCheckBox, QMessageBox, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal

from gui.widgets.metamask_connect import MetaMaskConnectWidget

class ExchangeConnectionWidget(QWidget):
    """
    Widget for managing connections to cryptocurrency exchanges.
    Allows selection of exchange and API credentials input.
    """
    # Signal emitted when connection status changes
    connection_changed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Connection state
        self.is_connected = False
        
        # Initialize UI
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface components"""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Connection group box
        self.connection_group = QGroupBox("Exchange Connection")
        self.connection_layout = QVBoxLayout()
        
        # Exchange selection form
        self.form_layout = QFormLayout()
        
        # Exchange selector
        self.exchange_combo = QComboBox()
        self.exchange_combo.addItems([
            "Binance", "Binance US", "Coinbase Pro", "Kraken", 
            "KuCoin", "Huobi", "Gate.io", "OKX", "FTX"
        ])
        self.exchange_combo.currentTextChanged.connect(self.on_exchange_changed)
        self.form_layout.addRow("Exchange:", self.exchange_combo)
        
        # API Key input
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter API Key")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.form_layout.addRow("API Key:", self.api_key_input)
        
        # API Secret input
        self.api_secret_input = QLineEdit()
        self.api_secret_input.setPlaceholderText("Enter API Secret")
        self.api_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.form_layout.addRow("API Secret:", self.api_secret_input)
        
        # Additional settings (optional)
        self.additional_settings = QCheckBox("Use Testnet")
        self.form_layout.addRow("", self.additional_settings)
        
        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_exchange)
        
        # Disconnect button (initially disabled)
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect_exchange)
        self.disconnect_button.setEnabled(False)
        
        # Button layout
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.connect_button)
        self.button_layout.addWidget(self.disconnect_button)
        
        # Add layouts to connection group
        self.connection_layout.addLayout(self.form_layout)
        self.connection_layout.addLayout(self.button_layout)
        
        self.connection_group.setLayout(self.connection_layout)
        
        # DEX Tab (MetaMask)
        self.dex_tab = QWidget()
        self.dex_layout = QVBoxLayout(self.dex_tab)
        
        self.metamask_widget = MetaMaskConnectWidget()
        self.dex_layout.addWidget(self.metamask_widget)
        
        # Add tabs
        self.tab_widget.addTab(self.connection_group, "Exchange")
        self.tab_widget.addTab(self.dex_tab, "DEX")
        
        # Status indicator
        self.status_layout = QHBoxLayout()
        self.status_label = QLabel("Status:")
        self.status_value = QLabel("Not Connected")
        self.status_value.setStyleSheet("color: red; font-weight: bold;")
        
        self.status_layout.addWidget(self.status_label)
        self.status_layout.addWidget(self.status_value)
        self.status_layout.addStretch(1)
        
        # Add components to main layout
        self.layout.addWidget(self.tab_widget)
        self.layout.addLayout(self.status_layout)
        self.layout.addStretch(1)
        
    def on_exchange_changed(self, exchange_name):
        """Handle exchange selection change"""
        # In a real implementation, we would adjust the form fields
        # based on the selected exchange's requirements
        pass
        
    def connect_exchange(self):
        """Handle connect button click to connect to the exchange"""
        exchange = self.exchange_combo.currentText()
        api_key = self.api_key_input.text().strip()
        api_secret = self.api_secret_input.text().strip()
        
        if not api_key or not api_secret:
            QMessageBox.warning(
                self, 
                "Missing Credentials", 
                "Please enter both API Key and API Secret to connect."
            )
            return
        
        # In a real implementation, we would attempt to connect to the exchange
        # using the provided credentials and handle the result
        
        # For demonstration, simulate successful connection
        self.set_connected_state(True)
        
        QMessageBox.information(
            self, 
            "Connection Successful", 
            f"Successfully connected to {exchange}."
        )
        
    def disconnect_exchange(self):
        """Handle disconnect button click"""
        # In a real implementation, we would close the connection to the exchange
        
        # For demonstration, simulate disconnection
        self.set_connected_state(False)
        
        QMessageBox.information(
            self, 
            "Disconnected", 
            f"Disconnected from {self.exchange_combo.currentText()}."
        )
    
    def set_connected_state(self, connected):
        """Update the UI to reflect connection state"""
        self.is_connected = connected
        
        if connected:
            # Update status indicator
            self.status_value.setText("Connected")
            self.status_value.setStyleSheet("color: green; font-weight: bold;")
            
            # Update button states
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            
            # Disable form inputs
            self.exchange_combo.setEnabled(False)
            self.api_key_input.setEnabled(False)
            self.api_secret_input.setEnabled(False)
            self.additional_settings.setEnabled(False)
        else:
            # Update status indicator
            self.status_value.setText("Not Connected")
            self.status_value.setStyleSheet("color: red; font-weight: bold;")
            
            # Update button states
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            
            # Enable form inputs
            self.exchange_combo.setEnabled(True)
            self.api_key_input.setEnabled(True)
            self.api_secret_input.setEnabled(True)
            self.additional_settings.setEnabled(True)
        
        # Emit signal for connection state change
        self.connection_changed.emit(connected)
