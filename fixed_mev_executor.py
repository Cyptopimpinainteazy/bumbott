"""
Fixed MEV Strategy Execution with TripleFlashloan Contracts
Compatible with multiple web3.py versions
"""
import os
import json
import time
import logging
from web3 import Web3
from dotenv import load_dotenv
from datetime import datetime

# Import token pairs database functions
from token_pairs_database import get_top_pairs, get_arbitrage_paths, get_pairs_for_token

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mev_trades.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MEV_Trader")

# Your deployed contracts (from previous sessions)
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

# Token addresses
TOKEN_ADDRESSES = {
    "arbitrum": {
        "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "USDC": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
        "ARB": "0x912CE59144191C1204E64559FE8253a0e49E6548",
    },
    "polygon": {
        "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
        "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "MATIC": "0x0000000000000000000000000000000000001010",
    },
    "optimism": {
        "WETH": "0x4200000000000000000000000000000000000006",
        "USDC": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
        "OP": "0x4200000000000000000000000000000000000042",
    },
    "bsc": {
        "WBNB": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
        "BUSD": "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56",
        "CAKE": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
    }
}

# Simplified MEV contract ABI
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

# Chain IDs for networks
CHAIN_IDS = {
    "arbitrum": 42161,
    "polygon": 137,
    "optimism": 10,
    "bsc": 56
}

# Convert decimal value to float
def to_float(value):
    """Convert decimal values to float safely"""
    if hasattr(value, 'to_float'):
        return value.to_float()
    return float(value)

# Safe transaction sender that works with different web3.py versions
def send_transaction_safely(w3, signed_txn):
    """Send transaction with compatibility for different web3.py versions"""
    try:
        # For newer web3.py versions
        if hasattr(signed_txn, 'raw_transaction'):
            return w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        # For older web3.py versions
        elif hasattr(signed_txn, 'rawTransaction'):
            return w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        else:
            # Direct attempt for other versions
            logger.warning("Unable to determine transaction format, trying direct send")
            return w3.eth.send_raw_transaction(signed_txn)
    except Exception as e:
        logger.error(f"Error sending transaction: {str(e)}")
        raise e

