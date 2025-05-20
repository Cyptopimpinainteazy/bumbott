"""
Chainstack Provider - Blockchain Integration Module for BumBot Quantum Trading

This module provides a high-performance interface to Arbitrum and Polygon networks
via Chainstack, optimized for real-time trading operations.
"""
from web3 import Web3, HTTPProvider
from dotenv import load_dotenv
import os
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/chainstack.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('chainstack')

class ChainstackProvider:
    """Chainstack blockchain infrastructure connection manager"""
    
    def __init__(self):
        load_dotenv()
        # Initialize connections dictionary
        self.web3_connections = {}
        self.chainstack_endpoints = {
            "arbitrum": os.getenv("CHAINSTACK_ARBITRUM_URL"),
            "polygon": os.getenv("CHAINSTACK_POLYGON_URL"),
            "optimism": os.getenv("CHAINSTACK_OPTIMISM_URL"),
            "base": os.getenv("CHAINSTACK_BASE_URL"),
            "zksync": os.getenv("CHAINSTACK_ZKSYNC_URL"),
            "linea": os.getenv("CHAINSTACK_LINEA_URL")
        }
        
        # Network-specific authentication
        self.chainstack_auth = {
            "arbitrum": {
                "username": os.getenv("CHAINSTACK_ARBITRUM_USERNAME"),
                "password": os.getenv("CHAINSTACK_ARBITRUM_PASSWORD")
            },
            "polygon": {
                "username": os.getenv("CHAINSTACK_POLYGON_USERNAME"),
                "password": os.getenv("CHAINSTACK_POLYGON_PASSWORD")
            },
            "optimism": {
                "username": os.getenv("CHAINSTACK_OPTIMISM_USERNAME"),
                "password": os.getenv("CHAINSTACK_OPTIMISM_PASSWORD")
            },
            "base": {
                "username": os.getenv("CHAINSTACK_BASE_USERNAME"),
                "password": os.getenv("CHAINSTACK_BASE_PASSWORD")
            },
            "zksync": {
                "username": os.getenv("CHAINSTACK_ZKSYNC_USERNAME"),
                "password": os.getenv("CHAINSTACK_ZKSYNC_PASSWORD")
            },
            "linea": {
                "username": os.getenv("CHAINSTACK_LINEA_USERNAME"),
                "password": os.getenv("CHAINSTACK_LINEA_PASSWORD")
            }
        }
        
        # Fall back to generic credentials if network-specific ones aren't available
        generic_username = os.getenv("CHAINSTACK_USERNAME")
        generic_password = os.getenv("CHAINSTACK_PASSWORD")
        
        if generic_username and generic_password:
            for network in self.chainstack_endpoints:
                if not self.chainstack_auth[network]["username"]:
                    self.chainstack_auth[network]["username"] = generic_username
                if not self.chainstack_auth[network]["password"]:
                    self.chainstack_auth[network]["password"] = generic_password
        
        # Network specifications
        self.network_specs = {
            "arbitrum": {
                "chain_id": 42161,
                "explorer": "https://arbiscan.io/tx/",
                "gas_multiplier": float(os.getenv("ARBITRUM_GAS_MULTIPLIER", 1.1)),
                "routers": {
                    "uniswap": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",  # Uniswap V3 Router
                    "sushiswap": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"  # Sushiswap Router
                },
                "tokens": {
                    "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
                    "USDC": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
                    "LINK": "0xf97f4df75117a78c1A5a0DBb814Af92458539FB4",
                    "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
                    "ARB": "0x912CE59144191C1204E64559FE8253a0e49E6548",
                    "GMX": "0xfc5A1A6EB076a2C7aD06eD22C90d7E710E35ad0a",
                    "RDNT": "0x3082CC23568eA640225c2467653dB90e9250AaA0"
                }
            },
            "polygon": {
                "chain_id": 137,
                "explorer": "https://polygonscan.com/tx/",
                "gas_multiplier": float(os.getenv("POLYGON_GAS_MULTIPLIER", 1.5)),
                "routers": {
                    "quickswap": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",  # QuickSwap Router
                    "sushiswap": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"  # Sushiswap Router
                },
                "tokens": {
                    "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
                    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
                    "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
                    "LINK": "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39",
                    "AAVE": "0xD6DF932A45C0f255f85145f286eA0b292B21C90B",
                    "QUICK": "0xB5C064F955D8e7F38fE0460C556a72987494eE17",
                    "SUSHI": "0x0b3F868E0BE5597D5DB7fEB59E1CADBb0fdDa50a"
                }
            },
            "optimism": {
                "chain_id": 10,
                "explorer": "https://optimistic.etherscan.io/tx/",
                "gas_multiplier": float(os.getenv("OPTIMISM_GAS_MULTIPLIER", 1.1)),
                "routers": {
                    "uniswap": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",  # Uniswap V3 Router
                    "velodrome": "0xa132DAB612dB5cB9fC9Ac426A0Cc215A3423F9c9"  # Velodrome Router
                },
                "tokens": {
                    "WETH": "0x4200000000000000000000000000000000000006",
                    "USDC": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
                    "DAI": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
                    "OP": "0x4200000000000000000000000000000000000042",
                    "SNX": "0x8700dAec35aF8Ff88c16BdF0418774CB3D7599B4",
                    "VELO": "0x9560e827aF36c94D2Ac33a39bCE1Fe78631088Db"
                }
            },
            "base": {
                "chain_id": 8453,
                "explorer": "https://basescan.org/tx/",
                "gas_multiplier": float(os.getenv("BASE_GAS_MULTIPLIER", 1.2)),
                "routers": {
                    "aerodrome": "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43",  # Aerodrome Router
                    "baseswap": "0x327Df1E6de05895d2ab08513aaDD9313Fe505d86"  # BaseSwap Router
                },
                "tokens": {
                    "WETH": "0x4200000000000000000000000000000000000006",
                    "USDbC": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",
                    "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                    "DAI": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
                    "AERO": "0x940181a94A35A4569E4529A3CDfB74e38FD98631",
                    "BSWAP": "0x78a087d713Be963Bf307b18F2Ff8122EF9A63ae9"
                }
            },
            "zksync": {
                "chain_id": 324,
                "explorer": "https://explorer.zksync.io/tx/",
                "gas_multiplier": float(os.getenv("ZKSYNC_GAS_MULTIPLIER", 1.05)),
                "routers": {
                    "syncswap": "0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295",  # SyncSwap Router
                    "mute": "0x8B791913eB07C32779a16750e3868aA8495F5964"  # Mute.io Router
                },
                "tokens": {
                    "WETH": "0x5AEa5775959fBC2557Cc8789bC1bf90A239D9a91",
                    "USDC": "0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4",
                    "USDT": "0x493257fD37EDB34451f62EDf8D2a0C418852bA4C",
                    "BUSD": "0x2039bb4116B4EFc145Ec4f0e2eA75012D6C0f181",
                    "SYNC": "0xB2b3Dd486d813E0f68F5e35021A4aed0f6FB5EEc",
                    "MUTE": "0x0e97C7a0F8B2C9885C8ac9fC6136e829CbC21d42"
                }
            },
            "linea": {
                "chain_id": 59144,
                "explorer": "https://lineascan.build/tx/",
                "gas_multiplier": float(os.getenv("LINEA_GAS_MULTIPLIER", 1.2)),
                "routers": {
                    "horizondex": "0xE4e60B6A4cF0Af7f106e4773Ea5C1e6BaAD1B1c9",  # HorizonDEX Router
                    "syncswap": "0x80e38291e06339d10AAB483C65695D004dBD5C69"  # SyncSwap Router
                },
                "tokens": {
                    "WETH": "0xe5D7C2a44FfDDf6b295A15c148167daaAf5Cf34f",
                    "USDC": "0x176211869cA2b568f2A7D4EE941E073a821EE1ff",
                    "USDT": "0xA219439258ca9da29E9Cc4cE5596924745e12B93",
                    "DAI": "0x4AF15ec2A0BD43Db75dd04E62FAA3B8EF36b00d5",
                    "WBTC": "0x3aAB2285ddcDdaD8edf438C1bAB47e1a9D05a9b4",
                    "HORIZON": "0xc7D8489DaE3D2EbEF075b1dB2e4D6d071c955313"
                }
            }
        }
        
        # Initialize Web3 connections
        self.web3_connections = {}
        self._init_connections()
        
        # Load ABIs
        os.makedirs('abi', exist_ok=True)
        self._ensure_abi_files()
        
    def _init_connections(self):
        """Initialize Web3 connections to Chainstack nodes"""
        for network, endpoint in self.chainstack_endpoints.items():
            if not endpoint or endpoint.find("YOUR_PROJECT_ID") > -1:
                logger.warning(f"No valid Chainstack endpoint defined for {network}")
                continue
                
            # Get network-specific authentication
            network_auth = self.chainstack_auth.get(network, {})
            username = network_auth.get("username")
            password = network_auth.get("password")
            
            # Log connection attempt with masked credentials
            logger.info(f"Connecting to {network} using credentials: {username[:3]}*** / {password[:3]}***")
                
            http_provider = HTTPProvider(
                endpoint,
                request_kwargs={
                    "auth": (
                        username,
                        password
                    ) if username and password else None
                }
            )
            
            web3 = Web3(http_provider)
            
            # Add middleware for Arbitrum and Polygon which are POA chains
            try:
                # Try to import it from different locations based on web3 version
                try:
                    from web3.middleware import geth_poa_middleware
                    web3.middleware_onion.inject(geth_poa_middleware, layer=0)
                except ImportError:
                    try:
                        from web3.middleware.geth import geth_poa_middleware
                        web3.middleware_onion.inject(geth_poa_middleware, layer=0)
                    except (ImportError, AttributeError):
                        # Some versions use different patterns
                        try:
                            web3.middleware_stack.inject(geth_poa_middleware, layer=0)
                        except:
                            logger.warning(f"Could not add POA middleware to {network} connection")
            except Exception as e:
                logger.warning(f"Error adding middleware: {str(e)}")
                
            self.web3_connections[network] = web3
            connected = web3.is_connected()
            connection_status = "SUCCESS" if connected else "FAILED"
            logger.info(f"Chainstack {network} connection: {connection_status}")
            
    def _ensure_abi_files(self):
        """Create ABI files if they don't exist"""
        abi_files = {
            "uniswap_v3_router.json": [
                {"inputs":[{"name":"tokenIn","type":"address"},{"name":"tokenOut","type":"address"},
                {"name":"fee","type":"uint24"},{"name":"recipient","type":"address"},
                {"name":"deadline","type":"uint256"},{"name":"amountIn","type":"uint256"},
                {"name":"amountOutMinimum","type":"uint256"},{"name":"sqrtPriceLimitX96","type":"uint160"}],
                "name":"exactInputSingle","outputs":[{"name":"amountOut","type":"uint256"}],
                "stateMutability":"payable","type":"function"}
            ],
            "uniswap_v2_router.json": [
                {"inputs":[{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},
                {"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],
                "name":"swapExactTokensForTokens","outputs":[{"name":"amounts","type":"uint256[]"}],
                "stateMutability":"nonpayable","type":"function"}
            ],
            "quickswap_router.json": [
                {"inputs":[{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},
                {"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],
                "name":"swapExactTokensForTokens","outputs":[{"name":"amounts","type":"uint256[]"}],
                "stateMutability":"nonpayable","type":"function"}
            ],
            "erc20.json": [
                {"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":False,"stateMutability":"view","type":"function"},
                {"constant":False,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],
                "name":"approve","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"nonpayable","type":"function"},
                {"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},
                {"constant":False,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],
                "name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"nonpayable","type":"function"},
                {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":False,"stateMutability":"view","type":"function"},
                {"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],
                "payable":False,"stateMutability":"view","type":"function"},
                {"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":False,"stateMutability":"view","type":"function"},
                {"constant":False,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],
                "name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":False,"stateMutability":"nonpayable","type":"function"},
                {"constant":True,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],
                "name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"}
            ]
        }
        
        for filename, abi in abi_files.items():
            file_path = os.path.join('abi', filename)
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump(abi, f, indent=2)
                logger.info(f"Created ABI file: {filename}")
    
    def get_connection(self, network):
        """Get Web3 connection for specified network"""
        if network not in self.web3_connections:
            raise ValueError(f"No connection available for {network}")
            
        if not self.web3_connections[network].is_connected():
            raise ConnectionError(f"Connection to {network} is not active")
            
        return self.web3_connections[network]
        
    def get_network_specs(self, network):
        """Get network specifications"""
        if network not in self.network_specs:
            raise ValueError(f"Network specifications not available for {network}")
            
        return self.network_specs[network]
        
    def get_token_balance(self, network, token_address, wallet_address):
        """Get token balance for a wallet"""
        try:
            web3 = self.get_connection(network)
            with open(os.path.join('abi', 'erc20.json')) as f:
                erc20_abi = json.load(f)
                
            token_contract = web3.eth.contract(address=token_address, abi=erc20_abi)
            balance = token_contract.functions.balanceOf(wallet_address).call()
            decimals = token_contract.functions.decimals().call()
            symbol = token_contract.functions.symbol().call()
            
            return {
                "symbol": symbol,
                "balance_raw": balance,
                "balance": balance / (10 ** decimals),
                "decimals": decimals
            }
        except Exception as e:
            logger.error(f"Error getting token balance: {str(e)}")
            return {"error": str(e)}
            
    def submit_transaction(self, network, transaction, private_key):
        """Sign and submit transaction to the network"""
        try:
            web3 = self.get_connection(network)
            signed_tx = web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            return {
                "status": "submitted",
                "tx_hash": tx_hash.hex(),
                "network": network,
                "explorer_url": f"{self.network_specs[network]['explorer']}{tx_hash.hex()}"
            }
        except Exception as e:
            logger.error(f"Error submitting transaction: {str(e)}")
            return {"error": str(e)}

# Simple test function
if __name__ == "__main__":
    provider = ChainstackProvider()
    for network in provider.chainstack_endpoints:
        try:
            connection = provider.web3_connections.get(network)
            if connection and connection.is_connected():
                block = connection.eth.block_number
                print(f"{network.capitalize()} current block: {block}")
        except Exception as e:
            print(f"Error checking {network}: {str(e)}")
