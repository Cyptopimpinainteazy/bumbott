"""
Quantum-Enhanced L2 Trading Bot - Main Execution Script

This script provides a command-line interface to run the quantum trading system
with options to check wallet balances, run analysis, or execute trades.
"""
import argparse
import json
import sys
import os
from datetime import datetime
from quantum_trader_strategy import QuantumTradingStrategy
from metamask_trader import MetaMaskTrader
from chainstack_provider import ChainstackProvider
from quantum_orchestrator import QuantumOrchestrator

def setup_logging():
    """Setup log directory"""
    os.makedirs('logs', exist_ok=True)
    
    # Create log files if they don't exist
    log_files = ['strategy.log', 'metamask.log', 'quantum.log', 'chainstack.log']
    for file in log_files:
        log_path = os.path.join('logs', file)
        if not os.path.exists(log_path):
            with open(log_path, 'w') as f:
                f.write(f"# {file} created {datetime.now().isoformat()}\n")

def check_environment():
    """Check if environment is properly configured"""
    required_env = [
        "IBM_QUANTUM_TOKEN",
        "METAMASK_ADDRESS",
        "METAMASK_PRIVATE_KEY"
    ]
    
    missing = []
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    for env in required_env:
        if not os.getenv(env):
            missing.append(env)
            
    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        print("Please update your .env file with these values")
        return False
        
    return True

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Quantum-Enhanced L2 Trading Bot")
    
    # Command options
    parser.add_argument("command", choices=[
        "balance", "analyze", "trade", "status", "performance", "test"
    ], help="Command to execute")
    
    # Network option
    parser.add_argument("--network", choices=["arbitrum", "polygon"], default="arbitrum",
                     help="L2 network to use (default: arbitrum)")
    
    # Token pair options
    parser.add_argument("--base", default="ETH", help="Base token symbol (default: ETH)")
    parser.add_argument("--quote", default="USDC", help="Quote token symbol (default: USDC)")
    
    # Amount option
    parser.add_argument("--amount", type=float, default=0.001, 
                     help="Amount to trade (default: 0.001)")
    
    # Transaction hash for status
    parser.add_argument("--tx", help="Transaction hash for status check")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Check environment
    if not check_environment():
        return 1
        
    # Initialize components based on command
    if args.command == "balance":
        trader = MetaMaskTrader()
        balances = trader.get_wallet_balances()
        print(json.dumps(balances, indent=2))
        
    elif args.command == "analyze":
        strategy = QuantumTradingStrategy()
        analysis = strategy.execute_quantum_analysis(args.network, args.base, args.quote)
        print(json.dumps(analysis, indent=2))
        
    elif args.command == "trade":
        strategy = QuantumTradingStrategy()
        result = strategy.execute_trade(args.network, args.base, args.quote, None, args.amount)
        print(json.dumps(result, indent=2))
        
    elif args.command == "status":
        if not args.tx:
            print("ERROR: Transaction hash (--tx) required for status command")
            return 1
            
        trader = MetaMaskTrader()
        status = trader.check_transaction_status(args.network, args.tx)
        print(json.dumps(status, indent=2))
        
    elif args.command == "performance":
        strategy = QuantumTradingStrategy()
        metrics = strategy.get_performance_metrics()
        print(json.dumps(metrics, indent=2))
        
    elif args.command == "test":
        # Test quantum execution
        print("Testing IBM Quantum connection...")
        quantum = QuantumOrchestrator()
        circuit = quantum.create_bell_circuit()
        result = quantum.execute_circuit(circuit)
        print(f"Quantum test result: {json.dumps(result, indent=2)}")
        
        # Test Chainstack connection
        print("\nTesting Chainstack connection...")
        chainstack = ChainstackProvider()
        for network in chainstack.web3_connections:
            try:
                web3 = chainstack.get_connection(network)
                if web3 and web3.is_connected():
                    block = web3.eth.block_number
                    print(f"{network} connection successful. Current block: {block}")
                else:
                    print(f"{network} connection failed.")
            except Exception as e:
                print(f"Error connecting to {network}: {str(e)}")
                
    return 0

if __name__ == "__main__":
    sys.exit(main())
