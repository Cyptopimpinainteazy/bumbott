"""
Comprehensive Token Pairs Database for MEV Strategies
This database contains trading pairs across multiple L2 networks with 
metadata for liquidity, volume, and opportunity scores.
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union

# Token base information - Addresses and metadata
TOKEN_INFO = {
    "arbitrum": {
        "WETH": {
            "address": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
            "decimals": 18,
            "is_base_token": True
        },
        "ARB": {
            "address": "0x912CE59144191C1204E64559FE8253a0e49E6548",
            "decimals": 18,
            "is_base_token": True
        },
        "USDC": {
            "address": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
            "decimals": 6,
            "is_base_token": True
        },
        "USDT": {
            "address": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
            "decimals": 6,
            "is_base_token": True
        },
        "WBTC": {
            "address": "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f",
            "decimals": 8,
            "is_base_token": True
        },
        "GMX": {
            "address": "0xfc5A1A6EB076a2C7aD06eD22C90d7E710E35ad0a",
            "decimals": 18,
            "is_base_token": False
        },
        "LINK": {
            "address": "0xf97f4df75117a78c1A5a0DBb814Af92458539FB4",
            "decimals": 18,
            "is_base_token": False
        },
        "UNI": {
            "address": "0xFa7F8980b0f1E64A2062791cc3b0871572f1F7f0",
            "decimals": 18,
            "is_base_token": False
        },
        "MAGIC": {
            "address": "0x539bdE0d7Dbd336b79148AA742883198BBF60342",
            "decimals": 18,
            "is_base_token": False
        },
        "JONES": {
            "address": "0x10393c20975cF177a3513071bC110f7962CD67da",
            "decimals": 18,
            "is_base_token": False
        },
        "DPX": {
            "address": "0x6C2C06790b3E3E3c38e12Ee22F8183b37a13EE55",
            "decimals": 18,
            "is_base_token": False
        },
        "RDPX": {
            "address": "0x32Eb7902D4134bf98A28b963D26de779AF92A212",
            "decimals": 18,
            "is_base_token": False
        },
        "GRAIL": {
            "address": "0x3d9907F9a368ad0a51Be60f7Da3b97cf940982D8",
            "decimals": 18,
            "is_base_token": False
        },
        "PENDLE": {
            "address": "0x0c880f6761F1af8d9Aa9C466984b80DAb9a8c9e8",
            "decimals": 18,
            "is_base_token": False
        },
        "STG": {
            "address": "0x6694340fc020c5E6B96567843da2df01b2CE1eb6",
            "decimals": 18,
            "is_base_token": False
        }
    },
    "optimism": {
        "WETH": {
            "address": "0x4200000000000000000000000000000000000006",
            "decimals": 18,
            "is_base_token": True
        },
        "OP": {
            "address": "0x4200000000000000000000000000000000000042",
            "decimals": 18,
            "is_base_token": True
        },
        "USDC": {
            "address": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
            "decimals": 6,
            "is_base_token": True
        },
        "USDT": {
            "address": "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",
            "decimals": 6,
            "is_base_token": True
        },
        "DAI": {
            "address": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
            "decimals": 18,
            "is_base_token": True
        },
        "WBTC": {
            "address": "0x68f180fcCe6836688e9084f035309E29Bf0A2095",
            "decimals": 8,
            "is_base_token": True
        },
        "SNX": {
            "address": "0x8700dAec35aF8Ff88c16BdF0418774CB3D7599B4",
            "decimals": 18,
            "is_base_token": False
        },
        "PERP": {
            "address": "0x9e1028F5F1D5eDE59748FFceE5532509976840E0",
            "decimals": 18,
            "is_base_token": False
        },
        "LYRA": {
            "address": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
            "decimals": 18,
            "is_base_token": False
        },
        "THALES": {
            "address": "0x217D47011b23BB961eB6D93cA9945B7501a5BB11",
            "decimals": 18,
            "is_base_token": False
        },
        "sUSD": {
            "address": "0x8c6f28f2F1A3C87F0f938b96d27520d9751ec8d9",
            "decimals": 18,
            "is_base_token": False
        },
        "VELO": {
            "address": "0x3c8B650257cFb5f272f799F5e2b4e65093a11a05",
            "decimals": 18,
            "is_base_token": False
        },
        "BIFI": {
            "address": "0x4E720DD3Ac5CFe1e1fbDE4935f386Bb1C66F4642",
            "decimals": 18,
            "is_base_token": False
        },
        "FRAX": {
            "address": "0x2E3D870790dC77A83DD1d18184Acc7439A53f475",
            "decimals": 18,
            "is_base_token": False
        }
    },
    "polygon": {
        "WETH": {
            "address": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
            "decimals": 18,
            "is_base_token": True
        },
        "MATIC": {
            "address": "0x0000000000000000000000000000000000001010",
            "decimals": 18,
            "is_base_token": True
        },
        "WMATIC": {
            "address": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
            "decimals": 18,
            "is_base_token": True
        },
        "USDC": {
            "address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "decimals": 6,
            "is_base_token": True
        },
        "USDT": {
            "address": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
            "decimals": 6,
            "is_base_token": True
        },
        "DAI": {
            "address": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
            "decimals": 18,
            "is_base_token": True
        },
        "WBTC": {
            "address": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
            "decimals": 8,
            "is_base_token": True
        },
        "AAVE": {
            "address": "0xD6DF932A45C0f255f85145f286eA0b292B21C90B",
            "decimals": 18,
            "is_base_token": False
        },
        "QUICK": {
            "address": "0xB5C064F955D8e7F38fE0460C556a72987494eE17",
            "decimals": 18,
            "is_base_token": False
        },
        "CRV": {
            "address": "0x172370d5Cd63279eFa6d502DAB29171933a610AF",
            "decimals": 18,
            "is_base_token": False
        },
        "GHST": {
            "address": "0x385Eeac5cB85A38A9a07A70c73e0a3271CfB54A7",
            "decimals": 18,
            "is_base_token": False
        },
        "LINK": {
            "address": "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39",
            "decimals": 18,
            "is_base_token": False
        },
        "SUSHI": {
            "address": "0x0b3F868E0BE5597D5DB7fEB59E1CADBb0fdDa50a",
            "decimals": 18,
            "is_base_token": False
        },
        "SAND": {
            "address": "0xBbba073C31bF03b8ACf7c28EF0738DeCF3695683",
            "decimals": 18,
            "is_base_token": False
        },
        "BAL": {
            "address": "0x9a71012B13CA4d3D0Cdc72A177DF3ef03b0E76A3",
            "decimals": 18,
            "is_base_token": False
        }
    },
    "bsc": {
        "WBNB": {
            "address": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
            "decimals": 18,
            "is_base_token": True
        },
        "BUSD": {
            "address": "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56",
            "decimals": 18,
            "is_base_token": True
        },
        "USDT": {
            "address": "0x55d398326f99059fF775485246999027B3197955",
            "decimals": 18,
            "is_base_token": True
        },
        "USDC": {
            "address": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
            "decimals": 18,
            "is_base_token": True
        },
        "BTCB": {
            "address": "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c",
            "decimals": 18,
            "is_base_token": True
        },
        "ETH": {
            "address": "0x2170Ed0880ac9A755fd29B2688956BD959F933F8",
            "decimals": 18,
            "is_base_token": True
        },
        "CAKE": {
            "address": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
            "decimals": 18,
            "is_base_token": False
        },
        "XVS": {
            "address": "0xcF6BB5389c92Bdda8a3747Ddb454cB7a64626C63",
            "decimals": 18,
            "is_base_token": False
        },
        "ADA": {
            "address": "0x3EE2200Efb3400fAbB9AacF31297cBdD1d435D47",
            "decimals": 18,
            "is_base_token": False
        },
        "DOT": {
            "address": "0x7083609fCE4d1d8Dc0C979AAb8c869Ea2C873402",
            "decimals": 18,
            "is_base_token": False
        },
        "XRP": {
            "address": "0x1D2F0da169ceB9fC7B3144628dB156f3F6c60dBE",
            "decimals": 18,
            "is_base_token": False
        },
        "TRX": {
            "address": "0x85EAC5Ac2F758618dFa09bDbe0cf174e7d574D5B",
            "decimals": 18,
            "is_base_token": False
        },
        "BAKE": {
            "address": "0xE02dF9e3e622DeBdD69fb838bB799E3F168902c5",
            "decimals": 18,
            "is_base_token": False
        },
        "AUTO": {
            "address": "0xa184088a740c695E156F91f5cC086a06bb78b827",
            "decimals": 18,
            "is_base_token": False
        }
    }
}

# Generate Trading Pairs from Token Info
def generate_trading_pairs():
    """Generate trading pairs for each network with metadata"""
    trading_pairs = {}
    
    for network, tokens in TOKEN_INFO.items():
        network_pairs = []
        base_tokens = [symbol for symbol, info in tokens.items() if info.get('is_base_token', False)]
        
        # Generate pairs between base tokens and all other tokens
        for base_token in base_tokens:
            for token_symbol in tokens.keys():
                # Skip same token pairs and already created pairs
                if token_symbol == base_token:
                    continue
                
                # Create the pair
                pair = (base_token, token_symbol)
                
                # Add liquidity and volume metrics (this would be fetched from on-chain in production)
                liquidity = round(float(hash(f"{network}:{base_token}:{token_symbol}") % 1000000) / 10000, 2)
                daily_volume = round(float(hash(f"{network}:{token_symbol}:{base_token}") % 5000000) / 10000, 2)
                
                # Calculate opportunity score based on liquidity and volume
                # Higher score = better MEV opportunity
                opportunity_score = round((daily_volume * 0.7 + liquidity * 0.3) / 100, 2)
                
                # Add to network pairs
                network_pairs.append({
                    "pair": pair,
                    "token0": {
                        "symbol": base_token,
                        "address": tokens[base_token]["address"],
                        "decimals": tokens[base_token]["decimals"]
                    },
                    "token1": {
                        "symbol": token_symbol,
                        "address": tokens[token_symbol]["address"],
                        "decimals": tokens[token_symbol]["decimals"]
                    },
                    "liquidity": liquidity,
                    "daily_volume": daily_volume,
                    "opportunity_score": opportunity_score,
                    "updated_at": datetime.now().isoformat()
                })
        
        # Sort pairs by opportunity score (highest first)
        network_pairs.sort(key=lambda x: x["opportunity_score"], reverse=True)
        trading_pairs[network] = network_pairs
    
    return trading_pairs

# Get top pairs for a specific network
def get_top_pairs(network, count=10):
    """Get top trading pairs for a network based on opportunity score"""
    all_pairs = generate_trading_pairs()
    
    if network not in all_pairs:
        return []
    
    return all_pairs[network][:count]

# Get pairs for specific tokens
def get_pairs_for_token(network, token_symbol, count=None):
    """Get all pairs that include a specific token"""
    all_pairs = generate_trading_pairs()
    
    if network not in all_pairs:
        return []
    
    token_pairs = [
        pair for pair in all_pairs[network] 
        if pair["token0"]["symbol"] == token_symbol or pair["token1"]["symbol"] == token_symbol
    ]
    
    if count:
        return token_pairs[:count]
    return token_pairs

# Get pairs for arbitrage (minimum 3 tokens in a cycle)
def get_arbitrage_paths(network, token_symbol, max_depth=3):
    """Find potential arbitrage paths starting and ending with the same token"""
    all_pairs = generate_trading_pairs()
    
    if network not in all_pairs:
        return []
    
    # Convert to adjacency list for path finding
    adjacency_list = {}
    for pair in all_pairs[network]:
        token0 = pair["token0"]["symbol"]
        token1 = pair["token1"]["symbol"]
        
        if token0 not in adjacency_list:
            adjacency_list[token0] = []
        if token1 not in adjacency_list:
            adjacency_list[token1] = []
        
        adjacency_list[token0].append((token1, pair["opportunity_score"]))
        adjacency_list[token1].append((token0, pair["opportunity_score"]))
    
    # Find paths using DFS (this is a simplified version)
    def dfs(current, path, visited, paths):
        # If we found a cycle back to starting token and path length is at least 3
        if current == token_symbol and len(path) >= 3 and len(path) <= max_depth:
            paths.append(path.copy())
            return
        
        # If path is too long, stop searching
        if len(path) >= max_depth:
            return
        
        # Visit neighbors
        if current in adjacency_list:
            for neighbor, _ in adjacency_list[current]:
                if neighbor not in visited or neighbor == token_symbol:
                    path.append(neighbor)
                    visited.add(neighbor)
                    dfs(neighbor, path, visited, paths)
                    path.pop()
                    if neighbor != token_symbol:
                        visited.remove(neighbor)
    
    paths = []
    dfs(token_symbol, [token_symbol], {token_symbol}, paths)
    
    # Rank paths by opportunity score
    ranked_paths = []
    for path in paths:
        total_score = 0
        for i in range(len(path) - 1):
            for neighbor, score in adjacency_list[path[i]]:
                if neighbor == path[i+1]:
                    total_score += score
                    break
        
        ranked_paths.append({
            "path": path,
            "score": total_score / len(path)
        })
    
    ranked_paths.sort(key=lambda x: x["score"], reverse=True)
    return ranked_paths

# Get tokens and pairs statistics
def get_database_stats():
    """Get statistics about the token pairs database"""
    stats = {
        "total_tokens": 0,
        "total_pairs": 0,
        "networks": {}
    }
    
    for network, tokens in TOKEN_INFO.items():
        token_count = len(tokens)
        pair_count = len(generate_trading_pairs().get(network, []))
        
        stats["networks"][network] = {
            "token_count": token_count,
            "pair_count": pair_count,
            "base_tokens": [symbol for symbol, info in tokens.items() if info.get('is_base_token', False)]
        }
        
        stats["total_tokens"] += token_count
        stats["total_pairs"] += pair_count
    
    return stats

# Export all pairs to JSON
def export_to_json(filename="token_pairs.json"):
    """Export the entire token pairs database to JSON file"""
    all_pairs = generate_trading_pairs()
    
    with open(filename, 'w') as f:
        json.dump(all_pairs, f, indent=2)
    
    return f"Exported {sum(len(pairs) for pairs in all_pairs.values())} pairs to {filename}"

# Example usage
if __name__ == "__main__":
    stats = get_database_stats()
    print(f"Token Pairs Database Statistics:")
    print(f"Total Tokens: {stats['total_tokens']}")
    print(f"Total Trading Pairs: {stats['total_pairs']}")
    print("\nNetwork Breakdown:")
    for network, data in stats["networks"].items():
        print(f"  {network}: {data['token_count']} tokens, {data['pair_count']} pairs")
    
    # Get top pairs for Arbitrum
    print("\nTop 5 Arbitrum Pairs by Opportunity Score:")
    for pair in get_top_pairs("arbitrum", 5):
        print(f"  {pair['token0']['symbol']}/{pair['token1']['symbol']} - Score: {pair['opportunity_score']}")
    
    # Get WETH pairs on Optimism
    print("\nTop 3 WETH Pairs on Optimism:")
    for pair in get_pairs_for_token("optimism", "WETH", 3):
        print(f"  WETH/{pair['token1']['symbol']} - Volume: ${pair['daily_volume']:,.2f}")
    
    # Get arbitrage paths for WETH on Polygon
    print("\nTop 3 Arbitrage Paths for WETH on Polygon:")
    for path_data in get_arbitrage_paths("polygon", "WETH")[:3]:
        path_str = " -> ".join(path_data["path"])
        print(f"  {path_str} - Score: {path_data['score']:.2f}")
    
    # Export to JSON file
    print("\n" + export_to_json())
