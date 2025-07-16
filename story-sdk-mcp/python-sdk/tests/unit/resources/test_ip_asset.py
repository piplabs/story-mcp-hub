import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from web3 import Web3
from eth_utils import is_address, to_checksum_address

current_dir = os.path.dirname(__file__)
src_path = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if src_path not in sys.path:
    sys.path.append(src_path)

from src.story_protocol_python_sdk.resources.IPAsset import IPAsset

ZERO_HASH = "0x0000000000000000000000000000000000000000000000000000000000000000"
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

class MockWeb3:
    def __init__(self):
        self.eth = MagicMock()
        
    @staticmethod
    def to_checksum_address(address):
        if not is_address(address):
            raise ValueError(f"Invalid address: {address}")
        return to_checksum_address(address)
    
    @staticmethod
    def to_bytes(hexstr=None, **kwargs):
        return Web3.to_bytes(hexstr=hexstr, **kwargs)
    
    @staticmethod
    def to_wei(number, unit):
        return Web3.to_wei(number, unit)
    
    @staticmethod
    def is_address(address):
        return is_address(address)
    
    @staticmethod
    def keccak(text=None):
        return Web3.keccak(text=text)
        
    def is_connected(self):
        return True

@pytest.fixture
def mock_web3():
    return MockWeb3()

@pytest.fixture
def mock_account():
    account = MagicMock()
    account.address = "0xF60cBF0Ea1A61567F1dDaf79A6219D20d189155c"
    return account

@pytest.fixture
def ip_asset(mock_web3, mock_account):
    chain_id = 1516
    return IPAsset(mock_web3, mock_account, chain_id)

class TestIPAssetRegister:
    def test_register_invalid_deadline_type(self, ip_asset):
        with patch.object(ip_asset, '_get_ip_id', return_value="0xd142822Dc1674154EaF4DDF38bbF7EF8f0D8ECe4"), \
             patch.object(ip_asset, '_is_registered', return_value=False):
            with pytest.raises(ValueError):
                ip_asset.register(
                    nft_contract="0x1daAE3197Bc469Cb97B917aa460a12dD95c6627c",
                    token_id=3,
                    deadline="error",
                    ip_metadata={
                        'ip_metadata_uri': "1",
                        'ip_metadata_hash': ZERO_HASH
                    }
                )

    def test_register_already_registered(self, ip_asset):
        token_contract = "0x1daAE3197Bc469Cb97B917aa460a12dD95c6627c"
        token_id = 3
        ip_id = "0xd142822Dc1674154EaF4DDF38bbF7EF8f0D8ECe4"

        with patch.object(ip_asset, '_get_ip_id', return_value=ip_id), \
             patch.object(ip_asset, '_is_registered', return_value=True):
            response = ip_asset.register(token_contract, token_id)
            assert response['ip_id'] == ip_id
            assert response['tx_hash'] is None

    def test_register_successful(self, ip_asset):
        token_contract = "0x1daAE3197Bc469Cb97B917aa460a12dD95c6627c"
        token_id = 3
        ip_id = "0x1daAE3197Bc469Cb97B917aa460a12dD95c6627c"
        tx_hash = "0x129f7dd802200f096221dd89d5b086e4bd3ad6eafb378a0c75e3b04fc375f997"

        
        class MockTxHash:
            def hex(self):
                return tx_hash

        mock_tx_hash = MockTxHash()

        mock_signed_txn = MagicMock()
        mock_signed_txn.raw_transaction = b'raw_transaction_bytes'

        
        ip_asset.account.sign_transaction = MagicMock(return_value=mock_signed_txn)

        with patch.object(ip_asset, '_get_ip_id', return_value=ip_id), \
             patch.object(ip_asset, '_is_registered', return_value=False), \
             patch.object(ip_asset.web3.eth, 'get_transaction_count', return_value=0), \
             patch.object(ip_asset.web3.eth, 'send_raw_transaction', return_value=mock_tx_hash), \
             patch.object(ip_asset.web3.eth, 'wait_for_transaction_receipt', return_value={'status': 1, 'logs': []}), \
             patch.object(ip_asset, '_parse_tx_ip_registered_event', return_value={'ip_id': ip_id}):

            result = ip_asset.register(token_contract, token_id)
            assert result['tx_hash'] == tx_hash
            assert result['ip_id'] == ip_id

    def test_register_with_metadata(self, ip_asset):
        token_contract = "0x1daAE3197Bc469Cb97B917aa460a12dD95c6627c"
        token_id = 3
        ip_id = "0x1daAE3197Bc469Cb97B917aa460a12dD95c6627c"
        tx_hash = "0x129f7dd802200f096221dd89d5b086e4bd3ad6eafb378a0c75e3b04fc375f997"

        metadata = {
            'ip_metadata_uri': "",
            'ip_metadata_hash': ZERO_HASH,
            'nft_metadata_uri': "",
            'nft_metadata_hash': ZERO_HASH,
        }

        calculated_deadline = 1000

        class MockTxHash:
            def hex(self):
                return tx_hash

        mock_tx_hash = MockTxHash()

        mock_signed_txn = MagicMock()
        mock_signed_txn.raw_transaction = b'raw_transaction_bytes'

        ip_asset.account.sign_transaction = MagicMock(return_value=mock_signed_txn)

        with patch.object(ip_asset, '_get_ip_id', return_value=ip_id), \
             patch.object(ip_asset, '_is_registered', return_value=False), \
             patch.object(ip_asset.sign_util, 'get_deadline', return_value=calculated_deadline), \
             patch.object(ip_asset.sign_util, 'get_permission_signature', return_value={"signature": tx_hash}), \
             patch.object(ip_asset.web3.eth, 'get_transaction_count', return_value=0), \
             patch.object(ip_asset.web3.eth, 'send_raw_transaction', return_value=mock_tx_hash), \
             patch.object(ip_asset.web3.eth, 'wait_for_transaction_receipt', return_value={'status': 1, 'logs': []}), \
             patch.object(ip_asset, '_parse_tx_ip_registered_event', return_value={'ip_id': ip_id, 'token_id': token_id}):

            result = ip_asset.register(
                nft_contract=token_contract,
                token_id=token_id,
                ip_metadata=metadata,
                deadline=1000
            )

            assert result['tx_hash'] == tx_hash
            assert result['ip_id'] == ip_id