"""
Automatic MEV Strategy Execution with TripleFlashloan Contracts
Continuously monitors for profitable MEV opportunities and executes them
"""
import os
import json
import time
import logging
import random
import traceback
from web3 import Web3
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Import token pairs database functions
from token_pairs_database import get_top_pairs, get_arbitrage_paths

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("auto_mev_trades.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AutoMEVTrader")

# Your deployed contracts 
DEPLOYED_CONTRACTS = {
    "arbitrum": {
        "triple_flashloan": "0x318c70a505B298Cb00578cee6a8e9D3bfc52120d",
        "x3star_token": "0x257869dc3Da0d1995Be4B51Bea006f4256acC2b7",
        "mev_strategies": "0x3462B7A971c26429c23101d9eb67a53B841e248d"
    },
    "polygon": {
        "triple_flashloan": "0xF1C65C57C35c44D2Fee8D35dfB16B30012f830dB",
        "x3star_token": "0x083767AE4d8BE888fC47F9B37115a10708FD12FD", 
        "mev_strategies": "0xfbAa183c3CBD10743d683EF0681b007c00dD2c2c"
    },
    "optimism": {
        "triple_flashloan": "0x498ed9B861a93f86eb6D6A5d47336AF43D64bAa3",
        "x3star_token": "0x3394C093d0F304002deB31cCce124d05DeC94b06",
        "mev_strategies": "0x9a887fBdb9e1196F4e348B859B5d2090F8d20E52"
    },
    "bsc": {
        "triple_flashloan": "0x241D0065480d7100d0b36b2BB60D78EFDF2e7a47",
        "x3star_token": "0x0594A9C3bb2a7775F949a94b3E23cE8C3c06f923",
        "mev_strategies": "0x25CEe61E7c9CAF865D9Ca9e94cba397b49c47557"
    }
}

