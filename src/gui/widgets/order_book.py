#!/usr/bin/env python3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

class OrderBookWidget(QWidget):
    """
    Widget displaying the order book for a trading pair.
    Shows bid and ask orders with price and volume.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(300)
        
        # Initialize UI
        self.init_ui()
        
        # Load sample data
        self.load_sample_data()
        
    def init_ui(self):
        """Initialize the user interface components"""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        
        # Header
        self.header = QLabel("Order Book")
        self.header.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.layout.addWidget(self.header)
        
        # Spread display
        self.spread_frame = QFrame()
        self.spread_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.spread_frame.setStyleSheet("background-color: #2A2A2A;")
        
        self.spread_layout = QHBoxLayout(self.spread_frame)
        self.spread_layout.setContentsMargins(10, 5, 10, 5)
        
        self.spread_label = QLabel("Spread:")
        self.spread_value = QLabel("0.00 (0.00%)")
        self.spread_value.setStyleSheet("color: #FFC107; font-weight: bold;")
        
        self.spread_layout.addWidget(self.spread_label)
        self.spread_layout.addWidget(self.spread_value, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.layout.addWidget(self.spread_frame)
        
        # Ask orders (sell)
        self.asks_label = QLabel("Sell Orders")
        self.asks_label.setStyleSheet("color: #EF5350; margin-top: 10px;")
        self.layout.addWidget(self.asks_label)
        
        self.asks_table = QTableWidget(0, 3)
        self.asks_table.setHorizontalHeaderLabels(["Price", "Amount", "Total"])
        self.asks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.asks_table.verticalHeader().setVisible(False)
        self.asks_table.setShowGrid(False)
        self.asks_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.asks_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.asks_table.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E1E;
                border: none;
            }
            QHeaderView::section {
                background-color: #2A2A2A;
                color: #E0E0E0;
                border: none;
                padding: 4px;
            }
            QTableWidget::item {
                border-bottom: 1px solid #2A2A2A;
                padding: 4px;
            }
        """)
        
        self.layout.addWidget(self.asks_table)
        
        # Bid orders (buy)
        self.bids_label = QLabel("Buy Orders")
        self.bids_label.setStyleSheet("color: #26A69A; margin-top: 10px;")
        self.layout.addWidget(self.bids_label)
        
        self.bids_table = QTableWidget(0, 3)
        self.bids_table.setHorizontalHeaderLabels(["Price", "Amount", "Total"])
        self.bids_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.bids_table.verticalHeader().setVisible(False)
        self.bids_table.setShowGrid(False)
        self.bids_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.bids_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.bids_table.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E1E;
                border: none;
            }
            QHeaderView::section {
                background-color: #2A2A2A;
                color: #E0E0E0;
                border: none;
                padding: 4px;
            }
            QTableWidget::item {
                border-bottom: 1px solid #2A2A2A;
                padding: 4px;
            }
        """)
        
        self.layout.addWidget(self.bids_table)
        
    def load_sample_data(self):
        """Load sample order book data for demonstration"""
        # Clear existing data
        self.asks_table.setRowCount(0)
        self.bids_table.setRowCount(0)
        
        # Sample data
        base_price = 49950.25
        
        # Generate ask orders (10 rows)
        asks = []
        for i in range(10):
            price = base_price + (i + 1) * 10 + (i * i)
            amount = 0.05 + 0.01 * (10 - i)
            total = price * amount
            asks.append((price, amount, total))
        
        # Generate bid orders (10 rows)
        bids = []
        for i in range(10):
            price = base_price - (i + 1) * 10 - (i * i)
            amount = 0.04 + 0.015 * (10 - i)
            total = price * amount
            bids.append((price, amount, total))
        
        # Calculate and display spread
        spread = asks[0][0] - bids[0][0]
        spread_percent = (spread / asks[0][0]) * 100
        self.spread_value.setText(f"{spread:.2f} ({spread_percent:.2f}%)")
        
        # Populate ask table (sells)
        self.asks_table.setRowCount(len(asks))
        
        # Fill asks table from bottom to top (lowest ask at bottom)
        asks.reverse()
        for i, (price, amount, total) in enumerate(asks):
            # Price
            price_item = QTableWidgetItem(f"{price:.2f}")
            price_item.setForeground(QColor("#EF5350"))
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.asks_table.setItem(i, 0, price_item)
            
            # Amount
            amount_item = QTableWidgetItem(f"{amount:.4f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.asks_table.setItem(i, 1, amount_item)
            
            # Total
            total_item = QTableWidgetItem(f"{total:.2f}")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.asks_table.setItem(i, 2, total_item)
        
        # Populate bid table (buys)
        self.bids_table.setRowCount(len(bids))
        
        for i, (price, amount, total) in enumerate(bids):
            # Price
            price_item = QTableWidgetItem(f"{price:.2f}")
            price_item.setForeground(QColor("#26A69A"))
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.bids_table.setItem(i, 0, price_item)
            
            # Amount
            amount_item = QTableWidgetItem(f"{amount:.4f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.bids_table.setItem(i, 1, amount_item)
            
            # Total
            total_item = QTableWidgetItem(f"{total:.2f}")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.bids_table.setItem(i, 2, total_item)
    
    def update_order_book(self, asks, bids):
        """
        Update the order book with real data
        
        Args:
            asks (list): List of (price, amount) tuples for ask orders
            bids (list): List of (price, amount) tuples for bid orders
        """
        # Implementation for real data would go here
        pass
