#!/usr/bin/env python3
import asyncio
import time
import random
import logging
import copy
import uuid
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class PatternObfuscator:
    """Obfuscates trading patterns to avoid detection by exchanges"""
    
    def __init__(self):
        """Initialize pattern obfuscator components"""
        self.patterns = self._initialize_detectable_patterns()
        self.counters = {}
        
    def _initialize_detectable_patterns(self) -> Dict[str, Any]:
        """Initialize patterns that could be detected by exchanges"""
        return {
            "fixed_interval": {
                "description": "Orders at fixed time intervals",
                "detection_risk": "high",
                "countermeasures": ["random_delay", "batch_variance"]
            },
            "round_numbers": {
                "description": "Orders with round number sizes/prices",
                "detection_risk": "medium",
                "countermeasures": ["price_noise", "size_noise"]
            },
            "fixed_sizes": {
                "description": "Orders with same size repeatedly",
                "detection_risk": "high", 
                "countermeasures": ["size_variance", "split_orders"]
            },
            "regular_cancellation": {
                "description": "Cancelling orders at regular intervals",
                "detection_risk": "high",
                "countermeasures": ["cancel_variance", "longer_placements"]
            },
            "ping_pong": {
                "description": "Rapidly placing and cancelling orders",
                "detection_risk": "extreme",
                "countermeasures": ["reduced_frequency", "random_delay", "size_variance"]
            },
            "extreme_speed": {
                "description": "Reacting to market changes too quickly",
                "detection_risk": "extreme",
                "countermeasures": ["forced_delay", "random_delay"]
            }
        }
        
    async def apply_obfuscation(self, order: Any, pattern_types: List[str] = None) -> Any:
        """
        Apply pattern obfuscation to an order to avoid detection
        
        Args:
            order: The order to obfuscate
            pattern_types: Specific patterns to counter, or None for auto-detection
            
        Returns:
            Obfuscated order
        """
        # Make a copy of the order
        obfuscated_order = copy.deepcopy(order)
        
        # If no specific patterns, detect likely patterns
        if not pattern_types:
            pattern_types = self._detect_patterns(order)
            
        # Apply countermeasures for each pattern
        for pattern in pattern_types:
            if pattern in self.patterns:
                pattern_info = self.patterns[pattern]
                
                # Apply each suitable countermeasure
                for countermeasure in pattern_info["countermeasures"]:
                    obfuscated_order = await self._apply_countermeasure(
                        obfuscated_order, 
                        countermeasure
                    )
                    
        # Keep track of patterns we've addressed
        for pattern in pattern_types:
            self.counters[pattern] = self.counters.get(pattern, 0) + 1
            
        return obfuscated_order
        
    def _detect_patterns(self, order: Any) -> List[str]:
        """Detect likely detectable patterns in an order"""
        detected_patterns = []
        
        # Check for round numbers in size
        if hasattr(order, 'size'):
            if order.size == round(order.size, 0) or order.size == round(order.size, 1):
                detected_patterns.append("round_numbers")
                
        # Check for repeated order sizes (using order history if available)
        if hasattr(order, 'client_order_id') and hasattr(order, 'size'):
            order_id_parts = str(order.client_order_id).split('_')
            if len(order_id_parts) > 1 and order_id_parts[0] == "hbot":
                # This appears to be a Hummingbot order
                detected_patterns.append("fixed_sizes")
                
        # Check if we need to add random delay
        # (always do this unless specifically instructed not to)
        detected_patterns.append("fixed_interval")
        
        return detected_patterns
        
    async def _apply_countermeasure(self, order: Any, countermeasure: str) -> Any:
        """Apply a specific countermeasure to an order"""
        if countermeasure == "random_delay":
            # Add random delay before order submission
            delay_ms = random.randint(50, 500)
            await asyncio.sleep(delay_ms / 1000)
            
        elif countermeasure == "batch_variance":
            # Batch order processing time would vary in real implementation
            # For now just add a marker to the order
            if hasattr(order, 'metadata'):
                if not order.metadata:
                    order.metadata = {}
                order.metadata["batch_variance"] = True
                
        elif countermeasure == "price_noise":
            # Add small random noise to price
            if hasattr(order, 'price') and order.price:
                noise_factor = random.uniform(-0.001, 0.001)  # ±0.1%
                order.price = order.price * (1 + noise_factor)
                
                # Ensure we're using appropriate precision
                if hasattr(order, 'exchange'):
                    # In real implementation, lookup exchange price precision
                    price_precision = 8  # Default for crypto
                    order.price = round(order.price, price_precision)
                    
        elif countermeasure == "size_noise":
            # Add small random noise to size
            if hasattr(order, 'size'):
                noise_factor = random.uniform(-0.01, 0.01)  # ±1%
                order.size = order.size * (1 + noise_factor)
                
                # Ensure we're respecting minimum order size
                if hasattr(order, 'min_order_size'):
                    order.size = max(order.min_order_size, order.size)
                    
                # Ensure using appropriate precision
                if hasattr(order, 'exchange'):
                    # In real implementation, lookup exchange size precision
                    size_precision = 6  # Default for crypto
                    order.size = round(order.size, size_precision)
                    
        elif countermeasure == "size_variance":
            # Vary order size more significantly
            if hasattr(order, 'size'):
                variance_factor = random.uniform(0.9, 1.1)  # ±10%
                order.size = order.size * variance_factor
                
                # Handle exchange-specific constraints
                if hasattr(order, 'min_order_size'):
                    order.size = max(order.min_order_size, order.size)
                    
                if hasattr(order, 'max_order_size'):
                    order.size = min(order.max_order_size, order.size)
                    
                # Round to appropriate precision
                if hasattr(order, 'exchange'):
                    size_precision = 6  # Default
                    order.size = round(order.size, size_precision)
                    
        elif countermeasure == "cancel_variance":
            # For cancel operations, just mark that we should vary cancellation time
            if hasattr(order, 'metadata'):
                if not order.metadata:
                    order.metadata = {}
                order.metadata["vary_cancellation"] = True
                
        elif countermeasure == "longer_placements":
            # Indicate order should stay longer before cancelling
            if hasattr(order, 'time_in_force'):
                # Increase time in force if specified
                if order.time_in_force and order.time_in_force < 60:
                    order.time_in_force = order.time_in_force * 1.5
                    
        elif countermeasure == "reduced_frequency":
            # Mark order for reduced frequency processing
            if hasattr(order, 'metadata'):
                if not order.metadata:
                    order.metadata = {}
                order.metadata["reduced_frequency"] = True
                
        elif countermeasure == "forced_delay":
            # Force a significant delay
            delay_ms = random.randint(500, 1500)
            await asyncio.sleep(delay_ms / 1000)
            
        return order


