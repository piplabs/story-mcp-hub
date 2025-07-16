# ERC20 ABI Refactoring

## Overview

We've successfully refactored the ERC20 ABI handling to eliminate hardcoding and provide a more maintainable, standardized approach.

## What Changed

### Before ❌
```python
class StoryService:
    # Complete ERC20 ABI - Standard interface for all ERC20 tokens
    ERC20_ABI = [
        # 100+ lines of hardcoded ABI definitions...
    ]
    
    def _get_erc20_contract(self, token_address: str):
        return self.web3.eth.contract(address=token_address, abi=self.ERC20_ABI)
```

### After ✅
```python
# services/erc20_abi.py - Dedicated ABI module
from .erc20_abi import ERC20_ABI, ERC20_FUNCTIONS

class StoryService:
    def _get_erc20_contract(self, token_address: str):
        return self.web3.eth.contract(address=token_address, abi=ERC20_ABI)
```

## New File Structure

```
story-sdk-mcp/
├── services/
│   ├── erc20_abi.py          # 🆕 Dedicated ERC20 ABI definitions
│   ├── story_service.py      # ✅ Now imports ABI instead of hardcoding
│   └── ...
├── server.py                 # ✅ New MCP tool to showcase ABI info
└── ...
```

## Benefits

### 🎯 **Single Source of Truth**
- All ERC20 ABI definitions in one place
- No more code duplication
- Consistent ABI across the entire project

### 🔧 **Easy Maintenance**
- Update ABI once, changes apply everywhere
- Add new functions without touching multiple files
- Clear separation of concerns

### 📈 **Extended Functionality**
- Standard ERC20 ABI (9 functions, 2 events)
- Extended ABI with EIP-2612 permit support (14 functions, 2 events)
- Function name mapping for easy reference

### 🚀 **Better Developer Experience**
- Import what you need: `from .erc20_abi import ERC20_ABI`
- Utility functions: `get_erc20_abi(extended=True)`
- Function mapping: `ERC20_FUNCTIONS['balance_of']` → `'balanceOf'`

## Available ABIs

### Standard ERC20 ABI
- **Functions**: name, symbol, decimals, totalSupply, balanceOf, allowance, transfer, approve, transferFrom
- **Events**: Transfer, Approval
- **Use case**: Basic ERC20 token operations

### Extended ERC20 ABI
- **Additional Functions**: increaseAllowance, decreaseAllowance, permit, nonces, DOMAIN_SEPARATOR
- **Features**: EIP-2612 permit support for gasless approvals
- **Use case**: Advanced token operations

## Usage Examples

### Basic Import
```python
from services.erc20_abi import ERC20_ABI
contract = web3.eth.contract(address=token_address, abi=ERC20_ABI)
```

### Extended ABI
```python
from services.erc20_abi import get_erc20_abi
extended_abi = get_erc20_abi(extended=True)
contract = web3.eth.contract(address=token_address, abi=extended_abi)
```

### Function Mapping
```python
from services.erc20_abi import ERC20_FUNCTIONS
function_name = ERC20_FUNCTIONS['balance_of']  # Returns 'balanceOf'
```

## MCP Tool Integration

New MCP tool `get_erc20_abi_info()` provides:
- ABI statistics and function counts
- Available function names
- Implementation details
- Usage examples

## Migration Guide

If you're working with this codebase:

1. **Remove hardcoded ABIs**: Delete any ERC20_ABI definitions in your code
2. **Import from module**: `from services.erc20_abi import ERC20_ABI`
3. **Use utility functions**: `get_erc20_abi(extended=True)` for advanced features
4. **Leverage function mapping**: Use `ERC20_FUNCTIONS` for consistent naming

## Future Enhancements

- Add more EIP standard ABIs (ERC721, ERC1155, etc.)
- Integrate with external ABI registries
- Add ABI validation utilities
- Support for custom token extensions

## Testing

Run the verification script:
```bash
cd story-sdk-mcp
python -c "from services.erc20_abi import *; print('✅ ERC20 ABI import successful')"
```

## Summary

This refactoring eliminates hardcoding, improves maintainability, and provides a foundation for future ABI management. The approach follows best practices for Python module organization and makes the codebase more professional and scalable. 