"""Mock data and objects for API-related tests."""
from unittest.mock import Mock
from typing import Dict, Any, Optional
import json

class MockResponse:
    """Mock for HTTP response objects"""
    def __init__(self, status_code: int = 200, json_data: Optional[Dict[str, Any]] = None, text: str = "", content: bytes = b""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self._text = text or json.dumps(self._json_data)
        self._content = content
        
    def json(self):
        """Return the JSON data"""
        return self._json_data
    
    @property
    def text(self) -> str:
        """Return the text content"""
        return self._text
    
    @property
    def content(self) -> bytes:
        """Return the raw content"""
        return self._content
        
    def raise_for_status(self):
        """Mock the raise_for_status method from requests.Response"""
        if 400 <= self.status_code < 600:
            from requests.exceptions import HTTPError
            raise HTTPError(f"HTTP Error: {self.status_code}")
        return None

# Mock IPFS responses
MOCK_IPFS_HASH = "QmXyZ123456789abcdef"
MOCK_IPFS_URI = f"ipfs://{MOCK_IPFS_HASH}"

def mock_pinata_upload_response() -> MockResponse:
    """Generate a mock response for Pinata upload requests"""
    return MockResponse(json_data={"IpfsHash": MOCK_IPFS_HASH})

# Mock StoryScan responses
def mock_storyscan_address_overview() -> Dict[str, Any]:
    """Generate a mock address overview response"""
    return {
        "hash": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        "coin_balance": "100000000000000000000",  # 100 IP
        "exchange_rate": 1.25,
        "block_number_balance_updated_at": 12345,
        "is_contract": False,
        "is_verified": True,
        "is_scam": False,
        "ens_domain_name": "alice.ip",
        "has_tokens": True,
        "has_token_transfers": True,
        "has_logs": True,
        "has_beacon_chain_withdrawals": False,
        "has_validated_blocks": False,
        "has_decompiled_code": False,
        "public_tags": [{"display_name": "Alice"}],
        "private_tags": [],
        "watchlist_names": [],
        "implementations": [],  # Add the missing field
        "is_verified": True,
        "is_scam": False,
    }

def mock_storyscan_transaction_history() -> Dict[str, Any]:
    """Generate a mock transaction history response"""
    return {
        "items": [
            {
                "timestamp": "2025-03-15T12:00:00Z",
                "hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
                "block_number": 12345,
                "from": {"hash": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"},
                "to": {"hash": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"},
                "value": "1000000000000000000",  # 1 IP
                "fee": {"value": "21000000000000"},
                "status": "ok",
                "method": "transfer",
                "transaction_types": ["token_transfer"],
                "gas_used": 21000,
                "gas_limit": 21000,
                "gas_price": "20000000000",  # 20 gwei
            }
        ]
    }

def mock_storyscan_blockchain_stats() -> Dict[str, Any]:
    """Generate a mock blockchain stats response"""
    return {
        "average_block_time": 2000,  # 2 seconds in ms
        "total_blocks": "12345",
        "total_transactions": "67890",
        "transactions_today": "1234",
        "total_addresses": "5678",
        "coin_price": "1.25",
        "market_cap": "125000000",
        "network_utilization_percentage": 35,
        "gas_prices": {
            "slow": 20,
            "average": 30,
            "fast": 50
        },
        "gas_prices_update_in": 120000,  # 120 seconds in ms
        "gas_price_updated_at": "2025-03-15T12:00:00Z",
        "gas_used_today": "500000000",
        "total_gas_used": "10000000000",
        "static_gas_price": "20"
    }