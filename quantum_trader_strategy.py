"""
Quantum Trading Strategy - Core Trading Logic for BumBot

This module integrates quantum computing analysis with L2 blockchain execution
to implement advanced trading strategies optimized for Arbitrum and Polygon.
"""
from quantum_orchestrator import QuantumOrchestrator
from metamask_trader import MetaMaskTrader
from chainstack_provider import ChainstackProvider
import pandas as pd
import numpy as np
import json
import logging
import os
import time
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/strategy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('strategy')

class QuantumTradingStrategy:
    """
    Implements quantum-enhanced trading strategies optimized for 
    L2 networks (Arbitrum and Polygon)
    """
    
    def __init__(self):
        self.quantum = QuantumOrchestrator()
        self.metamask = MetaMaskTrader()
        self.chainstack = ChainstackProvider()
        
        # Strategy parameters
        self.default_trade_amount = 0.01  # Small amount for testing
        self.default_slippage = 0.01  # 1% slippage
        self.risk_level = "medium"  # low, medium, high
        
        # Trading tokens with token addresses dynamically loaded
        self.trading_pairs = {
            "arbitrum": [
                {"base": "ETH", "quote": "USDC"},
                {"base": "LINK", "quote": "ETH"}
            ],
            "polygon": [
                {"base": "MATIC", "quote": "USDC"},
                {"base": "WETH", "quote": "MATIC"}
            ]
        }
        
        # Initialize market data cache
        self.market_data = {}
        
        # Trading history
        self.trade_history_file = 'logs/trade_history.json'
        self.trade_history = self._load_trade_history()
        
        logger.info("Quantum Trading Strategy initialized with providers: IBM Quantum, Chainstack")
        
    def _load_trade_history(self):
        """Load trade history from file"""
        if os.path.exists(self.trade_history_file):
            try:
                with open(self.trade_history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load trade history: {str(e)}")
                
        return []
        
    def _save_trade_history(self):
        """Save trade history to file"""
        try:
            os.makedirs(os.path.dirname(self.trade_history_file), exist_ok=True)
            with open(self.trade_history_file, 'w') as f:
                json.dump(self.trade_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save trade history: {str(e)}")
            
    def _fetch_token_price(self, token_symbol, vs_currency="usd"):
        """Fetch token price from CoinGecko (or similar API)"""
        # In production, you would use a paid API with better rate limits
        # This is a simplified example using CoinGecko's free API
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_symbol.lower()}&vs_currencies={vs_currency}"
            response = requests.get(url)
            data = response.json()
            return data.get(token_symbol.lower(), {}).get(vs_currency)
        except Exception as e:
            logger.error(f"Error fetching price for {token_symbol}: {str(e)}")
            return None
            
    def _get_market_data(self, network, token_symbol, lookback_days=30):
        """
        Get market data for token including price and metrics
        
        In production, this would use a proper market data provider API
        with historical OHLCV data. This is a simplified mock implementation.
        """
        # Check cache first
        cache_key = f"{network}_{token_symbol}"
        if cache_key in self.market_data and datetime.now() - self.market_data[cache_key]["timestamp"] < timedelta(minutes=15):
            return self.market_data[cache_key]["data"]
            
        # Mock data generation
        np.random.seed(int(time.time()) % 1000)
        
        # Get current price (or use mock)
        current_price = self._fetch_token_price(token_symbol) or np.random.uniform(10, 2000)
        
        # Generate mock price history
        days = lookback_days
        price_history = [current_price]
        volatility = 0.02  # 2% daily volatility
        
        for i in range(1, days):
            daily_return = np.random.normal(0, volatility)
            previous_price = price_history[-1]
            new_price = previous_price * (1 + daily_return)
            price_history.append(new_price)
            
        price_history.reverse()  # oldest first
        
        # Calculate mock indicators
        price_changes = [price_history[i]/price_history[i-1] - 1 for i in range(1, len(price_history))]
        
        rsi_period = 14
        gains = [max(0, change) for change in price_changes[-rsi_period:]]
        losses = [max(0, -change) for change in price_changes[-rsi_period:]]
        
        avg_gain = sum(gains) / rsi_period if gains else 0
        avg_loss = sum(losses) / rsi_period if losses else 0.001  # Avoid division by zero
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Calculate volatility
        volatility_estimate = np.std(price_changes) * 100  # as percentage
        
        # Recent price change
        recent_change = ((price_history[-1] / price_history[-7]) - 1) * 100  # 7-day change
        
        market_data = {
            "price": current_price,
            "volume": np.random.uniform(1e6, 5e7),  # Mock 24h volume
            "market_cap": current_price * np.random.uniform(1e6, 1e9),  # Mock market cap
            "price_history": price_history,
            "24h_change": ((price_history[-1] / price_history[-2]) - 1) * 100,
            "7d_change": recent_change,
            "volatility": volatility_estimate,
            "rsi": rsi
        }
        
        # Cache data
        self.market_data[cache_key] = {
            "data": market_data,
            "timestamp": datetime.now()
        }
        
        return market_data
        
    def analyze_market_conditions(self, network, base_token, quote_token):
        """Analyze market conditions for a trading pair"""
        base_data = self._get_market_data(network, base_token)
        quote_data = self._get_market_data(network, quote_token)
        
        # Compare relative strength
        relative_strength = base_data["rsi"] - quote_data["rsi"]
        
        # Recent performance differential
        performance_diff = base_data["7d_change"] - quote_data["7d_change"]
        
        # Volatility comparison
        volatility_ratio = base_data["volatility"] / max(0.01, quote_data["volatility"])
        
        # Determine market regime
        if base_data["rsi"] > 70:
            regime = "overbought"
        elif base_data["rsi"] < 30:
            regime = "oversold"
        elif abs(base_data["24h_change"]) > 5:
            regime = "trending"
        else:
            regime = "ranging"
            
        return {
            "base_token": {
                "symbol": base_token,
                "price": base_data["price"],
                "rsi": base_data["rsi"],
                "24h_change": base_data["24h_change"]
            },
            "quote_token": {
                "symbol": quote_token,
                "price": quote_data["price"],
                "rsi": quote_data["rsi"],
                "24h_change": quote_data["24h_change"]
            },
            "relative_strength": relative_strength,
            "performance_diff": performance_diff,
            "volatility_ratio": volatility_ratio,
            "market_regime": regime
        }
        
    def select_quantum_circuit(self, market_analysis):
        """Select appropriate quantum circuit based on market conditions"""
        regime = market_analysis["market_regime"]
        
        if regime == "trending":
            # For trending markets, use momentum circuit
            trend_value = market_analysis["base_token"]["24h_change"] / 10  # Normalize to -1 to 1
            volatility = min(1.0, market_analysis["volatility_ratio"] / 5)  # Normalize to 0 to 1
            
            circuit = self.quantum.create_momentum_circuit(trend_value, volatility)
            strategy_type = "momentum"
            
        elif regime in ["overbought", "oversold"]:
            # For overbought/oversold, use mean reversion
            # Extract recent price history for circuit
            historical_data = self._get_market_data(
                "arbitrum", market_analysis["base_token"]["symbol"]
            )["price_history"]
            
            # Normalize to -1 to 1 scale
            data_points = 4
            prices = historical_data[-data_points:]
            min_price = min(prices)
            max_price = max(prices)
            price_range = max_price - min_price if max_price > min_price else 1
            
            normalized_prices = [(p - min_price) / price_range * 2 - 1 for p in prices]
            
            circuit = self.quantum.create_price_prediction_circuit(normalized_prices)
            strategy_type = "mean_reversion"
            
        else:  # ranging market
            # Use simple Bell circuit for ranging markets
            circuit = self.quantum.create_bell_circuit()
            strategy_type = "ranging"
            
        return {
            "circuit": circuit,
            "strategy_type": strategy_type,
            "market_regime": regime
        }
        
    def execute_quantum_analysis(self, network, base_token, quote_token):
        """Execute full quantum analysis for a trading pair"""
        logger.info(f"Analyzing {base_token}/{quote_token} on {network}")
        
        # Step 1: Analyze market conditions
        market_analysis = self.analyze_market_conditions(network, base_token, quote_token)
        logger.info(f"Market regime: {market_analysis['market_regime']}, RSI: {market_analysis['base_token']['rsi']:.2f}")
        
        # Step 2: Select and prepare quantum circuit
        circuit_info = self.select_quantum_circuit(market_analysis)
        
        # Step 3: Execute quantum circuit
        circuit = circuit_info["circuit"]
        logger.info(f"Executing quantum circuit for {circuit_info['strategy_type']} strategy...")
        
        quantum_result = self.quantum.execute_circuit(circuit)
        
        if "error" in quantum_result:
            logger.error(f"Quantum execution error: {quantum_result['error']}")
            return {
                "error": quantum_result["error"],
                "market_analysis": market_analysis
            }
            
        # Step 4: Interpret results
        if circuit_info["strategy_type"] == "momentum":
            trading_signal = self.quantum.interpret_momentum_results(quantum_result)
        elif circuit_info["strategy_type"] == "mean_reversion":
            # For mean reversion, interpret differently
            probabilities = quantum_result.get("probabilities", {})
            
            # A measurement of 1 suggests reversion (sell if up, buy if down)
            reversion_probability = probabilities.get("1", 0)
            continuation_probability = probabilities.get("0", 0)
            
            # RSI over 70 = overbought, under 30 = oversold
            is_overbought = market_analysis["base_token"]["rsi"] > 70
            is_oversold = market_analysis["base_token"]["rsi"] < 30
            
            if is_overbought and reversion_probability > 0.6:
                action = "SELL"
                confidence = reversion_probability
            elif is_oversold and reversion_probability > 0.6:
                action = "BUY"
                confidence = reversion_probability
            else:
                action = "HOLD"
                confidence = max(continuation_probability, 1 - reversion_probability)
                
            trading_signal = {
                "buy": 0.8 if action == "BUY" else 0.0,
                "sell": 0.8 if action == "SELL" else 0.0,
                "hold": 0.8 if action == "HOLD" else 0.2,
                "recommended_action": action,
                "confidence": confidence,
                "quantum_result": quantum_result
            }
        else:
            # For ranging/bell state, interpret based on probabilities
            probabilities = quantum_result.get("probabilities", {})
            state_00 = probabilities.get("0", 0)  # |00⟩ state
            state_01 = probabilities.get("1", 0)  # |01⟩ state
            state_10 = probabilities.get("2", 0)  # |10⟩ state
            state_11 = probabilities.get("3", 0)  # |11⟩ state
            
            # Simple interpretation: |00⟩ = buy, |11⟩ = sell, others = hold
            action = "HOLD"
            confidence = max(state_01, state_10)
            
            if state_00 > 0.6:
                action = "BUY"
                confidence = state_00
            elif state_11 > 0.6:
                action = "SELL"
                confidence = state_11
                
            trading_signal = {
                "buy": state_00,
                "sell": state_11,
                "hold": state_01 + state_10,
                "recommended_action": action,
                "confidence": confidence,
                "quantum_result": quantum_result
            }
            
        logger.info(f"Trading signal: {trading_signal['recommended_action']} with {trading_signal['confidence']:.2f} confidence")
        
        # Return complete analysis
        return {
            "market_analysis": market_analysis,
            "strategy_type": circuit_info["strategy_type"],
            "quantum_result": {
                "backend": quantum_result.get("backend", "unknown"),
                "job_id": quantum_result.get("job_id", "unknown"),
                "execution_time": quantum_result.get("execution_time", 0),
                "probabilities": quantum_result.get("probabilities", {})
            },
            "trading_signal": trading_signal
        }
        
    def execute_trade(self, network, base_token, quote_token, analysis=None, amount=None):
        """Execute trade based on quantum analysis"""
        # Get fresh analysis if not provided
        if analysis is None:
            analysis = self.execute_quantum_analysis(network, base_token, quote_token)
            
        if "error" in analysis:
            return {"error": analysis["error"]}
            
        # Determine action from trading signal
        signal = analysis["trading_signal"]
        action = signal["recommended_action"]
        confidence = signal["confidence"]
        
        # Set trade amount
        if amount is None:
            # Scale amount based on confidence
            confidence_scaling = 0.5 + (confidence * 0.5)  # 0.5 to 1.0
            amount = self.default_trade_amount * confidence_scaling
            
        # Skip trade if confidence is too low or action is HOLD
        if confidence < 0.6 or action == "HOLD":
            logger.info(f"No trade: {action} signal with {confidence:.2f} confidence")
            return {
                "status": "no_trade",
                "reason": f"{action} signal with {confidence:.2f} confidence",
                "analysis": analysis
            }
            
        # Check wallet balances
        balances = self.metamask.get_wallet_balances()
        if "error" in balances.get(network, {}):
            return {"error": f"Error checking balances: {balances[network]['error']}"}
            
        # Determine tokens for the swap
        network_specs = self.chainstack.get_network_specs(network)
        
        if action == "BUY":
            from_token = quote_token
            to_token = base_token
        else:  # SELL
            from_token = base_token
            to_token = quote_token
            
        # Check if we have token addresses
        if from_token not in network_specs["tokens"]:
            return {"error": f"Token {from_token} not configured for {network}"}
        if to_token not in network_specs["tokens"]:
            return {"error": f"Token {to_token} not configured for {network}"}
            
        from_token_address = network_specs["tokens"][from_token]
        to_token_address = network_specs["tokens"][to_token]
        
        # Check if we have enough balance
        from_token_balance = balances.get(network, {}).get("tokens", {}).get(from_token, {}).get("balance", 0)
        if from_token_balance < amount:
            logger.warning(f"Insufficient balance: {from_token_balance} {from_token}, needed {amount}")
            # Adjust amount to available balance (minus a small buffer)
            amount = from_token_balance * 0.95
            
        if amount <= 0:
            return {"error": "Zero or negative trade amount after adjustment"}
            
        # Execute the swap
        logger.info(f"Executing {action}: Swap {amount} {from_token} to {to_token} on {network}")
        swap_result = self.metamask.execute_swap(
            network, from_token, to_token, amount, self.default_slippage
        )
        
        # Record trade in history
        trade_record = {
            "timestamp": datetime.now().isoformat(),
            "network": network,
            "action": action,
            "from_token": from_token,
            "to_token": to_token,
            "amount": amount,
            "confidence": confidence,
            "strategy_type": analysis["strategy_type"],
            "market_regime": analysis["market_analysis"]["market_regime"],
            "tx_hash": swap_result.get("tx_hash", "unknown"),
            "status": swap_result.get("status", "error"),
            "quantum_backend": analysis["quantum_result"]["backend"]
        }
        
        self.trade_history.append(trade_record)
        self._save_trade_history()
        
        return {
            "trade_result": swap_result,
            "analysis": analysis,
            "trade_record": trade_record
        }

    def run_trading_cycle(self, network=None):
        """Run complete trading cycle for all configured pairs"""
        if network is None:
            networks = ["arbitrum", "polygon"]
        else:
            networks = [network]
            
        results = {}
        
        for net in networks:
            results[net] = {}
            pairs = self.trading_pairs.get(net, [])
            
            for pair in pairs:
                base = pair["base"]
                quote = pair["quote"]
                
                logger.info(f"Trading cycle: {base}/{quote} on {net}")
                
                try:
                    # Execute analysis
                    analysis = self.execute_quantum_analysis(net, base, quote)
                    
                    # Execute trade if analysis successful
                    if "error" not in analysis:
                        trade_result = self.execute_trade(net, base, quote, analysis)
                        results[net][f"{base}/{quote}"] = {
                            "analysis": analysis,
                            "trade_result": trade_result
                        }
                    else:
                        results[net][f"{base}/{quote}"] = {"error": analysis["error"]}
                        
                except Exception as e:
                    error_msg = f"Error in trading cycle for {base}/{quote} on {net}: {str(e)}"
                    logger.error(error_msg)
                    results[net][f"{base}/{quote}"] = {"error": error_msg}
                    
        return results
        
    def get_performance_metrics(self):
        """Calculate performance metrics from trade history"""
        if not self.trade_history:
            return {"error": "No trade history available"}
            
        # Count successful and failed trades
        total_trades = len(self.trade_history)
        successful_trades = sum(1 for t in self.trade_history if t.get("status") == "success")
        
        # Group by strategy type
        strategy_counts = {}
        for trade in self.trade_history:
            strategy = trade.get("strategy_type", "unknown")
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            
        # Group by network
        network_counts = {}
        for trade in self.trade_history:
            network = trade.get("network", "unknown")
            network_counts[network] = network_counts.get(network, 0) + 1
            
        # Group by quantum backend
        backend_counts = {}
        for trade in self.trade_history:
            backend = trade.get("quantum_backend", "unknown")
            backend_counts[backend] = backend_counts.get(backend, 0) + 1
            
        return {
            "total_trades": total_trades,
            "successful_trades": successful_trades,
            "success_rate": successful_trades / total_trades if total_trades > 0 else 0,
            "strategies": strategy_counts,
            "networks": network_counts,
            "quantum_backends": backend_counts,
            "first_trade": self.trade_history[0]["timestamp"] if self.trade_history else None,
            "last_trade": self.trade_history[-1]["timestamp"] if self.trade_history else None
        }

# Test function
if __name__ == "__main__":
    strategy = QuantumTradingStrategy()
    
    # Check wallet configuration
    balances = strategy.metamask.get_wallet_balances()
    print(f"Wallet configured: {'True' if strategy.metamask.wallet_address else 'False'}")
    
    # Run test analysis
    if strategy.metamask.wallet_address:
        print("Running quantum analysis for ETH/USDC on Arbitrum...")
        analysis = strategy.execute_quantum_analysis("arbitrum", "ETH", "USDC")
        print(f"Analysis result: {json.dumps(analysis, indent=2)}")
    else:
        print("Please configure MetaMask wallet in .env file to run trading operations.")
