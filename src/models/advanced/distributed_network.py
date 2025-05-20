#!/usr/bin/env python3
import asyncio
import time
import logging
import uuid
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class HummingbotNode:
    def __init__(self, node_id: str, region: str, backup_nodes: List[str] = None):
        """
        Initialize a node in the distributed Hummingbot network.
        
        Args:
            node_id: Unique identifier for this node
            region: Geographic region where this node is deployed
            backup_nodes: List of node_ids that can serve as backups for this node
        """
        self.node_id = node_id
        self.region = region
        self.backup_nodes = backup_nodes or []
        self.status = "active"
        self.network = None
        self.running_strategies = {}
        
    async def connect_to_network(self, network):
        """Connect this node to the network coordinator"""
        self.network = network
        await self.network.register_node(self.node_id, self.region, self.backup_nodes)
        logger.info(f"Node {self.node_id} connected to network in region {self.region}")
        
    async def heartbeat(self):
        """
        Send regular heartbeats to network coordinator and execute assigned strategies.
        This runs as a continuous background task.
        """
        while True:
            try:
                # Send status to network coordinator
                if self.network:
                    await self.network.update_node_status(self.node_id, self.status)
                    
                    # Check if primary node for any strategies
                    strategies = await self.network.get_assigned_strategies(self.node_id)
                    
                    # Execute strategies if assigned
                    for strategy in strategies:
                        if strategy.id not in self.running_strategies:
                            # Start new strategy execution
                            self.running_strategies[strategy.id] = asyncio.create_task(
                                self.execute_strategy(strategy)
                            )
                            
                # Clean up completed strategy tasks
                completed_strategies = []
                for strategy_id, task in self.running_strategies.items():
                    if task.done():
                        completed_strategies.append(strategy_id)
                        if task.exception():
                            exception = task.exception()
                            logger.error(f"Strategy {strategy_id} failed with error: {exception}")
                            if self.network:
                                await self.network.report_failure(self.node_id, strategy_id, str(exception))
                
                for strategy_id in completed_strategies:
                    del self.running_strategies[strategy_id]
                    
            except Exception as e:
                logger.error(f"Error in node heartbeat: {str(e)}")
                self.status = "error"
                
            await asyncio.sleep(5)
            
    async def execute_strategy(self, strategy):
        """
        Execute a trading strategy with failover capability.
        If execution fails, notify network of failure and trigger failover.
        
        Args:
            strategy: Strategy object containing execution parameters
        """
        try:
            logger.info(f"Node {self.node_id} starting execution of strategy {strategy.id}")
            
            # Strategy setup
            await self._strategy_setup(strategy)
            
            # Strategy execution loop
            while True:
                # Check if this node is still assigned to this strategy
                if not await self.network.is_strategy_assigned(strategy.id, self.node_id):
                    logger.info(f"Strategy {strategy.id} no longer assigned to node {self.node_id}, stopping execution")
                    break
                
                # Execute strategy step
                result = await self._execute_strategy_step(strategy)
                
                # Report results to network
                await self.network.report_strategy_result(self.node_id, strategy.id, result)
                
                # Check for stop condition
                if result.get("status") == "completed":
                    logger.info(f"Strategy {strategy.id} completed successfully")
                    break
                
                # Wait before next execution step
                await asyncio.sleep(strategy.interval)
                
        except Exception as e:
            logger.error(f"Error executing strategy {strategy.id}: {str(e)}")
            
            # Notify network of failure
            if self.network:
                await self.network.report_failure(self.node_id, strategy.id, str(e))
                
                # Trigger failover to backup node
                await self.network.trigger_failover(strategy.id, self.backup_nodes)
                
            raise  # Re-raise to mark the task as failed
    
    async def _strategy_setup(self, strategy):
        """Setup phase for strategy execution"""
        # Implementation will vary based on strategy type
        pass
        
    async def _execute_strategy_step(self, strategy):
        """Execute a single step of the strategy"""
        # Implementation will vary based on strategy type
        return {"status": "running"}


