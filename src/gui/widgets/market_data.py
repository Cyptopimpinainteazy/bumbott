#!/usr/bin/env python3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QGroupBox, QComboBox, QPushButton, QLineEdit,
    QGridLayout, QScrollArea, QFrame, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
import random
from datetime import datetime, timedelta

class CryptoInfoWidget(QWidget):
    """Widget displaying information about a specific cryptocurrency"""
    
    def __init__(self, symbol="BTC", parent=None):
        super().__init__(parent)
        self.symbol = symbol
        
        # Initialize UI
        self.init_ui()
        
        # Don't use timers for now to avoid crashes
        # Update with static data immediately
        self.update_data()
        
    def init_ui(self):
        """Initialize the user interface components"""
        # Main layout
        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        
        # Coin name and logo
        self.name_label = QLabel("Bitcoin (BTC)")
        self.name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.layout.addWidget(self.name_label, 0, 0, 1, 2)
        
        # Current price
        self.price_frame = QFrame()
        self.price_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.price_frame.setStyleSheet("background-color: #2A2A2A; border-radius: 5px; padding: 10px;")
        
        self.price_layout = QVBoxLayout(self.price_frame)
        
        self.price_label = QLabel("Price (USDT)")
        self.price_label.setStyleSheet("color: #AAAAAA;")
        
        self.price_value = QLabel("$0.00")
        self.price_value.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.price_change = QLabel("0.00%")
        
        self.price_layout.addWidget(self.price_label)
        self.price_layout.addWidget(self.price_value)
        self.price_layout.addWidget(self.price_change)
        
        self.layout.addWidget(self.price_frame, 1, 0, 1, 1)
        
        # Market cap
        self.market_cap_frame = QFrame()
        self.market_cap_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.market_cap_frame.setStyleSheet("background-color: #2A2A2A; border-radius: 5px; padding: 10px;")
        
        self.market_cap_layout = QVBoxLayout(self.market_cap_frame)
        
        self.market_cap_label = QLabel("Market Cap")
        self.market_cap_label.setStyleSheet("color: #AAAAAA;")
        
        self.market_cap_value = QLabel("$0.00")
        self.market_cap_value.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.market_cap_layout.addWidget(self.market_cap_label)
        self.market_cap_layout.addWidget(self.market_cap_value)
        
        self.layout.addWidget(self.market_cap_frame, 1, 1, 1, 1)
        
        # Volume
        self.volume_frame = QFrame()
        self.volume_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.volume_frame.setStyleSheet("background-color: #2A2A2A; border-radius: 5px; padding: 10px;")
        
        self.volume_layout = QVBoxLayout(self.volume_frame)
        
        self.volume_label = QLabel("24h Volume")
        self.volume_label.setStyleSheet("color: #AAAAAA;")
        
        self.volume_value = QLabel("$0.00")
        self.volume_value.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.volume_layout.addWidget(self.volume_label)
        self.volume_layout.addWidget(self.volume_value)
        
        self.layout.addWidget(self.volume_frame, 2, 0, 1, 1)
        
        # Supply
        self.supply_frame = QFrame()
        self.supply_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.supply_frame.setStyleSheet("background-color: #2A2A2A; border-radius: 5px; padding: 10px;")
        
        self.supply_layout = QVBoxLayout(self.supply_frame)
        
        self.supply_label = QLabel("Circulating Supply")
        self.supply_label.setStyleSheet("color: #AAAAAA;")
        
        self.supply_value = QLabel("0")
        self.supply_value.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.supply_layout.addWidget(self.supply_label)
        self.supply_layout.addWidget(self.supply_value)
        
        self.layout.addWidget(self.supply_frame, 2, 1, 1, 1)
        
        # Recent trades
        self.trades_group = QGroupBox("Recent Trades")
        self.trades_layout = QVBoxLayout(self.trades_group)
        
        self.trades_table = QTableWidget(0, 4)
        self.trades_table.setHorizontalHeaderLabels(["Time", "Price", "Amount", "Total"])
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
        
        self.trades_layout.addWidget(self.trades_table)
        
        self.layout.addWidget(self.trades_group, 3, 0, 1, 2)
        
    def update_data(self):
        """Update cryptocurrency data with sample values"""
        # For demonstration, update with random sample data based on symbol
        
        coin_data = {
            "BTC": {
                "name": "Bitcoin",
                "price": random.uniform(47000, 52000),
                "change": random.uniform(-2.5, 2.5),
                "market_cap": random.uniform(900, 950) * 1e9,
                "volume": random.uniform(20, 30) * 1e9,
                "supply": random.uniform(19.2, 19.3) * 1e6
            },
            "ETH": {
                "name": "Ethereum",
                "price": random.uniform(2600, 2900),
                "change": random.uniform(-3.0, 3.0),
                "market_cap": random.uniform(310, 330) * 1e9,
                "volume": random.uniform(10, 15) * 1e9,
                "supply": random.uniform(120, 121) * 1e6
            },
            "BNB": {
                "name": "Binance Coin",
                "price": random.uniform(300, 330),
                "change": random.uniform(-2.0, 2.0),
                "market_cap": random.uniform(50, 55) * 1e9,
                "volume": random.uniform(1, 1.5) * 1e9,
                "supply": random.uniform(155, 156) * 1e6
            },
            "SOL": {
                "name": "Solana",
                "price": random.uniform(45, 55),
                "change": random.uniform(-4.0, 4.0),
                "market_cap": random.uniform(20, 22) * 1e9,
                "volume": random.uniform(1.5, 2.5) * 1e9,
                "supply": random.uniform(410, 415) * 1e6
            },
            "XRP": {
                "name": "XRP",
                "price": random.uniform(0.5, 0.6),
                "change": random.uniform(-2.0, 2.0),
                "market_cap": random.uniform(25, 28) * 1e9,
                "volume": random.uniform(1, 2) * 1e9,
                "supply": random.uniform(45, 46) * 1e9
            }
        }
        
        # Default to BTC if symbol not found
        data = coin_data.get(self.symbol, coin_data["BTC"])
        
        # Update UI with new data
        self.name_label.setText(f"{data['name']} ({self.symbol})")
        
        # Update price
        self.price_value.setText(f"${data['price']:.2f}")
        
        # Update price change
        change_color = "green" if data['change'] >= 0 else "red"
        change_sign = "+" if data['change'] >= 0 else ""
        self.price_change.setText(f"{change_sign}{data['change']:.2f}%")
        self.price_change.setStyleSheet(f"color: {change_color};")
        
        # Update market cap
        if data['market_cap'] >= 1e9:
            market_cap_str = f"${data['market_cap'] / 1e9:.2f}B"
        else:
            market_cap_str = f"${data['market_cap'] / 1e6:.2f}M"
        self.market_cap_value.setText(market_cap_str)
        
        # Update volume
        if data['volume'] >= 1e9:
            volume_str = f"${data['volume'] / 1e9:.2f}B"
        else:
            volume_str = f"${data['volume'] / 1e6:.2f}M"
        self.volume_value.setText(volume_str)
        
        # Update supply
        if data['supply'] >= 1e9:
            supply_str = f"{data['supply'] / 1e9:.2f}B"
        elif data['supply'] >= 1e6:
            supply_str = f"{data['supply'] / 1e6:.2f}M"
        else:
            supply_str = f"{data['supply']:,.0f}"
        self.supply_value.setText(f"{supply_str} {self.symbol}")
        
        # Generate and update recent trades
        self.update_recent_trades(data['price'])
    
    def update_recent_trades(self, current_price):
        """Update the recent trades table with sample data"""
        # Clear existing rows
        self.trades_table.setRowCount(0)
        
        # Generate random trades
        num_trades = 10
        trades = []
        
        for i in range(num_trades):
            # Random time (within the last hour)
            trade_time = datetime.now() - timedelta(minutes=random.randint(0, 59), seconds=random.randint(0, 59))
            
            # Random price around current price
            price = current_price * (1 + random.uniform(-0.001, 0.001))
            
            # Random amount
            if self.symbol == "BTC":
                amount = random.uniform(0.001, 0.5)
            elif self.symbol in ["ETH", "BNB"]:
                amount = random.uniform(0.01, 5)
            else:
                amount = random.uniform(1, 100)
            
            # Calculate total
            total = price * amount
            
            trades.append((trade_time, price, amount, total))
        
        # Sort by time (newest first)
        trades.sort(key=lambda x: x[0], reverse=True)
        
        # Add to table
        self.trades_table.setRowCount(len(trades))
        
        for i, (time, price, amount, total) in enumerate(trades):
            # Time
            time_item = QTableWidgetItem(time.strftime("%H:%M:%S"))
            self.trades_table.setItem(i, 0, time_item)
            
            # Price
            price_item = QTableWidgetItem(f"${price:.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.trades_table.setItem(i, 1, price_item)
            
            # Amount
            amount_item = QTableWidgetItem(f"{amount:.6f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.trades_table.setItem(i, 2, amount_item)
            
            # Total
            total_item = QTableWidgetItem(f"${total:.2f}")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.trades_table.setItem(i, 3, total_item)

class MarketOverviewWidget(QWidget):
    """Widget displaying an overview of the cryptocurrency market"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize UI
        self.init_ui()
        
        # Don't use timers for now to avoid crashes
        # Update with static data immediately
        self.update_data()
        
    def init_ui(self):
        """Initialize the user interface components"""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with market stats
        self.header_frame = QFrame()
        self.header_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.header_frame.setStyleSheet("background-color: #2A2A2A; border-radius: 5px;")
        
        self.header_layout = QHBoxLayout(self.header_frame)
        
        # Market cap
        self.market_cap_layout = QVBoxLayout()
        self.market_cap_label = QLabel("Total Market Cap")
        self.market_cap_label.setStyleSheet("color: #AAAAAA;")
        self.market_cap_value = QLabel("$0.00T")
        self.market_cap_value.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.market_cap_layout.addWidget(self.market_cap_label)
        self.market_cap_layout.addWidget(self.market_cap_value)
        
        # 24h volume
        self.volume_layout = QVBoxLayout()
        self.volume_label = QLabel("24h Volume")
        self.volume_label.setStyleSheet("color: #AAAAAA;")
        self.volume_value = QLabel("$0.00B")
        self.volume_value.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.volume_layout.addWidget(self.volume_label)
        self.volume_layout.addWidget(self.volume_value)
        
        # BTC dominance
        self.btc_dom_layout = QVBoxLayout()
        self.btc_dom_label = QLabel("BTC Dominance")
        self.btc_dom_label.setStyleSheet("color: #AAAAAA;")
        self.btc_dom_value = QLabel("0.00%")
        self.btc_dom_value.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.btc_dom_layout.addWidget(self.btc_dom_label)
        self.btc_dom_layout.addWidget(self.btc_dom_value)
        
        # Add to header layout
        self.header_layout.addLayout(self.market_cap_layout)
        self.header_layout.addLayout(self.volume_layout)
        self.header_layout.addLayout(self.btc_dom_layout)
        
        # Market table
        self.market_table = QTableWidget(0, 7)
        self.market_table.setHorizontalHeaderLabels([
            "#", "Name", "Price", "24h Change", "24h Volume", "Market Cap", "7d Chart"
        ])
        
        # Set column widths
        self.market_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.market_table.setColumnWidth(0, 40)
        self.market_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.market_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.market_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.market_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.market_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.market_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.market_table.setColumnWidth(6, 100)
        
        self.market_table.verticalHeader().setVisible(False)
        self.market_table.setShowGrid(False)
        self.market_table.setStyleSheet("""
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
        
        # Search bar
        self.search_layout = QHBoxLayout()
        
        self.search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search cryptocurrencies...")
        self.search_input.textChanged.connect(self.filter_market_table)
        
        self.search_layout.addWidget(self.search_label)
        self.search_layout.addWidget(self.search_input)
        
        # Add components to layout
        self.layout.addWidget(self.header_frame)
        self.layout.addLayout(self.search_layout)
        self.layout.addWidget(self.market_table)
        
    def update_data(self):
        """Update market data with sample values"""
        # For demonstration, use sample market data
        
        # Update market stats
        total_market_cap = random.uniform(2.1, 2.3) * 1e12
        total_volume = random.uniform(80, 120) * 1e9
        btc_dominance = random.uniform(45, 51)
        
        self.market_cap_value.setText(f"${total_market_cap / 1e12:.2f}T")
        self.volume_value.setText(f"${total_volume / 1e9:.2f}B")
        self.btc_dom_value.setText(f"{btc_dominance:.2f}%")
        
        # Sample cryptocurrency data
        cryptos = [
            {
                "rank": 1,
                "name": "Bitcoin",
                "symbol": "BTC",
                "price": random.uniform(47000, 52000),
                "change_24h": random.uniform(-2.5, 2.5),
                "volume_24h": random.uniform(20, 30) * 1e9,
                "market_cap": random.uniform(900, 950) * 1e9
            },
            {
                "rank": 2,
                "name": "Ethereum",
                "symbol": "ETH",
                "price": random.uniform(2600, 2900),
                "change_24h": random.uniform(-3.0, 3.0),
                "volume_24h": random.uniform(10, 15) * 1e9,
                "market_cap": random.uniform(310, 330) * 1e9
            },
            {
                "rank": 3,
                "name": "Tether",
                "symbol": "USDT",
                "price": random.uniform(0.999, 1.001),
                "change_24h": random.uniform(-0.1, 0.1),
                "volume_24h": random.uniform(50, 60) * 1e9,
                "market_cap": random.uniform(85, 86) * 1e9
            },
            {
                "rank": 4,
                "name": "BNB",
                "symbol": "BNB",
                "price": random.uniform(300, 330),
                "change_24h": random.uniform(-2.0, 2.0),
                "volume_24h": random.uniform(1, 1.5) * 1e9,
                "market_cap": random.uniform(50, 55) * 1e9
            },
            {
                "rank": 5,
                "name": "Solana",
                "symbol": "SOL",
                "price": random.uniform(45, 55),
                "change_24h": random.uniform(-4.0, 4.0),
                "volume_24h": random.uniform(1.5, 2.5) * 1e9,
                "market_cap": random.uniform(20, 22) * 1e9
            },
            {
                "rank": 6,
                "name": "XRP",
                "symbol": "XRP",
                "price": random.uniform(0.5, 0.6),
                "change_24h": random.uniform(-2.0, 2.0),
                "volume_24h": random.uniform(1, 2) * 1e9,
                "market_cap": random.uniform(25, 28) * 1e9
            },
            {
                "rank": 7,
                "name": "USD Coin",
                "symbol": "USDC",
                "price": random.uniform(0.999, 1.001),
                "change_24h": random.uniform(-0.1, 0.1),
                "volume_24h": random.uniform(3, 4) * 1e9,
                "market_cap": random.uniform(28, 29) * 1e9
            },
            {
                "rank": 8,
                "name": "Cardano",
                "symbol": "ADA",
                "price": random.uniform(0.45, 0.55),
                "change_24h": random.uniform(-3.0, 3.0),
                "volume_24h": random.uniform(0.5, 1) * 1e9,
                "market_cap": random.uniform(16, 18) * 1e9
            },
            {
                "rank": 9,
                "name": "Dogecoin",
                "symbol": "DOGE",
                "price": random.uniform(0.12, 0.15),
                "change_24h": random.uniform(-4.0, 4.0),
                "volume_24h": random.uniform(0.5, 1) * 1e9,
                "market_cap": random.uniform(16, 18) * 1e9
            },
            {
                "rank": 10,
                "name": "Avalanche",
                "symbol": "AVAX",
                "price": random.uniform(32, 38),
                "change_24h": random.uniform(-3.0, 3.0),
                "volume_24h": random.uniform(0.4, 0.8) * 1e9,
                "market_cap": random.uniform(12, 14) * 1e9
            }
        ]
        
        # Update table
        self.market_table.setRowCount(len(cryptos))
        
        for i, crypto in enumerate(cryptos):
            # Rank
            rank_item = QTableWidgetItem(str(crypto["rank"]))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.market_table.setItem(i, 0, rank_item)
            
            # Name
            name_item = QTableWidgetItem(f"{crypto['name']} ({crypto['symbol']})")
            font = QFont()
            font.setBold(True)
            name_item.setFont(font)
            self.market_table.setItem(i, 1, name_item)
            
            # Price
            price_item = QTableWidgetItem(f"${crypto['price']:.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.market_table.setItem(i, 2, price_item)
            
            # 24h Change
            change_color = "green" if crypto['change_24h'] >= 0 else "red"
            change_sign = "+" if crypto['change_24h'] >= 0 else ""
            change_item = QTableWidgetItem(f"{change_sign}{crypto['change_24h']:.2f}%")
            change_item.setForeground(QColor(change_color))
            change_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.market_table.setItem(i, 3, change_item)
            
            # 24h Volume
            if crypto['volume_24h'] >= 1e9:
                volume_str = f"${crypto['volume_24h'] / 1e9:.2f}B"
            else:
                volume_str = f"${crypto['volume_24h'] / 1e6:.2f}M"
            volume_item = QTableWidgetItem(volume_str)
            volume_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.market_table.setItem(i, 4, volume_item)
            
            # Market Cap
            if crypto['market_cap'] >= 1e9:
                market_cap_str = f"${crypto['market_cap'] / 1e9:.2f}B"
            else:
                market_cap_str = f"${crypto['market_cap'] / 1e6:.2f}M"
            market_cap_item = QTableWidgetItem(market_cap_str)
            market_cap_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.market_table.setItem(i, 5, market_cap_item)
            
            # 7d Chart (placeholder)
            chart_item = QTableWidgetItem("Chart")
            chart_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.market_table.setItem(i, 6, chart_item)
    
    def filter_market_table(self):
        """Filter the market table based on search input"""
        search_text = self.search_input.text().lower()
        
        for i in range(self.market_table.rowCount()):
            name_item = self.market_table.item(i, 1)
            name_text = name_item.text().lower() if name_item else ""
            
            # Show row if search text is in the name/symbol
            self.market_table.setRowHidden(i, search_text and search_text not in name_text)

class MarketDataWidget(QWidget):
    """
    Widget for displaying cryptocurrency market data, including
    market overview, specific coin details, and trade information.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize UI
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface components"""
        # Main layout
        self.layout = QVBoxLayout(self)
        
        # Create tabs
        self.tabs = QTabWidget()
        
        # Market overview tab
        self.overview_tab = MarketOverviewWidget()
        self.tabs.addTab(self.overview_tab, "Market Overview")
        
        # Specific coin tabs
        self.btc_tab = CryptoInfoWidget("BTC")
        self.tabs.addTab(self.btc_tab, "Bitcoin (BTC)")
        
        self.eth_tab = CryptoInfoWidget("ETH")
        self.tabs.addTab(self.eth_tab, "Ethereum (ETH)")
        
        self.bnb_tab = CryptoInfoWidget("BNB")
        self.tabs.addTab(self.bnb_tab, "Binance Coin (BNB)")
        
        self.sol_tab = CryptoInfoWidget("SOL")
        self.tabs.addTab(self.sol_tab, "Solana (SOL)")
        
        # Add tabs to layout
        self.layout.addWidget(self.tabs)
