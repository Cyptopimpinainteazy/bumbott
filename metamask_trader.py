"""
MetaMask Trader - L2 Trading Integration for BumBot Trading System

This module provides secure transaction execution on Arbitrum and Polygon networks 
via MetaMask wallet integration with optimized gas strategies.
"""
from web3 import Web3

# Handle compatibility with different web3 versions
try:
    from web3.middleware import geth_poa_middleware
except ImportError:
    # In newer web3 versions, middleware might be in a different location
    try:
        from web3.middleware.geth import geth_poa_middleware
    except ImportError:
        # If still not found, create a basic middleware
        def geth_poa_middleware(make_request, web3):
            def middleware(method, params):
                return make_request(method, params)
            return middleware
from chainstack_provider import ChainstackProvider
from dotenv import load_dotenv
import os
import json
import time
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/metamask.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('metamask')

class MetaMaskTrader:
    """Manages secure L2 trading execution through MetaMask wallet integration"""
    
    def __init__(self):
        self.chainstack = ChainstackProvider()
        load_dotenv()
        
        # MetaMask credentials (these should be securely stored)
        self.wallet_address = os.getenv("METAMASK_ADDRESS")
        self.private_key = os.getenv("METAMASK_PRIVATE_KEY")
        
        # Trading parameters
        self.default_slippage = 0.005  # 0.5% slippage tolerance
        self.transaction_deadline = 20  # minutes
        
        # Transaction history
        self.tx_history_file = 'logs/transaction_history.json'
        self.tx_history = self._load_tx_history()
        
        # Initialize ABI references
        self.abis = self._load_abis()
        
        logger.info(f"MetaMask trader initialized for wallet: {self._mask_address(self.wallet_address)}")
        
    def _mask_address(self, address):
        """Mask address for security in logs"""
        if not address or len(address) < 10:
            return "Invalid Address"
        return f"{address[:6]}...{address[-4:]}"
        
    def _load_abis(self):
        """Load contract ABIs"""
        abis = {}
        abi_files = [
            "erc20.json",
            "uniswap_v2_router.json",
            "uniswap_v3_router.json",
            "quickswap_router.json"
        ]
        
        for filename in abi_files:
            try:
                with open(os.path.join('abi', filename), 'r') as f:
                    abis[filename.replace('.json', '')] = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load ABI {filename}: {str(e)}")
                
        return abis
        
    def _load_tx_history(self):
        """Load transaction history from file"""
        if os.path.exists(self.tx_history_file):
            try:
                with open(self.tx_history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load transaction history: {str(e)}")
                
        return []
        
    def _save_tx_history(self):
        """Save transaction history to file"""
        try:
            os.makedirs(os.path.dirname(self.tx_history_file), exist_ok=True)
            with open(self.tx_history_file, 'w') as f:
                json.dump(self.tx_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save transaction history: {str(e)}")
    
    def get_wallet_balances(self):
        """Check wallet balances across networks"""
        if not self.wallet_address:
            return {"error": "No wallet address configured"}
            
        balances = {}
        
        for network in self.chainstack.web3_connections:
            try:
                web3 = self.chainstack.get_connection(network)
                if not web3 or not web3.is_connected():
                    balances[network] = {"error": "Network connection not available"}
                    continue
                    
                # Get native token balance
                native_balance = web3.eth.get_balance(self.wallet_address)
                token_symbol = "ETH" if network == "arbitrum" else "MATIC"
                
                balances[network] = {
                    "native": {
                        "symbol": token_symbol,
                        "balance": web3.from_wei(native_balance, 'ether')
                    },
                    "tokens": {}
                }
                
                # Get token balances for common tokens
                network_specs = self.chainstack.get_network_specs(network)
                for symbol, address in network_specs["tokens"].items():
                    try:
                        token_info = self.chainstack.get_token_balance(
                            network, address, self.wallet_address
                        )
                        balances[network]["tokens"][symbol] = token_info
                    except Exception as e:
                        logger.error(f"Error getting {symbol} balance on {network}: {str(e)}")
                        
            except Exception as e:
                balances[network] = {"error": str(e)}
                
        return balances
        
    def approve_token_if_needed(self, network, token_address, spender_address, amount):
        """Check and approve token spending allowance if needed"""
        try:
            web3 = self.chainstack.get_connection(network)
            token_contract = web3.eth.contract(address=token_address, abi=self.abis["erc20"])
            
            # Check current allowance
            current_allowance = token_contract.functions.allowance(
                self.wallet_address, spender_address
            ).call()
            
            # If allowance is sufficient, no action needed
            if current_allowance >= amount:
                logger.info(f"Existing allowance sufficient: {current_allowance}")
                return {"status": "already_approved", "allowance": current_allowance}
                
            # Need to approve
            logger.info(f"Approving token {token_address} for spender {spender_address}")
            
            # Prepare approval transaction
            gas_price = web3.eth.gas_price
            gas_price_adjusted = int(gas_price * self.chainstack.network_specs[network]["gas_multiplier"])
            
            approve_txn = token_contract.functions.approve(
                spender_address, 
                2**256 - 1  # Max approval (uint256 max value)
            ).build_transaction({
                'from': self.wallet_address,
                'gas': 100000,  # Standard gas limit for approvals
                'gasPrice': gas_price_adjusted,
                'nonce': web3.eth.get_transaction_count(self.wallet_address)
            })
            
            # Submit transaction
            signed_txn = web3.eth.account.sign_transaction(approve_txn, self.private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for transaction receipt
            logger.info(f"Approval submitted with hash: {tx_hash.hex()}")
            tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            
            # Check status
            if tx_receipt.status == 1:
                logger.info(f"Approval successful: {tx_receipt.transactionHash.hex()}")
                return {
                    "status": "approved",
                    "tx_hash": tx_receipt.transactionHash.hex(),
                    "explorer_url": f"{self.chainstack.network_specs[network]['explorer']}{tx_receipt.transactionHash.hex()}"
                }
            else:
                error_msg = f"Approval transaction failed: {tx_receipt.transactionHash.hex()}"
                logger.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"Error approving token: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    def execute_swap(self, network, from_token, to_token, amount, slippage=None):
        """
        Execute token swap on specified network
        
        Args:
            network (str): "arbitrum" or "polygon"
            from_token (str): Token symbol or address to swap from
            to_token (str): Token symbol or address to swap to
            amount (float): Amount to swap in token units (not wei)
            slippage (float, optional): Slippage tolerance (e.g., 0.01 for 1%)
            
        Returns:
            dict: Transaction result
        """
        if not self.wallet_address or not self.private_key:
            return {"error": "MetaMask credentials not configured"}
            
        if slippage is None:
            slippage = self.default_slippage
            
        try:
            # Get network connection
            web3 = self.chainstack.get_connection(network)
            network_specs = self.chainstack.get_network_specs(network)
            
            # Determine token addresses
            from_token_address = from_token
            to_token_address = to_token
            
            # If symbols provided, convert to addresses
            if isinstance(from_token, str) and from_token in network_specs["tokens"]:
                from_token_address = network_specs["tokens"][from_token]
            if isinstance(to_token, str) and to_token in network_specs["tokens"]:
                to_token_address = network_specs["tokens"][to_token]
                
            # Get token decimals for amount calculation
            from_token_contract = web3.eth.contract(address=from_token_address, abi=self.abis["erc20"])
            from_token_decimals = from_token_contract.functions.decimals().call()
            from_token_symbol = from_token_contract.functions.symbol().call()
            
            # Convert amount to token units with decimals
            amount_in_wei = int(amount * (10 ** from_token_decimals))
            
            # Choose DEX based on network
            if network == "arbitrum":
                dex = "uniswap_v3_router"
                router_address = network_specs["routers"]["uniswap"]
            else:  # polygon
                dex = "quickswap_router"
                router_address = network_specs["routers"]["quickswap"]
                
            router_contract = web3.eth.contract(address=router_address, abi=self.abis[dex])
            
            # Approve token spending if needed
            if from_token_address != network_specs["tokens"].get("WETH") and from_token_address != network_specs["tokens"].get("WMATIC"):
                approval_result = self.approve_token_if_needed(
                    network, from_token_address, router_address, amount_in_wei
                )
                if "error" in approval_result:
                    return approval_result
                    
            # Calculate minimum amount out with slippage
            # This is simplified - in a production app you would get price quotes first
            min_amount_out = int(amount_in_wei * (1 - slippage))
            
            # Calculate deadline
            deadline = int(time.time() + 60 * self.transaction_deadline)
            
            # Build swap transaction
            if network == "arbitrum" and dex == "uniswap_v3_router":
                # Uniswap V3 on Arbitrum
                # This is simplified - in production you would need proper path and fee settings
                pass
            else:
                # Regular Uniswap V2/QuickSwap style router for other networks
                swap_txn = router_contract.functions.swapExactTokensForTokens(
                    amount_in_wei,
                    min_amount_out,
                    [from_token_address, to_token_address],  # Path
                    self.wallet_address,  # Recipient
                    deadline
                ).build_transaction({
                    'from': self.wallet_address,
                    'gas': 300000,  # Gas limit - this should be estimated in production
                    'gasPrice': int(web3.eth.gas_price * network_specs["gas_multiplier"]),
                    'nonce': web3.eth.get_transaction_count(self.wallet_address)
                })
                
            # Sign and submit transaction
            signed_txn = web3.eth.account.sign_transaction(swap_txn, self.private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            logger.info(f"Swap submitted with hash: {tx_hash_hex}")
            
            # Record in transaction history
            tx_record = {
                "type": "swap",
                "network": network,
                "from_token": from_token_symbol,
                "to_token": to_token,
                "amount": amount,
                "tx_hash": tx_hash_hex,
                "timestamp": datetime.now().isoformat(),
                "status": "pending",
                "explorer_url": f"{network_specs['explorer']}{tx_hash_hex}"
            }
            
            self.tx_history.append(tx_record)
            self._save_tx_history()
            
            return {
                "status": "submitted",
                "tx_hash": tx_hash_hex,
                "network": network,
                "from_token": from_token_symbol,
                "to_token": to_token,
                "amount": amount,
                "explorer_url": f"{network_specs['explorer']}{tx_hash_hex}"
            }
            
        except Exception as e:
            error_msg = f"Error executing swap: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
            
    def check_transaction_status(self, network, tx_hash):
        """Check status of a transaction"""
        try:
            web3 = self.chainstack.get_connection(network)
            receipt = web3.eth.get_transaction_receipt(tx_hash)
            
            if receipt is None:
                return {"status": "pending", "tx_hash": tx_hash}
                
            # Update transaction history
            for tx in self.tx_history:
                if tx.get("tx_hash") == tx_hash:
                    tx["status"] = "success" if receipt.status == 1 else "failed"
                    self._save_tx_history()
                    break
                    
            return {
                "status": "success" if receipt.status == 1 else "failed",
                "tx_hash": tx_hash,
                "block_number": receipt.blockNumber,
                "gas_used": receipt.gasUsed,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking transaction: {str(e)}")
            return {"error": str(e), "tx_hash": tx_hash}

# Simple test function
if __name__ == "__main__":
    trader = MetaMaskTrader()
    
    # Check balances
    balances = trader.get_wallet_balances()
    print("Wallet balances across networks:")
    print(json.dumps(balances, indent=2))
