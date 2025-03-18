"""
Tests for the address resolver utility in the utils module.
"""
import sys
import os
import pytest
from unittest.mock import patch, Mock, MagicMock

# Add the project root to the path so we can import from 'utils'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from utils.address_resolver import create_address_resolver, AddressResolver
from tests.mocks.web3_mocks import create_mock_web3

# Sample data for testing
VALID_ETH_ADDRESS = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
LOWERCASE_ETH_ADDRESS = "0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266"
ENS_DOMAIN = "vitalik.eth"
SPACE_ID_DOMAIN = "alice.ip"


class TestAddressResolver:
    """Test suite for AddressResolver class"""
    
    @pytest.fixture
    def mock_web3(self):
        """Create a mock Web3 instance for testing"""
        mock_w3 = create_mock_web3()
        # Add is_address method since it's used in _is_ethereum_address
        mock_w3.is_address = lambda addr: addr.startswith("0x") and len(addr) == 42
        return mock_w3
    
    @pytest.fixture
    def address_resolver(self, mock_web3, mock_ens):
        """Create an AddressResolver instance with mocked dependencies"""
        with patch("utils.address_resolver.ENS", return_value=mock_ens):
            resolver = AddressResolver(mock_web3, chain_id=1315)
            
            # Mock Space ID API responses by patching the method directly
            def mock_space_id_resolver(domain):
                if domain == SPACE_ID_DOMAIN:
                    return VALID_ETH_ADDRESS
                return None
            
            resolver._resolve_domain_to_address = mock_space_id_resolver
            
            return resolver
    
    def test_create_address_resolver(self, mock_web3):
        """Test creating an address resolver"""
        with patch("utils.address_resolver.ENS") as mock_ens_class:
            mock_ens_class.return_value = Mock()
            resolver = create_address_resolver(mock_web3, chain_id=1315)
            assert isinstance(resolver, AddressResolver)
            assert resolver.chain_id == 1315
            assert resolver.web3 == mock_web3
    
    def test_resolve_address_with_ethereum_address(self, address_resolver):
        """Test resolving a valid Ethereum address"""
        result = address_resolver.resolve_address(VALID_ETH_ADDRESS)
        
        # Should return the same address (checksummed)
        assert result == VALID_ETH_ADDRESS
    
    def test_resolve_address_with_lowercase(self, address_resolver):
        """Test resolving a lowercase Ethereum address"""
        result = address_resolver.resolve_address(LOWERCASE_ETH_ADDRESS)
        
        # Should return checksum address
        assert result == VALID_ETH_ADDRESS
    
    def test_resolve_address_with_ens_domain(self, address_resolver, mock_ens):
        """Test resolving an ENS domain name"""
        result = address_resolver.resolve_address(ENS_DOMAIN)
        
        # Should return resolved address
        assert result == VALID_ETH_ADDRESS
        
        # Verify ENS address method was called
        mock_ens.address.assert_called_with(ENS_DOMAIN)
    
    def test_resolve_address_with_space_id_domain(self, address_resolver):
        """Test resolving a Space ID domain name"""
        # Use the mocked Space ID resolver in our fixture
        result = address_resolver.resolve_address(SPACE_ID_DOMAIN)
        
        # Should return resolved address
        assert result == VALID_ETH_ADDRESS
    
    def test_resolve_address_with_invalid_domain(self, address_resolver):
        """Test resolving an invalid domain name"""
        invalid_domain = "invalid.domain"
        
        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            address_resolver.resolve_address(invalid_domain)
        
        assert "Could not resolve address or domain" in str(exc_info.value)
    
    def test_get_domain_for_address(self, address_resolver, mock_ens):
        """Test getting a domain name for an address"""
        # Mock the _get_ens_name method to use our mock_ens fixture
        with patch.object(address_resolver, '_get_ens_name', return_value=ENS_DOMAIN):
            result = address_resolver.get_domain_for_address(VALID_ETH_ADDRESS)
            
            # Should return the domain name
            assert result == ENS_DOMAIN
    
    def test_get_domain_for_address_with_space_id(self, address_resolver, mock_ens, mock_requests_get):
        """Test getting a domain name with Space ID when ENS returns None"""
        # Mock ENS to return None
        with patch.object(address_resolver, '_get_ens_name', return_value=None):
            result = address_resolver.get_domain_for_address(VALID_ETH_ADDRESS)
            
            # Should use Space ID API
            mock_requests_get.assert_called_once()
            
            # Should return the domain name from mock response
            assert result == "alice.ip"
    
    def test_is_ethereum_address(self, address_resolver):
        """Test checking if a string is a valid Ethereum address"""
        # Valid address
        assert address_resolver._is_ethereum_address(VALID_ETH_ADDRESS) is True
        
        # Invalid addresses
        assert address_resolver._is_ethereum_address("not-an-address") is False
        assert address_resolver._is_ethereum_address("0x1234") is False
        assert address_resolver._is_ethereum_address(123) is False