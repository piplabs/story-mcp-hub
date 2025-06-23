from web3 import Web3
from typing import Union, Dict, Any, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gas_utils")


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

        # Use Web3.py's built-in conversion, cast to float for consistency
        return float(Web3.from_wei(wei_value, "gwei"))
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
        return Web3.to_wei(gwei_value, "gwei")
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
        return Web3.from_wei(wei_value, "ether")
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

        # Use Web3.py's built-in conversion, cast to float for consistency
        return float(Web3.from_wei(wei_value, "ether"))
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
        return Web3.to_wei(eth_value, "ether")
    except Exception as e:
        logger.error(f"Error converting eth to wei: {e}")
        return 0


def format_gas_prices(
    gas_prices: Dict[str, float], to_unit: str = "gwei"
) -> Dict[str, float]:
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
            if to_unit.lower() == "gwei":
                result[key] = wei_to_gwei(value)
            elif to_unit.lower() == "eth":
                result[key] = wei_to_eth(value)
            else:  # Default to wei
                result[key] = value if isinstance(value, int) else int(value)

        return result
    except Exception as e:
        logger.error(f"Error formatting gas prices: {e}")
        return gas_prices


def get_gas_price_strategy(
    strategy: str = "average", storyscan_service=None
) -> Optional[float]:
    """
    Get gas price based on a strategy using the StoryScan API.

    Args:
        strategy: Strategy to use ('slow', 'average', 'fast')
        storyscan_service: An instance of StoryScanService to fetch gas prices

    Returns:
        Optional[float]: Gas price in gwei based on the strategy
    """
    try:
        if not storyscan_service:
            logger.warning("StoryscanService instance is required to fetch gas prices")
            return None

        # Get stats from StoryScan API which includes gas prices
        stats = storyscan_service.get_stats()

        if not stats or "gas_prices" not in stats:
            logger.warning("Failed to fetch gas prices from StoryScan API")
            return None

        # Get gas price based on strategy
        if strategy.lower() not in ["slow", "average", "fast"]:
            logger.warning(
                f"Invalid gas price strategy: {strategy}. Using 'average' instead."
            )
            strategy = "average"

        gas_price = stats["gas_prices"].get(strategy.lower())

        if gas_price is None:
            logger.warning(
                f"Gas price for strategy '{strategy}' not found. Using 'average' instead."
            )
            gas_price = stats["gas_prices"].get("average")

        return gas_price
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
        return float(balance) / (10**decimals)
    except (ValueError, TypeError):
        return balance


def calculate_fee(gas_price: float, gas_limit: int) -> str:
    """
    Calculate the transaction fee based on gas price (in gwei) and gas limit.
    Returns a formatted string with the fee calculation.

    Args:
        gas_price: Gas price in gwei
        gas_limit: Gas limit for the transaction

    Returns:
        str: Formatted transaction fee calculation
    """
    try:
        # Convert gas price from gwei to wei
        gas_price_wei = gwei_to_wei(gas_price)

        # Calculate fee in wei
        fee_wei = gas_price_wei * gas_limit

        # Convert fee back to gwei
        fee_gwei = wei_to_gwei(fee_wei)

        # Also calculate in ETH for reference
        fee_eth = wei_to_eth(fee_wei)

        return {
            "gas_price_gwei": gas_price,
            "gas_limit": gas_limit,
            "fee_wei": fee_wei,
            "fee_gwei": fee_gwei,
            "fee_eth": fee_eth,
            "formatted_output": (
                f"Transaction Fee Calculation:\n"
                f"Gas Price: {gas_price} gwei\n"
                f"Gas Limit: {gas_limit}\n"
                f"Fee: {fee_gwei} gwei ({fee_eth} ETH)"
            ),
        }
    except Exception as e:
        logger.error(f"Error calculating transaction fee: {e}")
        return {
            "error": str(e),
            "formatted_output": f"Error calculating transaction fee: {str(e)}",
        }


def convert_units(value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
    """
    Convert between different units (wei, gwei, and IP/ETH).

    Args:
        value: The value to convert
        from_unit: The unit to convert from ('wei', 'gwei', or 'ip'/'eth')
        to_unit: The unit to convert to ('wei', 'gwei', or 'ip'/'eth')

    Returns:
        Dict: Conversion result with raw value and formatted output
    """
    try:
        # Normalize units
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()

        # Replace 'ip' with 'eth' for consistency with utility functions
        if from_unit == "ip":
            from_unit = "eth"
        if to_unit == "ip":
            to_unit = "eth"

        # Validate units
        valid_units = ["wei", "gwei", "eth"]
        if from_unit not in valid_units:
            return {
                "error": f"Invalid from_unit: {from_unit}",
                "formatted_output": f"Invalid from_unit: {from_unit}. Valid options are 'wei', 'gwei', or 'ip'/'eth'.",
            }
        if to_unit not in valid_units:
            return {
                "error": f"Invalid to_unit: {to_unit}",
                "formatted_output": f"Invalid to_unit: {to_unit}. Valid options are 'wei', 'gwei', or 'ip'/'eth'.",
            }

        # Perform conversion
        result = None

        # Wei to other units
        if from_unit == "wei":
            if to_unit == "gwei":
                result = wei_to_gwei(value)
            elif to_unit == "eth":
                result = wei_to_eth(value)
            else:  # wei to wei
                result = value

        # Gwei to other units
        elif from_unit == "gwei":
            if to_unit == "wei":
                result = gwei_to_wei(value)
            elif to_unit == "eth":
                result = gwei_to_eth(value)
            else:  # gwei to gwei
                result = value

        # ETH to other units
        elif from_unit == "eth":
            if to_unit == "wei":
                result = eth_to_wei(value)
            elif to_unit == "gwei":
                wei_value = eth_to_wei(value)
                result = wei_to_gwei(wei_value)
            else:  # eth to eth
                result = value

        # Format the result based on the to_unit
        if to_unit == "wei":
            formatted_result = f"{int(result):,} wei"
        elif to_unit == "gwei":
            formatted_result = f"{result:,.9f} gwei"
        else:  # eth
            formatted_result = f"{result:,.18f} IP"

        # Display the original value and unit
        if from_unit == "wei":
            original = f"{int(value):,} wei"
        elif from_unit == "gwei":
            original = f"{value:,.9f} gwei"
        else:  # eth
            original = f"{value:,.18f} IP"

        return {
            "original_value": value,
            "original_unit": from_unit,
            "converted_value": result,
            "converted_unit": to_unit,
            "formatted_output": f"Conversion: {original} = {formatted_result}",
        }
    except Exception as e:
        logger.error(f"Error converting units: {e}")
        return {
            "error": str(e),
            "formatted_output": f"Error converting units: {str(e)}",
        }


def format_gas_amount(gas_amount: str) -> str:
    """
    Format large gas amounts to be more readable with units.

    Args:
        gas_amount: Gas amount as string

    Returns:
        str: Formatted gas amount with appropriate units
    """
    try:
        amount = int(gas_amount)
        if amount >= 1_000_000_000_000:  # Trillions
            return f"{amount / 1_000_000_000_000:.2f} T gas"
        elif amount >= 1_000_000_000:  # Billions
            return f"{amount / 1_000_000_000:.2f} B gas"
        elif amount >= 1_000_000:  # Millions
            return f"{amount / 1_000_000:.2f} M gas"
        elif amount >= 1_000:  # Thousands
            return f"{amount / 1_000:.2f} K gas"
        else:
            return f"{amount} gas"
    except (ValueError, TypeError):
        return gas_amount  # Return original if conversion fails
