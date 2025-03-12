from web3 import Web3
from typing import Union, Dict, Any, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('gas_utils')

def wei_to_gwei(wei_value: Union[int, str]) -> float:
    """
    Convert wei to gwei.
    
    Args:
        wei_value: Value in wei (as int or string)
        
    Returns:
        float: Value in gwei
    """
    try:
        # Convert to int if it's a string
        if isinstance(wei_value, str):
            wei_value = int(wei_value)
        
        # Use Web3.py's built-in conversion
        return Web3.from_wei(wei_value, 'gwei')
    except Exception as e:
        logger.error(f"Error converting wei to gwei: {e}")
        return 0.0

def gwei_to_wei(gwei_value: Union[float, int, str]) -> int:
    """
    Convert gwei to wei.
    
    Args:
        gwei_value: Value in gwei (as float, int, or string)
        
    Returns:
        int: Value in wei
    """
    try:
        # Convert to float if it's a string
        if isinstance(gwei_value, str):
            gwei_value = float(gwei_value)
        
        # Use Web3.py's built-in conversion
        return Web3.to_wei(gwei_value, 'gwei')
    except Exception as e:
        logger.error(f"Error converting gwei to wei: {e}")
        return 0

def gwei_to_eth(gwei_value: Union[float, int, str]) -> float:
    """
    Convert gwei to eth.
    
    Args:
        gwei_value: Value in gwei (as float, int, or string)
        
    Returns:
        float: Value in eth
    """
    try:
        # First convert gwei to wei
        wei_value = gwei_to_wei(gwei_value)
        
        # Then convert wei to eth
        return Web3.from_wei(wei_value, 'ether')
    except Exception as e:
        logger.error(f"Error converting gwei to eth: {e}")
        return 0.0

def wei_to_eth(wei_value: Union[int, str]) -> float:
    """
    Convert wei to eth.
    
    Args:
        wei_value: Value in wei (as int or string)
        
    Returns:
        float: Value in eth
    """
    try:
        # Convert to int if it's a string
        if isinstance(wei_value, str):
            wei_value = int(wei_value)
        
        # Use Web3.py's built-in conversion
        return Web3.from_wei(wei_value, 'ether')
    except Exception as e:
        logger.error(f"Error converting wei to eth: {e}")
        return 0.0

def eth_to_wei(eth_value: Union[float, int, str]) -> int:
    """
    Convert eth to wei.
    
    Args:
        eth_value: Value in eth (as float, int, or string)
        
    Returns:
        int: Value in wei
    """
    try:
        # Convert to float if it's a string
        if isinstance(eth_value, str):
            eth_value = float(eth_value)
        
        # Use Web3.py's built-in conversion
        return Web3.to_wei(eth_value, 'ether')
    except Exception as e:
        logger.error(f"Error converting eth to wei: {e}")
        return 0

def format_gas_prices(gas_prices: Dict[str, float], to_unit: str = 'gwei') -> Dict[str, float]:
    """
    Format gas prices to a specific unit.
    
    Args:
        gas_prices: Dictionary containing gas prices (slow, average, fast)
        to_unit: Target unit ('wei', 'gwei', or 'eth')
        
    Returns:
        Dict: Gas prices in the specified unit
    """
    try:
        result = {}
        
        # Assume input is in wei by default
        for key, value in gas_prices.items():
            if to_unit.lower() == 'gwei':
                result[key] = wei_to_gwei(value)
            elif to_unit.lower() == 'eth':
                result[key] = wei_to_eth(value)
            else:  # Default to wei
                result[key] = value if isinstance(value, int) else int(value)
                
        return result
    except Exception as e:
        logger.error(f"Error formatting gas prices: {e}")
        return gas_prices

def calculate_transaction_fee(gas_price: Union[int, float, str], gas_limit: Union[int, str]) -> Dict[str, Any]:
    """
    Calculate the transaction fee based on gas price and gas limit.
    
    Args:
        gas_price: Gas price in wei
        gas_limit: Gas limit for the transaction
        
    Returns:
        Dict: Transaction fee in wei, gwei, and eth
    """
    try:
        # Convert to int if they're strings
        if isinstance(gas_price, str):
            gas_price = int(gas_price)
        if isinstance(gas_limit, str):
            gas_limit = int(gas_limit)
        
        # Calculate fee in wei
        fee_wei = gas_price * gas_limit
        
        return {
            'wei': fee_wei,
            'gwei': wei_to_gwei(fee_wei),
            'eth': wei_to_eth(fee_wei)
        }
    except Exception as e:
        logger.error(f"Error calculating transaction fee: {e}")
        return {'wei': 0, 'gwei': 0.0, 'eth': 0.0}

def get_gas_price_strategy(strategy: str = 'average') -> Optional[float]:
    """
    Get gas price based on a strategy.
    
    Args:
        strategy: Strategy to use ('slow', 'average', 'fast')
        
    Returns:
        Optional[float]: Gas price in gwei based on the strategy
    """
    try:
        # This would typically connect to a node or service to get current gas prices
        # For now, we'll just return None to indicate this needs to be implemented
        # with actual blockchain connection
        logger.warning("get_gas_price_strategy needs to be implemented with actual blockchain connection")
        return None
    except Exception as e:
        logger.error(f"Error getting gas price strategy: {e}")
        return None

def format_token_balance(balance, decimals=18):
    """
    Format a token balance from its raw form to a human-readable decimal value.
    
    Args:
        balance (str or int): The raw token balance
        decimals (int): Number of decimal places for the token (default: 18 for most ERC20 tokens)
        
    Returns:
        float: The formatted token balance
    """
    try:
        return float(balance) / (10 ** decimals)
    except (ValueError, TypeError):
        return balance 