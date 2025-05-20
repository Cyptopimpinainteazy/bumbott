#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Real MEV Trade Executor

This script executes real MEV trades across multiple L2 networks using deployed flashloan contracts.
It includes improved error handling, contract verification, and token decimal handling.
"""

import os
import json
import time
import logging
import datetime
from web3 import Web3
from dotenv import load_dotenv
from eth_account.messages import encode_defunct

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mev_trades.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MEV_EXECUTOR")

# Load environment variables
load_dotenv()

# Configuration
REAL_MODE = True  # Set to True for real trades, False for simulation
MICRO_TRANSACTIONS = True  # Use very small amounts for testing
MAX_TRADES_PER_SESSION = 25  # Safety limit
COOLDOWN_BETWEEN_TRADES = 60  # Seconds between trades
PREFERRED_NETWORKS = ["polygon", "arbitrum", "optimism"]  # Order of network preference

# Token decimal mappings (for proper amount calculations)
TOKEN_DECIMALS = {
    "USDC": 6,
    "USDT": 6,
    "DAI": 18,
    "WETH": 18,
    "WMATIC": 18,
    "WBTC": 8,
    "LINK": 18,
    "UNI": 18,
    "AAVE": 18,
}

# Contract addresses by network
CONTRACT_ADDRESSES = {
    "polygon": {
        "flashloan": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",  # QuickSwap Router
        "router": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",  # SushiSwap Router
        "factory": "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32"  # Quickswap Factory
    },
    "arbitrum": {
        "flashloan": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",  # SushiSwap Router
        "router": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
        "factory": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4"
    }
}


TOKEN_ADDRESSES = {
    "polygon": {
        "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
        "WMATIC": "0x0000000000000000000000000000000000001010",
        "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    },
    "arbitrum": {
        "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "USDC": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"
    }
}

# Token pairs by network that we want to focus on
PREFERRED_PAIRS = {
    "polygon": [
        ("USDC", "WMATIC"),
        ("WETH", "WMATIC"),
        ("USDC", "WETH"),
    ],
    "arbitrum": [
        ("USDC", "WETH"),
        ("USDT", "WETH"),
        ("WBTC", "WETH"),
    ],
    "optimism": [
        ("USDC", "WETH"),
        ("DAI", "WETH"),
        ("LINK", "WETH"),
    ],
}

class Web3Connection:
    """Manages Web3 connections to multiple networks."""
    
    def __init__(self):
        self.connections = {}
        self.network_urls = {
            "polygon": os.getenv("CHAINSTACK_POLYGON_URL"),
            "arbitrum": os.getenv("CHAINSTACK_ARBITRUM_URL"),
            "optimism": os.getenv("CHAINSTACK_OPTIMISM_URL"),
            "bsc": os.getenv("CHAINSTACK_BSC_URL"),
        }

    def connect_all(self):
        """Establish validated connections"""
        for network, url in self.network_urls.items():
            if not url:
                logger.warning(f"Skipping {network} - No URL configured")
                continue
            
            try:
                w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 10}))
                if not w3.is_connected():
                    raise ConnectionError(f"Failed to connect to {network}")
                
                # Verify chain ID
                expected_chain_id = {
                    "polygon": 137,
                    "arbitrum": 42161,
                    "optimism": 10
                }.get(network)
                
                if w3.eth.chain_id != expected_chain_id:
                    raise ValueError(f"Chain ID mismatch on {network}")
                
                self.connections[network] = w3
                logger.info(f"Validated connection to {network}")
                
            except Exception as e:
                logger.error(f"Network connection failed: {str(e)}")
                continue

    def get_connection(self, network_id):
        """Get Web3 connection for a specific network."""
        if network_id not in self.connections:
            raise ValueError(f"No connection available for {network_id}")
        return self.connections[network_id]
    
    def is_connected(self, network_id):
        """Check if a specific network is connected."""
        return network_id in self.connections and self.connections[network_id].is_connected()
    
    def get_connected_networks(self):
        """Return a list of all connected networks."""
        return [net for net, w3 in self.connections.items() if w3.is_connected()]


class MEVTrader:
    def __init__(self, web3_connection):
        self.web3_connection = web3_connection
        self.address = os.getenv("METAMASK_ADDRESS")
        self.private_key = os.getenv("METAMASK_PRIVATE_KEY")
        self.trades_executed = 0
        self.failed_attempts = 0
        self.last_trade_time = None
        self.flashloan_abi = []  # Initialize first
        self.load_abis()  # Then load
        
    def load_abis(self):
        """Load contract ABIs with validation"""
        try:
            # Load flashloan ABI
            with open("abis/flashloan_abi.json", "r") as f:
                self.flashloan_abi = json.load(f)
                
            # Load router ABI 
            with open("abis/router_abi.json", "r") as f:
                self.router_abi = json.load(f)
                
            logger.info("ABIs loaded successfully")
            
        except Exception as e:
            logger.error(f"ABI loading failed: {str(e)}")
            raise RuntimeError("Critical infrastructure failure - ABIs missing")
                
            logger.info("ABIs loaded successfully")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in ABI file: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"ABI loading failed: {str(e)}")
            raise RuntimeError("Critical infrastructure failure - ABIs corrupted")

        with open("abis/router_abi.json", "r") as f:
            self.router_abi = json.load(f)
            
        with open("abis/factory_abi.json", "r") as f:
            self.factory_abi = json.load(f)
            
        logger.info("ABIs loaded successfully")
        
    def convert_to_token_units(self, amount, token_symbol):
        """Convert human-readable amounts to token units based on decimals."""
        decimals = TOKEN_DECIMALS.get(token_symbol, 18)  # Default to 18 if not found
        return int(amount * (10 ** decimals))
        
    def convert_from_token_units(self, amount, token_symbol):
        """Convert token units to human-readable amounts based on decimals."""
        decimals = TOKEN_DECIMALS.get(token_symbol, 18)  # Default to 18 if not found
        return amount / (10 ** decimals)
    
    def verify_contract(self, network, contract_type):
        """Verify a contract exists and has code."""
        contract_address = CONTRACT_ADDRESSES.get(network, {}).get(contract_type)
        if not contract_address:
            logger.error(f"No {contract_type} contract address configured for {network}")
            return False
            
        w3 = self.web3_connection.get_connection(network)
        code = w3.eth.get_code(Web3.to_checksum_address(contract_address))
        
        if code == b'' or code == '0x':
            logger.error(f"{contract_type} contract on {network} has no code at {contract_address}")
            return False
            
        logger.info(f"{contract_type} contract on {network} verified at {contract_address}")
        return True
        
    def check_wallet_balance(self, network):
        """Check wallet balance on specific network."""
        w3 = self.web3_connection.get_connection(network)
        balance_wei = w3.eth.get_balance(Web3.to_checksum_address(self.address))
        balance_eth = w3.from_wei(balance_wei, 'ether')
        
        logger.info(f"Wallet balance on {network}: {balance_eth} ETH")
        
        # Ensure we have enough for gas fees (0.01 ETH minimum)
        if balance_eth < 0.01:
            logger.warning(f"Low balance on {network}: {balance_eth} ETH")
            return False
            
        return True
        
    def execute_sandwich_attack(self, network, token_pair, amount, quantum_params=None):
        """Execute a sandwich attack MEV trade."""
        # Safety checks
        if self.trades_executed >= MAX_TRADES_PER_SESSION:
            logger.warning("Maximum trades per session reached")
            return False
            
        current_time = time.time()
        if self.last_trade_time is not None and (current_time - self.last_trade_time) < COOLDOWN_BETWEEN_TRADES:
            logger.warning(f"Cooldown active - {COOLDOWN_BETWEEN_TRADES - (current_time - self.last_trade_time):.1f}s remaining")
            return False
            
        # Verify contracts
        if not self.verify_contract(network, "flashloan"):
            return False
            
        # Verify we have funds
        if not self.check_wallet_balance(network):
            return False
            
        # Setup
        w3 = self.web3_connection.get_connection(network)
        flashloan_address = Web3.to_checksum_address(CONTRACT_ADDRESSES[network]["flashloan"])
        flashloan_contract = w3.eth.contract(address=flashloan_address, abi=self.flashloan_abi)
        
        token0, token1 = token_pair
        
        # Use micro amounts for testing if enabled
        if MICRO_TRANSACTIONS:
            if "ETH" in token0 or "MATIC" in token0:
                amount0 = 0.001  # 0.001 ETH/MATIC
            else:
                amount0 = 1  # 1 USDC/USDT/etc
        else:
            amount0 = amount
            
        # Convert to token units
        amount0_units = self.convert_to_token_units(amount0, token0)
        
        try:
            # Prepare transaction
            gas_price = w3.eth.gas_price
            # Add 10% to gas price to ensure transaction goes through
            adjusted_gas_price = int(gas_price * 1.1)
            
            # Get current nonce
            nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(self.address))
            
            # Prepare function call with quantum parameters if provided
            if quantum_params:
                txn = flashloan_contract.functions.executeSandwichAttack(
                    token0,
                    token1,
                    amount0_units,
                    quantum_params["entanglement_factor"],
                    quantum_params["superposition_threshold"]
                ).build_transaction({
                    'from': self.address,
                    'gas': 3000000,  # High gas limit
                    'gasPrice': adjusted_gas_price,
                    'nonce': nonce,
                })
            else:
                # Standard call without quantum parameters
                txn = flashloan_contract.functions.executeSandwichAttack(
                    token0,
                    token1,
                    amount0_units
                ).build_transaction({
                    'from': self.address,
                    'gas': 3000000,  # High gas limit
                    'gasPrice': adjusted_gas_price,
                    'nonce': nonce,
                })
                
            # Log transaction details before sending
            logger.info(f"Prepared sandwich attack on {network}: {token0}/{token1} with {amount0} {token0}")
            
            # First, try a dry run to catch any issues
            try:
                # Simulate the transaction
                w3.eth.call(txn)
                logger.info("Dry run successful, proceeding with real transaction")
            except Exception as e:
                logger.error(f"Dry run failed: {str(e)}")
                return False
                
            # Sign and send transaction
            signed_txn = w3.eth.account.sign_transaction(txn, private_key=self.private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            logger.info(f"Transaction sent! Hash: {tx_hash_hex}")
            
            # Wait for confirmation
            logger.info("Waiting for transaction confirmation...")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            
            # Check transaction status
            if receipt.status == 1:
                logger.info(f"Transaction confirmed! Gas used: {receipt.gasUsed}")
                self.trades_executed += 1
                self.last_trade_time = time.time()
                return True
            else:
                logger.error(f"Transaction failed! Receipt: {json.dumps(dict(receipt), default=str)}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing sandwich attack: {str(e)}")
            return False
            
    def execute_arbitrage(self, network, token_path, amount, quantum_params=None):
        """Execute an arbitrage MEV trade across multiple DEXes."""
        # Similar implementation to sandwich attack with arbitrage-specific logic
        # Safety checks
        if self.trades_executed >= MAX_TRADES_PER_SESSION:
            logger.warning("Maximum trades per session reached")
            return False
            
        current_time = time.time()
        if self.last_trade_time is not None and (current_time - self.last_trade_time) < COOLDOWN_BETWEEN_TRADES:
            logger.warning(f"Cooldown active - {COOLDOWN_BETWEEN_TRADES - (current_time - self.last_trade_time):.1f}s remaining")
            return False
            
        # Verify contracts
        if not self.verify_contract(network, "flashloan"):
            return False
            
        # Verify we have funds
        if not self.check_wallet_balance(network):
            return False
            
        # Setup
        w3 = self.web3_connection.get_connection(network)
        flashloan_address = Web3.to_checksum_address(CONTRACT_ADDRESSES[network]["flashloan"])
        flashloan_contract = w3.eth.contract(address=flashloan_address, abi=self.flashloan_abi)
        
        start_token = token_path[0]
        
        # Use micro amounts for testing if enabled
        if MICRO_TRANSACTIONS:
            if "ETH" in start_token or "MATIC" in start_token:
                amount_value = 0.001  # 0.001 ETH/MATIC
            else:
                amount_value = 1  # 1 USDC/USDT/etc
        else:
            amount_value = amount
            
        # Convert to token units
        amount_units = self.convert_to_token_units(amount_value, start_token)
        
        try:
            # Prepare transaction
            gas_price = w3.eth.gas_price
            # Add 10% to gas price to ensure transaction goes through
            adjusted_gas_price = int(gas_price * 1.1)
            
            # Get current nonce
            nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(self.address))
            
            # Prepare function call
            txn = flashloan_contract.functions.executeArbitrage(
                token_path,
                amount_units
            ).build_transaction({
                'from': self.address,
                'gas': 3000000,  # High gas limit
                'gasPrice': adjusted_gas_price,
                'nonce': nonce,
            })
                
            # Log transaction details before sending
            logger.info(f"Prepared arbitrage on {network}: {' -> '.join(token_path)} with {amount_value} {start_token}")
            
            # First, try a dry run to catch any issues
            try:
                # Simulate the transaction
                w3.eth.call(txn)
                logger.info("Dry run successful, proceeding with real transaction")
            except Exception as e:
                logger.error(f"Dry run failed: {str(e)}")
                return False
                
            # Sign and send transaction
            signed_txn = w3.eth.account.sign_transaction(txn, private_key=self.private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            logger.info(f"Transaction sent! Hash: {tx_hash_hex}")
            
            # Wait for confirmation
            logger.info("Waiting for transaction confirmation...")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            
            # Check transaction status
            if receipt.status == 1:
                logger.info(f"Transaction confirmed! Gas used: {receipt.gasUsed}")
                self.trades_executed += 1
                self.last_trade_time = time.time()
                return True
            else:
                logger.error(f"Transaction failed! Receipt: {json.dumps(dict(receipt), default=str)}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing arbitrage: {str(e)}")
            return False


def main():
    """Main execution function."""
    logger.info("=" * 50)
    logger.info("Starting Real MEV Trade Executor")
    logger.info(f"Mode: {'REAL' if REAL_MODE else 'SIMULATION'}")
    logger.info(f"Micro Transactions: {'ENABLED' if MICRO_TRANSACTIONS else 'DISABLED'}")
    logger.info("=" * 50)
    
    # Initialize connections
    web3_conn = Web3Connection()
    web3_conn.connect_all()
    
    connected_networks = web3_conn.get_connected_networks()
    if not connected_networks:
        logger.error("No networks connected. Exiting...")
        return
        
    logger.info(f"Connected to networks: {', '.join(connected_networks)}")
    
    # Initialize trader
    try:
        trader = MEVTrader(web3_conn)
        logger.info(f"Trader initialized with wallet: {trader.address}")
    except Exception as e:
        logger.error(f"Failed to initialize trader: {str(e)}")
        return
        
    # Check balances on all networks
    for network in connected_networks:
        trader.check_wallet_balance(network)
        
    # Check contracts on all networks
    for network in connected_networks:
        for contract_type in ["flashloan", "router", "factory"]:
            trader.verify_contract(network, contract_type)
            
    # Execute trades on preferred networks
    for network in PREFERRED_NETWORKS:
        if network not in connected_networks:
            logger.warning(f"Preferred network {network} not connected, skipping")
            continue
            
        logger.info(f"Looking for trading opportunities on {network}...")
        
        # Execute trades for preferred pairs
        for token_pair in PREFERRED_PAIRS.get(network, []):
            # Ask for confirmation before executing trade
            print(f"\nReady to execute sandwich attack on {network}: {token_pair[0]}/{token_pair[1]}")
            confirm = input("Proceed? (y/n): ").strip().lower()
            
            if confirm != 'y':
                logger.info("Trade skipped by user")
                continue
                
            # Execute trade
            success = trader.execute_sandwich_attack(
                network=network,
                token_pair=token_pair,
                amount=0.1,  # Base amount before micro-transaction adjustment
                quantum_params={
                    "entanglement_factor": 0.75,
                    "superposition_threshold": 0.5
                } if "quantum" in input("Use quantum parameters? (y/n): ").lower() else None
            )
            
            if success:
                logger.info(f"Successfully executed trade on {network} for {token_pair[0]}/{token_pair[1]}")
            else:
                logger.error(f"Failed to execute trade on {network} for {token_pair[0]}/{token_pair[1]}")
                
            # Cooldown between trades
            if trader.trades_executed < MAX_TRADES_PER_SESSION:
                logger.info(f"Cooling down for {COOLDOWN_BETWEEN_TRADES} seconds...")
                time.sleep(COOLDOWN_BETWEEN_TRADES)
                
    # Summary
    logger.info("=" * 50)
    logger.info(f"Trading session completed. Trades executed: {trader.trades_executed}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
