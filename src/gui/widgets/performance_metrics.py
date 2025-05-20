#!/usr/bin/env python3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QGroupBox, QComboBox, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QLinearGradient, QGradient, QPolygonF
import math
import random

class MetricGaugeWidget(QWidget):
    """
    A gauge widget for displaying performance metrics visually
    """
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.value = 0
        self.min_value = 0
        self.max_value = 100
        self.color_zones = [
            (0, 33, QColor("#EF5350")),    # Red zone (0-33%)
            (33, 66, QColor("#FFC107")),   # Yellow zone (33-66%)
            (66, 100, QColor("#26A69A"))    # Green zone (66-100%)
        ]
        self.setMinimumSize(150, 150)
    
    def set_value(self, value):
        """Set the current value of the gauge"""
        self.value = max(self.min_value, min(self.max_value, value))
        self.update()
    
    def set_range(self, min_value, max_value):
        """Set the range of the gauge"""
        self.min_value = min_value
        self.max_value = max_value
        self.update()
    
    def set_color_zones(self, zones):
        """
        Set custom color zones for the gauge
        
        Args:
            zones (list): List of (start_percent, end_percent, color) tuples
        """
        self.color_zones = zones
        self.update()
    
    def paintEvent(self, event):
        """Paint the gauge on screen"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        width = self.width()
        height = self.height()
        margin = 10
        
        # Draw title
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(margin, margin, width - 2 * margin, 20, 
                        Qt.AlignmentFlag.AlignCenter, self.title)
        
        # Draw gauge arc
        center_x = width / 2
        center_y = height / 2 + 10  # Offset a bit to make room for title
        radius = min(width, height) / 2 - margin
        
        # Draw background arc
        painter.setPen(QPen(QColor("#3E3E42"), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(int(center_x - radius), int(center_y - radius), 
                       int(radius * 2), int(radius * 2), 
                       180 * 16, 180 * 16)  # 180 degrees (bottom half)
        
        # Draw colored zones
        for start_percent, end_percent, color in self.color_zones:
            # Convert percentages to angles
            start_angle = 180 - (start_percent / 100 * 180)
            end_angle = 180 - (end_percent / 100 * 180)
            span_angle = start_angle - end_angle
            
            painter.setPen(QPen(color, 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawArc(int(center_x - radius), int(center_y - radius), 
                           int(radius * 2), int(radius * 2), 
                           int(end_angle * 16), int(span_angle * 16))
        
        # Calculate value position
        value_range = self.max_value - self.min_value
        value_percent = ((self.value - self.min_value) / value_range) * 100 if value_range > 0 else 0
        value_angle = math.radians(180 - (value_percent / 100 * 180))
        
        # Draw needle
        needle_length = radius - 15
        needle_x = center_x + needle_length * math.cos(value_angle)
        needle_y = center_y - needle_length * math.sin(value_angle)
        
        painter.setPen(QPen(Qt.GlobalColor.white, 2, Qt.PenStyle.SolidLine))
        painter.drawLine(int(center_x), int(center_y), int(needle_x), int(needle_y))
        
        # Draw center point
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.drawEllipse(int(center_x - 5), int(center_y - 5), 10, 10)
        
        # Draw value text
        value_text = f"{self.value:.2f}"
        painter.drawText(int(center_x - 50), int(center_y + radius - 10), 
                        100, 30, Qt.AlignmentFlag.AlignCenter, value_text)

class LineChartWidget(QWidget):
    """
    A simple line chart widget for displaying time series data
    """
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.data_points = []
        self.max_points = 100
        self.min_value = 0
        self.max_value = 100
        self.line_color = QColor("#26A69A")
        self.setMinimumSize(300, 150)
    
    def add_data_point(self, value):
        """Add a new data point to the chart"""
        self.data_points.append(value)
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)
        
        # Update min/max values
        if self.data_points:
            self.min_value = min(self.min_value, min(self.data_points))
            self.max_value = max(self.max_value, max(self.data_points))
        
        self.update()
    
    def set_data(self, data_points):
        """Set the complete data set for the chart"""
        self.data_points = data_points[-self.max_points:] if len(data_points) > self.max_points else data_points
        
        # Update min/max values
        if self.data_points:
            self.min_value = min(self.data_points)
            self.max_value = max(self.data_points)
        
        self.update()
    
    def paintEvent(self, event):
        """Paint the line chart on screen"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        width = self.width()
        height = self.height()
        margin = 10
        chart_width = width - 2 * margin
        chart_height = height - 2 * margin - 20  # Extra space for title
        
        # Draw title
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(margin, margin, chart_width, 20, 
                        Qt.AlignmentFlag.AlignCenter, self.title)
        
        # Draw chart background
        chart_rect = self.rect().adjusted(margin, margin + 20, -margin, -margin)
        painter.fillRect(chart_rect, QColor("#262626"))
        
        # Draw grid lines
        painter.setPen(QPen(QColor("#3E3E42"), 1, Qt.PenStyle.SolidLine))
        
        # Horizontal grid lines (5 lines)
        for i in range(6):
            y = chart_rect.top() + i * chart_height / 5
            painter.drawLine(chart_rect.left(), int(y), chart_rect.right(), int(y))
        
        # Vertical grid lines (10 lines)
        for i in range(11):
            x = chart_rect.left() + i * chart_width / 10
            painter.drawLine(int(x), chart_rect.top(), int(x), chart_rect.bottom())
        
        # Draw data points
        if len(self.data_points) < 2:
            return
        
        # Calculate value range
        value_range = self.max_value - self.min_value
        if value_range == 0:
            value_range = 1  # Avoid division by zero
        
        # Draw line
        painter.setPen(QPen(self.line_color, 2, Qt.PenStyle.SolidLine))
        
        path_points = []
        for i, value in enumerate(self.data_points):
            x = chart_rect.left() + i * chart_width / (len(self.data_points) - 1)
            y = chart_rect.bottom() - ((value - self.min_value) / value_range) * chart_height
            path_points.append((x, y))
        
        for i in range(len(path_points) - 1):
            painter.drawLine(int(path_points[i][0]), int(path_points[i][1]), 
                            int(path_points[i+1][0]), int(path_points[i+1][1]))
        
        # Fill area under the line
        painter.setPen(Qt.PenStyle.NoPen)
        gradient = QLinearGradient(0, chart_rect.top(), 0, chart_rect.bottom())
        gradient.setColorAt(0, QColor(38, 166, 154, 100))
        gradient.setColorAt(1, QColor(38, 166, 154, 10))
        gradient.setSpread(QGradient.Spread.PadSpread)
        painter.setBrush(QBrush(gradient))
        
        # Create QPolygonF directly with all points
        polygon = QPolygonF()
        
        # First point (bottom-left)
        polygon.append(QPointF(chart_rect.left(), chart_rect.bottom()))
        
        # Add all data points
        for point in path_points:
            polygon.append(QPointF(point[0], point[1]))
        
        # Last point (bottom-right)
        polygon.append(QPointF(chart_rect.right(), chart_rect.bottom()))
        
        # Draw the polygon
        painter.drawPolygon(polygon)

