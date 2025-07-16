"""
ERC20 Standard ABI definitions.

This module provides the standard ERC20 ABI that can be imported
and used across the application without hardcoding.
"""

# Standard ERC20 ABI based on EIP-20 specification
# https://eips.ethereum.org/EIPS/eip-20
ERC20_ABI = [
    # Read-only functions
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    
    # State-changing functions
    {
        "constant": False,
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "from", "type": "address"},
            {"name": "to", "type": "address"},
            {"name": "value", "type": "uint256"}
        ],
        "name": "transferFrom",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    
    # Events
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "owner", "type": "address"},
            {"indexed": True, "name": "spender", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"}
        ],
        "name": "Approval",
        "type": "event"
    }
]

# Optional: Extended ERC20 ABI with additional common functions
# Some tokens implement additional functions beyond the standard
ERC20_EXTENDED_ABI = ERC20_ABI + [
    # Increase/Decrease allowance (safer than approve)
    {
        "constant": False,
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "addedValue", "type": "uint256"}
        ],
        "name": "increaseAllowance",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "subtractedValue", "type": "uint256"}
        ],
        "name": "decreaseAllowance",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    
    # Permit (EIP-2612) - gasless approvals
    {
        "constant": False,
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "deadline", "type": "uint256"},
            {"name": "v", "type": "uint8"},
            {"name": "r", "type": "bytes32"},
            {"name": "s", "type": "bytes32"}
        ],
        "name": "permit",
        "outputs": [],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "nonces",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "DOMAIN_SEPARATOR",
        "outputs": [{"name": "", "type": "bytes32"}],
        "type": "function"
    }
]

# Utility function to get ABI by preference
def get_erc20_abi(extended: bool = False) -> list:
    """
    Get ERC20 ABI.
    
    Args:
        extended: If True, returns extended ABI with additional functions
        
    Returns:
        List of ABI definitions
    """
    return ERC20_EXTENDED_ABI if extended else ERC20_ABI

# Function names for easy reference
ERC20_FUNCTIONS = {
    'name': 'name',
    'symbol': 'symbol', 
    'decimals': 'decimals',
    'total_supply': 'totalSupply',
    'balance_of': 'balanceOf',
    'allowance': 'allowance',
    'transfer': 'transfer',
    'approve': 'approve',
    'transfer_from': 'transferFrom',
    'increase_allowance': 'increaseAllowance',
    'decrease_allowance': 'decreaseAllowance',
    'permit': 'permit',
    'nonces': 'nonces',
    'domain_separator': 'DOMAIN_SEPARATOR'
}

# Event names for easy reference
ERC20_EVENTS = {
    'transfer': 'Transfer',
    'approval': 'Approval'
} 