class MEVTrader:
    """Simplified MEV Strategy Trader with fixed transaction handling"""
    
    def __init__(self, use_real_mode=True):
        self.use_real_mode = use_real_mode
        self.connections = {}
        self.wallet_address = os.getenv("METAMASK_ADDRESS")
        self.private_key = os.getenv("METAMASK_PRIVATE_KEY")
        
        # Check wallet configuration
        if not self.wallet_address or not self.private_key:
            logger.warning("Wallet address or private key not found in .env file")
            print("WARNING: Wallet not properly configured. Check your .env file.")
        
        # Set up connections
        self.setup_connections()
    
    def setup_connections(self):
        """Set up connections to different networks"""
        for network in DEPLOYED_CONTRACTS.keys():
            url_env_var = f"CHAINSTACK_{network.upper()}_URL"
            url = os.getenv(url_env_var)
            
            if not url:
                logger.warning(f"No URL found for {network} in .env file")
                continue
            
            try:
                w3 = Web3(Web3.HTTPProvider(url))
                if w3.is_connected():
                    self.connections[network] = w3
                    logger.info(f"Connected to {network}")
                else:
                    logger.warning(f"Failed to connect to {network}")
            except Exception as e:
                logger.error(f"Error connecting to {network}: {str(e)}")
    
    def check_balances(self):
        """Check wallet balances across connected networks"""
        results = {}
        
        if not self.wallet_address:
            logger.error("No wallet address configured")
            return {"error": "No wallet address configured"}
        
        for network, w3 in self.connections.items():
            try:
                native_balance_wei = w3.eth.get_balance(self.wallet_address)
                native_balance = to_float(w3.from_wei(native_balance_wei, "ether"))
                
                results[network] = {
                    "network": network,
                    "native_balance": native_balance,
                    "tokens": {}
                }
                
                # Check token balances
                for symbol, address in TOKEN_ADDRESSES.get(network, {}).items():
                    # Skip native token
                    if address == "0x0000000000000000000000000000000000000000":
                        continue
                    
                    try:
                        # Simple ERC20 balanceOf ABI
                        erc20_abi = [
                            {
                                "constant": True,
                                "inputs": [{"name": "_owner", "type": "address"}],
                                "name": "balanceOf",
                                "outputs": [{"name": "balance", "type": "uint256"}],
                                "type": "function"
                            },
                            {
                                "constant": True,
                                "inputs": [],
                                "name": "decimals",
                                "outputs": [{"name": "", "type": "uint8"}],
                                "type": "function"
                            }
                        ]
                        
                        token_contract = w3.eth.contract(address=address, abi=erc20_abi)
                        balance_wei = token_contract.functions.balanceOf(self.wallet_address).call()
                        
                        try:
                            decimals = token_contract.functions.decimals().call()
                        except:
                            decimals = 18
                        
                        balance = float(balance_wei) / (10 ** decimals)
                        results[network]["tokens"][symbol] = balance
                    except Exception as e:
                        logger.warning(f"Error checking {symbol} balance on {network}: {str(e)}")
            except Exception as e:
                logger.error(f"Error checking balances on {network}: {str(e)}")
        
        return results
    
    def execute_sandwich(self, network, token0, token1, amount0, amount1, expected_profit=None):
        """Execute a sandwich attack using deployed MEV contract"""
        if network not in self.connections:
            return {"error": f"Not connected to {network}"}
        
        if network not in TOKEN_ADDRESSES:
            return {"error": f"No token addresses for {network}"}
        
        # Get web3 connection
        w3 = self.connections[network]
        
        # Get token addresses
        token0_address = TOKEN_ADDRESSES[network].get(token0)
        token1_address = TOKEN_ADDRESSES[network].get(token1)
        
        if not token0_address or not token1_address:
            return {"error": f"Token addresses not found for {token0} or {token1} on {network}"}
        
        # Get contract address
        mev_contract_address = DEPLOYED_CONTRACTS[network]["mev_strategies"]
        
        # Convert amounts to wei
        amount0_wei = w3.to_wei(amount0, "ether")
        amount1_wei = w3.to_wei(amount1, "ether")
        
        # Calculate expected profit if not provided
        if expected_profit is None:
            expected_profit = (amount0 + amount1) * 0.02  # 2% profit
        expected_profit_wei = w3.to_wei(expected_profit, "ether")
        
        # Create contract instance
        mev_contract = w3.eth.contract(address=mev_contract_address, abi=MEV_ABI)
        
        # If not using real mode, only simulate
        if not self.use_real_mode:
            logger.info(f"SIMULATION: Sandwich attack on {network} for {token0}/{token1}")
            return {
                "status": "simulated",
                "network": network,
                "strategy": "sandwich",
                "token_pair": [token0, token1],
                "amount0": amount0,
                "amount1": amount1,
                "expected_profit": expected_profit,
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Get gas price
            gas_price = w3.eth.gas_price
            # Apply 10% buffer
            adjusted_gas_price = int(gas_price * 1.1)
            
            # Build transaction
            txn = mev_contract.functions.executeSandwich(
                [token0_address, token1_address],
                [amount0_wei, amount1_wei],
                expected_profit_wei
            ).build_transaction({
                'from': self.wallet_address,
                'gas': 800000,  # Gas limit
                'gasPrice': adjusted_gas_price,
                'nonce': w3.eth.get_transaction_count(self.wallet_address),
                'chainId': CHAIN_IDS[network]
            })
            
            # Sign transaction
            signed_txn = w3.eth.account.sign_transaction(txn, private_key=self.private_key)
            
            # Send transaction using our safe wrapper
            tx_hash = send_transaction_safely(w3, signed_txn)
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt['status'] == 1:
                logger.info(f"Sandwich attack successful on {network}")
                return {
                    "status": "success",
                    "network": network,
                    "strategy": "sandwich",
                    "token_pair": [token0, token1],
                    "amount0": amount0,
                    "amount1": amount1,
                    "expected_profit": expected_profit,
                    "tx_hash": tx_hash.hex(),
                    "block_number": tx_receipt['blockNumber'],
                    "gas_used": tx_receipt['gasUsed'],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"Sandwich attack failed on {network}")
                return {
                    "status": "failed",
                    "network": network,
                    "tx_hash": tx_hash.hex()
                }
        except Exception as e:
            logger.error(f"Error executing sandwich attack on {network}: {str(e)}")
            return {"error": str(e)}
    
    def execute_arbitrage(self, network, token_path, amount, expected_profit=None):
        """Execute an arbitrage trade using deployed MEV contract"""
        if network not in self.connections:
            return {"error": f"Not connected to {network}"}
        
        if network not in TOKEN_ADDRESSES:
            return {"error": f"No token addresses for {network}"}
        
        # Get web3 connection
        w3 = self.connections[network]
        
        # Get token addresses
        token_addresses = []
        for token in token_path:
            address = TOKEN_ADDRESSES[network].get(token)
            if not address:
                return {"error": f"Token address not found for {token} on {network}"}
            token_addresses.append(address)
        
        # Get contract address
        mev_contract_address = DEPLOYED_CONTRACTS[network]["mev_strategies"]
        
        # Convert amount to wei
        amount_wei = w3.to_wei(amount, "ether")
        
        # Calculate expected profit if not provided
        if expected_profit is None:
            expected_profit = amount * 0.01  # 1% profit
        expected_profit_wei = w3.to_wei(expected_profit, "ether")
        
        # Create contract instance
        mev_contract = w3.eth.contract(address=mev_contract_address, abi=MEV_ABI)
        
        # If not using real mode, only simulate
        if not self.use_real_mode:
            logger.info(f"SIMULATION: Arbitrage on {network} with path {' -> '.join(token_path)}")
            return {
                "status": "simulated",
                "network": network,
                "strategy": "arbitrage",
                "token_path": token_path,
                "amount": amount,
                "expected_profit": expected_profit,
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Get gas price
            gas_price = w3.eth.gas_price
            # Apply 10% buffer
            adjusted_gas_price = int(gas_price * 1.1)
            
            # Build transaction
            txn = mev_contract.functions.executeArbitrage(
                token_addresses,
                amount_wei,
                expected_profit_wei
            ).build_transaction({
                'from': self.wallet_address,
                'gas': 600000,  # Gas limit
                'gasPrice': adjusted_gas_price,
                'nonce': w3.eth.get_transaction_count(self.wallet_address),
                'chainId': CHAIN_IDS[network]
            })
            
            # Sign transaction
            signed_txn = w3.eth.account.sign_transaction(txn, private_key=self.private_key)
            
            # Send transaction using our safe wrapper
            tx_hash = send_transaction_safely(w3, signed_txn)
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt['status'] == 1:
                logger.info(f"Arbitrage successful on {network}")
                return {
                    "status": "success",
                    "network": network,
                    "strategy": "arbitrage",
                    "token_path": token_path,
                    "amount": amount,
                    "expected_profit": expected_profit,
                    "tx_hash": tx_hash.hex(),
                    "block_number": tx_receipt['blockNumber'],
                    "gas_used": tx_receipt['gasUsed'],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"Arbitrage failed on {network}")
                return {
                    "status": "failed",
                    "network": network,
                    "tx_hash": tx_hash.hex()
                }
        except Exception as e:
            logger.error(f"Error executing arbitrage on {network}: {str(e)}")
            return {"error": str(e)}

def main():
    # Check if we're in real mode or test mode
    # Running in real execution mode as requested
    use_real_mode = True  # Set to True for real execution
    
    # Print banner
    print("\n" + "="*70)
    print("TripleFlashloan MEV Strategy Executor")
    print("="*70)
    print(f"Mode: {'REAL EXECUTION' if use_real_mode else 'SIMULATION'}")
    print(f"WARNING: Real mode will execute actual transactions with your wallet!")
    print("="*70)
    
    # Initialize trader
    trader = MEVTrader(use_real_mode=use_real_mode)
    
    # Check number of connections
    connected_networks = list(trader.connections.keys())
    print(f"\nConnected to {len(connected_networks)} networks: {', '.join(connected_networks) if connected_networks else 'None'}")
    
    # If no connections, show error
    if not connected_networks:
        print("\nERROR: No connections established. Please check your .env file.")
        print("Make sure you have set up your Chainstack URLs for each network.")
        print("Example: CHAINSTACK_ARBITRUM_URL=https://arbitrum-mainnet.chainstacklabs.com/your-api-key")
        return
    
    # Check wallet
    if not trader.wallet_address or not trader.private_key:
        print("\nERROR: Wallet not properly configured. Check your .env file.")
        print("Make sure you have set METAMASK_ADDRESS and METAMASK_PRIVATE_KEY.")
        return
    
    # Check balances
    print("\nChecking wallet balances...")
    balances = trader.check_balances()
    
    # Print balances
    for network, data in balances.items():
        if isinstance(data, dict) and "error" not in data:
            print(f"\n{network.upper()} Balance:")
            print(f"  Native Token: {data['native_balance']:.6f}")
            
            for token, balance in data.get("tokens", {}).items():
                if balance > 0:
                    print(f"  {token}: {balance:.6f}")
    
    # Get top trading opportunities from token pairs database
    print("\nGetting top trading opportunities from database...")
    top_opportunities = {}
    for network in connected_networks:
        top_opportunities[network] = get_top_pairs(network, 5)
    
    # Display top opportunities by network
    for network, pairs in top_opportunities.items():
        if pairs:
            print(f"\nTop opportunities on {network.upper()}:")
            for i, pair in enumerate(pairs):
                token0 = pair['token0']['symbol']
                token1 = pair['token1']['symbol']
                score = pair['opportunity_score']
                print(f"  {i+1}. {token0}/{token1} - Score: {score}")
    
    # Get WETH arbitrage paths
    for network in connected_networks:
        if network != 'bsc':
            weth_paths = get_arbitrage_paths(network, "WETH", 3)[:2]
            if weth_paths:
                print(f"\nWETH arbitrage paths on {network.upper()}:")
                for i, path_data in enumerate(weth_paths):
                    path_str = " -> ".join(path_data["path"])
                    print(f"  {i+1}. {path_str} - Score: {path_data['score']:.2f}")
    
    # Execute strategies
    print("\n" + "-"*70)
    print("Available MEV Strategies:")
    print("1. Sandwich Attack on Arbitrum (WETH/USDC)")
    print("2. Arbitrage on Optimism (WETH -> OP -> USDC -> WETH)")
    print("3. Sandwich Attack on Polygon (WETH/MATIC)")
    print("4. Sandwich Attack on Arbitrum (USDC/ARB) - High Score")
    print("5. Exit")
    print("-"*70)
    
    while True:
        try:
            choice = input("\nSelect a strategy (1-5): ")
            
            if choice == "5":
                print("Exiting MEV Strategy Executor...")
                break
            
            if choice == "1" and "arbitrum" in connected_networks:
                print("\nExecuting Sandwich Attack on Arbitrum...")
                result = trader.execute_sandwich(
                    network="arbitrum",
                    token0="WETH",
                    token1="USDC",
                    amount0=0.5,
                    amount1=0.5
                )
                print("\nResult:")
                for key, value in result.items():
                    print(f"  {key}: {value}")
            
            elif choice == "2" and "optimism" in connected_networks:
                print("\nExecuting Arbitrage on Optimism...")
                result = trader.execute_arbitrage(
                    network="optimism",
                    token_path=["WETH", "OP", "USDC", "WETH"],
                    amount=0.8
                )
                print("\nResult:")
                for key, value in result.items():
                    print(f"  {key}: {value}")
            
            elif choice == "3" and "polygon" in connected_networks:
                print("\nExecuting Sandwich Attack on Polygon...")
                result = trader.execute_sandwich(
                    network="polygon",
                    token0="WETH",
                    token1="MATIC",
                    amount0=0.3,
                    amount1=0.3
                )
                print("\nResult:")
                for key, value in result.items():
                    print(f"  {key}: {value}")
            
            elif choice == "4" and "arbitrum" in connected_networks:
                print("\nExecuting Sandwich Attack on Arbitrum (USDC/ARB) - High Score...")
                result = trader.execute_sandwich(
                    network="arbitrum",
                    token0="USDC",
                    token1="ARB",
                    amount0=0.4,
                    amount1=0.4
                )
                print("\nResult:")
                for key, value in result.items():
                    print(f"  {key}: {value}")
            
            else:
                print(f"Invalid choice or network not connected: {choice}")
            
        except KeyboardInterrupt:
            print("\nExiting MEV Strategy Executor...")
            break
        except Exception as e:
            print(f"Error: {str(e)}")
    
    print("\nMEV Strategy Execution completed.")
    print("Remember to check your .syncignore file to ensure sensitive credentials are protected.")

if __name__ == "__main__":
    main()