class NetworkCoordinator:
    def __init__(self):
        """Initialize the network coordinator for distributed Hummingbot nodes"""
        self.nodes = {}  # node_id -> node_info
        self.strategy_assignments = {}  # strategy_id -> assigned_node_id
        self.strategy_backup_nodes = {}  # strategy_id -> list of backup node_ids
        self.strategy_status = {}  # strategy_id -> status_info
        
    async def register_node(self, node_id: str, region: str, backup_nodes: List[str]):
        """Register a new node with the network"""
        self.nodes[node_id] = {
            "region": region,
            "backup_nodes": backup_nodes,
            "status": "active",
            "last_heartbeat": time.time(),
            "assigned_strategies": []
        }
        logger.info(f"Registered node {node_id} in region {region}")
        
    async def update_node_status(self, node_id: str, status: str):
        """Update status and heartbeat timestamp for a node"""
        if node_id in self.nodes:
            self.nodes[node_id]["status"] = status
            self.nodes[node_id]["last_heartbeat"] = time.time()
            
    async def assign_strategy(self, strategy_id: str, primary_node_id: str, backup_node_ids: List[str] = None):
        """Assign a strategy to a primary node with optional backups"""
        if primary_node_id not in self.nodes:
            raise ValueError(f"Cannot assign strategy to unknown node {primary_node_id}")
            
        self.strategy_assignments[strategy_id] = primary_node_id
        self.strategy_backup_nodes[strategy_id] = backup_node_ids or []
        
        # Add to node's assigned strategies list
        self.nodes[primary_node_id]["assigned_strategies"].append(strategy_id)
        
        # Initialize strategy status
        self.strategy_status[strategy_id] = {
            "status": "assigned",
            "assigned_time": time.time(),
            "primary_node": primary_node_id,
            "backup_nodes": backup_node_ids or [],
            "last_result": None,
            "failures": []
        }
        
        logger.info(f"Assigned strategy {strategy_id} to node {primary_node_id} with backups {backup_node_ids}")
        
    async def get_assigned_strategies(self, node_id: str) -> List[Any]:
        """Get list of strategies assigned to a node"""
        if node_id not in self.nodes:
            return []
            
        # Return strategy objects for all assigned strategy_ids
        # In a real implementation, this would fetch the actual strategy objects
        return [{"id": strategy_id} for strategy_id in self.nodes[node_id]["assigned_strategies"]]
        
    async def is_strategy_assigned(self, strategy_id: str, node_id: str) -> bool:
        """Check if a strategy is assigned to a specific node"""
        return (strategy_id in self.strategy_assignments and 
                self.strategy_assignments[strategy_id] == node_id)
                
    async def is_strategy_running(self, strategy_id: str) -> bool:
        """Check if a strategy is currently running"""
        if strategy_id not in self.strategy_status:
            return False
            
        return self.strategy_status[strategy_id]["status"] in ["running", "assigned"]
        
    async def report_strategy_result(self, node_id: str, strategy_id: str, result: Dict[str, Any]):
        """Report result of strategy execution step"""
        if strategy_id in self.strategy_status:
            self.strategy_status[strategy_id]["last_result"] = result
            self.strategy_status[strategy_id]["last_update_time"] = time.time()
            self.strategy_status[strategy_id]["status"] = result.get("status", "running")
            
    async def report_failure(self, node_id: str, strategy_id: str, error_message: str):
        """Report a strategy execution failure"""
        if strategy_id in self.strategy_status:
            failure = {
                "node_id": node_id,
                "error": error_message,
                "time": time.time()
            }
            self.strategy_status[strategy_id]["failures"].append(failure)
            self.strategy_status[strategy_id]["status"] = "failed"
            logger.error(f"Strategy {strategy_id} failed on node {node_id}: {error_message}")
            
    async def trigger_failover(self, strategy_id: str, backup_nodes: List[str] = None):
        """
        Trigger failover of a strategy to a backup node.
        If backup_nodes is provided, it overrides the registered backup nodes.
        """
        if strategy_id not in self.strategy_status:
            logger.error(f"Cannot failover unknown strategy {strategy_id}")
            return False
            
        # Use provided backup nodes or the registered ones
        candidates = backup_nodes or self.strategy_status[strategy_id]["backup_nodes"]
        
        # Find first active backup node
        new_node_id = None
        for node_id in candidates:
            if node_id in self.nodes and self.nodes[node_id]["status"] == "active":
                new_node_id = node_id
                break
                
        if not new_node_id:
            logger.error(f"No active backup nodes available for strategy {strategy_id}")
            return False
            
        # Remove from old node's assignments
        old_node_id = self.strategy_assignments[strategy_id]
        if old_node_id in self.nodes:
            if strategy_id in self.nodes[old_node_id]["assigned_strategies"]:
                self.nodes[old_node_id]["assigned_strategies"].remove(strategy_id)
                
        # Assign to new node
        self.strategy_assignments[strategy_id] = new_node_id
        if strategy_id not in self.nodes[new_node_id]["assigned_strategies"]:
            self.nodes[new_node_id]["assigned_strategies"].append(strategy_id)
            
        # Update strategy status
        self.strategy_status[strategy_id].update({
            "status": "failover",
            "primary_node": new_node_id,
            "failover_time": time.time(),
            "previous_node": old_node_id
        })
        
        logger.info(f"Triggered failover of strategy {strategy_id} from {old_node_id} to {new_node_id}")
        return True
        
    async def monitor_nodes(self):
        """
        Monitor node health and trigger failover for strategies on unresponsive nodes.
        This runs as a continuous background task.
        """
        heartbeat_timeout = 30  # seconds
        
        while True:
            current_time = time.time()
            
            # Check each node's last heartbeat
            for node_id, node_info in list(self.nodes.items()):
                last_heartbeat = node_info["last_heartbeat"]
                if current_time - last_heartbeat > heartbeat_timeout:
                    logger.warning(f"Node {node_id} appears to be down (no heartbeat)")
                    
                    # Mark node as inactive
                    node_info["status"] = "inactive"
                    
                    # Trigger failover for all assigned strategies
                    for strategy_id in node_info["assigned_strategies"].copy():
                        await self.trigger_failover(strategy_id)
                        
            await asyncio.sleep(10)  # Check every 10 seconds
