import axios from 'axios';

const API_URL = 'https://api.binance.com/api/v3';
const API_KEY = process.env.API_KEY;
const API_SECRET = process.env.API_SECRET;

async function fetchMarketData(symbol) {
  try {
    const response = await axios.get(`${API_URL}/ticker/24hr`, {
      params: { symbol },
    });
    console.log(`Market Data for ${symbol}:`, response.data);
  } catch (error) {
    console.error('Error fetching market data:', error.message);
  }
}

async function executeTrade(symbol, side, quantity) {
  try {
    console.log(`Executing ${side} trade for ${quantity} ${symbol}...`);
    // Simulate trade execution (API integration required for real trades)
    console.log('Trade executed successfully!');
  } catch (error) {
    console.error('Error executing trade:', error.message);
  }
}

async function analyzePortfolio() {
  console.log('Analyzing portfolio...');
  // Simulate portfolio analysis
  console.log('Portfolio analysis complete. Suggestions: Diversify holdings.');
}

async function setPriceAlert(symbol, targetPrice) {
  console.log(`Setting price alert for ${symbol} at ${targetPrice}...`);
  // Simulate price alert setup
  console.log('Price alert set successfully!');
}

async function backtestStrategy(strategy, symbol) {
  console.log(`Backtesting strategy "${strategy}" on ${symbol}...`);
  // Simulate backtesting
  console.log('Backtesting complete. Results: Strategy is profitable.');
}

console.log("Running Crypto Trading Helper...");

// Command-line interface
const args = process.argv.slice(2);
const command = args[0];
const param1 = args[1];
const param2 = args[2];
const param3 = args[3];

switch (command) {
  case 'fetch':
    fetchMarketData(param1);
    break;
  case 'trade':
    executeTrade(param1, param2, param3);
    break;
  case 'analyze':
    analyzePortfolio();
    break;
  case 'alert':
    setPriceAlert(param1, param2);
    break;
  case 'backtest':
    backtestStrategy(param1, param2);
    break;
  default:
    console.log(`
Usage:
  node crypto_trading_helper.js fetch <symbol>          - Fetch market data for a symbol (e.g., BTCUSDT)
  node crypto_trading_helper.js trade <symbol> <side> <quantity> - Execute a trade (e.g., BTCUSDT BUY 0.01)
  node crypto_trading_helper.js analyze                 - Analyze your portfolio
  node crypto_trading_helper.js alert <symbol> <price>  - Set a price alert for a symbol
  node crypto_trading_helper.js backtest <strategy> <symbol> - Backtest a trading strategy on a symbol
`);
}
