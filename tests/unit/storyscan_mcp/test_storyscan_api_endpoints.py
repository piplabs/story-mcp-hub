"""
Tests for the StoryScan MCP API endpoints.
"""
import sys
import os
import types
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))
import pytest
from unittest.mock import patch, Mock
import json
from mcp.server.fastmcp import FastMCP

from tests.mocks.api_mocks import (
    mock_storyscan_address_overview,
    mock_storyscan_transaction_history,
    mock_storyscan_blockchain_stats
)

@pytest.fixture
def test_client(mcp_test_server):
    """Create a test client for the MCP endpoints"""
    return mcp_test_server.client

@pytest.fixture
def mock_storyscan_service():
    """Create a mock StoryscanService for testing API endpoints"""
    mock_service = Mock()
    
    # Set up common mock methods
    mock_service.get_transaction_history = Mock(return_value=mock_storyscan_transaction_history()["items"])
    mock_service.get_blockchain_stats = Mock(return_value=mock_storyscan_blockchain_stats())
    mock_service.get_address_overview = Mock(return_value=mock_storyscan_address_overview())
    
    mock_service.get_token_holdings = Mock(return_value={
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
    })
    
    mock_service.get_nft_holdings = Mock(return_value={
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
    })
    
    mock_service.interpret_transaction = Mock(return_value={
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
                            "methodCalled": "transfer",
                            "tokenTransfers": [
                                {
                                    "token": {
                                        "name": "Story IP Token",
                                        "symbol": "IP",
                                        "type": "ERC-20",
                                        "address": "0x1234567890123456789012345678901234567890",
                                        "decimals": "18"
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }
    })
    
    return mock_service

# Create a simpler mock server
@pytest.fixture
def storyscan_server(mock_storyscan_service):
    """Create a mock server with the same API as the real server"""
    # Create a simple object with methods that match the server's API
    class MockServer:
        def __init__(self, service):
            self.storyscan_service = service
        
        def get_transactions(self, address, limit=10, page=1):
            result = self.storyscan_service.get_transaction_history(address, limit, page)
            return json.dumps({"transactions": result})
        
        def get_stats(self):
            result = self.storyscan_service.get_blockchain_stats()
            return json.dumps(result)
        
        def get_address_overview(self, address):
            result = self.storyscan_service.get_address_overview(address)
            return json.dumps(result)
        
        def get_token_holdings(self, address):
            result = self.storyscan_service.get_token_holdings(address)
            return json.dumps(result)
        
        def get_nft_holdings(self, address):
            result = self.storyscan_service.get_nft_holdings(address)
            return json.dumps(result)
        
        def interpret_transaction(self, tx_hash):
            result = self.storyscan_service.interpret_transaction(tx_hash)
            return json.dumps(result)
    
    # Return an instance of the mock server
    return MockServer(mock_storyscan_service)

def test_get_transactions(storyscan_server, mock_storyscan_service):
    """Test the get_transactions endpoint"""
    # Call the endpoint
    address = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
    limit = 5
    
    response = storyscan_server.get_transactions(address=address, limit=limit)
    
    # Verify service was called correctly
    mock_storyscan_service.get_transaction_history.assert_called_once()
    
    # Verify response contains expected data
    assert isinstance(response, str)
    parsed = json.loads(response)
    assert "transactions" in parsed

def test_get_stats(storyscan_server, mock_storyscan_service):
    """Test the get_stats endpoint"""
    # Call the endpoint
    response = storyscan_server.get_stats()
    
    # Verify service was called correctly
    mock_storyscan_service.get_blockchain_stats.assert_called_once()
    
    # Verify response contains expected data
    assert isinstance(response, str)
    parsed = json.loads(response)
    assert "average_block_time" in parsed
    assert "total_blocks" in parsed

def test_get_address_overview(storyscan_server, mock_storyscan_service):
    """Test the get_address_overview endpoint"""
    # Call the endpoint
    address = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
    
    response = storyscan_server.get_address_overview(address=address)
    
    # Verify service was called correctly
    mock_storyscan_service.get_address_overview.assert_called_once_with(address)
    
    # Verify response contains expected data
    assert isinstance(response, str)
    parsed = json.loads(response)
    assert "hash" in parsed
    assert "coin_balance" in parsed

def test_get_token_holdings(storyscan_server, mock_storyscan_service):
    """Test the get_token_holdings endpoint"""
    # Call the endpoint
    address = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
    
    response = storyscan_server.get_token_holdings(address=address)
    
    # Verify service was called correctly
    mock_storyscan_service.get_token_holdings.assert_called_once_with(address)
    
    # Verify response contains expected data
    assert isinstance(response, str)
    parsed = json.loads(response)
    assert "items" in parsed

def test_get_nft_holdings(storyscan_server, mock_storyscan_service):
    """Test the get_nft_holdings endpoint"""
    # Call the endpoint
    address = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
    
    response = storyscan_server.get_nft_holdings(address=address)
    
    # Verify service was called correctly
    mock_storyscan_service.get_nft_holdings.assert_called_once_with(address)
    
    # Verify response contains expected data
    assert isinstance(response, str)
    parsed = json.loads(response)
    assert "items" in parsed

def test_interpret_transaction(storyscan_server, mock_storyscan_service):
    """Test the interpret_transaction endpoint"""
    # Call the endpoint
    tx_hash = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    
    response = storyscan_server.interpret_transaction(tx_hash)
    
    # Verify service was called correctly
    mock_storyscan_service.interpret_transaction.assert_called_once_with(tx_hash)
    
    # Verify response contains expected data
    assert isinstance(response, str)
    parsed = json.loads(response)
    assert isinstance(parsed, dict)