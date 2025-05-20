#!/usr/bin/env python3
import sys
import os
import logging
import traceback
import subprocess
import argparse
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QCoreApplication

# Add parent directory to path to allow imports from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configure application settings
QCoreApplication.setOrganizationName("BumBot")
QCoreApplication.setApplicationName("BumBot Crypto Trading")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bumbot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def run_update_mcp_settings(args):
    script_path = os.path.join(BASE_DIR, "update_mcp_settings.ts")
    print(f"Running update_mcp_settings.ts from: {script_path}")  # Log the path
    command = ["npx", "ts-node", script_path]  # Use npx ts-node instead of node
    if args.dry_run:
        command.append("--dry-run")
    if args.interactive:
        command.append("--interactive")
    if args.restore:
        command.append("--restore")
    if args.verbose:
        command.append("--verbose")
    subprocess.run(command)

def run_smart_contract_helper(args):
    node_path = "C:\\Program Files\\nodejs\\node.exe"  # Replace with the actual path to node
    script_path = os.path.join(BASE_DIR, "smart_contract_helper.js")
    print(f"Running smart_contract_helper.js from: {script_path}")  # Log the path
    command = [node_path, script_path, args.command]
    # Provide default parameters to avoid interactive prompts
    if args.param1:
        command.append(args.param1)
    else:
        if args.command == "generate":
            command.append("TestContract")
        elif args.command == "test":
            command.append("TestContract")
        elif args.command == "deploy":
            command.append("TestContract")
    if args.param2:
        command.append(args.param2)
    if args.yes:
        command.append("--yes")
    subprocess.run(command)

def run_crypto_trading_helper(args):
    node_path = "C:\\Program Files\\nodejs\\node.exe"  # Replace with the actual path to node
    script_path = os.path.join(BASE_DIR, "crypto_trading_helper.js")
    print(f"Running crypto_trading_helper.js from: {script_path}")  # Log the path
    command = [node_path, script_path, args.command]
    # Provide default parameters to avoid interactive prompts
    if args.param1:
        command.append(args.param1)
    else:
        if args.command == "fetch":
            command.append("BTCUSD")
        elif args.command == "trade":
            command.append("mean_reversion")
        elif args.command == "analyze":
            command.append("30d")
        elif args.command == "alert":
            command.append("5")
        elif args.command == "backtest":
            command.append("momentum")
    if args.param2:
        command.append(args.param2)
    if args.param3:
        command.append(args.param3)
    if args.yes:
        command.append("--yes")
    subprocess.run(command)

def main():
    """
    Main entry point for the BumBot application.
    Initializes and starts the GUI interface or runs command-line utilities.
    """
    parser = argparse.ArgumentParser(description="Centralized MCP Server Management")
    subparsers = parser.add_subparsers(dest="module", required=True)

    # Subparser for update_mcp_settings
    mcp_parser = subparsers.add_parser("update_mcp_settings", help="Run the MCP settings updater")
    mcp_parser.add_argument("--dry-run", action="store_true", help="Simulate changes without modifying the file")
    mcp_parser.add_argument("--interactive", action="store_true", help="Confirm changes interactively before applying them")
    mcp_parser.add_argument("--restore", action="store_true", help="Restore the settings file from the last backup")
    mcp_parser.add_argument("--verbose", action="store_true", help="Log detailed information about each step")
    mcp_parser.set_defaults(func=run_update_mcp_settings)

    # Subparser for smart_contract_helper
    sc_parser = subparsers.add_parser("smart_contract_helper", help="Run the Smart Contract Helper")
    sc_parser.add_argument("command", choices=["generate", "test", "deploy"], help="Command to execute")
    sc_parser.add_argument("param1", nargs="?", help="First parameter (e.g., contract name or network)")
    sc_parser.add_argument("param2", nargs="?", help="Second parameter (optional)")
    sc_parser.add_argument("--yes", action="store_true", help="Auto-confirm prompts")
    sc_parser.set_defaults(func=run_smart_contract_helper)

    # Subparser for crypto_trading_helper
    ct_parser = subparsers.add_parser("crypto_trading_helper", help="Run the Crypto Trading Helper")
    ct_parser.add_argument("command", choices=["fetch", "trade", "analyze", "alert", "backtest"], help="Command to execute")
    ct_parser.add_argument("param1", nargs="?", help="First parameter (e.g., symbol or strategy)")
    ct_parser.add_argument("param2", nargs="?", help="Second parameter (e.g., price or side)")
    ct_parser.add_argument("param3", nargs="?", help="Third parameter (e.g., quantity)")
    ct_parser.add_argument("--yes", action="store_true", help="Auto-confirm prompts")
    ct_parser.set_defaults(func=run_crypto_trading_helper)

    args = parser.parse_args()
    if args.module:
        args.func(args)
    else:
        # Create application first
        app = QApplication(sys.argv)
        
        try:
            # Import GUI components after application is created
            from gui.main_window import MainWindow
            
            # Create and show main window
            window = MainWindow()
            window.show()
            
            # Run the application
            sys.exit(app.exec())
            
        except ImportError as e:
            error_message = f"Import Error: {str(e)}\n\nPlease make sure all required packages are installed."
            logger.error(error_message)
            logger.error(traceback.format_exc())
            
            # Show error message to user
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Failed to load BumBot application components")
            msg.setInformativeText(error_message)
            msg.setWindowTitle("BumBot Error")
            msg.setDetailedText(traceback.format_exc())
            msg.exec()
            sys.exit(1)
            
        except Exception as e:
            error_message = f"Unexpected Error: {str(e)}"
            logger.error(error_message)
            logger.error(traceback.format_exc())
            
            # Show error message to user
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Failed to start BumBot application")
            msg.setInformativeText(error_message)
            msg.setWindowTitle("BumBot Error")
            msg.setDetailedText(traceback.format_exc())
            msg.exec()
            sys.exit(1)


if __name__ == "__main__":
    main()
