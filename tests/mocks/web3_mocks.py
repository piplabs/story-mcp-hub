"""Mock data and objects for Web3 and blockchain-related tests."""
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List

# Mock blockchain transaction data
MOCK_TX_RECEIPT = {
    "transactionHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    "blockNumber": 12345,
    "gasUsed": 21000,
    "logs": [
        {
            "address": "0x1234567890123456789012345678901234567890",
            "topics": [
                "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9",
                "0x0000000000000000000000000000000000000000000000000000000000000001"
            ],
            "data": "0x0000000000000000000000000000000000000000000000000000000000000000"
        }
    ],
    "status": 1
}

# Sample IP data (using valid Ethereum addresses)
SAMPLE_IP_ID = "0x9876543210abcdef9876543210abcdef98765432"  # IP IDs have their own format
SAMPLE_NFT_CONTRACT = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  # Valid Ethereum address (WETH contract)
SAMPLE_TOKEN_ID = 42
SAMPLE_LICENSE_TERMS_ID = 1

# Mock responses for common Story SDK operations
def get_mock_mint_and_register_response() -> Dict[str, Any]:
    """Get mock response for mint and register operations"""
    return {
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "ipId": SAMPLE_IP_ID,
        "tokenId": SAMPLE_TOKEN_ID,
        "licenseTermsIds": [SAMPLE_LICENSE_TERMS_ID]
    }

def get_mock_license_terms() -> List[Any]:
    """Get mock license terms data"""
    return [
        True,  # transferable
        "0x1234567890123456789012345678901234567890",  # royaltyPolicy
        0,  # defaultMintingFee
        0,  # expiration
        True,  # commercialUse
        False,  # commercialAttribution
        "0x0000000000000000000000000000000000000000",  # commercializerChecker
        b'0x',  # commercializerCheckerData
        10,  # commercialRevShare
        0,  # commercialRevCeiling
        True,  # derivativesAllowed
        True,  # derivativesAttribution
        False,  # derivativesApproval
        True,  # derivativesReciprocal
        0,  # derivativeRevCeiling
        "0x1514000000000000000000000000000000000000",  # currency
        "ipfs://example",  # uri
    ]

def get_mock_token_holdings() -> Dict[str, Any]:
    """Get mock token holdings response"""
    return {
        "items": [
            {
                "token": {
                    "name": "Story Token",
                    "symbol": "STORY",
                    "decimals": "18",
                    "type": "ERC-20",
                    "address": "0xabcdef1234567890abcdef1234567890abcdef1234",
                    "holders": "1000",
                    "total_supply": "1000000000000000000000000",
                    "exchange_rate": "0.5"
                },
                "value": "10000000000000000000"  # 10 STORY
            }
        ]
    }

# Mock objects for Web3 components
class MockAccount:
    """Mock for Web3 account"""
    def __init__(self, address: str = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"):
        self.address = address
    
    def sign_transaction(self, transaction):
        """Mock method for signing transactions"""
        signed_tx = MagicMock()
        signed_tx.raw_transaction = b"\x00\x01\x02\x03"  # Dummy bytes
        return signed_tx

def create_mock_web3() -> Mock:
    """Create a comprehensive mock Web3 instance with predefined behaviors"""
    mock_w3 = Mock()
    
    # Mock eth module
    mock_w3.eth = Mock()
    mock_w3.eth.chain_id = 1315  # Story Protocol chain ID
    mock_w3.eth.get_balance = Mock(return_value=100000000000000000000)  # 100 ETH in wei
    mock_w3.eth.get_transaction_count = Mock(return_value=0)
    mock_w3.eth.gas_price = 20000000000  # 20 gwei
    mock_w3.eth.wait_for_transaction_receipt = Mock(return_value=MOCK_TX_RECEIPT)
    mock_w3.eth.send_raw_transaction = Mock(return_value=b"tx_hash")
    
    # Mock account module
    mock_account = MockAccount()
    mock_w3.eth.account = Mock()
    mock_w3.eth.account.from_key = Mock(return_value=mock_account)
    
    # Mock middleware
    mock_w3.middleware_onion = Mock()
    
    # Mock utility methods
    mock_w3.to_wei = lambda amount, unit: int(amount * 10**18) if unit == "ether" else int(amount * 10**9) if unit == "gwei" else int(amount)
    mock_w3.from_wei = lambda amount, unit: amount / 10**18 if unit == "ether" else amount / 10**9 if unit == "gwei" else amount
    
    # Use the real Web3 checksumming for address validation
    from web3 import Web3 as RealWeb3
    mock_w3.to_checksum_address = RealWeb3.to_checksum_address
    
    mock_w3.to_bytes = lambda hexstr: bytes.fromhex(hexstr.replace("0x", ""))
    mock_w3.keccak = lambda text=None: b"\xab\xcd\xef\x12\x34\x56\x78\x90" if text else b"\xab\xcd\xef\x12\x34\x56\x78\x90"
    
    # Mock connection status
    mock_w3.is_connected = Mock(return_value=True)
    
    return mock_w3