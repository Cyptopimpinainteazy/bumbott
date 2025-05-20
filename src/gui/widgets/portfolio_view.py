#!/usr/bin/env python3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QGroupBox, QFrame, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen
import random

class DonutChart(QWidget):
    """
    A simple donut chart implementation for asset allocation visualization
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.asset_data = {}
        self.setMinimumSize(180, 180)
        self.colors = [
            QColor("#1E88E5"), QColor("#26A69A"), QColor("#7E57C2"), 
            QColor("#FFC107"), QColor("#EF5350"), QColor("#5D4037"),
            QColor("#26C6DA"), QColor("#66BB6A"), QColor("#EC407A")
        ]
    
    def set_data(self, asset_data):
        """
        Set the asset allocation data
        
        Args:
            asset_data (dict): Dictionary with asset names as keys and values as percentages
        """
        self.asset_data = asset_data
        self.update()
    
    def paintEvent(self, event):
        if not self.asset_data:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate center and radius
        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2
        outer_radius = min(width, height) / 2 - 10
        inner_radius = outer_radius * 0.6
        
        # Make sure we have data to draw
        total_percentage = sum(self.asset_data.values())
        if total_percentage <= 0:
            # Draw placeholder circle if no data
            painter.setPen(QPen(Qt.GlobalColor.gray, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(
                int(center_x - outer_radius), 
                int(center_y - outer_radius),
                int(outer_radius * 2), 
                int(outer_radius * 2)
            )
            return
        
        # Draw donut chart
        start_angle = 0
        for i, (asset, percentage) in enumerate(self.asset_data.items()):
            # Calculate angle for this asset (ensure valid values)
            angle = int(max(0, min(1, percentage)) * 360 * 16)  # QPainter uses 1/16th degrees
            if angle <= 0:
                continue
                
            # Set color for this segment
            painter.setBrush(QBrush(self.colors[i % len(self.colors)]))
            painter.setPen(Qt.PenStyle.NoPen)
            
            # Draw segment
            try:
                painter.drawPie(
                    int(center_x - outer_radius), 
                    int(center_y - outer_radius),
                    int(outer_radius * 2), 
                    int(outer_radius * 2),
                    start_angle, 
                    angle
                )
            except Exception as e:
                # Skip this segment if there's an error
                pass
            
            start_angle += angle
        
        # Draw inner circle (to create donut hole)
        painter.setBrush(QBrush(self.palette().window().color()))
        try:
            painter.drawEllipse(
                int(center_x - inner_radius), 
                int(center_y - inner_radius),
                int(inner_radius * 2), 
                int(inner_radius * 2)
            )
        except Exception as e:
            # Skip if there's an error
            pass

class PortfolioViewWidget(QWidget):
    """
    Widget displaying portfolio information, including asset balances,
    allocation, and value.
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
        
        # Portfolio group box
        self.portfolio_group = QGroupBox("Portfolio")
        self.portfolio_layout = QVBoxLayout()
        
        # Portfolio summary
        self.summary_frame = QFrame()
        self.summary_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.summary_frame.setStyleSheet("background-color: #262626;")
        
        self.summary_layout = QVBoxLayout(self.summary_frame)
        
        # Total value
        self.total_value_label = QLabel("Total Value")
        self.total_value_label.setStyleSheet("color: #AAAAAA;")
        self.total_value = QLabel("$0.00")
        self.total_value.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        # 24h change
        self.change_layout = QHBoxLayout()
        self.change_label = QLabel("24h Change:")
        self.change_value = QLabel("$0.00 (0.00%)")
        
        self.change_layout.addWidget(self.change_label)
        self.change_layout.addWidget(self.change_value)
        self.change_layout.addStretch(1)
        
        # Add to summary layout
        self.summary_layout.addWidget(self.total_value_label)
        self.summary_layout.addWidget(self.total_value)
        self.summary_layout.addLayout(self.change_layout)
        
        # Asset allocation visualization
        self.allocation_layout = QHBoxLayout()
        
        # Donut chart for visualization
        self.donut_chart = DonutChart()
        
        # Asset legend
        self.asset_legend = QTableWidget(0, 2)
        self.asset_legend.setHorizontalHeaderLabels(["Asset", "Allocation"])
        self.asset_legend.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.asset_legend.verticalHeader().setVisible(False)
        self.asset_legend.setShowGrid(False)
        self.asset_legend.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.asset_legend.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.asset_legend.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
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
        
        self.allocation_layout.addWidget(self.donut_chart)
        self.allocation_layout.addWidget(self.asset_legend)
        
        # Holdings table
        self.holdings_label = QLabel("Holdings")
        self.holdings_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        
        self.holdings_table = QTableWidget(0, 4)
        self.holdings_table.setHorizontalHeaderLabels(["Asset", "Balance", "Price", "Value"])
        self.holdings_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.holdings_table.verticalHeader().setVisible(False)
        self.holdings_table.setShowGrid(False)
        self.holdings_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.holdings_table.setStyleSheet("""
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
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_sample_data)
        
        # Add components to portfolio layout
        self.portfolio_layout.addWidget(self.summary_frame)
        self.portfolio_layout.addLayout(self.allocation_layout)
        self.portfolio_layout.addWidget(self.holdings_label)
        self.portfolio_layout.addWidget(self.holdings_table)
        self.portfolio_layout.addWidget(self.refresh_button)
        
        self.portfolio_group.setLayout(self.portfolio_layout)
        
        # Add to main layout
        self.layout.addWidget(self.portfolio_group)
        
    def load_sample_data(self):
        """Load sample portfolio data for demonstration"""
        # Sample portfolio data
        portfolio = [
            {"asset": "Bitcoin", "symbol": "BTC", "balance": 0.5, "price": 49950.25, "value": 24975.13},
            {"asset": "Ethereum", "symbol": "ETH", "balance": 4.2, "price": 2780.40, "value": 11677.68},
            {"asset": "Binance Coin", "symbol": "BNB", "balance": 25.0, "price": 312.75, "value": 7818.75},
            {"asset": "Solana", "symbol": "SOL", "balance": 120.0, "price": 48.35, "value": 5802.00},
            {"asset": "USDT", "symbol": "USDT", "balance": 2500.0, "price": 1.0, "value": 2500.00}
        ]
        
        # Calculate total value and allocations
        total_value = sum(item["value"] for item in portfolio)
        allocations = {item["symbol"]: item["value"] / total_value for item in portfolio}
        
        # Update total value display
        self.total_value.setText(f"${total_value:.2f}")
        
        # Generate random 24h change for demonstration
        change_amount = random.uniform(-total_value * 0.03, total_value * 0.05)
        change_percent = (change_amount / (total_value - change_amount)) * 100
        
        change_color = "green" if change_amount >= 0 else "red"
        change_sign = "+" if change_amount >= 0 else ""
        
        self.change_value.setText(f"{change_sign}${change_amount:.2f} ({change_sign}{change_percent:.2f}%)")
        self.change_value.setStyleSheet(f"color: {change_color};")
        
        # Update asset allocation chart
        self.donut_chart.set_data(allocations)
        
        # Update allocation legend
        self.asset_legend.setRowCount(len(allocations))
        for i, (symbol, percentage) in enumerate(allocations.items()):
            # Asset symbol
            symbol_item = QTableWidgetItem(symbol)
            self.asset_legend.setItem(i, 0, symbol_item)
            
            # Allocation percentage
            percentage_item = QTableWidgetItem(f"{percentage * 100:.2f}%")
            percentage_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.asset_legend.setItem(i, 1, percentage_item)
            
            # Set row color based on asset
            color = self.donut_chart.colors[i % len(self.donut_chart.colors)]
            symbol_item.setForeground(color)
            percentage_item.setForeground(color)
        
        # Update holdings table
        self.holdings_table.setRowCount(len(portfolio))
        for i, item in enumerate(portfolio):
            # Asset name
            asset_item = QTableWidgetItem(f"{item['asset']} ({item['symbol']})")
            self.holdings_table.setItem(i, 0, asset_item)
            
            # Balance
            balance_item = QTableWidgetItem(f"{item['balance']:.8f}")
            balance_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.holdings_table.setItem(i, 1, balance_item)
            
            # Price
            price_item = QTableWidgetItem(f"${item['price']:.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.holdings_table.setItem(i, 2, price_item)
            
            # Value
            value_item = QTableWidgetItem(f"${item['value']:.2f}")
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.holdings_table.setItem(i, 3, value_item)
