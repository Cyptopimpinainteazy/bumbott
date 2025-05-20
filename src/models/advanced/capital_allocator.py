#!/usr/bin/env python3
import time
import logging
import numpy as np
import copy
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class RiskModel:
    """Risk assessment and management model for portfolio allocation"""
    
    def __init__(self):
        """Initialize risk model"""
        self.volatility_cache = {}  # asset -> volatility data
        self.correlation_matrix = {}  # asset pairs -> correlation
        self.risk_factors = {}  # asset -> risk factors
        self.last_update = 0
        self.update_interval = 3600  # 1 hour
        
    async def assess_portfolio_risk(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risk factors for a portfolio of assets
        
        Args:
            portfolio: Current portfolio with assets and allocations
            
        Returns:
            Risk assessment for portfolio assets
        """
        # Check if update needed
        current_time = time.time()
        if current_time - self.last_update > self.update_interval:
            await self._update_risk_factors(portfolio)
            self.last_update = current_time
            
        # Get risk assessment for each asset
        risk_assessment = {}
        for asset, data in portfolio.items():
            risk_assessment[asset] = await self._assess_asset_risk(asset, data, portfolio)
            
        # Calculate portfolio-level metrics
        portfolio_risk = self._calculate_portfolio_risk(portfolio, risk_assessment)
        
        # Add portfolio-level risk metrics
        risk_assessment["_portfolio"] = portfolio_risk
        
        return risk_assessment
        
    async def _update_risk_factors(self, portfolio: Dict[str, Any]):
        """Update volatility and correlation data for assets"""
        # In a real implementation, this would fetch current market data
        # and calculate actual volatility and correlations
        
        # For development, use simulated values
        assets = list(portfolio.keys())
        
        # Update individual asset volatility
        for asset in assets:
            # Simulate volatility (different ranges for different asset types)
            if asset.endswith("BTC") or asset == "BTC":
                volatility = np.random.uniform(0.03, 0.08)  # 3-8% daily volatility
            elif asset.endswith("ETH") or asset == "ETH":
                volatility = np.random.uniform(0.04, 0.09)  # 4-9% daily volatility
            elif asset.endswith("USD") or asset.endswith("USDT") or asset.endswith("USDC"):
                volatility = np.random.uniform(0.001, 0.005)  # 0.1-0.5% for stablecoins
            else:
                volatility = np.random.uniform(0.05, 0.15)  # 5-15% for altcoins
                
            self.volatility_cache[asset] = {
                "daily_volatility": volatility,
                "weekly_volatility": volatility * np.sqrt(7),
                "monthly_volatility": volatility * np.sqrt(30),
                "timestamp": current_time
            }
            
        # Update correlation matrix
        for i, asset1 in enumerate(assets):
            for j, asset2 in enumerate(assets[i:]):
                if asset1 == asset2:
                    correlation = 1.0
                else:
                    # Simulate correlation between assets
                    # Stablecoins highly correlated with each other
                    if (asset1.endswith("USD") or asset1.endswith("USDT") or asset1.endswith("USDC")) and \
                       (asset2.endswith("USD") or asset2.endswith("USDT") or asset2.endswith("USDC")):
                        correlation = np.random.uniform(0.9, 0.99)
                    # BTC and ETH moderately correlated
                    elif (asset1 == "BTC" and asset2 == "ETH") or (asset1 == "ETH" and asset2 == "BTC"):
                        correlation = np.random.uniform(0.7, 0.9)
                    # Other crypto moderately to highly correlated
                    elif not (asset1.endswith("USD") or asset1.endswith("USDT") or asset1.endswith("USDC")) and \
                         not (asset2.endswith("USD") or asset2.endswith("USDT") or asset2.endswith("USDC")):
                        correlation = np.random.uniform(0.5, 0.9)
                    # Crypto to stablecoin low to negative correlation
                    else:
                        correlation = np.random.uniform(-0.2, 0.2)
                        
                # Store in correlation matrix
                pair_key = f"{asset1}:{asset2}"
                reverse_pair_key = f"{asset2}:{asset1}"
                self.correlation_matrix[pair_key] = correlation
                self.correlation_matrix[reverse_pair_key] = correlation
        
    async def _assess_asset_risk(self, asset: str, data: Dict[str, Any], portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk for a specific asset in the portfolio"""
        # Get volatility data
        if asset in self.volatility_cache:
            volatility_data = self.volatility_cache[asset]
        else:
            # Default values if no data
            volatility_data = {
                "daily_volatility": 0.05,
                "weekly_volatility": 0.13,
                "monthly_volatility": 0.27
            }
            
        # Calculate asset allocation percentage
        total_portfolio_value = sum(item.get("amount", 0) for item in portfolio.values())
        allocation_pct = data.get("amount", 0) / total_portfolio_value if total_portfolio_value > 0 else 0
        
        # Calculate value at risk (VaR)
        daily_var_95 = data.get("amount", 0) * volatility_data["daily_volatility"] * 1.645  # 95% confidence
        
        # Calculate asset-specific risk factor
        # Higher volatility = higher risk
        risk_factor = max(1.0, volatility_data["daily_volatility"] * 20)
        
        # Store risk factor
        self.risk_factors[asset] = risk_factor
        
        return {
            "volatility": volatility_data,
            "allocation_pct": allocation_pct,
            "daily_var_95": daily_var_95,
            "risk_factor": risk_factor
        }
        
    def _calculate_portfolio_risk(self, portfolio: Dict[str, Any], risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate portfolio-level risk metrics"""
        assets = [a for a in portfolio.keys()]
        
        if not assets:
            return {
                "portfolio_volatility": 0.0,
                "portfolio_var_95": 0.0,
                "diversification_score": 0.0,
                "risk_factor": 1.0
            }
            
        # Extract weights and volatilities
        weights = []
        volatilities = []
        for asset in assets:
            weight = risk_assessment[asset]["allocation_pct"]
            volatility = risk_assessment[asset]["volatility"]["daily_volatility"]
            weights.append(weight)
            volatilities.append(volatility)
            
        weights = np.array(weights)
        volatilities = np.array(volatilities)
        
        # Calculate portfolio volatility considering correlations
        portfolio_variance = 0.0
        for i, asset1 in enumerate(assets):
            for j, asset2 in enumerate(assets):
                pair_key = f"{asset1}:{asset2}"
                correlation = self.correlation_matrix.get(pair_key, 0.0 if asset1 != asset2 else 1.0)
                portfolio_variance += weights[i] * weights[j] * volatilities[i] * volatilities[j] * correlation
                
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        # Calculate portfolio VaR (95% confidence)
        total_value = sum(item.get("amount", 0) for item in portfolio.values())
        portfolio_var_95 = total_value * portfolio_volatility * 1.645
        
        # Calculate diversification score
        # Perfect diversification would reduce portfolio volatility significantly
        # compared to weighted average of individual volatilities
        weighted_avg_volatility = np.sum(weights * volatilities)
        diversification_score = 1.0 - (portfolio_volatility / weighted_avg_volatility) if weighted_avg_volatility > 0 else 0.0
        diversification_score = max(0.0, min(1.0, diversification_score))
        
        # Calculate portfolio risk factor 
        # Lower diversification = higher risk
        portfolio_risk_factor = 1.0 / (0.5 + diversification_score)
        
        return {
            "portfolio_volatility": portfolio_volatility,
            "portfolio_var_95": portfolio_var_95,
            "diversification_score": diversification_score,
            "risk_factor": portfolio_risk_factor
        }


class OpportunityEvaluator:
    """Evaluates trading opportunities for different assets"""
    
    def __init__(self):
        """Initialize opportunity evaluator"""
        self.opportunity_scores = {}
        self.last_evaluation = {}
        self.evaluation_validity = 1800  # 30 minutes
        
    async def evaluate_all_assets(self, assets: List[str]) -> Dict[str, float]:
        """
        Evaluate opportunity scores for a list of assets
        
        Args:
            assets: List of assets to evaluate
            
        Returns:
            Dictionary of opportunity scores for each asset
        """
        current_time = time.time()
        scores = {}
        
        for asset in assets:
            # Check if we have a recent evaluation
            if asset in self.last_evaluation:
                last_time, score = self.last_evaluation[asset]
                if current_time - last_time < self.evaluation_validity:
                    scores[asset] = score
                    continue
                    
            # Perform new evaluation
            scores[asset] = await self._evaluate_asset_opportunity(asset)
            
            # Store result
            self.last_evaluation[asset] = (current_time, scores[asset])
            self.opportunity_scores[asset] = scores[asset]
            
        return scores
        
    async def _evaluate_asset_opportunity(self, asset: str) -> float:
        """
        Evaluate opportunity score for a single asset
        
        Args:
            asset: Asset to evaluate
            
        Returns:
            Opportunity score (higher = better opportunity)
        """
        # In a real implementation, this would analyze:
        # 1. Technical indicators
        # 2. Market sentiment
        # 3. Trading volume and liquidity
        # 4. Historical performance
        # 5. Volatility
        
        # For development, use simulated values
        try:
            # Base opportunity score
            base_score = np.random.uniform(0.2, 0.8)
            
            # Adjust based on asset type
            if asset.endswith("BTC") or asset == "BTC":
                # Bitcoin typically has good opportunities
                base_score *= np.random.uniform(1.0, 1.3)
            elif asset.endswith("ETH") or asset == "ETH":
                # Ethereum also good
                base_score *= np.random.uniform(1.0, 1.2)
            elif asset.endswith("USD") or asset.endswith("USDT") or asset.endswith("USDC"):
                # Stablecoins less opportunity
                base_score *= np.random.uniform(0.1, 0.3)
                
            # Cap at 0-1 range
            return max(0.0, min(1.0, base_score))
            
        except Exception as e:
            logger.error(f"Error evaluating opportunity for {asset}: {str(e)}")
            return 0.5  # Default middle score on error


class CapitalAllocator:
    """Autonomous capital allocation system with dynamic risk adjustment"""
    
    def __init__(self, initial_capital: Dict[str, float] = None):
        """
        Initialize the capital allocation system
        
        Args:
            initial_capital: Dictionary of asset -> amount
        """
        self.portfolio = {}
        self.strategy_performance = {}
        self.risk_model = RiskModel()
        self.opportunity_evaluator = OpportunityEvaluator()
        self.rebalance_threshold = 0.1  # 10% threshold for rebalancing
        self.allocation_history = []
        self.max_history_records = 1000
        
        # Initialize portfolio if provided
        if initial_capital:
            for asset, amount in initial_capital.items():
                self.portfolio[asset] = {
                    "amount": amount,
                    "weight": 0.0,  # Will be calculated in initialize_portfolio
                    "last_updated": time.time()
                }
                
    async def initialize_portfolio(self, assets: List[str], initial_allocations: Dict[str, float] = None):
        """
        Initialize portfolio with assets and allocations
        
        Args:
            assets: List of assets to include in portfolio
            initial_allocations: Dictionary of asset -> amount
        """
        # Calculate total allocation
        total = sum(initial_allocations.values()) if initial_allocations else 0
        
        # Initialize each asset
        for asset in assets:
            allocation = initial_allocations.get(asset, 0) if initial_allocations else 0
            weight = allocation / total if total > 0 else 1.0 / len(assets)
            
            self.portfolio[asset] = {
                "amount": allocation,
                "weight": weight,
                "last_updated": time.time()
            }
            
        logger.info(f"Initialized portfolio with {len(assets)} assets")
        
    async def evaluate_rebalance_need(self) -> bool:
        """
        Check if portfolio needs rebalancing
        
        Returns:
            True if rebalancing is needed, False otherwise
        """
        # Get current weights
        current_weights = await self._get_current_weights()
        
        # Calculate target weights
        target_weights = await self.calculate_optimal_weights()
        
        # Calculate total weight deviation
        total_deviation = 0.0
        for asset in set(current_weights.keys()) | set(target_weights.keys()):
            current = current_weights.get(asset, 0.0)
            target = target_weights.get(asset, 0.0)
            deviation = abs(current - target)
            total_deviation += deviation
            
        logger.debug(f"Portfolio weight deviation: {total_deviation:.4f}, threshold: {self.rebalance_threshold:.4f}")
        
        # Need rebalancing if deviation exceeds threshold
        return total_deviation > self.rebalance_threshold
        
    async def _get_current_weights(self) -> Dict[str, float]:
        """Get current portfolio weights"""
        weights = {}
        total_value = sum(data.get("amount", 0) for data in self.portfolio.values())
        
        if total_value > 0:
            for asset, data in self.portfolio.items():
                weights[asset] = data.get("amount", 0) / total_value
                
        return weights
        
    async def calculate_optimal_weights(self) -> Dict[str, float]:
        """
        Calculate optimal asset weights based on opportunities and risk
        
        Returns:
            Dictionary of asset -> optimal weight
        """
        if not self.portfolio:
            return {}
            
        # Get opportunity scores for each asset
        opportunity_scores = await self.opportunity_evaluator.evaluate_all_assets(
            list(self.portfolio.keys())
        )
        
        # Get risk assessment
        risk_assessment = await self.risk_model.assess_portfolio_risk(self.portfolio)
        
        # Calculate base weights from opportunity scores
        total_score = sum(opportunity_scores.values())
        base_weights = {}
        
        if total_score > 0:
            for asset, score in opportunity_scores.items():
                base_weights[asset] = score / total_score
        else:
            # Equal weight if no scores
            equal_weight = 1.0 / len(opportunity_scores) if opportunity_scores else 0.0
            for asset in opportunity_scores:
                base_weights[asset] = equal_weight
                
        # Adjust weights based on risk assessment
        adjusted_weights = {}
        for asset, base_weight in base_weights.items():
            if asset in risk_assessment:
                risk_factor = risk_assessment[asset].get("risk_factor", 1.0)
                # Higher risk = lower weight
                adjusted_weights[asset] = base_weight / risk_factor
            else:
                adjusted_weights[asset] = base_weight
                
        # Normalize weights to sum to 1
        total_adjusted = sum(adjusted_weights.values())
        normalized_weights = {}
        
        if total_adjusted > 0:
            for asset, weight in adjusted_weights.items():
                normalized_weights[asset] = weight / total_adjusted
                
        logger.debug(f"Calculated optimal weights for {len(normalized_weights)} assets")
        
        return normalized_weights
        
    async def rebalance_portfolio(self) -> Dict[str, Any]:
        """
        Rebalance portfolio to optimal weights
        
        Returns:
            Rebalance result with trades needed
        """
        # Get current and target weights
        current_weights = await self._get_current_weights()
        target_weights = await self.calculate_optimal_weights()
        
        # Calculate trades needed
        trades = []
        total_value = sum(data.get("amount", 0) for data in self.portfolio.values())
        
        for asset in set(current_weights.keys()) | set(target_weights.keys()):
            current = current_weights.get(asset, 0.0)
            target = target_weights.get(asset, 0.0)
            current_amount = self.portfolio.get(asset, {}).get("amount", 0.0)
            target_amount = total_value * target
            
            # Only trade if difference is significant
            if abs(target_amount - current_amount) / total_value > 0.01:  # 1% minimum change
                trade = {
                    "asset": asset,
                    "current_weight": current,
                    "target_weight": target,
                    "current_amount": current_amount,
                    "target_amount": target_amount,
                    "trade_amount": target_amount - current_amount
                }
                trades.append(trade)
                
        # Update portfolio with new target weights
        for asset, weight in target_weights.items():
            if asset in self.portfolio:
                self.portfolio[asset]["weight"] = weight
            else:
                # New asset
                self.portfolio[asset] = {
                    "amount": 0.0,  # Will be updated after trades
                    "weight": weight,
                    "last_updated": time.time()
                }
                
        rebalance_result = {
            "timestamp": time.time(),
            "total_value": total_value,
            "trades_needed": trades,
            "weight_deviation": sum(abs(current_weights.get(a, 0.0) - target_weights.get(a, 0.0)) 
                                 for a in set(current_weights.keys()) | set(target_weights.keys()))
        }
        
        # Add to history
        self._add_to_history("rebalance", rebalance_result)
        
        logger.info(f"Portfolio rebalance calculated: {len(trades)} trades needed")
        
        return rebalance_result
        
    async def allocate_to_strategy(self, strategy_id: str, asset: str, amount: float) -> Dict[str, Any]:
        """
        Allocate capital from portfolio to a specific strategy
        
        Args:
            strategy_id: Identifier for the strategy
            asset: Asset to allocate
            amount: Amount to allocate
            
        Returns:
            Allocation result
        """
        if asset not in self.portfolio:
            logger.warning(f"Cannot allocate {asset} - not in portfolio")
            return {"success": False, "error": f"Asset {asset} not in portfolio"}
            
        if self.portfolio[asset]["amount"] < amount:
            logger.warning(f"Insufficient {asset} balance for allocation: {self.portfolio[asset]['amount']} < {amount}")
            return {"success": False, "error": f"Insufficient {asset} balance"}
            
        # Update portfolio
        self.portfolio[asset]["amount"] -= amount
        self.portfolio[asset]["last_updated"] = time.time()
        
        # Record allocation to strategy
        if strategy_id not in self.strategy_performance:
            self.strategy_performance[strategy_id] = {
                "allocations": {},
                "returns": {},
                "active_allocations": {},
                "start_time": time.time()
            }
            
        # Track this specific allocation
        allocation_id = f"{strategy_id}_{asset}_{int(time.time())}"
        
        # Update strategy allocations
        if asset not in self.strategy_performance[strategy_id]["allocations"]:
            self.strategy_performance[strategy_id]["allocations"][asset] = 0
            
        if asset not in self.strategy_performance[strategy_id]["active_allocations"]:
            self.strategy_performance[strategy_id]["active_allocations"][asset] = {}
            
        self.strategy_performance[strategy_id]["allocations"][asset] += amount
        self.strategy_performance[strategy_id]["active_allocations"][asset][allocation_id] = {
            "amount": amount,
            "timestamp": time.time()
        }
        
        allocation_result = {
            "success": True,
            "strategy_id": strategy_id,
            "allocation_id": allocation_id,
            "asset": asset,
            "amount": amount,
            "timestamp": time.time()
        }
        
        # Add to history
        self._add_to_history("allocation", allocation_result)
        
        logger.info(f"Allocated {amount} {asset} to strategy {strategy_id}")
        
        return allocation_result
        
    async def record_strategy_return(self, strategy_id: str, allocation_id: str, 
                                    asset: str, amount: float, 
                                    profit: float) -> Dict[str, Any]:
        """
        Record return from strategy execution
        
        Args:
            strategy_id: Strategy identifier
            allocation_id: Specific allocation identifier
            asset: Asset returned
            amount: Amount returned
            profit: Profit or loss amount
            
        Returns:
            Result of recording the return
        """
        if strategy_id not in self.strategy_performance:
            logger.warning(f"Unknown strategy {strategy_id}")
            return {"success": False, "error": f"Unknown strategy {strategy_id}"}
            
        # Update portfolio with returned amount
        if asset not in self.portfolio:
            self.portfolio[asset] = {
                "amount": 0,
                "weight": 0,
                "last_updated": time.time()
            }
            
        self.portfolio[asset]["amount"] += amount
        self.portfolio[asset]["last_updated"] = time.time()
        
        # Record return in strategy performance
        if asset not in self.strategy_performance[strategy_id]["returns"]:
            self.strategy_performance[strategy_id]["returns"][asset] = 0
            
        self.strategy_performance[strategy_id]["returns"][asset] += profit
        
        # Remove from active allocations if provided
        active_allocations = self.strategy_performance[strategy_id]["active_allocations"]
        if asset in active_allocations and allocation_id in active_allocations[asset]:
            original_amount = active_allocations[asset][allocation_id]["amount"]
            del active_allocations[asset][allocation_id]
            
            # If this is returning less than allocated, it's a partial return
            is_partial = amount < original_amount
            
            # If partial return, create a new allocation record for remainder
            if is_partial:
                remainder = original_amount - amount
                new_allocation_id = f"{allocation_id}_remainder"
                active_allocations[asset][new_allocation_id] = {
                    "amount": remainder,
                    "timestamp": time.time(),
                    "parent_allocation": allocation_id
                }
        
        # Update strategy ROI
        allocated = self.strategy_performance[strategy_id]["allocations"].get(asset, 0)
        roi = None
        
        if allocated > 0:
            roi = profit / allocated
            
            # Update strategy performance metrics
            if "roi" not in self.strategy_performance[strategy_id]:
                self.strategy_performance[strategy_id]["roi"] = {}
                
            self.strategy_performance[strategy_id]["roi"][asset] = roi
            
        return_result = {
            "success": True,
            "strategy_id": strategy_id,
            "allocation_id": allocation_id,
            "asset": asset,
            "amount_returned": amount,
            "profit": profit,
            "roi": roi,
            "timestamp": time.time()
        }
        
        # Add to history
        self._add_to_history("return", return_result)
        
        logger.info(f"Recorded return from strategy {strategy_id}: {amount} {asset}, profit {profit}")
        
        return return_result
        
    def get_strategy_performance(self, strategy_id: str = None) -> Dict[str, Any]:
        """
        Get performance metrics for strategies
        
        Args:
            strategy_id: Optional specific strategy to get metrics for
            
        Returns:
            Performance metrics
        """
        if strategy_id:
            # Return specific strategy performance
            if strategy_id not in self.strategy_performance:
                return {"error": f"Unknown strategy {strategy_id}"}
                
            return self._calculate_strategy_metrics(strategy_id)
            
        else:
            # Return all strategy performance
            results = {}
            for strategy_id in self.strategy_performance:
                results[strategy_id] = self._calculate_strategy_metrics(strategy_id)
                
            # Add overall summary
            results["_overall"] = self._calculate_overall_performance()
            
            return results
            
    def _calculate_strategy_metrics(self, strategy_id: str) -> Dict[str, Any]:
        """Calculate detailed metrics for a strategy"""
        if strategy_id not in self.strategy_performance:
            return {}
            
        perf = self.strategy_performance[strategy_id]
        
        # Calculate totals
        total_allocated = sum(amount for asset, amount in perf.get("allocations", {}).items())
        total_active = sum(sum(alloc["amount"] for alloc in asset_allocs.values()) 
                         for asset, asset_allocs in perf.get("active_allocations", {}).items())
        total_returned = total_allocated - total_active
        total_profit = sum(amount for asset, amount in perf.get("returns", {}).items())
        
        # Calculate ROI
        overall_roi = total_profit / total_allocated if total_allocated > 0 else 0
        
        # Other metrics
        duration = time.time() - perf.get("start_time", time.time())
        annual_roi = overall_roi * (86400 * 365) / duration if duration > 0 else 0
        
        return {
            "strategy_id": strategy_id,
            "total_allocated": total_allocated,
            "total_active": total_active,
            "total_returned": total_returned,
            "total_profit": total_profit,
            "overall_roi": overall_roi,
            "annual_roi": annual_roi,
            "duration_days": duration / 86400,
            "asset_breakdown": {
                asset: {
                    "allocated": amount,
                    "active": sum(alloc["amount"] for alloc in perf["active_allocations"].get(asset, {}).values()),
                    "profit": perf["returns"].get(asset, 0),
                    "roi": perf["roi"].get(asset, 0) if asset in perf.get("roi", {}) else None
                }
                for asset, amount in perf.get("allocations", {}).items()
            }
        }
        
    def _calculate_overall_performance(self) -> Dict[str, Any]:
        """Calculate overall performance across all strategies"""
        total_allocated = 0
        total_active = 0
        total_profit = 0
        
        for strategy_id, perf in self.strategy_performance.items():
            # Sum allocations
            total_allocated += sum(amount for asset, amount in perf.get("allocations", {}).items())
            
            # Sum active allocations
            strategy_active = sum(sum(alloc["amount"] for alloc in asset_allocs.values()) 
                               for asset, asset_allocs in perf.get("active_allocations", {}).items())
            total_active += strategy_active
            
            # Sum profits
            total_profit += sum(amount for asset, amount in perf.get("returns", {}).items())
        
        # Calculate overall metrics
        total_returned = total_allocated - total_active
        overall_roi = total_profit / total_allocated if total_allocated > 0 else 0
        
        return {
            "total_allocated": total_allocated,
            "total_active": total_active,
            "total_returned": total_returned,
            "total_profit": total_profit,
            "overall_roi": overall_roi,
            "strategy_count": len(self.strategy_performance)
        }
        
    def _add_to_history(self, action_type: str, data: Dict[str, Any]):
        """Add an entry to allocation history"""
        self.allocation_history.append({
            "type": action_type,
            "data": data,
            "timestamp": time.time()
        })
        
        # Trim history if too long
        if len(self.allocation_history) > self.max_history_records:
            self.allocation_history = self.allocation_history[-self.max_history_records:]
            
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get summary of current portfolio
        
        Returns:
            Portfolio summary
        """
        if not self.portfolio:
            return {
                "assets": 0,
                "total_value": 0,
                "asset_breakdown": {}
            }
            
        total_value = sum(data.get("amount", 0) for data in self.portfolio.values())
        
        # Calculate current weights
        current_weights = {}
        for asset, data in self.portfolio.items():
            if total_value > 0:
                current_weights[asset] = data.get("amount", 0) / total_value
            else:
                current_weights[asset] = 0
                
        return {
            "assets": len(self.portfolio),
            "total_value": total_value,
            "asset_breakdown": {
                asset: {
                    "amount": data.get("amount", 0),
                    "weight": current_weights.get(asset, 0),
                    "target_weight": data.get("weight", 0),
                    "last_updated": data.get("last_updated", 0)
                }
                for asset, data in self.portfolio.items()
            },
            "timestamp": time.time()
        }
