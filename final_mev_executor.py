"""
Fixed MEV Strategy Execution with TripleFlashloan Contracts
Corrected wallet handling for "invalid sender" errors
"""
import os
import json
import time
import logging
from web3 import Web3
from dotenv import load_dotenv
from datetime import datetime

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

# Example Wallet for Testing (REPLACE WITH REAL VALUES FROM .env)
# Using hardcoded example for demonstration - YOUR CODE SHOULD USE .env VALUES
EXAMPLE_WALLET_ADDRESS = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
EXAMPLE_PRIVATE_KEY = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

class MEVTrader:
    """MEV Strategy Trader with fixed wallet handling"""
    
    def __init__(self, use_real_mode=False):
        self.use_real_mode = use_real_mode
        self.connections = {}
        
        # Get wallet from .env or use example for testing
        self.wallet_address = os.getenv("METAMASK_ADDRESS", EXAMPLE_WALLET_ADDRESS)
        self.private_key = os.getenv("METAMASK_PRIVATE_KEY", EXAMPLE_PRIVATE_KEY)
        
        # Properly checksum the wallet address
        try:
            self.wallet_address = Web3.to_checksum_address(self.wallet_address)
            logger.info(f"Wallet address checksummed: {self.wallet_address}")
        except Exception as e:
            logger.error(f"Invalid wallet address format: {str(e)}")
            print(f"ERROR: Invalid wallet address format. Please check your .env file.")
        
        # Set up connections
        self.setup_connections()
    
    def setup_connections(self):
        """Set up connections to different networks"""
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
                logger.warning(f"No URL found for {network}")
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
    
    def execute_sandwich(self, network, token0, token1, amount0, amount1):
        """Execute a sandwich attack using deployed MEV contract"""
        if network not in self.connections:
            return {"error": f"Not connected to {network}"}
        
        # Get web3 connection
        w3 = self.connections[network]
        
        # Get token addresses
        token0_address = TOKEN_ADDRESSES[network].get(token0)
        token1_address = TOKEN_ADDRESSES[network].get(token1)
        
        if not token0_address or not token1_address:
            return {"error": f"Token addresses not found for {token0} or {token1}"}
        
        # Ensure addresses are checksummed
        token0_address = Web3.to_checksum_address(token0_address)
        token1_address = Web3.to_checksum_address(token1_address)
        
        # Get contract address (checksummed)
        mev_contract_address = Web3.to_checksum_address(DEPLOYED_CONTRACTS[network]["mev_strategies"])
        
        # Convert amounts to wei
        amount0_wei = w3.to_wei(amount0, "ether")
        amount1_wei = w3.to_wei(amount1, "ether")
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
            # Print wallet info for debugging
            print(f"Using wallet: {self.wallet_address}")
            print(f"Contract: {mev_contract_address}")
            print(f"Token addresses: {token0_address}, {token1_address}")
            
            # Get gas price with safety buffer
            gas_price = w3.eth.gas_price
            adjusted_gas_price = int(gas_price * 1.1)
            
            # Get nonce for the transaction
            nonce = w3.eth.get_transaction_count(self.wallet_address)
            print(f"Current nonce: {nonce}")
            
            # Build transaction with explicit parameters
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
            
            # Sign transaction - handle error carefully
            try:
                print("Signing transaction...")
                signed_txn = w3.eth.account.sign_transaction(txn, private_key=self.private_key)
                
                # Print some info about the signed transaction
                if hasattr(signed_txn, 'rawTransaction'):
                    print(f"Transaction signed successfully (rawTransaction)")
                elif hasattr(signed_txn, 'raw_transaction'):
                    print(f"Transaction signed successfully (raw_transaction)")
                else:
                    print(f"Transaction signed with unknown format")
                
                # Send transaction - handle different web3.py versions
                print("Sending transaction...")
                tx_hash = None
                
                if hasattr(signed_txn, 'rawTransaction'):
                    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                elif hasattr(signed_txn, 'raw_transaction'):
                    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
                
                if not tx_hash:
                    return {"error": "Could not send transaction - unknown signed transaction format"}
                
                print(f"Transaction sent with hash: {tx_hash.hex()}")
                
                # Wait for receipt
                tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                
                if tx_receipt['status'] == 1:
                    logger.info(f"Sandwich attack successful on {network}")
                    return {
                        "status": "success",
                        "tx_hash": tx_hash.hex(),
                        "block_number": tx_receipt['blockNumber']
                    }
                else:
                    logger.error(f"Sandwich attack failed on {network}")
                    return {
                        "status": "failed",
                        "tx_hash": tx_hash.hex()
                    }
            
            except Exception as e:
                logger.error(f"Error in transaction signing/sending: {str(e)}")
                return {"error": f"Transaction error: {str(e)}"}
            
        except Exception as e:
            logger.error(f"Error executing sandwich attack on {network}: {str(e)}")
            return {"error": str(e)}

def main():
    # We'll use simulation mode for safety by default
    use_real_mode = input("Do you want to run in REAL execution mode? (yes/no): ").lower() == "yes"
    
    # Print banner
    print("\n" + "="*70)
    print("TripleFlashloan MEV Strategy Executor - Fixed Wallet Handling")
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
        print("\nERROR: No connections established.")
        print("Using example URLs for testing. Replace with real endpoints in production.")
    
    # Execute strategies
    print("\n" + "-"*70)
    print("Available MEV Strategies:")
    print("1. Sandwich Attack on Arbitrum (WETH/USDC)")
    print("2. Sandwich Attack on Polygon (WETH/MATIC)")
    print("3. Sandwich Attack on Optimism (WETH/OP)")
    print("4. Sandwich Attack on Arbitrum (USDC/ARB)")
    print("5. Exit")
    print("-"*70)
    
    while True:
        try:
            choice = input("\nSelect a strategy (1-5): ")
            
            if choice == "5":
                print("Exiting MEV Strategy Executor...")
                break
            
            if choice == "1" and "arbitrum" in connected_networks:
                print("\nExecuting Sandwich Attack on Arbitrum (WETH/USDC)...")
                result = trader.execute_sandwich("arbitrum", "WETH", "USDC", 0.1, 0.1)
            
            elif choice == "2" and "polygon" in connected_networks:
                print("\nExecuting Sandwich Attack on Polygon (WETH/MATIC)...")
                result = trader.execute_sandwich("polygon", "WETH", "MATIC", 0.1, 0.1)
            
            elif choice == "3" and "optimism" in connected_networks:
                print("\nExecuting Sandwich Attack on Optimism (WETH/OP)...")
                result = trader.execute_sandwich("optimism", "WETH", "OP", 0.1, 0.1)
            
            elif choice == "4" and "arbitrum" in connected_networks:
                print("\nExecuting Sandwich Attack on Arbitrum (USDC/ARB)...")
                result = trader.execute_sandwich("arbitrum", "USDC", "ARB", 0.1, 0.1)
            
            else:
                print(f"Invalid choice or network not connected: {choice}")
                continue
            
            print("\nResult:")
            for key, value in result.items():
                print(f"  {key}: {value}")
            
        except KeyboardInterrupt:
            print("\nExiting MEV Strategy Executor...")
            break
        except Exception as e:
            print(f"Error: {str(e)}")
    
    print("\nMEV Strategy Execution completed.")
    print("Remember to check your .syncignore file to ensure sensitive credentials are protected.")
    print("The .syncignore file uses standard .gitignore syntax for exclusion patterns.")

if __name__ == "__main__":
    main()