class PerformanceMetricsWidget(QWidget):
    """
    Widget for displaying trading performance metrics and visualizations.
    Shows key performance indicators like Sharpe ratio, drawdown, etc.
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
        
        # Header with time period selector
        self.header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Performance Analytics")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        
        self.period_label = QLabel("Time Period:")
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Today", "This Week", "This Month", "This Year", "All Time"])
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch(1)
        self.header_layout.addWidget(self.period_label)
        self.header_layout.addWidget(self.period_combo)
        
        # Key metrics gauges
        self.gauges_layout = QHBoxLayout()
        
        # Sharpe Ratio gauge
        self.sharpe_gauge = MetricGaugeWidget("Sharpe Ratio")
        self.sharpe_gauge.set_range(0, 3)
        self.sharpe_gauge.set_color_zones([
            (0, 33, QColor("#EF5350")),    # < 1 (Poor)
            (33, 66, QColor("#FFC107")),   # 1-2 (Good)
            (66, 100, QColor("#26A69A"))   # > 2 (Excellent)
        ])
        
        # Profit Factor gauge
        self.profit_factor_gauge = MetricGaugeWidget("Profit Factor")
        self.profit_factor_gauge.set_range(0, 3)
        self.profit_factor_gauge.set_color_zones([
            (0, 33, QColor("#EF5350")),    # < 1 (Losing)
            (33, 50, QColor("#FFC107")),   # 1-1.5 (Marginal)
            (50, 100, QColor("#26A69A"))   # > 1.5 (Profitable)
        ])
        
        # Win Rate gauge
        self.win_rate_gauge = MetricGaugeWidget("Win Rate")
        self.win_rate_gauge.set_range(0, 100)
        self.win_rate_gauge.set_color_zones([
            (0, 40, QColor("#EF5350")),    # < 40% (Poor)
            (40, 60, QColor("#FFC107")),   # 40-60% (Average)
            (60, 100, QColor("#26A69A"))   # > 60% (Good)
        ])
        
        # Add gauges to layout
        self.gauges_layout.addWidget(self.sharpe_gauge)
        self.gauges_layout.addWidget(self.profit_factor_gauge)
        self.gauges_layout.addWidget(self.win_rate_gauge)
        
        # Performance charts
        self.charts_layout = QVBoxLayout()
        
        # Equity curve
        self.equity_chart = LineChartWidget("Equity Curve")
        
        # Drawdown chart
        self.drawdown_chart = LineChartWidget("Drawdown")
        self.drawdown_chart.line_color = QColor("#EF5350")
        
        # Add charts to layout
        self.charts_layout.addWidget(self.equity_chart)
        self.charts_layout.addWidget(self.drawdown_chart)
        
        # Additional metrics table
        self.metrics_table = QTableWidget(6, 2)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.metrics_table.verticalHeader().setVisible(False)
        self.metrics_table.setShowGrid(False)
        self.metrics_table.setStyleSheet("""
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
        
        # Add all components to main layout
        self.layout.addLayout(self.header_layout)
        self.layout.addLayout(self.gauges_layout)
        self.layout.addLayout(self.charts_layout)
        self.layout.addWidget(self.metrics_table)
        
    def on_period_changed(self, period):
        """Handle time period selection change"""
        self.load_sample_data(period)
        
    def load_sample_data(self, period="This Month"):
        """Load sample performance data for demonstration"""
        # Generate random performance metrics based on selected period
        
        # For demonstration, we'll use different metrics for different periods
        if period == "Today":
            sharpe = random.uniform(0.5, 1.5)
            profit_factor = random.uniform(0.8, 1.5)
            win_rate = random.uniform(35, 55)
            max_drawdown = random.uniform(1, 3)
            total_trades = random.randint(5, 20)
        elif period == "This Week":
            sharpe = random.uniform(0.8, 2.0)
            profit_factor = random.uniform(1.0, 1.8)
            win_rate = random.uniform(40, 60)
            max_drawdown = random.uniform(2, 5)
            total_trades = random.randint(20, 50)
        elif period == "This Month":
            sharpe = random.uniform(1.0, 2.5)
            profit_factor = random.uniform(1.2, 2.0)
            win_rate = random.uniform(45, 65)
            max_drawdown = random.uniform(3, 8)
            total_trades = random.randint(50, 150)
        elif period == "This Year":
            sharpe = random.uniform(1.5, 2.8)
            profit_factor = random.uniform(1.5, 2.5)
            win_rate = random.uniform(50, 70)
            max_drawdown = random.uniform(5, 15)
            total_trades = random.randint(200, 600)
        else:  # All Time
            sharpe = random.uniform(1.8, 3.0)
            profit_factor = random.uniform(1.8, 3.0)
            win_rate = random.uniform(55, 75)
            max_drawdown = random.uniform(8, 20)
            total_trades = random.randint(500, 1500)
        
        # Update gauges
        self.sharpe_gauge.set_value(sharpe)
        self.profit_factor_gauge.set_value(profit_factor)
        self.win_rate_gauge.set_value(win_rate)
        
        # Generate equity curve data
        equity_data = []
        initial_equity = 10000
        current_equity = initial_equity
        
        points = 100
        for i in range(points):
            # Random daily return based on performance characteristics
            daily_return = random.normalvariate(
                (profit_factor - 1) * 0.1 / points,  # Expected return
                0.2 / math.sqrt(points)  # Volatility
            )
            current_equity *= (1 + daily_return)
            equity_data.append(current_equity)
        
        self.equity_chart.set_data(equity_data)
        
        # Calculate drawdowns
        drawdown_data = []
        peak = equity_data[0]
        
        for equity in equity_data:
            peak = max(peak, equity)
            drawdown = (peak - equity) / peak * 100
            drawdown_data.append(drawdown)
        
        self.drawdown_chart.set_data(drawdown_data)
        
        # Update metrics table
        metrics = [
            ("Total Return", f"{(current_equity / initial_equity - 1) * 100:.2f}%"),
            ("Sharpe Ratio", f"{sharpe:.2f}"),
            ("Win Rate", f"{win_rate:.2f}%"),
            ("Profit Factor", f"{profit_factor:.2f}"),
            ("Max Drawdown", f"{max(drawdown_data):.2f}%"),
            ("Total Trades", str(total_trades))
        ]
        
        for i, (metric, value) in enumerate(metrics):
            # Metric name
            metric_item = QTableWidgetItem(metric)
            self.metrics_table.setItem(i, 0, metric_item)
            
            # Metric value
            value_item = QTableWidgetItem(value)
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Color code certain metrics
            if metric == "Sharpe Ratio":
                if sharpe < 1:
                    value_item.setForeground(QColor("#EF5350"))
                elif sharpe < 2:
                    value_item.setForeground(QColor("#FFC107"))
                else:
                    value_item.setForeground(QColor("#26A69A"))
            elif metric == "Win Rate":
                if win_rate < 40:
                    value_item.setForeground(QColor("#EF5350"))
                elif win_rate < 60:
                    value_item.setForeground(QColor("#FFC107"))
                else:
                    value_item.setForeground(QColor("#26A69A"))
            elif metric == "Profit Factor":
                if profit_factor < 1:
                    value_item.setForeground(QColor("#EF5350"))
                elif profit_factor < 1.5:
                    value_item.setForeground(QColor("#FFC107"))
                else:
                    value_item.setForeground(QColor("#26A69A"))
            
            self.metrics_table.setItem(i, 1, value_item)