class DecoyGenerator:
    """Generates believable decoy orders to mask trading intentions"""
    
    def __init__(self):
        """Initialize decoy generator"""
        self.decoy_configs = {
            "limit_order": {
                "placement": ["near_best", "mid_book", "far_book"],
                "lifetime": ["short", "medium", "long"],
                "size_profile": ["small", "medium", "matching"]
            },
            "iceberg_order": {
                "visibility": ["low", "medium", "high"],
                "refresh_interval": ["fast", "medium", "slow"],
                "size_profile": ["small", "medium", "large"]
            }
        }
        
    async def generate_decoys(self, real_order: Any, exchange: Any, num_decoys: int = 2) -> List[Any]:
        """
        Generate decoy orders based on a real order
        
        Args:
            real_order: The real order being placed
            exchange: Exchange the order is being placed on
            num_decoys: Number of decoy orders to generate
            
        Returns:
            List of decoy orders
        """
        try:
            # Choose decoy types to generate
            decoy_types = self._choose_decoy_types(real_order, num_decoys)
            
            decoys = []
            for decoy_type in decoy_types:
                # Generate each decoy
                decoy = await self._create_decoy(real_order, exchange, decoy_type)
                if decoy:
                    decoys.append(decoy)
                    
            logger.debug(f"Generated {len(decoys)} decoy orders")
            return decoys
            
        except Exception as e:
            logger.error(f"Error generating decoy orders: {str(e)}")
            return []
            
    def _choose_decoy_types(self, real_order: Any, num_decoys: int) -> List[str]:
        """Choose what types of decoys to generate"""
        # For now, just generate limit order decoys
        return ["limit_order"] * num_decoys
        
    async def _create_decoy(self, real_order: Any, exchange: Any, decoy_type: str) -> Optional[Any]:
        """
        Create a single decoy order
        
        Args:
            real_order: Real order to base decoy on
            exchange: Exchange for the order
            decoy_type: Type of decoy to create
            
        Returns:
            Decoy order or None if creation failed
        """
        try:
            # Create basic decoy structure by copying real order
            decoy = copy.deepcopy(real_order)
            
            # Mark as decoy in metadata
            if hasattr(decoy, 'metadata'):
                if not decoy.metadata:
                    decoy.metadata = {}
                decoy.metadata["is_decoy"] = True
            
            # Generate a new ID
            if hasattr(decoy, 'id'):
                decoy.id = f"decoy_{uuid.uuid4()}"
                
            if hasattr(decoy, 'client_order_id'):
                decoy.client_order_id = f"decoy_{uuid.uuid4()}"
                
            # Modify order based on decoy type
            if decoy_type == "limit_order":
                # Choose decoy config options
                placement = random.choice(self.decoy_configs["limit_order"]["placement"])
                lifetime = random.choice(self.decoy_configs["limit_order"]["lifetime"])
                size_profile = random.choice(self.decoy_configs["limit_order"]["size_profile"])
                
                # 1. Set opposite side for some decoys
                if random.random() < 0.7:  # 70% of decoys on opposite side
                    if hasattr(decoy, 'side'):
                        decoy.side = "buy" if decoy.side == "sell" else "sell"
                        
                # 2. Adjust price based on placement strategy
                if hasattr(decoy, 'price') and decoy.price:
                    # Get current best price
                    current_price = decoy.price
                    side = getattr(decoy, 'side', None)
                    
                    if placement == "near_best":
                        # Place near best price 
                        if side == "buy":
                            adjustment = random.uniform(-0.01, -0.005)  # Slightly below
                        else:  # sell
                            adjustment = random.uniform(0.005, 0.01)  # Slightly above
                    elif placement == "mid_book":
                        # Place in the middle of the order book
                        if side == "buy":
                            adjustment = random.uniform(-0.05, -0.02)  # Below
                        else:  # sell
                            adjustment = random.uniform(0.02, 0.05)  # Above
                    else:  # far_book
                        # Place far from best price
                        if side == "buy":
                            adjustment = random.uniform(-0.1, -0.05)  # Far below
                        else:  # sell
                            adjustment = random.uniform(0.05, 0.1)  # Far above
                            
                    # Apply price adjustment
                    decoy.price = current_price * (1 + adjustment)
                    
                    # Ensure using appropriate precision
                    if hasattr(exchange, 'price_precision'):
                        price_precision = exchange.price_precision
                    else:
                        price_precision = 8  # Default
                        
                    decoy.price = round(decoy.price, price_precision)
                    
                # 3. Adjust size based on profile
                if hasattr(decoy, 'size'):
                    real_size = decoy.size
                    
                    if size_profile == "small":
                        # Small size relative to real order
                        size_factor = random.uniform(0.1, 0.3)
                    elif size_profile == "medium":
                        # Medium size
                        size_factor = random.uniform(0.3, 0.7)
                    else:  # matching
                        # Similar to real order
                        size_factor = random.uniform(0.7, 1.1)
                        
                    decoy.size = real_size * size_factor
                    
                    # Respect minimum order size
                    if hasattr(exchange, 'min_order_size'):
                        decoy.size = max(exchange.min_order_size, decoy.size)
                        
                    # Round to appropriate precision
                    if hasattr(exchange, 'size_precision'):
                        size_precision = exchange.size_precision
                    else:
                        size_precision = 6  # Default
                        
                    decoy.size = round(decoy.size, size_precision)
                    
                # 4. Set lifetime based on profile
                if hasattr(decoy, 'time_in_force'):
                    if lifetime == "short":
                        decoy.time_in_force = random.randint(10, 30)  # seconds
                    elif lifetime == "medium":
                        decoy.time_in_force = random.randint(30, 120)
                    else:  # long
                        decoy.time_in_force = random.randint(120, 300)
                        
            elif decoy_type == "iceberg_order":
                # Configure iceberg-specific options
                visibility = random.choice(self.decoy_configs["iceberg_order"]["visibility"])
                
                # Set visible portion
                if hasattr(decoy, 'size'):
                    if visibility == "low":
                        visible_pct = random.uniform(0.05, 0.15)
                    elif visibility == "medium":
                        visible_pct = random.uniform(0.15, 0.3)
                    else:  # high
                        visible_pct = random.uniform(0.3, 0.5)
                        
                    if hasattr(decoy, 'metadata'):
                        decoy.metadata["visible_size"] = decoy.size * visible_pct
                        
            return decoy
            
        except Exception as e:
            logger.error(f"Error creating decoy order: {str(e)}")
            return None


