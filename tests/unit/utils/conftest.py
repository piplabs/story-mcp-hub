"""
Test fixtures specific to utils module tests.
"""
import sys
import os
import pytest
from unittest.mock import Mock, patch

# Add the project root to the path so we can import from 'utils'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

# Now we can import utils
from utils.address_resolver import AddressResolver

@pytest.fixture
def mock_ens():
    """Create a mock ENS instance"""
    mock_ens = Mock()
    
    # Mock the ENS address method
    mock_ens.address = Mock(return_value="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")
    
    # Mock the ENS name (reverse lookup) method
    mock_ens.name = Mock(return_value="vitalik.eth")
    
    return mock_ens

@pytest.fixture
def mock_requests_get():
    """Mock the requests.get function for Space ID API"""
    with patch("requests.get") as mock_get:
        # Configure the mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "name": "alice.ip"
        }
        mock_get.return_value = mock_response
        yield mock_get