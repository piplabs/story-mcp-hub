from web3 import Web3
from unittest.mock import MagicMock, Mock

from tests.unit.fixtures.data import ADDRESS


mock_web3 = Mock(spec=Web3)
mock_web3.to_checksum_address = MagicMock(return_value=ADDRESS)

# Add eth attribute with contract method
mock_eth = Mock()


# Create a function that returns a new mock contract each time
def create_mock_contract(*args, **kwargs):
    """Create a new mock contract instance with address"""
    mock_contract = Mock()
    mock_contract.address = ADDRESS
    mock_contract.encode_abi = MagicMock(return_value="0x00")
    return mock_contract


# Set up the contract method to return new mock contracts
mock_eth.contract = create_mock_contract
mock_web3.eth = mock_eth
