# Utility Functions

This directory contains utility functions used across the Story MCP Hub project.

## Gas Utilities (`gas_utils.py`)

The `gas_utils.py` file provides functions for working with blockchain gas prices and unit conversions.

### Key Functions:

- **Unit Conversions**:
  - `wei_to_gwei(wei_value)`: Convert wei to gwei
  - `gwei_to_wei(gwei_value)`: Convert gwei to wei
  - `wei_to_eth(wei_value)`: Convert wei to ETH
  - `eth_to_wei(eth_value)`: Convert ETH to wei
  - `gwei_to_eth(gwei_value)`: Convert gwei to ETH

- **Gas Price Formatting**:
  - `format_gas_prices(gas_prices, to_unit)`: Format gas prices to a specific unit (wei, gwei, or eth)

- **Fee Calculation**:
  - `calculate_transaction_fee(gas_price, gas_limit)`: Calculate transaction fee based on gas price and limit

### Usage Example:

```python
from utils.gas_utils import wei_to_gwei, calculate_transaction_fee

# Convert wei to gwei
gas_price_gwei = wei_to_gwei(1000000000)  # 1.0 gwei

# Calculate transaction fee
fee = calculate_transaction_fee(1000000000, 21000)
print(f"Fee in ETH: {fee['eth']}")
```

### Notes:

- Gas prices in the Blockscout API are typically expressed in Gwei (gigawei), which is a unit of value equal to 1 billion Wei (10^-9 ETH).
- These utilities help standardize gas price handling across the application.
- The functions leverage Web3.py's built-in conversion utilities for accuracy. 