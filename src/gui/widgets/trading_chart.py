#!/usr/bin/env python3
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class TradingChartWidget(QWidget):
    """
    Advanced trading chart widget that displays price action, volume, and indicators
    using Plotly for high-quality, interactive visualizations.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(400)
        
        # Sample data for demonstration
        self.sample_data_loaded = False
        
        # Initialize UI
        self.init_ui()
        
        # Load sample data for demonstration
        self.load_sample_data()
        
    def init_ui(self):
        """Initialize the user interface components"""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with controls
        self.header = QWidget()
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(5, 5, 5, 5)
        
        # Chart type selector
        self.chart_type_label = QLabel("Chart Type:")
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["Candlestick", "OHLC", "Line", "Area"])
        self.chart_type_combo.currentTextChanged.connect(self.update_chart)
        
        # Timeframe selector
        self.timeframe_label = QLabel("Timeframe:")
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["1m", "5m", "15m", "1h", "4h", "1d"])
        self.timeframe_combo.setCurrentText("15m")
        self.timeframe_combo.currentTextChanged.connect(self.update_chart)
        
        # Indicator selector
        self.indicator_label = QLabel("Indicators:")
        self.indicator_combo = QComboBox()
        self.indicator_combo.addItems(["None", "MA", "EMA", "MACD", "RSI", "Bollinger Bands"])
        self.indicator_combo.currentTextChanged.connect(self.update_chart)
        
        # Add widgets to header layout
        self.header_layout.addWidget(self.chart_type_label)
        self.header_layout.addWidget(self.chart_type_combo)
        self.header_layout.addWidget(self.timeframe_label)
        self.header_layout.addWidget(self.timeframe_combo)
        self.header_layout.addWidget(self.indicator_label)
        self.header_layout.addWidget(self.indicator_combo)
        self.header_layout.addStretch(1)
        
        # Chart container
        self.chart_container = QFrame()
        self.chart_container.setFrameShape(QFrame.Shape.StyledPanel)
        self.chart_container.setStyleSheet("background-color: #1E1E1E;")
        self.chart_container.setMinimumHeight(350)
        
        self.chart_layout = QVBoxLayout(self.chart_container)
        self.chart_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add placeholder text
        self.chart_placeholder = QLabel("Chart loading...")
        self.chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chart_layout.addWidget(self.chart_placeholder)
        
        # Add components to main layout
        self.layout.addWidget(self.header)
        self.layout.addWidget(self.chart_container)
    
    def load_sample_data(self):
        """Load sample data for demonstration purposes"""
        # Generate sample price data
        np.random.seed(42)
        
        # Create date range for the past 30 days with 15-minute intervals
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Generate dates (15-minute intervals)
        date_range = pd.date_range(start=start_date, end=end_date, freq='15min')
        
        # Generate prices
        base_price = 50000  # Starting price in USD
        daily_volatility = 0.02  # 2% daily volatility
        
        # Convert daily volatility to 15-minute volatility
        interval_volatility = daily_volatility / np.sqrt(4 * 24)  # 4 15-minute intervals per hour * 24 hours
        
        # Generate price series with random walk
        log_returns = np.random.normal(0, interval_volatility, size=len(date_range))
        log_prices = np.cumsum(log_returns) + np.log(base_price)
        prices = np.exp(log_prices)
        
        # Create OHLC data
        opens = prices.copy()
        
        # Generate high, low, and close prices relative to open
        highs = opens * np.exp(np.random.normal(0.001, interval_volatility / 2, size=len(opens)))
        lows = opens * np.exp(np.random.normal(-0.001, interval_volatility / 2, size=len(opens)))
        closes = prices * np.exp(np.random.normal(0, interval_volatility / 4, size=len(opens)))
        
        # Make sure high is always the highest and low is always the lowest
        for i in range(len(opens)):
            max_price = max(opens[i], closes[i])
            min_price = min(opens[i], closes[i])
            highs[i] = max(highs[i], max_price)
            lows[i] = min(lows[i], min_price)
        
        # Generate volumes (higher on price movements)
        price_changes = np.abs(np.diff(np.append(base_price, closes)))
        volumes = np.random.normal(100000, 50000, size=len(closes)) * (1 + 5 * price_changes / base_price)
        
        # Create DataFrame
        self.df = pd.DataFrame({
            'timestamp': date_range,
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes
        })
        
        self.sample_data_loaded = True
        self.update_chart()
        
    def update_chart(self):
        """Update the chart based on current settings"""
        if not self.sample_data_loaded:
            return
        
        # Create figure with secondary y-axis for volume
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.03, 
                           row_heights=[0.7, 0.3],
                           subplot_titles=('BTC/USDT', 'Volume'))
        
        # Get current chart type
        chart_type = self.chart_type_combo.currentText()
        
        # Parse data for chart
        df = self.df[-200:]  # Show last 200 data points for demonstration
        
        # Add appropriate traces based on chart type
        if chart_type == "Candlestick":
            fig.add_trace(
                go.Candlestick(
                    x=df['timestamp'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    increasing_line_color='#26A69A', 
                    decreasing_line_color='#EF5350',
                    name='Price'
                ),
                row=1, col=1
            )
        elif chart_type == "OHLC":
            fig.add_trace(
                go.Ohlc(
                    x=df['timestamp'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    increasing_line_color='#26A69A', 
                    decreasing_line_color='#EF5350',
                    name='Price'
                ),
                row=1, col=1
            )
        elif chart_type == "Line":
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['close'],
                    line=dict(color='#2196F3', width=2),
                    name='Price'
                ),
                row=1, col=1
            )
        elif chart_type == "Area":
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['close'],
                    fill='tozeroy',
                    fillcolor='rgba(33, 150, 243, 0.3)',
                    line=dict(color='#2196F3', width=2),
                    name='Price'
                ),
                row=1, col=1
            )
        
        # Add volume bars
        # Fix for DataFrame indexing - use df.iloc for integer-based indexing
        colors = ['#26A69A' if df['close'].iloc[i] >= df['open'].iloc[i] else '#EF5350' for i in range(len(df))]
        
        fig.add_trace(
            go.Bar(
                x=df['timestamp'],
                y=df['volume'],
                marker_color=colors,
                name='Volume'
            ),
            row=2, col=1
        )
        
        # Add indicators if selected
        indicator = self.indicator_combo.currentText()
        
        if indicator == "MA":
            # Add 20 and 50 period moving averages
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['close'].rolling(window=20).mean(),
                    line=dict(color='#FFA726', width=1),
                    name='MA (20)'
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['close'].rolling(window=50).mean(),
                    line=dict(color='#AB47BC', width=1),
                    name='MA (50)'
                ),
                row=1, col=1
            )
        elif indicator == "EMA":
            # Add 20 and 50 period exponential moving averages
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['close'].ewm(span=20, adjust=False).mean(),
                    line=dict(color='#FFA726', width=1),
                    name='EMA (20)'
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['close'].ewm(span=50, adjust=False).mean(),
                    line=dict(color='#AB47BC', width=1),
                    name='EMA (50)'
                ),
                row=1, col=1
            )
        elif indicator == "Bollinger Bands":
            # Calculate Bollinger Bands (20-period, 2 standard deviations)
            window = 20
            sma = df['close'].rolling(window=window).mean()
            std = df['close'].rolling(window=window).std()
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)
            
            # Add Bollinger Bands to chart
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=upper_band,
                    line=dict(color='rgba(250, 170, 10, 0.75)', width=1),
                    name='Upper BB'
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=sma,
                    line=dict(color='rgba(250, 170, 10, 1)', width=1),
                    name='SMA (20)'
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=lower_band,
                    line=dict(color='rgba(250, 170, 10, 0.75)', width=1),
                    name='Lower BB'
                ),
                row=1, col=1
            )
        elif indicator == "RSI":
            # Calculate RSI (14-period)
            window = 14
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=window).mean()
            avg_loss = loss.rolling(window=window).mean()
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            # Add RSI to chart as a separate subplot
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                               vertical_spacing=0.03, 
                               row_heights=[0.6, 0.2, 0.2],
                               subplot_titles=('BTC/USDT', 'Volume', 'RSI (14)'))
            
            # Re-add the price chart
            if chart_type == "Candlestick":
                fig.add_trace(
                    go.Candlestick(
                        x=df['timestamp'],
                        open=df['open'],
                        high=df['high'],
                        low=df['low'],
                        close=df['close'],
                        increasing_line_color='#26A69A', 
                        decreasing_line_color='#EF5350',
                        name='Price'
                    ),
                    row=1, col=1
                )
            
            # Re-add volume
            fig.add_trace(
                go.Bar(
                    x=df['timestamp'],
                    y=df['volume'],
                    marker_color=colors,
                    name='Volume'
                ),
                row=2, col=1
            )
            
            # Add RSI
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=rsi,
                    line=dict(color='#9C27B0', width=1),
                    name='RSI (14)'
                ),
                row=3, col=1
            )
            
            # Add RSI reference lines (30 and 70)
            fig.add_shape(
                type="line",
                x0=df['timestamp'].iloc[0],
                y0=30,
                x1=df['timestamp'].iloc[-1],
                y1=30,
                line=dict(color="red", width=1, dash="dash"),
                row=3, col=1
            )
            
            fig.add_shape(
                type="line",
                x0=df['timestamp'].iloc[0],
                y0=70,
                x1=df['timestamp'].iloc[-1],
                y1=70,
                line=dict(color="red", width=1, dash="dash"),
                row=3, col=1
            )
            
            # Update y-axis range for RSI
            fig.update_yaxes(range=[0, 100], row=3, col=1)
        
        # Update layout for better visualization
        fig.update_layout(
            title=f'BTC/USDT - {self.timeframe_combo.currentText()}',
            template='plotly_dark',
            plot_bgcolor='#1E1E1E',
            paper_bgcolor='#1E1E1E',
            font=dict(color='#E0E0E0'),
            xaxis_rangeslider_visible=False,
            height=500,
            margin=dict(l=50, r=50, t=50, b=50),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Update X axis to show date in appropriate format
        fig.update_xaxes(
            rangebreaks=[dict(bounds=["sat", "mon"])],
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.1)'
        )
        
        # Update Y axis
        fig.update_yaxes(
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.1)',
            zeroline=False
        )
        
        # Convert the figure to HTML
        chart_html = fig.to_html(include_plotlyjs='cdn', config={'responsive': True})
        
        # Create HTML file (this is a temporary solution - in a real app we'd use QWebEngineView)
        with open('temp_chart.html', 'w') as f:
            f.write(chart_html)
        
        # Instead of showing the actual chart (which would require QWebEngineView),
        # we'll display a placeholder message in this example
        self.chart_placeholder.setText(f"Interactive {chart_type} chart with {indicator} indicator would display here.\nIn a complete implementation, this would use QWebEngineView to display the Plotly chart.")
