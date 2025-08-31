"""
Pytest fixtures for Story MCP Hub tests.
"""
import pytest
import os
from unittest.mock import Mock, MagicMock, patch
import json
from web3 import Web3
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load test environment variables
@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load .env.test file if it exists, otherwise load .env"""
    if os.path.exists(".env.test"):
        load_dotenv(".env.test", override=True)
    else:
        load_dotenv(override=True)
    
    # Set test mode environment variable
    os.environ["TESTING"] = "1"
    
    yield
    
    # Cleanup
    if "TESTING" in os.environ:
        del os.environ["TESTING"]

# Web3 mocks
@pytest.fixture
def mock_web3():
    """Create a mock Web3 instance with predefined responses"""
    mock_w3 = Mock(spec=Web3)
    
    # Mock eth module
    mock_w3.eth = Mock()
    mock_w3.eth.chain_id = 1315  # Story Protocol chain ID
    mock_w3.eth.get_balance = Mock(return_value=100000000000000000000)  # 100 ETH in wei
    mock_w3.eth.get_transaction_count = Mock(return_value=0)
    mock_w3.eth.gas_price = 20000000000  # 20 gwei
    
    # Mock account module
    mock_account = Mock()
    mock_account.address = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
    mock_w3.eth.account = Mock()
    mock_w3.eth.account.from_key = Mock(return_value=mock_account)
    
    # Helper methods
    mock_w3.to_wei = Web3.to_wei
    mock_w3.from_wei = Web3.from_wei
    mock_w3.to_checksum_address = Web3.to_checksum_address
    mock_w3.keccak = Web3.keccak
    
    # Mock connection status
    mock_w3.is_connected = Mock(return_value=True)
    
    return mock_w3

@pytest.fixture
def mock_story_client():
    """Create a mock Story Protocol client with predefined responses"""
    mock_client = Mock()
    
    # Mock License module
    mock_client.License = Mock()
    mock_client.License.getLicenseTerms = Mock(return_value=[
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
    ])
    
    mock_client.License.mintLicenseTokens = Mock(return_value={
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "licenseTokenIds": [1, 2, 3]
    })
    
    # Mock IPAsset module
    mock_client.IPAsset = Mock()
    mock_client.IPAsset.mintAndRegisterIpAssetWithPilTerms = Mock(return_value={
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "ipId": "0x9876543210abcdef9876543210abcdef98765432",
        "tokenId": 1,
        "licenseTermsIds": [1]
    })
    
    mock_client.IPAsset.register = Mock(return_value={
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "ipId": "0x9876543210abcdef9876543210abcdef98765432"
    })
    
    mock_client.IPAsset.registerDerivative = Mock(return_value={
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    })
    
    # Mock Royalty module
    mock_client.Royalty = Mock()
    mock_client.Royalty.payRoyaltyOnBehalf = Mock(return_value={
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    })
    
    mock_client.Royalty.claimRevenue = Mock(return_value={
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "claimableToken": 1000
    })
    
    return mock_client

@pytest.fixture
def mock_nft_client():
    """Create a mock NFT client with predefined responses"""
    mock_nft_client = Mock()
    
    mock_nft_client.create_nft_collection = Mock(return_value={
        "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "nft_contract": "0xabcdef1234567890abcdef1234567890abcdef1234"
    })
    
    return mock_nft_client

@pytest.fixture
def mock_pinata_response():
    """Create a mock response for Pinata API calls"""
    class MockResponse:
        def __init__(self, status_code=200, json_data=None):
            self.status_code = status_code
            self.json_data = json_data or {}
            self.text = json.dumps(self.json_data)
            self.content = b"mock image content"
        
        def json(self):
            return self.json_data
    
    return MockResponse(json_data={"IpfsHash": "QmXyZ123456789"})

# MCP server fixtures
@pytest.fixture
def mcp_test_server():
    """Create a test MCP server instance"""
    mcp = FastMCP("Test MCP Server")
    return mcp

# Storyscan API mock responses
@pytest.fixture
def mock_transaction_history_response():
    """Mock response for transaction history endpoint"""
    return {
        "items": [
            {
                "timestamp": "2025-03-15T12:00:00Z",
                "hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
                "block_number": 12345,
                "from_": {"hash": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"},
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

@pytest.fixture
def mock_blockchain_stats_response():
    """Mock response for blockchain stats endpoint"""
    return {
        "average_block_time": 2000,  # 2 seconds in ms
        "total_blocks": 12345,
        "total_transactions": 67890,
        "transactions_today": 1234,
        "total_addresses": 5678,
        "coin_price": "1.25",
        "market_cap": "125000000",
        "network_utilization_percentage": 35,
        "gas_prices": {
            "slow": 20,
            "average": 30,
            "fast": 50
        },
        "gas_prices_update_in_seconds": 120,
        "gas_used_today": "500000000",
        "total_gas_used": "10000000000"
    }

@pytest.fixture
def mock_address_overview_response():
    """Mock response for address overview endpoint"""
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
        "has_decompiled_code": False,  # This field may be missing in actual API responses
        "public_tags": [{"display_name": "Alice"}],
        "private_tags": [],
        "watchlist_names": []
    }

@pytest.fixture
def mock_token_holdings_response():
    """Mock response for token holdings endpoint"""
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

@pytest.fixture
def mock_nft_holdings_response():
    """Mock response for NFT holdings endpoint"""
    return {
        "items": [
            {
                "token": {
                    "name": "Story NFT Collection",
                    "symbol": "SNFT",
                    "type": "ERC-721",
                    "address": "0xabcdef1234567890abcdef1234567890abcdef1234",
                    "holders": "100",
                    "total_supply": "1000"
                },
                "id": "42",
                "token_type": "ERC-721",
                "value": "1",
                "image_url": "ipfs://QmXyZ123456789",
                "metadata": {
                    "name": "Story NFT #42",
                    "description": "A test NFT for Story Protocol",
                    "attributes": [
                        {"trait_type": "Rarity", "value": "Legendary"},
                        {"trait_type": "Type", "value": "Artwork"}
                    ]
                }
            }
        ]
    }

@pytest.fixture
def mock_transaction_interpretation_response():
    """Mock response for transaction interpretation endpoint"""
    return {
        "summaries": [
            {
                "summary_template": "{sender} transferred {amount} {token} to {receiver}",
                "summary_template_variables": {
                    "sender": {
                        "type": "address",
                        "value": {
                            "hash": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
                            "name": "Alice"
                        }
                    },
                    "amount": {
                        "type": "currency",
                        "value": "1000000000000000000"
                    },
                    "token": {
                        "type": "token",
                        "value": {
                            "symbol": "IP",
                            "name": "Story IP Token",
                            "decimals": "18"
                        }
                    },
                    "receiver": {
                        "type": "address",
                        "value": {
                            "hash": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                            "name": "Bob"
                        }
                    }
                }
            }
        ],
        "data": {
            "debug_data": {
                "model_classification_type": "token_transfer",
                "summary_template": {
                    "transfer": {
                        "template_vars": {
                            "token": {
                                "name": "Story IP Token",
                                "symbol": "IP",
                                "type": "ERC-20",
                                "address": "0x1234567890123456789012345678901234567890",
                                "holders": "10000",
                                "total_supply": "1000000000000000000000000000",
                                "decimals": "18"
                            },
                            "methodCalled": "transfer",
                            "tokenTransfers": [
                                {
                                    "token": {
                                        "name": "Story IP Token",
                                        "symbol": "IP",
                                        "type": "ERC-20",
                                        "address": "0x1234567890123456789012345678901234567890",
                                        "holders": "10000",
                                        "total_supply": "1000000000000000000000000000",
                                        "decimals": "18"
                                    },
                                    "from": {"hash": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"},
                                    "to": {"hash": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"},
                                    "total": {"value": "1000000000000000000"}
                                }
                            ]
                        }
                    }
                }
            }
        }
    }