class FingerprintAnalyzer:
    """Analyzes exchanges for bot detection mechanisms"""
    
    def __init__(self):
        """Initialize fingerprint analyzer"""
        self.exchange_profiles = {}
        self.last_analysis = {}
        self.analysis_validity = 86400  # 24 hours
        
    async def analyze_exchange(self, exchange: Any) -> float:
        """
        Analyze an exchange for bot detection risk
        
        Args:
            exchange: Exchange to analyze
            
        Returns:
            Detection risk score (0-1)
        """
        exchange_id = self._get_exchange_id(exchange)
        
        # Check if we have a recent analysis
        current_time = time.time()
        if exchange_id in self.last_analysis:
            last_time, risk_score = self.last_analysis[exchange_id]
            if current_time - last_time < self.analysis_validity:
                return risk_score
                
        # Perform new analysis
        risk_score = await self._calculate_risk_score(exchange)
        
        # Store result
        self.last_analysis[exchange_id] = (current_time, risk_score)
        
        logger.debug(f"Analyzed exchange {exchange_id}: detection risk {risk_score:.2f}")
        
        return risk_score
        
    def _get_exchange_id(self, exchange: Any) -> str:
        """Get a unique identifier for the exchange"""
        if hasattr(exchange, 'id'):
            return str(exchange.id)
        elif hasattr(exchange, 'name'):
            return str(exchange.name)
        else:
            return str(id(exchange))
            
    async def _calculate_risk_score(self, exchange: Any) -> float:
        """Calculate bot detection risk score for an exchange"""
        # In a real implementation, this would analyze:
        # 1. Known exchange policies about bots
        # 2. User experiences and reports
        # 3. Exchange API rate limiting
        # 4. Observed detection patterns
        
        # Start with a base score
        base_score = 0.5
        
        # Adjust based on exchange properties
        if hasattr(exchange, 'has_strict_rate_limits') and exchange.has_strict_rate_limits:
            base_score += 0.2
            
        if hasattr(exchange, 'has_user_agent_restrictions') and exchange.has_user_agent_restrictions:
            base_score += 0.1
            
        if hasattr(exchange, 'requires_human_verification') and exchange.requires_human_verification:
            base_score += 0.3
            
        # Check exchange name for well-known bot policy
        exchange_name = self._get_exchange_name(exchange).lower()
        
        if "binance" in exchange_name:
            # Binance has sophisticated detection 
            base_score = 0.7
        elif "coinbase" in exchange_name:
            # Coinbase has strict rate limits
            base_score = 0.6
        elif "kraken" in exchange_name:
            # Kraken has moderate detection
            base_score = 0.5
        elif "kucoin" in exchange_name:
            # KuCoin has some detection
            base_score = 0.6
            
        # Cap score at 0.95 (never assume perfect detection)
        return min(0.95, base_score)
        
    def _get_exchange_name(self, exchange: Any) -> str:
        """Get exchange name"""
        if hasattr(exchange, 'name'):
            return str(exchange.name)
        elif hasattr(exchange, 'id'):
            return str(exchange.id)
        else:
            return "unknown"


