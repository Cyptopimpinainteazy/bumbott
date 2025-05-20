#!/usr/bin/env python3
import asyncio
import time
import logging
import networkx as nx
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import uuid

logger = logging.getLogger(__name__)

class CrossProtocolArbitrageEngine:
    def __init__(self, connectors: List[Any] = None):
        """
        Initialize the cross-protocol arbitrage detection engine.
        
        Args:
            connectors: List of exchange/protocol connectors
        """
        self.connectors = connectors or []
        self.opportunity_graph = nx.DiGraph()
        self.route_cache = {}
        self.min_profit_threshold = 0.001  # 0.1% minimum profit to consider
        self.execution_history = []
        self.last_graph_update = 0
        self.graph_update_interval = 60  # Update graph every 60 seconds
        
    async def add_connector(self, connector: Any):
        """
        Add a new exchange/protocol connector and update the opportunity graph.
        
        Args:
            connector: Connector to the exchange/protocol
        """
        # Add new exchange/protocol connector
        self.connectors.append(connector)
        
        # Update opportunity graph with new vertices
        await self.update_graph_for_connector(connector)
        logger.info(f"Added connector: {connector.name if hasattr(connector, 'name') else 'Unknown'}")
        
    async def update_graph_for_connector(self, connector: Any):
        """
        Update the opportunity graph with trading pairs from a connector.
        
        Args:
            connector: Connector to update graph for
        """
        # Get all trading pairs from connector
        connector_name = connector.name if hasattr(connector, 'name') else str(connector)
        logger.debug(f"Updating graph for connector: {connector_name}")
        
        try:
            pairs = await connector.get_tradeable_pairs()
            logger.debug(f"Found {len(pairs)} tradeable pairs for {connector_name}")
            
            # Add edges to opportunity graph
            for pair in pairs:
                await self._add_pair_to_graph(connector, pair)
                
            # Add cross-connector edges for same asset
            assets = await connector.get_assets()
            await self._add_cross_connector_edges(connector, assets)
            
            logger.debug(f"Graph now has {len(self.opportunity_graph.nodes)} nodes and {len(self.opportunity_graph.edges)} edges")
            
        except Exception as e:
            logger.error(f"Error updating graph for connector {connector_name}: {str(e)}")
            
    async def _add_pair_to_graph(self, connector: Any, pair: str):
        """
        Add trading pair edges to the opportunity graph.
        
        Args:
            connector: Exchange connector
            pair: Trading pair (e.g. 'BTC-USDT')
        """
        connector_name = connector.name if hasattr(connector, 'name') else str(connector)
        try:
            # Parse the trading pair
            base, quote = pair.split('-')
            
            # Add forward edge (buy)
            self.opportunity_graph.add_edge(
                f"{quote}:{connector_name}", 
                f"{base}:{connector_name}",
                action="buy",
                connector=connector,
                pair=pair,
                trade_type="spot"
            )
            
            # Add backward edge (sell)
            self.opportunity_graph.add_edge(
                f"{base}:{connector_name}", 
                f"{quote}:{connector_name}",
                action="sell",
                connector=connector,
                pair=pair,
                trade_type="spot"
            )
            
            # Add edge attributes for fees and liquidity
            for edge in [(f"{quote}:{connector_name}", f"{base}:{connector_name}"),
                        (f"{base}:{connector_name}", f"{quote}:{connector_name}")]:
                try:
                    fee = await connector.get_fee(pair)
                    liquidity = await connector.get_liquidity(pair)
                    self.opportunity_graph.edges[edge]['fee'] = fee
                    self.opportunity_graph.edges[edge]['liquidity'] = liquidity
                except:
                    # Default values if methods not available
                    self.opportunity_graph.edges[edge]['fee'] = 0.001  # 0.1% default fee
                    self.opportunity_graph.edges[edge]['liquidity'] = 1.0  # Default liquidity
            
        except Exception as e:
            logger.error(f"Error adding pair {pair} to graph: {str(e)}")
            
    async def _add_cross_connector_edges(self, connector: Any, assets: List[str]):
        """
        Add cross-connector edges for asset transfers between protocols.
        
        Args:
            connector: Exchange connector
            assets: List of assets available on this connector
        """
        connector_name = connector.name if hasattr(connector, 'name') else str(connector)
        
        # Add transfer edges between connectors for the same asset
        for asset in assets:
            for other_connector in self.connectors:
                other_name = other_connector.name if hasattr(other_connector, 'name') else str(other_connector)
                
                # Skip self-connections
                if other_connector == connector:
                    continue
                    
                # Check if asset exists on other connector
                try:
                    other_assets = await other_connector.get_assets()
                    if asset in other_assets:
                        # Add deposit/withdrawal edges
                        self.opportunity_graph.add_edge(
                            f"{asset}:{connector_name}",
                            f"{asset}:{other_name}",
                            action="transfer",
                            source=connector,
                            destination=other_connector,
                            asset=asset,
                            trade_type="transfer"
                        )
                        
                        # Add transfer fee and time attributes
                        try:
                            transfer_fee = await connector.get_withdrawal_fee(asset, other_connector)
                            transfer_time = await connector.get_withdrawal_time(asset, other_connector)
                        except:
                            # Default values if methods not available
                            transfer_fee = self._get_default_transfer_fee(asset, connector, other_connector)
                            transfer_time = self._get_default_transfer_time(connector, other_connector)
                            
                        edge = (f"{asset}:{connector_name}", f"{asset}:{other_name}")
                        self.opportunity_graph.edges[edge]['fee'] = transfer_fee
                        self.opportunity_graph.edges[edge]['time'] = transfer_time
                        
                except Exception as e:
                    logger.error(f"Error adding cross-connector edge for {asset}: {str(e)}")
    
    def _get_default_transfer_fee(self, asset: str, source: Any, destination: Any) -> float:
        """Get default transfer fee for an asset between connectors"""
        # In production, this would be based on known network fees
        if asset == "BTC":
            return 0.0001  # Typical BTC withdrawal fee
        elif asset == "ETH":
            return 0.005   # Typical ETH withdrawal fee
        elif asset.endswith("USDT") or asset.endswith("USDC"):
            return 1.0     # Typical stablecoin fee
        else:
            return 0.01    # Generic default
            
    def _get_default_transfer_time(self, source: Any, destination: Any) -> int:
        """Get default transfer time in seconds between connectors"""
        # In production, this would be based on known network confirmation times
        source_name = source.name if hasattr(source, 'name') else str(source)
        dest_name = destination.name if hasattr(destination, 'name') else str(destination)
        
        # Check if same blockchain/network for instant transfers
        if ("dex" in source_name.lower() and "dex" in dest_name.lower()):
            return 10  # Fast for on-chain transfers on same network
            
        # Default times based on typical blockchain confirmation times
        return 600  # 10 minutes for cross-chain/exchange transfers
            
    async def update_opportunity_graph(self):
        """
        Update the entire opportunity graph with current rates and liquidity.
        Should be called periodically to refresh pricing data.
        """
        current_time = time.time()
        
        # Only update if interval has elapsed
        if current_time - self.last_graph_update < self.graph_update_interval:
            return
            
        logger.info("Updating entire opportunity graph with current rates")
        self.last_graph_update = current_time
        
        # Update all connector data
        for connector in self.connectors:
            await self.update_graph_for_connector(connector)
            
        # Update edge weights based on current rates
        for u, v, data in self.opportunity_graph.edges(data=True):
            if data.get('action') in ['buy', 'sell']:
                try:
                    connector = data.get('connector')
                    pair = data.get('pair')
                    
                    if connector and pair:
                        # Get current rate for this edge
                        if data['action'] == 'buy':
                            rate = await connector.get_buy_price(pair)
                        else:  # sell
                            rate = await connector.get_sell_price(pair)
                            
                        # Update edge with current rate
                        self.opportunity_graph.edges[u, v]['rate'] = rate
                        
                        # Calculate edge weight for pathfinding (negative log of rate)
                        # Negative because we want to maximize product of rates
                        if rate > 0:
                            self.opportunity_graph.edges[u, v]['weight'] = -np.log(rate)
                        else:
                            self.opportunity_graph.edges[u, v]['weight'] = float('inf')
                            
                except Exception as e:
                    logger.error(f"Error updating edge weight for {u} -> {v}: {str(e)}")
                    self.opportunity_graph.edges[u, v]['weight'] = float('inf')
        
        # Clear route cache after update
        self.route_cache = {}
                    
    async def find_arbitrage_cycles(self, start_asset: str, min_profit_pct: float = 0.5) -> List[Dict[str, Any]]:
        """
        Find all profitable arbitrage cycles starting and ending with the same asset.
        
        Args:
            start_asset: Asset to start and end with (e.g. 'USDT')
            min_profit_pct: Minimum profit percentage to consider a cycle profitable
            
        Returns:
            List of profitable cycles with profit percentage and execution steps
        """
        # Update graph with current rates
        await self.update_opportunity_graph()
        
        profitable_cycles = []
        
        # Try each connector as a starting point
        for connector in self.connectors:
            connector_name = connector.name if hasattr(connector, 'name') else str(connector)
            start_node = f"{start_asset}:{connector_name}"
            
            if start_node not in self.opportunity_graph:
                logger.debug(f"Start node {start_node} not in graph")
                continue
                
            logger.debug(f"Searching for cycles starting at {start_node}")
            
            # Find simple cycles up to a reasonable length
            max_cycle_length = 5  # Limit to prevent excessive computation
            
            try:
                # Using a modified DFS to find negative cycles in log-transformed graph
                # This is equivalent to finding cycles with product of rates > 1
                for cycle in self._find_negative_cycles(start_node, max_length=max_cycle_length):
                    # Check if cycle starts and ends at the same node
                    if cycle[0] == cycle[-1] == start_node:
                        # Calculate expected profit for this cycle
                        profit_pct, details = await self.calculate_cycle_profit(cycle)
                        
                        if profit_pct >= min_profit_pct:
                            # Generate execution steps
                            steps = await self.cycle_to_steps(cycle)
                            
                            profitable_cycles.append({
                                "cycle": cycle,
                                "profit_pct": profit_pct,
                                "steps": steps,
                                "details": details,
                                "id": str(uuid.uuid4())
                            })
                            
                            logger.debug(f"Found profitable cycle: {profit_pct:.2f}% profit, {len(steps)} steps")
                            
            except Exception as e:
                logger.error(f"Error finding cycles from {start_node}: {str(e)}")
        
        # Sort by profit percentage
        return sorted(profitable_cycles, key=lambda x: x["profit_pct"], reverse=True)
        
    def _find_negative_cycles(self, start_node: str, max_length: int = 5) -> List[List[str]]:
        """
        Find negative weight cycles in the graph (profitable arbitrage cycles).
        Uses Bellman-Ford algorithm with early termination.
        
        Args:
            start_node: Starting node
            max_length: Maximum cycle length to consider
            
        Returns:
            List of cycles
        """
        # Implementation uses a simplified negative cycle detection
        all_cycles = []
        visited = {start_node: 0}  # node -> depth
        path = [start_node]
        
        def dfs(node, depth):
            if depth >= max_length:
                return
                
            for neighbor in self.opportunity_graph.neighbors(node):
                edge_data = self.opportunity_graph.edges[node, neighbor]
                
                # Skip edges with infinite weight (invalid)
                if edge_data.get('weight', float('inf')) == float('inf'):
                    continue
                    
                # If we've found a cycle back to start
                if neighbor == start_node and depth > 1:
                    cycle = path + [start_node]
                    all_cycles.append(cycle)
                    # Early termination if we've found enough cycles
                    if len(all_cycles) >= 100:
                        return
                # Visit unvisited nodes or revisit if better path
                elif neighbor not in visited or visited[neighbor] > depth + 1:
                    visited[neighbor] = depth + 1
                    path.append(neighbor)
                    dfs(neighbor, depth + 1)
                    path.pop()
        
        dfs(start_node, 0)
        return all_cycles
        
    async def calculate_cycle_profit(self, cycle: List[str]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate expected profit percentage for a cycle.
        
        Args:
            cycle: List of nodes in the cycle
            
        Returns:
            Tuple of (profit percentage, detailed breakdown)
        """
        # Base asset and amount
        start_node = cycle[0]
        asset = start_node.split(':')[0]
        start_amount = 1.0  # Normalized to 1 unit
        
        current_amount = start_amount
        current_asset = asset
        
        details = {
            "steps": [],
            "fees": 0.0,
            "slippage": 0.0,
            "execution_time": 0
        }
        
        # Simulate execution of each step
        for i in range(len(cycle) - 1):
            from_node = cycle[i]
            to_node = cycle[i + 1]
            
            if not self.opportunity_graph.has_edge(from_node, to_node):
                return 0.0, {"error": f"Edge not found: {from_node} -> {to_node}"}
                
            edge_data = self.opportunity_graph.edges[from_node, to_node]
            action = edge_data.get('action')
            
            # Extract rate from edge
            rate = edge_data.get('rate', 0.0)
            fee = edge_data.get('fee', 0.001)  # Default 0.1% fee
            
            # Apply rate and fee to current amount
            if action == 'buy':
                to_asset = to_node.split(':')[0]
                from_asset = from_node.split(':')[0]
                
                # Buying to_asset with from_asset
                new_amount = current_amount * rate * (1 - fee)
                
                step_details = {
                    "action": "buy",
                    "pair": f"{to_asset}-{from_asset}",
                    "rate": rate,
                    "from_amount": current_amount,
                    "from_asset": from_asset,
                    "to_amount": new_amount,
                    "to_asset": to_asset,
                    "fee": current_amount * fee,
                    "fee_asset": from_asset
                }
                
                current_amount = new_amount
                current_asset = to_asset
                
            elif action == 'sell':
                to_asset = to_node.split(':')[0]
                from_asset = from_node.split(':')[0]
                
                # Selling from_asset for to_asset
                new_amount = current_amount * rate * (1 - fee)
                
                step_details = {
                    "action": "sell",
                    "pair": f"{from_asset}-{to_asset}",
                    "rate": rate,
                    "from_amount": current_amount,
                    "from_asset": from_asset,
                    "to_amount": new_amount,
                    "to_asset": to_asset,
                    "fee": current_amount * rate * fee,
                    "fee_asset": to_asset
                }
                
                current_amount = new_amount
                current_asset = to_asset
                
            elif action == 'transfer':
                to_exchange = to_node.split(':')[1]
                from_exchange = from_node.split(':')[1]
                
                # Transferring asset between exchanges
                new_amount = current_amount * (1 - fee)
                transfer_time = edge_data.get('time', 600)  # Default 10 min
                
                step_details = {
                    "action": "transfer",
                    "from_exchange": from_exchange,
                    "to_exchange": to_exchange,
                    "asset": current_asset,
                    "amount": current_amount,
                    "fee": current_amount * fee,
                    "fee_asset": current_asset,
                    "time": transfer_time
                }
                
                current_amount = new_amount
                details["execution_time"] += transfer_time
                
            else:
                # Unknown action type
                return 0.0, {"error": f"Unknown action type: {action}"}
                
            details["steps"].append(step_details)
            details["fees"] += step_details.get("fee", 0.0)
            
        # Calculate profit percentage
        if start_amount > 0:
            profit_pct = (current_amount - start_amount) / start_amount * 100
        else:
            profit_pct = 0.0
            
        # Account for estimated slippage based on liquidity
        estimated_slippage = self._estimate_slippage(cycle, start_amount)
        adjusted_profit_pct = profit_pct - estimated_slippage
        
        details["raw_profit_pct"] = profit_pct
        details["slippage_estimate_pct"] = estimated_slippage
        details["adjusted_profit_pct"] = adjusted_profit_pct
        
        return adjusted_profit_pct, details
        
    def _estimate_slippage(self, cycle: List[str], amount: float) -> float:
        """
        Estimate slippage for a cycle based on liquidity of each edge.
        
        Args:
            cycle: List of nodes in the cycle
            amount: Base amount
            
        Returns:
            Estimated slippage percentage
        """
        total_slippage_pct = 0.0
        
        for i in range(len(cycle) - 1):
            from_node = cycle[i]
            to_node = cycle[i + 1]
            
            if self.opportunity_graph.has_edge(from_node, to_node):
                edge_data = self.opportunity_graph.edges[from_node, to_node]
                
                # Get liquidity data if available
                liquidity = edge_data.get('liquidity', 1.0)
                
                # Simple slippage model: higher liquidity = lower slippage
                # amount/liquidity represents what percentage of available liquidity
                # we're using, which impacts slippage
                if liquidity > 0:
                    step_slippage = min(5.0, (amount / liquidity) * 0.5)  # Cap at 5%
                else:
                    step_slippage = 5.0  # Assume worst case for unknown liquidity
                    
                total_slippage_pct += step_slippage
                
        return total_slippage_pct
        
    async def cycle_to_steps(self, cycle: List[str]) -> List[Dict[str, Any]]:
        """
        Convert a cycle to concrete execution steps.
        
        Args:
            cycle: List of nodes in the cycle
            
        Returns:
            List of execution steps
        """
        execution_steps = []
        
        for i in range(len(cycle) - 1):
            from_node = cycle[i]
            to_node = cycle[i + 1]
            
            if self.opportunity_graph.has_edge(from_node, to_node):
                edge_data = self.opportunity_graph.edges[from_node, to_node]
                
                from_asset, from_exchange = from_node.split(':')
                to_asset, to_exchange = to_node.split(':')
                
                action = edge_data.get('action')
                
                if action == 'buy':
                    step = {
                        "step_type": "trade",
                        "action": "buy",
                        "base_asset": to_asset,
                        "quote_asset": from_asset,
                        "pair": f"{to_asset}-{from_asset}",
                        "exchange": from_exchange,
                        "connector": edge_data.get('connector')
                    }
                elif action == 'sell':
                    step = {
                        "step_type": "trade",
                        "action": "sell",
                        "base_asset": from_asset,
                        "quote_asset": to_asset,
                        "pair": f"{from_asset}-{to_asset}",
                        "exchange": from_exchange,
                        "connector": edge_data.get('connector')
                    }
                elif action == 'transfer':
                    step = {
                        "step_type": "transfer",
                        "asset": from_asset,
                        "from_exchange": from_exchange,
                        "to_exchange": to_exchange,
                        "source": edge_data.get('source'),
                        "destination": edge_data.get('destination')
                    }
                else:
                    continue  # Skip unknown actions
                    
                execution_steps.append(step)
                
        return execution_steps
        
    async def get_best_opportunity(self, base_asset: str = "USDT", min_profit_pct: float = 0.5) -> Optional[Dict[str, Any]]:
        """
        Get the best arbitrage opportunity for a base asset.
        
        Args:
            base_asset: Base asset to start and end with
            min_profit_pct: Minimum profit percentage
            
        Returns:
            Best opportunity details or None
        """
        opportunities = await self.find_arbitrage_cycles(base_asset, min_profit_pct)
        
        if not opportunities:
            return None
            
        # Return the most profitable opportunity
        return opportunities[0]
        
    async def execute_opportunity(self, opportunity: Dict[str, Any], amount: float) -> Dict[str, Any]:
        """
        Execute an arbitrage opportunity.
        
        Args:
            opportunity: Opportunity details from find_arbitrage_cycles
            amount: Amount of base asset to use
            
        Returns:
            Execution result
        """
        if not opportunity:
            return {"success": False, "error": "No opportunity provided"}
            
        steps = opportunity.get("steps", [])
        cycle = opportunity.get("cycle", [])
        
        if not steps or not cycle:
            return {"success": False, "error": "Invalid opportunity format"}
            
        # Get base asset from cycle
        base_asset = cycle[0].split(':')[0]
        
        logger.info(f"Executing arbitrage opportunity with {amount} {base_asset}")
        
        execution_result = {
            "opportunity_id": opportunity.get("id", str(uuid.uuid4())),
            "start_time": time.time(),
            "base_asset": base_asset,
            "start_amount": amount,
            "steps_executed": 0,
            "steps_results": [],
            "current_amount": amount,
            "current_asset": base_asset,
            "status": "executing"
        }
        
        try:
            # Execute each step
            current_amount = amount
            current_asset = base_asset
            
            for i, step in enumerate(steps):
                step_type = step.get("step_type")
                
                if step_type == "trade":
                    # Execute trade
                    action = step.get("action")
                    pair = step.get("pair")
                    exchange = step.get("exchange")
                    connector = step.get("connector")
                    
                    if not connector:
                        raise ValueError(f"Missing connector for step {i}")
                        
                    logger.debug(f"Executing {action} of {current_amount} {current_asset} on {exchange}")
                    
                    # Execute the trade
                    if action == "buy":
                        trade_result = await connector.execute_buy(
                            pair=pair,
                            amount=current_amount,
                            asset=current_asset
                        )
                    else:  # sell
                        trade_result = await connector.execute_sell(
                            pair=pair,
                            amount=current_amount,
                            asset=current_asset
                        )
                        
                    # Update current state
                    if trade_result.get("success", False):
                        current_amount = trade_result.get("executed_amount", 0)
                        current_asset = trade_result.get("resulting_asset", "")
                        
                    step_result = {
                        "step": i,
                        "type": step_type,
                        "action": action,
                        "pair": pair,
                        "exchange": exchange,
                        "input_amount": execution_result["current_amount"],
                        "input_asset": execution_result["current_asset"],
                        "output_amount": current_amount,
                        "output_asset": current_asset,
                        "success": trade_result.get("success", False),
                        "details": trade_result
                    }
                    
                elif step_type == "transfer":
                    # Execute transfer
                    asset = step.get("asset")
                    from_exchange = step.get("from_exchange")
                    to_exchange = step.get("to_exchange")
                    source = step.get("source")
                    destination = step.get("destination")
                    
                    if not source or not destination:
                        raise ValueError(f"Missing source or destination for step {i}")
                        
                    logger.debug(f"Executing transfer of {current_amount} {current_asset} from {from_exchange} to {to_exchange}")
                    
                    # Execute the transfer
                    transfer_result = await source.execute_withdrawal(
                        asset=current_asset,
                        amount=current_amount,
                        destination=destination
                    )
                    
                    # Update current state
                    if transfer_result.get("success", False):
                        current_amount = transfer_result.get("executed_amount", 0)
                        # Asset remains the same for transfers
                        
                    step_result = {
                        "step": i,
                        "type": step_type,
                        "asset": asset,
                        "from_exchange": from_exchange,
                        "to_exchange": to_exchange,
                        "input_amount": execution_result["current_amount"],
                        "output_amount": current_amount,
                        "success": transfer_result.get("success", False),
                        "details": transfer_result
                    }
                    
                else:
                    raise ValueError(f"Unknown step type: {step_type}")
                    
                # Update execution result
                execution_result["steps_executed"] += 1
                execution_result["steps_results"].append(step_result)
                execution_result["current_amount"] = current_amount
                execution_result["current_asset"] = current_asset
                
                # Check if step failed
                if not step_result["success"]:
                    execution_result["status"] = "partial_failure"
                    execution_result["error"] = f"Step {i} failed: {step_result['details'].get('error', 'Unknown error')}"
                    break
                
            # Check if we completed all steps
            if execution_result["steps_executed"] == len(steps):
                execution_result["status"] = "completed"
                
                # Calculate profit
                if (execution_result["current_asset"] == execution_result["base_asset"] and 
                    execution_result["start_amount"] > 0):
                    profit = execution_result["current_amount"] - execution_result["start_amount"]
                    profit_pct = profit / execution_result["start_amount"] * 100
                    execution_result["profit"] = profit
                    execution_result["profit_pct"] = profit_pct
                    
        except Exception as e:
            logger.error(f"Error executing opportunity: {str(e)}")
            execution_result["status"] = "error"
            execution_result["error"] = str(e)
            
        # Record completion time
        execution_result["end_time"] = time.time()
        execution_result["duration"] = execution_result["end_time"] - execution_result["start_time"]
        
        # Add to execution history
        self.execution_history.append(execution_result)
        
        # Trim history if too long
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
            
        return execution_result
