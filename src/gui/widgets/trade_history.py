#!/usr/bin/env python3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QGroupBox, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import random
from datetime import datetime, timedelta

class TradeHistoryWidget(QWidget):
    """
    Widget displaying the trade history for the active trading session.
    Shows executed trades with relevant details.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize UI
        self.init_ui()
        
        # Load sample data for demonstration
        self.load_sample_data()
        
    def init_ui(self):
        """Initialize the user interface components"""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        self.header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Trade History")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        # Period filter
        self.period_label = QLabel("Period:")
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Today", "Yesterday", "This Week", "Last 7 Days", "This Month", "All Time"])
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        
        # Add to header layout
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch(1)
        self.header_layout.addWidget(self.period_label)
        self.header_layout.addWidget(self.period_combo)
        
        # Trade history table
        self.trades_table = QTableWidget(0, 6)
        self.trades_table.setHorizontalHeaderLabels(["Time", "Pair", "Side", "Price", "Amount", "Total"])
        self.trades_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.trades_table.verticalHeader().setVisible(False)
        self.trades_table.setShowGrid(False)
        self.trades_table.setStyleSheet("""
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
        
        # Summary stats
        self.summary_layout = QHBoxLayout()
        
        # Total trades
        self.total_trades_label = QLabel("Total Trades:")
        self.total_trades_value = QLabel("0")
        
        # Total volume
        self.total_volume_label = QLabel("Total Volume:")
        self.total_volume_value = QLabel("$0.00")
        
        # Net profit
        self.net_profit_label = QLabel("Net Profit:")
        self.net_profit_value = QLabel("$0.00 (0.00%)")
        
        # Add to summary layout
        self.summary_layout.addWidget(self.total_trades_label)
        self.summary_layout.addWidget(self.total_trades_value)
        self.summary_layout.addStretch(1)
        self.summary_layout.addWidget(self.total_volume_label)
        self.summary_layout.addWidget(self.total_volume_value)
        self.summary_layout.addStretch(1)
        self.summary_layout.addWidget(self.net_profit_label)
        self.summary_layout.addWidget(self.net_profit_value)
        
        # Add components to main layout
        self.layout.addLayout(self.header_layout)
        self.layout.addWidget(self.trades_table)
        self.layout.addLayout(self.summary_layout)
        
    def on_period_changed(self, period):
        """Handle period filter change"""
        self.load_sample_data(period)
        
    def load_sample_data(self, period="Today"):
        """Load sample trade history data for demonstration"""
        # Clear existing data
        self.trades_table.setRowCount(0)
        
        # Generate random trades based on selected period
        trades = []
        
        # Determine date range based on period
        end_date = datetime.now()
        
        if period == "Today":
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            num_trades = random.randint(5, 15)
        elif period == "Yesterday":
            end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            num_trades = random.randint(10, 25)
        elif period == "This Week":
            start_date = end_date - timedelta(days=end_date.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            num_trades = random.randint(20, 50)
        elif period == "Last 7 Days":
            start_date = end_date - timedelta(days=7)
            num_trades = random.randint(30, 70)
        elif period == "This Month":
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            num_trades = random.randint(50, 100)
        else:  # All Time
            start_date = end_date - timedelta(days=90)  # Just use last 90 days for demo
            num_trades = random.randint(100, 200)
        
        # Trading pairs
        pairs = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT"]
        
        # Generate random trades
        total_volume = 0
        net_profit = 0
        
        for _ in range(num_trades):
            # Random time within period
            time_delta = random.random() * (end_date - start_date).total_seconds()
            trade_time = start_date + timedelta(seconds=time_delta)
            
            # Random pair
            pair = random.choice(pairs)
            
            # Random side (buy/sell)
            side = random.choice(["BUY", "SELL"])
            
            # Random price based on pair
            if pair == "BTC/USDT":
                price = random.uniform(45000, 52000)
            elif pair == "ETH/USDT":
                price = random.uniform(2500, 3200)
            elif pair == "BNB/USDT":
                price = random.uniform(280, 350)
            elif pair == "SOL/USDT":
                price = random.uniform(40, 60)
            else:  # XRP/USDT
                price = random.uniform(0.5, 0.7)
            
            # Random amount
            if pair == "BTC/USDT":
                amount = random.uniform(0.01, 0.2)
            elif pair == "ETH/USDT":
                amount = random.uniform(0.1, 2.0)
            elif pair == "BNB/USDT":
                amount = random.uniform(0.5, 5.0)
            elif pair == "SOL/USDT":
                amount = random.uniform(1.0, 20.0)
            else:  # XRP/USDT
                amount = random.uniform(50, 1000)
            
            # Calculate total
            total = price * amount
            
            # Add to trades list
            trades.append({
                "time": trade_time,
                "pair": pair,
                "side": side,
                "price": price,
                "amount": amount,
                "total": total
            })
            
            # Update summary stats
            total_volume += total
            if side == "SELL":
                # For demo, assume a random profit percentage on sells
                profit_pct = random.uniform(-1.5, 3.0)
                profit_amount = total * profit_pct / 100
                net_profit += profit_amount
        
        # Sort trades by time (newest first)
        trades.sort(key=lambda x: x["time"], reverse=True)
        
        # Update trades table
        self.trades_table.setRowCount(len(trades))
        
        for i, trade in enumerate(trades):
            # Time
            time_item = QTableWidgetItem(trade["time"].strftime("%Y-%m-%d %H:%M:%S"))
            self.trades_table.setItem(i, 0, time_item)
            
            # Pair
            pair_item = QTableWidgetItem(trade["pair"])
            self.trades_table.setItem(i, 1, pair_item)
            
            # Side
            side_item = QTableWidgetItem(trade["side"])
            side_item.setForeground(QColor("#26A69A" if trade["side"] == "BUY" else "#EF5350"))
            self.trades_table.setItem(i, 2, side_item)
            
            # Price
            price_item = QTableWidgetItem(f"${trade['price']:.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.trades_table.setItem(i, 3, price_item)
            
            # Amount
            amount_item = QTableWidgetItem(f"{trade['amount']:.6f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.trades_table.setItem(i, 4, amount_item)
            
            # Total
            total_item = QTableWidgetItem(f"${trade['total']:.2f}")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.trades_table.setItem(i, 5, total_item)
        
        # Update summary stats
        self.total_trades_value.setText(str(len(trades)))
        self.total_volume_value.setText(f"${total_volume:.2f}")
        
        profit_color = "green" if net_profit >= 0 else "red"
        profit_sign = "+" if net_profit >= 0 else ""
        profit_pct = (net_profit / total_volume) * 100 if total_volume > 0 else 0
        
        self.net_profit_value.setText(f"{profit_sign}${net_profit:.2f} ({profit_sign}{profit_pct:.2f}%)")
        self.net_profit_value.setStyleSheet(f"color: {profit_color}; font-weight: bold;")