class DeceptionDefense:
    """Anti-detection countermeasures for trading bots"""
    
    def __init__(self):
        """Initialize deception defense system"""
        self.pattern_obfuscator = PatternObfuscator()
        self.decoy_generator = DecoyGenerator()
        self.fingerprint_analyzer = FingerprintAnalyzer()
        
    async def apply_countermeasures(self, order: Any, exchange: Any) -> Any:
        """
        Apply anti-detection countermeasures to an order
        
        Args:
            order: Order to protect
            exchange: Exchange the order will be placed on
            
        Returns:
            Protected order or a list containing the protected order and possibly decoys
        """
        # Analyze exchange for detection systems
        detection_risk = await self.fingerprint_analyzer.analyze_exchange(exchange)
        
        logger.debug(f"Detection risk for exchange: {detection_risk:.2f}")
        
        if detection_risk > 0.7:  # High risk of being detected as a bot
            # Apply strong countermeasures
            return await self.apply_strong_countermeasures(order, exchange)
        elif detection_risk > 0.3:  # Moderate risk
            # Apply moderate countermeasures
            return await self.apply_moderate_countermeasures(order, exchange)
        else:
            # Apply minimal countermeasures
            return await self.apply_minimal_countermeasures(order, exchange)
            
    async def apply_strong_countermeasures(self, order: Any, exchange: Any) -> Any:
        """
        Apply strong anti-detection countermeasures
        
        Args:
            order: Order to protect
            exchange: Exchange for the order
            
        Returns:
            List of protected order and decoys, or protected order
        """
        logger.info("Applying strong anti-detection countermeasures")
        
        # 1. Randomize order size slightly
        obfuscated_order = await self.pattern_obfuscator.apply_obfuscation(
            order, ["round_numbers", "fixed_sizes"]
        )
        
        # 2. Add random delay
        await self.add_random_delay(50, 200)
        
        # 3. Check if order is large enough to split
        min_order_size = self._get_min_order_size(exchange, order)
        
        if hasattr(obfuscated_order, 'size') and obfuscated_order.size > min_order_size * 3:
            # Split into multiple orders
            split_orders = await self.split_order(obfuscated_order, parts=3)
            
            # 4. Deploy decoy orders
            decoys = await self.decoy_generator.generate_decoys(obfuscated_order, exchange)
            
            # 5. Execute real orders and decoys in unpredictable sequence
            return await self.prepare_mixed_sequence(split_orders, decoys)
        else:
            # Just execute with randomized parameters
            return obfuscated_order
            
    async def apply_moderate_countermeasures(self, order: Any, exchange: Any) -> Any:
        """
        Apply moderate anti-detection countermeasures
        
        Args:
            order: Order to protect
            exchange: Exchange for the order
            
        Returns:
            Protected order (possibly with decoys)
        """
        logger.info("Applying moderate anti-detection countermeasures")
        
        # 1. Randomize order slightly
        obfuscated_order = await self.pattern_obfuscator.apply_obfuscation(
            order, ["round_numbers"]
        )
        
        # 2. Add small random delay
        await self.add_random_delay(20, 100)
        
        # 3. Decide whether to use decoys (50% chance)
        if random.random() < 0.5:
            # Generate 1-2 decoys
            num_decoys = random.randint(1, 2)
            decoys = await self.decoy_generator.generate_decoys(
                obfuscated_order, exchange, num_decoys
            )
            
            if decoys:
                # Return main order plus decoys
                return [obfuscated_order] + decoys
                
        return obfuscated_order
        
    async def apply_minimal_countermeasures(self, order: Any, exchange: Any) -> Any:
        """
        Apply minimal anti-detection countermeasures
        
        Args:
            order: Order to protect
            exchange: Exchange for the order
            
        Returns:
            Slightly protected order
        """
        logger.debug("Applying minimal anti-detection countermeasures")
        
        # Just add a small amount of randomization
        obfuscated_order = await self.pattern_obfuscator.apply_obfuscation(
            order, ["fixed_interval"]
        )
        
        # Small delay occasionally (20% chance)
        if random.random() < 0.2:
            await self.add_random_delay(10, 50)
            
        return obfuscated_order
        
    def _get_min_order_size(self, exchange: Any, order: Any) -> float:
        """Get minimum order size for the exchange"""
        if hasattr(exchange, 'min_order_size'):
            return exchange.min_order_size
        elif hasattr(order, 'min_order_size'):
            return order.min_order_size
        else:
            # Default minimum
            return 0.001
            
    async def add_random_delay(self, min_ms: int = 10, max_ms: int = 100):
        """
        Add a random delay to make behavior less predictable
        
        Args:
            min_ms: Minimum delay in milliseconds
            max_ms: Maximum delay in milliseconds
        """
        delay = random.uniform(min_ms, max_ms) / 1000  # Convert to seconds
        await asyncio.sleep(delay)
        
    async def split_order(self, order: Any, parts: int = 2) -> List[Any]:
        """
        Split an order into multiple smaller orders
        
        Args:
            order: Order to split
            parts: Number of parts to split into
            
        Returns:
            List of smaller orders
        """
        if not hasattr(order, 'size'):
            # Can't split if no size attribute
            return [order]
            
        # Calculate part size, slightly randomized
        base_part_size = order.size / parts
        split_orders = []
        
        remaining_size = order.size
        for i in range(parts - 1):  # Process all but the last part
            # Randomize this part's size slightly (±10%)
            part_size = base_part_size * random.uniform(0.9, 1.1)
            
            # Make sure we don't exceed remaining size
            part_size = min(part_size, remaining_size * 0.95)
            
            # Create new order with appropriate size
            new_order = copy.deepcopy(order)
            new_order.size = part_size
            
            # Generate a new ID
            if hasattr(new_order, 'id'):
                new_order.id = f"{order.id}_part{i+1}"
                
            if hasattr(new_order, 'client_order_id'):
                new_order.client_order_id = f"{order.client_order_id}_part{i+1}"
                
            split_orders.append(new_order)
            remaining_size -= part_size
            
        # Last part gets the remainder
        if remaining_size > 0:
            last_order = copy.deepcopy(order)
            last_order.size = remaining_size
            
            if hasattr(last_order, 'id'):
                last_order.id = f"{order.id}_part{parts}"
                
            if hasattr(last_order, 'client_order_id'):
                last_order.client_order_id = f"{order.client_order_id}_part{parts}"
                
            split_orders.append(last_order)
            
        return split_orders
        
    async def prepare_mixed_sequence(self, real_orders: List[Any], decoy_orders: List[Any]) -> List[Any]:
        """
        Mix real and decoy orders in an unpredictable sequence
        
        Args:
            real_orders: List of real orders
            decoy_orders: List of decoy orders
            
        Returns:
            Mixed sequence of orders
        """
        # Mix real and decoy orders
        all_orders = real_orders.copy()
        all_orders.extend(decoy_orders)
        
        # Shuffle to get a random sequence
        random.shuffle(all_orders)
        
        # Mark the sequence for correct processing
        for order in all_orders:
            if hasattr(order, 'metadata'):
                if not order.metadata:
                    order.metadata = {}
                order.metadata["part_of_mixed_sequence"] = True
                
        return all_orders
