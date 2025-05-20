"""
Connection Verification Script for BumBot Quantum Trading System

This script performs basic tests to verify:
1. IBM Quantum connection
2. Chainstack connection to Arbitrum and Polygon
"""
import os
import json
from dotenv import load_dotenv
from web3 import Web3
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger('verify')

def test_quantum_connection():
    """Test connection to IBM Quantum"""
    print("\n===== Testing IBM Quantum Connection =====")
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
        
        # Load credentials
        load_dotenv()
        token = os.getenv("IBM_QUANTUM_TOKEN")
        if not token:
            print("❌ ERROR: IBM_QUANTUM_TOKEN not found in .env file")
            return False
            
        print(f"✓ Found IBM Quantum token: {token[:8]}...")
        
        # Initialize service with explicit channel
        print("Connecting to IBM Quantum service...")
        try:
            service = QiskitRuntimeService(channel="ibm_quantum", token=token)
            print("✓ Successfully initialized IBM Quantum service")
            
            # List available backends
            backends = service.backends()
            print(f"✓ Found {len(backends)} available backends:")
            for i, backend in enumerate(backends):
                print(f"  {i+1}. {backend.name}")
                
            return True
            
        except Exception as e:
            print(f"❌ Error connecting to IBM Quantum: {str(e)}")
            return False
            
    except ImportError:
        print("❌ qiskit_ibm_runtime module not found. Install with: pip install qiskit-ibm-runtime")
        return False

def test_chainstack_connection():
    """Test connection to Chainstack L2 networks"""
    print("\n===== Testing Chainstack Connection =====")
    try:
        # Load credentials
        load_dotenv()
        
        # Check for Arbitrum credentials
        arb_url = os.getenv("CHAINSTACK_ARBITRUM_URL")
        arb_user = os.getenv("CHAINSTACK_ARBITRUM_USERNAME")
        arb_pass = os.getenv("CHAINSTACK_ARBITRUM_PASSWORD")
        
        if not all([arb_url, arb_user, arb_pass]):
            print("❌ ERROR: Arbitrum credentials missing in .env file")
            return False
            
        print(f"✓ Found Arbitrum credentials: {arb_user}")
        
        # Check for Polygon credentials
        poly_url = os.getenv("CHAINSTACK_POLYGON_URL")
        poly_user = os.getenv("CHAINSTACK_POLYGON_USERNAME") 
        poly_pass = os.getenv("CHAINSTACK_POLYGON_PASSWORD")
        
        if not all([poly_url, poly_user, poly_pass]):
            print("❌ WARNING: Polygon credentials missing in .env file")
            
        # Test Arbitrum connection
        print("\nConnecting to Arbitrum via Chainstack...")
        try:
            # Create HTTP provider with auth
            http_provider = Web3.HTTPProvider(
                arb_url,
                request_kwargs={"auth": (arb_user, arb_pass)}
            )
            
            # Initialize Web3 instance
            web3 = Web3(http_provider)
            
            # Check connection
            if web3.is_connected():
                block_number = web3.eth.block_number
                print(f"✓ Successfully connected to Arbitrum! Current block: {block_number}")
                
                # Check chain ID to verify it's actually Arbitrum
                chain_id = web3.eth.chain_id
                print(f"✓ Chain ID: {chain_id} {'(Arbitrum One)' if chain_id == 42161 else '(Unknown)'}")
                
                # Get gas price for reference
                gas_price = web3.eth.gas_price
                gas_price_gwei = web3.from_wei(gas_price, 'gwei')
                print(f"✓ Current gas price: {gas_price_gwei:.2f} gwei")
                
                return True
            else:
                print("❌ Failed to connect to Arbitrum network")
                return False
                
        except Exception as e:
            print(f"❌ Error connecting to Arbitrum: {str(e)}")
            return False
            
    except ImportError:
        print("❌ web3 module not found. Install with: pip install web3")
        return False

def test_metamask_connection():
    """Test MetaMask wallet configuration"""
    print("\n===== Testing MetaMask Configuration =====")
    
    # Load credentials
    load_dotenv()
    address = os.getenv("METAMASK_ADDRESS")
    private_key = os.getenv("METAMASK_PRIVATE_KEY")
    
    if not address or not private_key:
        print("❌ ERROR: MetaMask credentials missing in .env file")
        return False
        
    # Mask private key for display
    masked_pk = f"{private_key[:6]}...{private_key[-4:]}" if len(private_key) > 10 else "Invalid"
    print(f"✓ Found MetaMask configuration:")
    print(f"  Address: {address}")
    print(f"  Private Key: {masked_pk}")
    
    # Attempt to check balance if Arbitrum is connected
    try:
        # Load configurations
        arb_url = os.getenv("CHAINSTACK_ARBITRUM_URL")
        arb_user = os.getenv("CHAINSTACK_ARBITRUM_USERNAME")
        arb_pass = os.getenv("CHAINSTACK_ARBITRUM_PASSWORD")
        
        if all([arb_url, arb_user, arb_pass]):
            # Create HTTP provider with auth
            http_provider = Web3.HTTPProvider(
                arb_url,
                request_kwargs={"auth": (arb_user, arb_pass)}
            )
            
            # Initialize Web3 instance
            web3 = Web3(http_provider)
            
            if web3.is_connected() and Web3.is_address(address):
                balance = web3.eth.get_balance(address)
                eth_balance = web3.from_wei(balance, 'ether')
                print(f"✓ Arbitrum ETH Balance: {eth_balance:.6f} ETH")
                
                if eth_balance == 0:
                    print("⚠️  WARNING: Wallet has zero ETH balance on Arbitrum")
                    
                return True
    except Exception as e:
        print(f"❌ Error checking wallet balance: {str(e)}")
        
    return True

def main():
    """Main verification function"""
    print("BumBot Quantum Trading System - Connection Verification")
    print("======================================================")
    
    # Test IBM Quantum
    quantum_ok = test_quantum_connection()
    
    # Test Chainstack
    chainstack_ok = test_chainstack_connection()
    
    # Test MetaMask
    metamask_ok = test_metamask_connection()
    
    # Overall status
    print("\n===== Overall Status =====")
    print(f"IBM Quantum: {'✓ Connected' if quantum_ok else '❌ Not Connected'}")
    print(f"Chainstack: {'✓ Connected' if chainstack_ok else '❌ Not Connected'}")
    print(f"MetaMask: {'✓ Configured' if metamask_ok else '❌ Not Configured'}")
    
    if quantum_ok and chainstack_ok and metamask_ok:
        print("\n✅ SUCCESS: All components are properly configured!")
        print("You can now run your quantum trading system with:")
        print("  python run_quantum_trader.py analyze --network arbitrum --base ETH --quote USDC")
    else:
        print("\n⚠️  WARNING: Some components are not properly configured.")
        print("Please fix the issues above before running the trading system.")
        
    return 0

if __name__ == "__main__":
    main()
