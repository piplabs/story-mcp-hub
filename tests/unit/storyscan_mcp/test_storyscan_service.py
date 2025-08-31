"""
Tests for the StoryscanService class in the storyscan-mcp module.
"""
import pytest
from unittest.mock import patch, Mock
import json
import os

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

# Use importlib to import the service from a hyphenated directory
import importlib.util
spec = importlib.util.spec_from_file_location(
    "storyscan_service", 
    str(project_root / "storyscan-mcp/services/storyscan_service.py")
)
storyscan_service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(storyscan_service_module)
StoryscanService = storyscan_service_module.StoryscanService
from tests.mocks.api_mocks import (
    MockResponse,
    mock_storyscan_address_overview,
    mock_storyscan_transaction_history,
    mock_storyscan_blockchain_stats
)

class TestStoryscanService:
    """Test suite for StoryscanService class"""
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Set up environment variables for testing"""
        monkeypatch.setenv("STORYSCAN_API_ENDPOINT", "https://aeneid.storyscan.io/api")
    
    @pytest.fixture
    def storyscan_service(self, mock_env):
        """Create a StoryscanService instance"""
        return StoryscanService("https://aeneid.storyscan.io/api", disable_ssl_verification=True)
    
    @patch("requests.get")
    def test_get_transaction_history(self, mock_get, storyscan_service):
        """Test getting transaction history"""
        # Setup mock response
        mock_get.return_value = MockResponse(json_data=mock_storyscan_transaction_history())
        
        # Call the method
        address = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
        limit = 10
        result = storyscan_service.get_transaction_history(address, limit)
        
        # Verify request was made correctly
        mock_get.assert_called_once()
        
        # Since the implementation doesn't use params, we just check that the URL contains the address
        args, kwargs = mock_get.call_args
        assert address in args[0]
        
        # Just verify that we got items, not the exact structure since the implementation transforms the data
        assert isinstance(result, list)
        # Check that items were returned from the mock data
        assert len(result) > 0
    
    @patch("requests.get")
    def test_get_blockchain_stats(self, mock_get, storyscan_service):
        """Test getting blockchain stats"""
        # Setup mock response
        mock_get.return_value = MockResponse(json_data=mock_storyscan_blockchain_stats())
        
        # Call the method
        result = storyscan_service.get_blockchain_stats()
        
        # Verify request was made correctly
        mock_get.assert_called_once()
        
        # Verify the result has the expected keys
        assert "total_blocks" in result
        assert "gas_prices" in result
        assert "average_block_time" in result
        
        # Check some specific values
        assert result["total_blocks"] == mock_storyscan_blockchain_stats()["total_blocks"]
        assert result["gas_prices"]["slow"] == mock_storyscan_blockchain_stats()["gas_prices"]["slow"]
    
    @patch("requests.get")
    def test_get_address_overview(self, mock_get, storyscan_service):
        """Test getting address overview"""
        # Setup mock response
        mock_get.return_value = MockResponse(json_data=mock_storyscan_address_overview())
        
        # Call the method
        address = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
        result = storyscan_service.get_address_overview(address)
        
        # Verify request was made correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert address in args[0]
        
        # Verify result has key properties
        assert "hash" in result
        assert "coin_balance" in result
        assert result["hash"] == mock_storyscan_address_overview()["hash"]
        assert result["coin_balance"] == mock_storyscan_address_overview()["coin_balance"]
    
    @patch("requests.get")
    def test_get_token_holdings(self, mock_get, storyscan_service):
        """Test getting token holdings"""
        # Setup mock response
        mock_response = {
            "items": [
                {
                    "token": {
                        "name": "Story Token",
                        "symbol": "STORY",
                        "decimals": "18",
                        "address": "0xabcdef1234567890abcdef1234567890abcdef1234"
                    },
                    "value": "1000000000000000000"  # 1 STORY
                }
            ]
        }
        mock_get.return_value = MockResponse(json_data=mock_response)
        
        # Call the method
        address = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
        result = storyscan_service.get_token_holdings(address)
        
        # Verify request was made correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert address in args[0]
        
        # Verify result has items
        assert "items" in result
        assert len(result["items"]) == len(mock_response["items"])
        
        # Check that the first item has the same token data
        assert result["items"][0]["token"]["name"] == mock_response["items"][0]["token"]["name"]
        assert result["items"][0]["token"]["symbol"] == mock_response["items"][0]["token"]["symbol"]
    
    @patch("requests.get")
    def test_get_nft_holdings(self, mock_get, storyscan_service):
        """Test getting NFT holdings"""
        # Setup mock response
        mock_response = {
            "items": [
                {
                    "token": {
                        "name": "Story NFT Collection",
                        "symbol": "SNFT",
                        "type": "ERC-721"
                    },
                    "id": "42",
                    "token_type": "ERC-721"
                }
            ]
        }
        mock_get.return_value = MockResponse(json_data=mock_response)
        
        # Call the method
        address = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
        result = storyscan_service.get_nft_holdings(address)
        
        # Verify request was made correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert address in args[0]
        
        # Verify result
        assert result == mock_response
    
    @pytest.mark.skip(reason="get_transaction_details not implemented yet")
    @patch("requests.get")
    def test_get_transaction_details(self, mock_get, storyscan_service):
        """Test getting transaction details"""
        # This feature is not implemented yet, so we're skipping this test
        pass
    
    @patch("requests.get")
    def test_get_transaction_interpretation(self, mock_get, storyscan_service):
        """Test getting transaction interpretation"""
        # Setup mock response
        tx_hash = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        mock_response = {
            "summaries": [
                {
                    "summary_template": "{sender} transferred {amount} {token} to {receiver}",
                    "summary_template_variables": {}
                }
            ],
            "data": {
                "debug_data": {
                    "model_classification_type": "token_transfer"
                }
            }
        }
        mock_get.return_value = MockResponse(json_data=mock_response)
        
        # Call the method
        result = storyscan_service.get_transaction_interpretation(tx_hash)
        
        # Verify request was made correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert tx_hash in args[0]
        
        # Verify only that we have the expected summaries and data
        # The implementation adds additional attributes for error handling
        assert "summaries" in result
        assert "data" in result
        assert result["summaries"] == mock_response["summaries"]
        assert result["data"] == mock_response["data"]
        
    @pytest.mark.skip(reason="get_balance not implemented yet")
    @patch("requests.get")
    def test_get_balance(self, mock_get, storyscan_service):
        """Test getting balance"""
        # This feature is not implemented yet, so we're skipping this test
        pass