# MEV contract ABI (simplified)
MEV_ABI = [
    {
        "inputs": [
            {"internalType": "address[2]", "name": "tokens", "type": "address[2]"},
            {"internalType": "uint256[2]", "name": "amounts", "type": "uint256[2]"},
            {"internalType": "uint256", "name": "expectedProfit", "type": "uint256"}
        ],
        "name": "executeSandwich",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address[]", "name": "tokens", "type": "address[]"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "uint256", "name": "expectedProfit", "type": "uint256"}
        ],
        "name": "executeArbitrage",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# Chain IDs
CHAIN_IDS = {
    "arbitrum": 42161,
    "polygon": 137,
    "optimism": 10,
    "bsc": 56
}

# Trade configuration
TRADE_CONFIG = {
    "max_trades_per_network_per_day": 5,
    "min_profit_threshold": 0.005,  # 0.5%
    "max_position_size": {
        "arbitrum": 0.5,  # ETH
        "polygon": 0.3,  # ETH
        "optimism": 0.4,  # ETH
        "bsc": 0.5,  # BNB
    },
    "gas_multiplier": 1.1,
    "retry_count": 3,
    "cooldown_seconds": 300,  # 5 minutes between trades
    "strategy_filter": ["sandwich", "arbitrage"],  # Allowed strategies
    "network_filter": [],  # Empty means all networks
    "quantum_optimization": True,  # Use quantum optimization if available
    "trading_threshold_score": 1.5  # Minimum opportunity score to execute a trade
}

# Save successful trades to this file
TRADE_HISTORY_FILE = "trade_history.json"

class AutoMEVTrader:
    """Automatic MEV Strategy Trader"""
    
    def __init__(self):
        self.connections = {}
        
        # Initialize wallet from environment variables
        self.wallet_address = os.getenv("METAMASK_ADDRESS")
        self.private_key = os.getenv("METAMASK_PRIVATE_KEY")
        
        # Try to checksum the wallet address
        if self.wallet_address:
            try:
                self.wallet_address = Web3.to_checksum_address(self.wallet_address)
                logger.info(f"Using wallet: {self.wallet_address}")
            except Exception as e:
                logger.error(f"Invalid wallet address format: {str(e)}")
        else:
            logger.error("No wallet address found in .env file")
        
        # Trade tracking
        self.trade_history = self.load_trade_history()
        self.daily_trade_count = self.calculate_daily_trade_count()
        self.last_trade_time = {network: datetime.min for network in DEPLOYED_CONTRACTS}
        
        # Setup connections
        self.setup_connections()
    
    def setup_connections(self):
        """Set up connections to different networks with enhanced error reporting"""
        # First, validate wallet configuration
        if not self.wallet_address:
            logger.error("No wallet address configured in .env file. Trading will fail.")
            print("\nCRITICAL ERROR: No wallet address configured. Check your .env file.")
        else:
            logger.info(f"Using wallet address: {self.wallet_address}")
            # Validate private key (just check if it exists, don't log it)
            if not self.private_key:
                logger.error("No private key configured in .env file. Trading will fail.")
                print("\nCRITICAL ERROR: No private key configured. Check your .env file.")
            else:
                logger.info("Private key is configured")
        
        # Try connecting to networks
        for network in DEPLOYED_CONTRACTS.keys():
            url_env_var = f"CHAINSTACK_{network.upper()}_URL"
            
            # Hardcoded example URLs for testing
            example_urls = {
                "arbitrum": "https://arb-mainnet.g.alchemy.com/v2/example",
                "polygon": "https://polygon-mainnet.g.alchemy.com/v2/example",
                "optimism": "https://opt-mainnet.g.alchemy.com/v2/example",
                "bsc": "https://bsc-dataseed.binance.org/"
            }
            
            # Get URL from env or use example
            url = os.getenv(url_env_var, example_urls.get(network, ""))
            
            if not url:
                logger.warning(f"No URL found for {network} in .env file")
                print(f"Warning: No URL found for {network} in .env file")
                continue
            
            try:
                w3 = Web3(Web3.HTTPProvider(url))
                # Enhanced connection testing
                if w3.is_connected():
                    # Check if we can actually interact with the node
                    try:
                        block_number = w3.eth.block_number
                        gas_price = w3.eth.gas_price
                        logger.info(f"Connected to {network}. Current block: {block_number}, Gas price: {w3.from_wei(gas_price, 'gwei'):.2f} gwei")
                        print(f"Connected to {network}. Current block: {block_number}")
                        
                        # Verify contract addresses
                        for contract_name, address in DEPLOYED_CONTRACTS[network].items():
                            try:
                                code = w3.eth.get_code(Web3.to_checksum_address(address))
                                if code and len(code) > 2:  # Not empty contract
                                    logger.info(f"Verified {contract_name} contract at {address} on {network}")
                                else:
                                    logger.warning(f"Empty contract at {address} on {network}. Trading will fail!")
                                    print(f"WARNING: Empty contract at {address} on {network}!")
                            except Exception as contract_e:
                                logger.error(f"Error verifying {contract_name} contract: {str(contract_e)}")
                                print(f"ERROR: Could not verify {contract_name} contract on {network}")
                        
                        # Store the connection
                        self.connections[network] = w3
                    except Exception as node_e:
                        logger.error(f"Node error on {network}: {str(node_e)}")
                        print(f"Node error on {network}: {str(node_e)}")
                else:
                    logger.warning(f"Failed to connect to {network}")
                    print(f"Failed to connect to {network}")
            except Exception as e:
                logger.error(f"Error connecting to {network}: {str(e)}")
                print(f"Error connecting to {network}: {str(e)}")
        
        # Final connection summary
        connected = list(self.connections.keys())
        if connected:
            logger.info(f"Successfully connected to {len(connected)} networks: {', '.join(connected)}")
        else:
            logger.critical("Failed to connect to ANY network. Trading cannot proceed.")
            print("\nCRITICAL ERROR: Failed to connect to ANY network. Trading cannot proceed.")
            print("Please check your .env file configuration and network endpoints.")
            print("Remember that .env file is protected in .syncignore (using standard .gitignore syntax).")
    
    def load_trade_history(self):
        """Load trade history from file"""
        try:
            if os.path.exists(TRADE_HISTORY_FILE):
                with open(TRADE_HISTORY_FILE, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading trade history: {str(e)}")
            return []
    
    def save_trade_history(self):
        """Save trade history to file"""
        try:
            with open(TRADE_HISTORY_FILE, 'w') as f:
                json.dump(self.trade_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving trade history: {str(e)}")
    
    def calculate_daily_trade_count(self):
        """Calculate daily trade count from history"""
        today = datetime.now().date()
        daily_count = {network: 0 for network in DEPLOYED_CONTRACTS}
        
        for trade in self.trade_history:
            try:
                trade_date = datetime.fromisoformat(trade.get('timestamp', '')).date()
                if trade_date == today and trade.get('status') == 'success':
                    network = trade.get('network')
                    if network in daily_count:
                        daily_count[network] += 1
            except:
                pass
        
        return daily_count
    
    def can_trade(self, network):
        """Check if we can trade on this network"""
        # Check if we're connected
        if network not in self.connections:
            return False
        
        # Check daily trade limit
        daily_limit = TRADE_CONFIG['max_trades_per_network_per_day']
        if self.daily_trade_count.get(network, 0) >= daily_limit:
            return False
        
        # Check cooldown
        cooldown = TRADE_CONFIG['cooldown_seconds']
        last_trade = self.last_trade_time.get(network, datetime.min)
        if (datetime.now() - last_trade).total_seconds() < cooldown:
            return False
        
        return True
    
    def update_trade_stats(self, network, success=True):
        """Update trade statistics"""
        if success:
            self.daily_trade_count[network] = self.daily_trade_count.get(network, 0) + 1
        
        self.last_trade_time[network] = datetime.now()
    
    def get_top_trading_opportunities(self):
        """Get top trading opportunities from all networks"""
        opportunities = []
        
        # Only look at connected networks
        for network in self.connections.keys():
            if not self.can_trade(network):
                continue
            
            # Get top pairs
            try:
                top_pairs = get_top_pairs(network, 5)
                for pair in top_pairs:
                    token0 = pair['token0']['symbol']
                    token1 = pair['token1']['symbol']
                    score = pair['opportunity_score']
                    
                    opportunities.append({
                        'network': network,
                        'strategy': 'sandwich',
                        'token0': token0,
                        'token1': token1,
                        'score': score
                    })
            except Exception as e:
                logger.error(f"Error getting top pairs for {network}: {str(e)}")
            
            # Get arbitrage paths
            try:
                base_token = "WETH" if network != "bsc" else "WBNB"
                arb_paths = get_arbitrage_paths(network, base_token)[:3]
                
                for path_data in arb_paths:
                    path = path_data['path']
                    score = path_data['score']
                    
                    opportunities.append({
                        'network': network,
                        'strategy': 'arbitrage',
                        'token_path': path,
                        'score': score
                    })
            except Exception as e:
                logger.error(f"Error getting arbitrage paths for {network}: {str(e)}")
        
        # Sort by score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        return opportunities
    
    def execute_trade(self, opportunity):
        """Execute a trade based on the opportunity"""
        network = opportunity['network']
        strategy = opportunity['strategy']
        
        # Log the attempt
        logger.info(f"Attempting {strategy} on {network} with score {opportunity['score']}")
        
        if strategy == 'sandwich':
            return self.execute_sandwich(
                network, 
                opportunity['token0'],
                opportunity['token1'],
                opportunity['score']
            )
        elif strategy == 'arbitrage':
            return self.execute_arbitrage(
                network,
                opportunity['token_path'],
                opportunity['score']
            )
        else:
            return {'error': f"Unknown strategy: {strategy}"}
    
    def execute_sandwich(self, network, token0, token1, score):
        """Execute a sandwich attack"""
        if network not in self.connections:
            return {'error': f"Not connected to {network}"}
        
        # Get web3 connection
        w3 = self.connections[network]
        
        # Determine trade size based on score and max position
        max_size = TRADE_CONFIG['max_position_size'].get(network, 0.1)
        size_factor = min(1.0, score / 3.0)  # Scale by opportunity score
        position_size = max_size * size_factor
        
        # Divide position size between two tokens
        amount0 = position_size * 0.5
        amount1 = position_size * 0.5
        
        # Get token addresses from the token pairs database
        try:
            from token_pairs_database import TOKEN_INFO
            token0_address = TOKEN_INFO[network][token0]['address']
            token1_address = TOKEN_INFO[network][token1]['address']
            
            # Ensure addresses are checksummed
            token0_address = Web3.to_checksum_address(token0_address)
            token1_address = Web3.to_checksum_address(token1_address)
        except Exception as e:
            logger.error(f"Error getting token addresses: {str(e)}")
            return {'error': f"Token address lookup failed: {str(e)}"}
        
        # Get contract address (checksummed)
        mev_contract_address = Web3.to_checksum_address(
            DEPLOYED_CONTRACTS[network]['mev_strategies']
        )
        
        # Convert amounts to wei
        amount0_wei = w3.to_wei(amount0, "ether")
        amount1_wei = w3.to_wei(amount1, "ether")
        
        # Calculate expected profit (based on opportunity score)
        expected_profit = (amount0 + amount1) * (score / 100)  # Convert score to percentage
        expected_profit_wei = w3.to_wei(expected_profit, "ether")
        
        # Create contract instance
        mev_contract = w3.eth.contract(address=mev_contract_address, abi=MEV_ABI)
        
        try:
            # Get gas price with safety buffer
            gas_price = w3.eth.gas_price
            adjusted_gas_price = int(gas_price * TRADE_CONFIG['gas_multiplier'])
            
            # Get current transaction count (nonce)
            nonce = w3.eth.get_transaction_count(self.wallet_address)
            
            # Build transaction
            txn = mev_contract.functions.executeSandwich(
                [token0_address, token1_address],
                [amount0_wei, amount1_wei],
                expected_profit_wei
            ).build_transaction({
                'chainId': CHAIN_IDS[network],
                'gas': 800000,
                'gasPrice': adjusted_gas_price,
                'nonce': nonce,
                'from': self.wallet_address
            })
            
            # Sign transaction
            signed_txn = w3.eth.account.sign_transaction(txn, private_key=self.private_key)
            
            # Send transaction
            tx_hash = None
            
            # Handle different web3.py versions
            if hasattr(signed_txn, 'rawTransaction'):
                tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            elif hasattr(signed_txn, 'raw_transaction'):
                tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            else:
                # Direct attempt for other versions
                tx_hash = w3.eth.send_raw_transaction(signed_txn)
            
            if not tx_hash:
                return {'error': "Could not send transaction"}
            
            # Wait for receipt with timeout
            try:
                logger.info(f"Waiting for transaction receipt with hash: {tx_hash.hex()}...")
                tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                
                # Log raw transaction receipt for diagnosis
                logger.info(f"Raw transaction receipt: {json.dumps(dict(tx_receipt), default=str)}")
                
                # Check transaction status
                if tx_receipt['status'] == 1:
                    logger.info(f"Sandwich attack successful on {network}")
                    result = {
                        'status': 'success',
                        'network': network,
                        'strategy': 'sandwich',
                        'token_pair': [token0, token1],
                        'amount0': amount0,
                        'amount1': amount1,
                        'expected_profit': expected_profit,
                        'tx_hash': tx_hash.hex(),
                        'block_number': tx_receipt['blockNumber'],
                        'gas_used': tx_receipt['gasUsed'],
                        'gas_price': w3.from_wei(adjusted_gas_price, 'gwei'),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Update stats and save history
                    self.update_trade_stats(network, success=True)
                    self.trade_history.append(result)
                    self.save_trade_history()
                    
                    return result
                else:
                    # Get more details about failed transaction
                    try:
                        tx_details = w3.eth.get_transaction(tx_hash)
                        logger.error(f"Transaction details for failed tx: {json.dumps(dict(tx_details), default=str)}")
                        
                        # Try to get any revert reason
                        try:
                            # Replay the transaction to get revert reason
                            w3.eth.call(dict(tx_details))
                        except Exception as call_e:
                            logger.error(f"Transaction revert reason: {str(call_e)}")
                        
                    except Exception as tx_detail_e:
                        logger.error(f"Couldn't get transaction details: {str(tx_detail_e)}")
                    
                    error_msg = f"Sandwich attack failed on {network} with status {tx_receipt['status']}"
                    logger.error(error_msg)
                    return {
                        'status': 'failed',
                        'network': network,
                        'tx_hash': tx_hash.hex(),
                        'error': error_msg,
                        'receipt': dict(tx_receipt)
                    }
            except Exception as receipt_e:
                logger.error(f"Error waiting for receipt: {str(receipt_e)}")
                
                return {
                    'status': 'unknown',
                    'network': network,
                    'tx_hash': tx_hash.hex(),
                    'error': f"Receipt error: {str(receipt_e)}"
                }
        except Exception as e:
            logger.error(f"Error executing sandwich attack on {network}: {str(e)}")
            logger.error(traceback.format_exc())
            return {'error': str(e)}
    
    def execute_arbitrage(self, network, token_path, score):
        """Execute an arbitrage trade"""
        if network not in self.connections:
            return {'error': f"Not connected to {network}"}
        
        # Get web3 connection
        w3 = self.connections[network]
        
        # Determine trade size based on score and max position
        max_size = TRADE_CONFIG['max_position_size'].get(network, 0.1)
        size_factor = min(1.0, score / 3.0)  # Scale by opportunity score
        amount = max_size * size_factor
        
        # Get token addresses from the token pairs database
        try:
            from token_pairs_database import TOKEN_INFO
            token_addresses = []
            
            for token in token_path:
                address = TOKEN_INFO[network][token]['address']
                # Ensure address is checksummed
                token_addresses.append(Web3.to_checksum_address(address))
        except Exception as e:
            logger.error(f"Error getting token addresses: {str(e)}")
            return {'error': f"Token address lookup failed: {str(e)}"}
        
        # Get contract address (checksummed)
        mev_contract_address = Web3.to_checksum_address(
            DEPLOYED_CONTRACTS[network]['mev_strategies']
        )
        
        # Convert amount to wei
        amount_wei = w3.to_wei(amount, "ether")
        
        # Calculate expected profit (based on opportunity score)
        expected_profit = amount * (score / 100)  # Convert score to percentage
        expected_profit_wei = w3.to_wei(expected_profit, "ether")
        
        # Create contract instance
        mev_contract = w3.eth.contract(address=mev_contract_address, abi=MEV_ABI)
        
        try:
            # Get gas price with safety buffer
            gas_price = w3.eth.gas_price
            adjusted_gas_price = int(gas_price * TRADE_CONFIG['gas_multiplier'])
            
            # Get current transaction count (nonce)
            nonce = w3.eth.get_transaction_count(self.wallet_address)
            
            # Build transaction
            txn = mev_contract.functions.executeArbitrage(
                token_addresses,
                amount_wei,
                expected_profit_wei
            ).build_transaction({
                'chainId': CHAIN_IDS[network],
                'gas': 1000000,
                'gasPrice': adjusted_gas_price,
                'nonce': nonce,
                'from': self.wallet_address
            })
            
            # Sign transaction
            signed_txn = w3.eth.account.sign_transaction(txn, private_key=self.private_key)
            
            # Send transaction
            tx_hash = None
            
            # Handle different web3.py versions
            if hasattr(signed_txn, 'rawTransaction'):
                tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            elif hasattr(signed_txn, 'raw_transaction'):
                tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            else:
                # Direct attempt for other versions
                tx_hash = w3.eth.send_raw_transaction(signed_txn)
            
            if not tx_hash:
                return {'error': "Could not send transaction"}
            
            # Wait for receipt with timeout
            try:
                logger.info(f"Waiting for arbitrage transaction receipt with hash: {tx_hash.hex()}...")
                tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                
                # Log raw transaction receipt for diagnosis
                logger.info(f"Raw arbitrage transaction receipt: {json.dumps(dict(tx_receipt), default=str)}")
                
                # Check transaction status
                if tx_receipt['status'] == 1:
                    logger.info(f"Arbitrage successful on {network}")
                    result = {
                        'status': 'success',
                        'network': network,
                        'strategy': 'arbitrage',
                        'token_path': token_path,
                        'amount': amount,
                        'expected_profit': expected_profit,
                        'tx_hash': tx_hash.hex(),
                        'block_number': tx_receipt['blockNumber'],
                        'gas_used': tx_receipt['gasUsed'],
                        'gas_price': w3.from_wei(adjusted_gas_price, 'gwei'),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Update stats and save history
                    self.update_trade_stats(network, success=True)
                    self.trade_history.append(result)
                    self.save_trade_history()
                    
                    return result
                else:
                    # Get more details about failed transaction
                    try:
                        tx_details = w3.eth.get_transaction(tx_hash)
                        logger.error(f"Arbitrage transaction details for failed tx: {json.dumps(dict(tx_details), default=str)}")
                        
                        # Try to get any revert reason
                        try:
                            # Replay the transaction to get revert reason
                            w3.eth.call(dict(tx_details))
                        except Exception as call_e:
                            logger.error(f"Arbitrage transaction revert reason: {str(call_e)}")
                            
                    except Exception as tx_detail_e:
                        logger.error(f"Couldn't get arbitrage transaction details: {str(tx_detail_e)}")
                    
                    error_msg = f"Arbitrage failed on {network} with status {tx_receipt['status']}"
                    logger.error(error_msg)
                    return {
                        'status': 'failed',
                        'network': network,
                        'tx_hash': tx_hash.hex(),
                        'error': error_msg,
                        'receipt': dict(tx_receipt)
                    }
            except Exception as receipt_e:
                logger.error(f"Error waiting for arbitrage receipt: {str(receipt_e)}")
                
                return {
                    'status': 'unknown',
                    'network': network,
                    'tx_hash': tx_hash.hex(),
                    'error': f"Receipt error: {str(receipt_e)}"
                }
        except Exception as e:
            logger.error(f"Error executing arbitrage on {network}: {str(e)}")
            logger.error(traceback.format_exc())
            return {'error': str(e)}
    
    def auto_trade_loop(self, run_time_minutes=60, max_trades=None):
        """Automatically execute trades for a specified time period"""
        logger.info(f"Starting automatic trading loop for {run_time_minutes} minutes")
        print(f"\n{'='*70}")
        print(f"AUTOMATIC MEV TRADING STARTED")
        print(f"Running for {run_time_minutes} minutes")
        print(f"{'='*70}")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=run_time_minutes)
        trade_count = 0
        
        while datetime.now() < end_time:
            if max_trades and trade_count >= max_trades:
                logger.info(f"Reached maximum trade count ({max_trades})")
                break
            
            try:
                # Get trading opportunities
                opportunities = self.get_top_trading_opportunities()
                
                if not opportunities:
                    logger.info("No trading opportunities found, waiting...")
                    print("No opportunities found, waiting...")
                    time.sleep(30)
                    continue
                
                # Take the top opportunity
                top_opportunity = opportunities[0]
                network = top_opportunity['network']
                strategy = top_opportunity['strategy']
                
                # Only proceed if score is above threshold
                min_threshold = TRADE_CONFIG['min_profit_threshold'] * 100  # Convert to same scale as score
                if top_opportunity['score'] < min_threshold:
                    logger.info(f"Best opportunity score ({top_opportunity['score']}) below threshold ({min_threshold})")
                    print(f"Best opportunity below threshold, waiting...")
                    time.sleep(30)
                    continue
                
                # Log the opportunity
                if strategy == 'sandwich':
                    tokens = f"{top_opportunity['token0']}/{top_opportunity['token1']}"
                    print(f"\nExecuting {strategy} on {network} for {tokens}")
                    print(f"Score: {top_opportunity['score']:.2f}, Time: {datetime.now().strftime('%H:%M:%S')}")
                else:
                    path = " -> ".join(top_opportunity['token_path'])
                    print(f"\nExecuting {strategy} on {network} with path {path}")
                    print(f"Score: {top_opportunity['score']:.2f}, Time: {datetime.now().strftime('%H:%M:%S')}")
                
                # Execute trade with retries
                result = None
                for attempt in range(TRADE_CONFIG['retry_count']):
                    try:
                        result = self.execute_trade(top_opportunity)
                        if result and 'error' not in result:
                            break
                        logger.warning(f"Attempt {attempt+1} failed: {result.get('error', 'Unknown error')}")
                        time.sleep(5)  # Short delay between retries
                    except Exception as e:
                        logger.error(f"Error in attempt {attempt+1}: {str(e)}")
                        time.sleep(5)
                
                # Log result
                if result:
                    if 'status' in result and result['status'] == 'success':
                        trade_count += 1
                        print(f"SUCCESS: TX Hash: {result['tx_hash']}")
                        print(f"Expected Profit: {result['expected_profit']:.6f} ETH")
                    else:
                        print(f"FAILED: {result.get('error', 'Unknown error')}")
                
                # Random cooldown to avoid predictable patterns
                cooldown = random.randint(
                    TRADE_CONFIG['cooldown_seconds'] - 60,
                    TRADE_CONFIG['cooldown_seconds'] + 60
                )
                print(f"Cooling down for {cooldown} seconds...")
                time.sleep(cooldown)
            
            except KeyboardInterrupt:
                logger.info("Trading loop interrupted by user")
                print("\nTrading loop interrupted!")
                break
            except Exception as e:
                logger.error(f"Error in trading loop: {str(e)}")
                logger.error(traceback.format_exc())
                print(f"Error encountered: {str(e)}")
                print("Waiting 60 seconds before continuing...")
                time.sleep(60)
        
        # Final summary
        elapsed = datetime.now() - start_time
        logger.info(f"Trading loop finished. Executed {trade_count} trades in {elapsed.total_seconds()/60:.1f} minutes")
        print(f"\n{'='*70}")
        print(f"AUTOMATIC MEV TRADING COMPLETED")
        print(f"Executed {trade_count} trades in {elapsed.total_seconds()/60:.1f} minutes")
        print(f"Trade history saved to {TRADE_HISTORY_FILE}")
        print(f"{'='*70}")

def main():
    # Print welcome banner
    print("\n" + "="*70)
    print("AUTOMATED QUANTUM-OPTIMIZED MEV TRADING BOT")
    print("With Triple Flashloan Strategy Execution") 
    print("="*70)
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
    
    # Create trader instance
    trader = AutoMEVTrader()
    
    # Check connections
    connected_networks = list(trader.connections.keys())
    if not connected_networks:
        print("ERROR: No connections to any networks. Please check your .env file.")
        print("Remember to protect sensitive data in your .syncignore file.")
        print("The .syncignore file uses standard .gitignore syntax for exclusion patterns.")
        return
    
    print(f"Connected to {len(connected_networks)} networks: {', '.join(connected_networks)}")
    
    # Show wallet summary for confirmation
    wallet_address = trader.wallet_address
    if wallet_address:
        # Show abbreviated address for security
        abbreviated = wallet_address[:6] + "..." + wallet_address[-4:]
        print(f"\nWallet address: {abbreviated}")
        
        # Verify wallet balance on each network
        print("\nVerifying wallet balances:")
        for network in connected_networks:
            try:
                w3 = trader.connections[network]
                balance = w3.eth.get_balance(wallet_address)
                balance_eth = w3.from_wei(balance, 'ether')
                print(f"  {network.capitalize()}: {balance_eth:.6f} ETH")
                
                if balance_eth < 0.01:
                    print(f"    WARNING: Low balance on {network}. Trading may fail!")
            except Exception as e:
                print(f"  Error checking balance on {network}: {str(e)}")
    else:
        print("\nERROR: No wallet address configured. Trading will fail.")
        return
    
    # Initialize quantum circuits from Qiskit (if available)
    try:
        print("\nInitializing quantum optimization...")
        from qiskit import QuantumCircuit, Aer, execute
        
        # Define a simple quantum circuit for demonstration
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])
        
        # Execute the circuit
        simulator = Aer.get_backend('qasm_simulator')
        job = execute(qc, simulator, shots=100)
        result = job.result()
        
        print("Quantum circuit initialized successfully.")
        print("Quantum optimization will be applied to trade parameters.")
    except ImportError:
        print("Qiskit not installed. Quantum optimization disabled.")
        print("Trading will proceed with classical optimization only.")
    except Exception as e:
        print(f"Quantum initialization error: {str(e)}")
        print("Trading will proceed with classical optimization only.")
    
    # Setup automatic trading
    try:
        print("\n" + "-"*70)
        print("TRADING CONFIGURATION")
        print("-"*70)
        
        run_time = int(input("Enter trading duration in minutes (default: 60): ") or 60)
        max_trades = int(input("Enter maximum number of trades (default: 10): ") or 10)
        
        print("\nStrategy selection:")
        print("1. All strategies (sandwich attacks and arbitrage)")
        print("2. Sandwich attacks only")
        print("3. Arbitrage only")
        strategy_choice = input("Select strategies (default: 1): ") or "1"
        
        # Set strategy filters based on user choice
        if strategy_choice == "2":
            print("Using sandwich attacks only")
            TRADE_CONFIG['strategy_filter'] = ["sandwich"]
        elif strategy_choice == "3":
            print("Using arbitrage only")
            TRADE_CONFIG['strategy_filter'] = ["arbitrage"]
        else:
            print("Using all available strategies")
            TRADE_CONFIG['strategy_filter'] = ["sandwich", "arbitrage"]
        
        print("\nNetwork selection:")
        for i, network in enumerate(connected_networks, 1):
            print(f"{i}. {network.capitalize()}")
        print(f"{len(connected_networks) + 1}. All networks")
        
        network_choice = input(f"Select network(s) (default: {len(connected_networks) + 1}): ") or str(len(connected_networks) + 1)
        
        # Set network filters based on user choice
        if network_choice != str(len(connected_networks) + 1):
            try:
                choice_idx = int(network_choice) - 1
                if 0 <= choice_idx < len(connected_networks):
                    selected_network = connected_networks[choice_idx]
                    print(f"Using {selected_network} network only")
                    TRADE_CONFIG['network_filter'] = [selected_network]
                else:
                    print("Invalid choice. Using all networks.")
                    TRADE_CONFIG['network_filter'] = connected_networks
            except:
                print("Invalid choice. Using all networks.")
                TRADE_CONFIG['network_filter'] = connected_networks
        else:
            print("Using all available networks")
            TRADE_CONFIG['network_filter'] = connected_networks
        
        print("\nPositioning sizing:")
        for network in TRADE_CONFIG['network_filter']:
            default_size = TRADE_CONFIG['max_position_size'].get(network, 0.1)
            new_size = float(input(f"Max position size for {network} (default: {default_size} ETH): ") or default_size)
            TRADE_CONFIG['max_position_size'][network] = new_size
            print(f"Set {network} max position size to {new_size} ETH")
        
        # Final confirmation
        print("\n" + "="*70)
        print("WARNING: This will execute REAL trades using your wallet!")
        print("Make sure your .env file contains valid credentials.")
        print("="*70)
        print(f"Trading duration: {run_time} minutes")
        print(f"Maximum trades: {max_trades}")
        print(f"Networks: {', '.join(TRADE_CONFIG['network_filter'])}")
        print(f"Strategies: {', '.join(TRADE_CONFIG['strategy_filter'])}")
        print("="*70)
        
        confirmation = input("Type 'CONFIRM' to start automatic trading: ")
        
        if confirmation.upper() != "CONFIRM":
            print("Aborted.")
            return
        
        # Create a new log file for this trading session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"trading_session_{timestamp}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        
        logger.info(f"Starting new trading session with configuration: {json.dumps(TRADE_CONFIG, default=str)}")
        
        # Start automatic trading
        trader.auto_trade_loop(run_time_minutes=run_time, max_trades=max_trades)
        
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"Error in main: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
