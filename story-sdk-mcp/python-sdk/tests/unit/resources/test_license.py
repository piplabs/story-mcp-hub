import logging
import pytest
from unittest.mock import patch, MagicMock
from web3 import Web3
import os
import sys
from eth_utils import is_address, to_checksum_address

current_dir = os.path.dirname(__file__)
src_path = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if src_path not in sys.path:
    sys.path.append(src_path)

from src.story_protocol_python_sdk.resources.License import License

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
VALID_ADDRESS = "0x1daAE3197Bc469Cb97B917aa460a12dD95c6627c"
TX_HASH = "0x129f7dd802200f096221dd89d5b086e4bd3ad6eafb378a0c75e3b04fc375f997"

class MockWeb3:
    """Mock Web3 instance with required functionality."""
    def __init__(self):
        self.eth = MagicMock()
        
    @staticmethod
    def to_checksum_address(address):
        if not is_address(address):
            raise ValueError(f'Address "{address}" is invalid')
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
    def keccak(text=None, hexstr=None, primitive=None):
        return Web3.keccak(text=text, hexstr=hexstr)
        
    def is_connected(self):
        return True

class MockTxHash:
    """Mock transaction hash that returns hash without '0x' prefix."""
    def hex(self):
        return TX_HASH[2:]

@pytest.fixture
def mock_web3():
    return MockWeb3()

@pytest.fixture
def mock_account():
    account = MagicMock()
    account.address = "0xF60cBF0Ea1A61567F1dDaf79A6219D20d189155c"
    return account

@pytest.fixture
def mock_signed_txn():
    signed_txn = MagicMock()
    signed_txn.rawTransaction = b'signed_tx'
    return signed_txn

@pytest.fixture
def license_client(mock_web3, mock_account):
    chain_id = 1315 
    return License(mock_web3, mock_account, chain_id)

class TestPILTermsRegistration:
    """Tests for PIL (Programmable IP License) terms registration."""

    def test_register_pil_terms_license_terms_id_registered(self, license_client):
        with patch.object(license_client.license_template_client, 'getLicenseTermsId', return_value=1), \
             patch.object(license_client.license_terms_util.royalty_module_client, 'isWhitelistedRoyaltyPolicy', return_value=True), \
             patch.object(license_client.license_terms_util.royalty_module_client, 'isWhitelistedRoyaltyToken', return_value=True):
            
            license_terms = {
                'default_minting_fee': 1513,
                'currency': VALID_ADDRESS,
                'royalty_policy': VALID_ADDRESS,
                'transferable': False,
                'expiration': 0,
                'commercial_use': True,
                'commercial_attribution': False,
                'commercializer_checker': ZERO_ADDRESS,
                'commercializer_checker_data': '0x',
                'commercial_rev_share': 0,
                'commercial_rev_ceiling': 0,
                'derivatives_allowed': False,
                'derivatives_attribution': False,
                'derivatives_approval': False,
                'derivatives_reciprocal': False,
                'derivative_rev_ceiling': 0,
                'uri': ''
            }
            
            response = license_client.register_pil_terms(**license_terms)
            assert response['license_terms_id'] == 1
            assert 'tx_hash' not in response

    def test_register_pil_terms_success(self, license_client, mock_signed_txn, mock_account):
        with patch.object(license_client.license_template_client, 'getLicenseTermsId', return_value=0), \
             patch.object(license_client.license_terms_util.royalty_module_client, 'isWhitelistedRoyaltyPolicy', return_value=True), \
             patch.object(license_client.license_terms_util.royalty_module_client, 'isWhitelistedRoyaltyToken', return_value=True), \
             patch.object(license_client.license_template_client, 'build_registerLicenseTerms_transaction', 
                return_value={'from': mock_account.address, 'nonce': 1, 'gas': 2000000, 'gasPrice': Web3.to_wei('100', 'gwei')}), \
             patch.object(mock_account, 'sign_transaction', return_value=mock_signed_txn), \
             patch.object(license_client.web3.eth, 'send_raw_transaction', return_value=MockTxHash()), \
             patch.object(license_client.web3.eth, 'wait_for_transaction_receipt', return_value=MagicMock()):

            response = license_client.register_pil_terms(
                transferable=False,
                royalty_policy=VALID_ADDRESS,
                default_minting_fee=1513,
                expiration=0,
                commercial_use=True,
                commercial_attribution=False,
                commercializer_checker=ZERO_ADDRESS,
                commercializer_checker_data='0x',
                commercial_rev_share=90,
                commercial_rev_ceiling=0,
                derivatives_allowed=False,
                derivatives_attribution=False,
                derivatives_approval=False,
                derivatives_reciprocal=False,
                derivative_rev_ceiling=0,
                currency=VALID_ADDRESS,
                uri=''
            )
            
            assert 'tx_hash' in response
            assert response['tx_hash'] == TX_HASH[2:]
            assert isinstance(response['tx_hash'], str)

    def test_register_pil_terms_commercial_rev_share_error_more_than_100(self, license_client):
        with patch.object(license_client.license_template_client, 'getLicenseTermsId', return_value=0), \
             patch.object(license_client.license_terms_util.royalty_module_client, 'isWhitelistedRoyaltyPolicy', return_value=True), \
             patch.object(license_client.license_terms_util.royalty_module_client, 'isWhitelistedRoyaltyToken', return_value=True):

            with pytest.raises(ValueError, match='CommercialRevShare should be between 0 and 100.'):
                license_client.register_pil_terms(
                    transferable=False,
                    royalty_policy=VALID_ADDRESS,
                    default_minting_fee=1,
                    expiration=0,
                    commercial_use=True,
                    commercial_attribution=False,
                    commercializer_checker=ZERO_ADDRESS,
                    commercializer_checker_data='0x',
                    commercial_rev_share=101,
                    commercial_rev_ceiling=0,
                    derivatives_allowed=False,
                    derivatives_attribution=False,
                    derivatives_approval=False,
                    derivatives_reciprocal=False,
                    derivative_rev_ceiling=0,
                    currency=VALID_ADDRESS,
                    uri=''
                )

    def test_register_pil_terms_commercial_rev_share_error_less_than_0(self, license_client):
        with patch.object(license_client.license_template_client, 'getLicenseTermsId', return_value=0), \
             patch.object(license_client.license_terms_util.royalty_module_client, 'isWhitelistedRoyaltyPolicy', return_value=True), \
             patch.object(license_client.license_terms_util.royalty_module_client, 'isWhitelistedRoyaltyToken', return_value=True):

            with pytest.raises(ValueError, match='CommercialRevShare should be between 0 and 100.'):
                license_client.register_pil_terms(
                    transferable=False,
                    royalty_policy=VALID_ADDRESS,
                    default_minting_fee=1,
                    expiration=0,
                    commercial_use=True,
                    commercial_attribution=False,
                    commercializer_checker=ZERO_ADDRESS,
                    commercializer_checker_data='0x',
                    commercial_rev_share=-1,
                    commercial_rev_ceiling=0,
                    derivatives_allowed=False,
                    derivatives_attribution=False,
                    derivatives_approval=False,
                    derivatives_reciprocal=False,
                    derivative_rev_ceiling=0,
                    currency=VALID_ADDRESS,
                    uri=''
                )
class TestNonComSocialRemixingPIL:
    """Tests for non-commercial social remixing PIL functionality."""

    def test_register_non_com_social_remixing_pil_license_terms_id_registered(self, license_client):
        with patch.object(license_client.license_template_client, 'getLicenseTermsId', return_value=1):
            response = license_client.register_non_com_social_remixing_pil()
            assert response['license_terms_id'] == 1
            assert 'tx_hash' not in response

    def test_register_non_com_social_remixing_pil_success(self, license_client, mock_signed_txn, mock_account):  
        with patch.object(license_client.license_template_client, 'getLicenseTermsId', return_value=0), \
             patch.object(license_client.license_template_client, 'build_registerLicenseTerms_transaction',
                return_value={'from': mock_account.address, 'nonce': 1, 'gas': 2000000, 'gasPrice': Web3.to_wei('100', 'gwei')}), \
             patch.object(mock_account, 'sign_transaction', return_value=mock_signed_txn), \
             patch.object(license_client.web3.eth, 'send_raw_transaction', return_value=MockTxHash()), \
             patch.object(license_client.web3.eth, 'get_transaction_count', return_value=1), \
             patch.object(license_client.web3.eth, 'wait_for_transaction_receipt', return_value=MagicMock()), \
             patch.object(license_client, '_parse_tx_license_terms_registered_event', return_value=1): 

            response = license_client.register_non_com_social_remixing_pil()
            assert 'tx_hash' in response
            assert response['tx_hash'] == TX_HASH[2:]
            assert isinstance(response['tx_hash'], str)
            assert 'license_terms_id' in response
            assert response['license_terms_id'] == 1

    def test_register_non_com_social_remixing_pil_error(self, license_client):
        with patch.object(license_client.license_template_client, 'getLicenseTermsId', return_value=0), \
             patch.object(license_client.license_terms_util.royalty_module_client, 'isWhitelistedRoyaltyPolicy', return_value=True), \
             patch.object(license_client.license_template_client, 'build_registerLicenseTerms_transaction', 
                side_effect=Exception("request fail.")):

            with pytest.raises(Exception, match="request fail."):
                license_client.register_non_com_social_remixing_pil()

class TestCommercialUsePIL:
    """Tests for commercial use PIL functionality."""
    
    def test_register_commercial_use_pil_license_terms_id_registered(self, license_client):
        with patch.object(license_client.license_template_client, 'getLicenseTermsId', return_value=1):
            response = license_client.register_commercial_use_pil(
                default_minting_fee=1,
                currency=ZERO_ADDRESS
            )
            assert response['license_terms_id'] == 1
            assert 'tx_hash' not in response

    def test_register_commercial_use_pil_success(self, license_client, mock_signed_txn, mock_account):  
        with patch.object(license_client.license_template_client, 'getLicenseTermsId', return_value=0), \
             patch.object(license_client.license_terms_util.royalty_module_client, 'isWhitelistedRoyaltyPolicy', return_value=True), \
             patch.object(license_client.license_template_client, 'build_registerLicenseTerms_transaction', 
                return_value={'from': mock_account.address, 'nonce': 1, 'gas': 2000000, 'gasPrice': Web3.to_wei('100', 'gwei')}), \
             patch.object(mock_account, 'sign_transaction', return_value=mock_signed_txn), \
             patch.object(license_client.web3.eth, 'send_raw_transaction', return_value=MockTxHash()), \
             patch.object(license_client.web3.eth, 'get_transaction_count', return_value=1), \
             patch.object(license_client.web3.eth, 'wait_for_transaction_receipt', return_value=MagicMock()), \
             patch.object(license_client, '_parse_tx_license_terms_registered_event', return_value=1):

            response = license_client.register_commercial_use_pil(
                default_minting_fee=1,
                currency=ZERO_ADDRESS
            )
            assert 'tx_hash' in response
            assert response['tx_hash'] == TX_HASH[2:]
            assert isinstance(response['tx_hash'], str)
            assert 'license_terms_id' in response
            assert response['license_terms_id'] == 1

    def test_register_commercial_use_pil_error(self, license_client):
        with patch.object(license_client.license_template_client, 'getLicenseTermsId', return_value=0), \
             patch.object(license_client.license_terms_util.royalty_module_client, 'isWhitelistedRoyaltyPolicy', return_value=True), \
             patch.object(license_client.license_template_client, 'build_registerLicenseTerms_transaction', 
                side_effect=Exception("request fail.")):
            with pytest.raises(Exception, match="request fail."):
                license_client.register_commercial_use_pil(
                    default_minting_fee=1,
                    currency=ZERO_ADDRESS
                )

class TestCommercialRemixPIL:
    """Tests for commercial remix PIL functionality."""

    def test_register_commercial_remix_pil_license_terms_id_registered(self, license_client):
        with patch.object(license_client.license_template_client, 'getLicenseTermsId', return_value=1), \
             patch.object(license_client.license_terms_util.royalty_module_client, 'isWhitelistedRoyaltyPolicy', return_value=True):
            response = license_client.register_commercial_remix_pil(
                default_minting_fee=1,
                commercial_rev_share=100,
                currency=ZERO_ADDRESS,
                royalty_policy=ZERO_ADDRESS
            )
            assert response['license_terms_id'] == 1
            assert 'tx_hash' not in response

    def test_register_commercial_remix_pil_success(self, license_client, mock_signed_txn, mock_account):
        with patch.object(license_client.license_template_client, 'getLicenseTermsId', return_value=0), \
             patch.object(license_client.license_terms_util.royalty_module_client, 'isWhitelistedRoyaltyPolicy', return_value=True), \
             patch.object(license_client.license_template_client, 'build_registerLicenseTerms_transaction', 
                return_value={'from': mock_account.address, 'nonce': 1, 'gas': 2000000, 'gasPrice': Web3.to_wei('100', 'gwei')}), \
             patch.object(mock_account, 'sign_transaction', return_value=mock_signed_txn), \
             patch.object(license_client.web3.eth, 'send_raw_transaction', return_value=MockTxHash()), \
             patch.object(license_client.web3.eth, 'get_transaction_count', return_value=1), \
             patch.object(license_client.web3.eth, 'wait_for_transaction_receipt', return_value=MagicMock()), \
             patch.object(license_client, '_parse_tx_license_terms_registered_event', return_value=1): 

            response = license_client.register_commercial_remix_pil(
                default_minting_fee=1,
                commercial_rev_share=100,
                currency=ZERO_ADDRESS,
                royalty_policy=ZERO_ADDRESS
            )
            assert 'tx_hash' in response
            assert response['tx_hash'] == TX_HASH[2:]
            assert isinstance(response['tx_hash'], str)
            assert response['license_terms_id'] == 1

class TestLicenseAttachment:
    """Tests for license attachment functionality."""

    def test_attach_license_terms_ip_not_registered(self, license_client):
        with patch.object(license_client.ip_asset_registry_client, 'isRegistered', return_value=False):
            with pytest.raises(ValueError, match=f'The IP with id {ZERO_ADDRESS} is not registered.'):
                license_client.attach_license_terms(
                    ip_id=ZERO_ADDRESS,
                    license_template=ZERO_ADDRESS,
                    license_terms_id=1
                )

    def test_attach_license_terms_license_terms_not_exist(self, license_client):
        with patch.object(license_client.ip_asset_registry_client, 'isRegistered', return_value=True), \
             patch.object(license_client.license_registry_client, 'exists', return_value=False):
            with pytest.raises(ValueError, match='License terms id 1 do not exist.'):
                license_client.attach_license_terms(
                    ip_id=ZERO_ADDRESS,
                    license_template=ZERO_ADDRESS,
                    license_terms_id=1
                )

    def test_attach_license_terms_already_attached(self, license_client):
        with patch.object(license_client.ip_asset_registry_client, 'isRegistered', return_value=True), \
             patch.object(license_client.license_registry_client, 'exists', return_value=True), \
             patch.object(license_client.license_registry_client, 'hasIpAttachedLicenseTerms', return_value=True):
            with pytest.raises(ValueError, 
                match=f'License terms id 1 is already attached to the IP with id {ZERO_ADDRESS}.'):
                license_client.attach_license_terms(
                    ip_id=ZERO_ADDRESS,
                    license_template=ZERO_ADDRESS,
                    license_terms_id=1
                )

    def test_attach_license_terms_success(self, license_client, mock_signed_txn, mock_account):
        with patch.object(license_client.ip_asset_registry_client, 'isRegistered', return_value=True), \
             patch.object(license_client.license_registry_client, 'exists', return_value=True), \
             patch.object(license_client.license_registry_client, 'hasIpAttachedLicenseTerms', return_value=False), \
             patch.object(license_client.licensing_module_client, 'build_attachLicenseTerms_transaction', 
                return_value={'from': mock_account.address, 'nonce': 1, 'gas': 2000000, 'gasPrice': Web3.to_wei('100', 'gwei')}), \
             patch.object(mock_account, 'sign_transaction', return_value=mock_signed_txn), \
             patch.object(license_client.web3.eth, 'send_raw_transaction', return_value=MockTxHash()), \
             patch.object(license_client.web3.eth, 'get_transaction_count', return_value=1), \
             patch.object(license_client.web3.eth, 'wait_for_transaction_receipt', return_value=MagicMock()), \
             patch.object(license_client, '_parse_tx_license_terms_registered_event', return_value=1): 

            response = license_client.attach_license_terms(
                ip_id=ZERO_ADDRESS,
                license_template=ZERO_ADDRESS,
                license_terms_id=1
            )

            assert 'tx_hash' in response
            assert response['tx_hash'] == TX_HASH[2:]
            assert isinstance(response['tx_hash'], str)

class TestLicenseTokens:
    """Tests for license token minting functionality."""

    def test_mint_license_tokens_licensor_ip_not_registered(self, license_client):
        with patch.object(license_client.ip_asset_registry_client, 'isRegistered', return_value=False):
            with pytest.raises(ValueError, match=f"The licensor IP with id {ZERO_ADDRESS} is not registered."):
                license_client.mint_license_tokens(
                    licensor_ip_id=ZERO_ADDRESS,
                    license_template=ZERO_ADDRESS,
                    license_terms_id=1,
                    amount=1,
                    receiver=ZERO_ADDRESS
                )

    def test_mint_license_tokens_license_terms_not_exist(self, license_client):
        with patch.object(license_client.ip_asset_registry_client, 'isRegistered', return_value=True), \
             patch.object(license_client.license_template_client, 'exists', return_value=False):
            with pytest.raises(ValueError, match='License terms id 1 do not exist.'):
                license_client.mint_license_tokens(
                    licensor_ip_id=ZERO_ADDRESS,
                    license_template=ZERO_ADDRESS,
                    license_terms_id=1,
                    amount=1,
                    receiver=ZERO_ADDRESS
                )

    def test_mint_license_tokens_not_attached(self, license_client):
        with patch.object(license_client.ip_asset_registry_client, 'isRegistered', return_value=True), \
             patch.object(license_client.license_template_client, 'exists', return_value=True), \
             patch.object(license_client.license_registry_client, 'hasIpAttachedLicenseTerms', return_value=False):
            with pytest.raises(ValueError, 
                match=f'License terms id 1 is not attached to the IP with id {ZERO_ADDRESS}.'):
                license_client.mint_license_tokens(
                    licensor_ip_id=ZERO_ADDRESS,
                    license_template=ZERO_ADDRESS,
                    license_terms_id=1,
                    amount=1,
                    receiver=ZERO_ADDRESS
                )

    def test_mint_license_tokens_invalid_template(self, license_client):
        with patch.object(license_client.ip_asset_registry_client, 'isRegistered', return_value=True):
            with pytest.raises(ValueError, match='Address "invalid address" is invalid'):
                license_client.mint_license_tokens(
                    licensor_ip_id=ZERO_ADDRESS,
                    license_template="invalid address",
                    license_terms_id=1,
                    amount=1,
                    receiver=ZERO_ADDRESS
                )

    def test_mint_license_tokens_invalid_receiver(self, license_client):
        with patch.object(license_client.ip_asset_registry_client, 'isRegistered', return_value=True):
            with pytest.raises(ValueError, match='Address "invalid address" is invalid'):
                license_client.mint_license_tokens(
                    licensor_ip_id=ZERO_ADDRESS,
                    license_template=ZERO_ADDRESS,
                    license_terms_id=1,
                    amount=1,
                    receiver="invalid address"
                )

    def test_mint_license_tokens_success(self, license_client, mock_signed_txn, mock_account):
        with patch.object(license_client.ip_asset_registry_client, 'isRegistered', return_value=True), \
             patch.object(license_client.license_template_client, 'exists', return_value=True), \
             patch.object(license_client.license_registry_client, 'hasIpAttachedLicenseTerms', return_value=True), \
             patch.object(license_client.licensing_module_client, 'build_mintLicenseTokens_transaction', 
                return_value={'from': mock_account.address, 'nonce': 1, 'gas': 2000000, 'gasPrice': Web3.to_wei('100', 'gwei')}), \
             patch.object(mock_account, 'sign_transaction', return_value=mock_signed_txn), \
             patch.object(license_client.web3.eth, 'send_raw_transaction', return_value=MockTxHash()), \
             patch.object(license_client.web3.eth, 'wait_for_transaction_receipt', return_value=MagicMock()), \
             patch.object(license_client, '_parse_tx_license_terms_registered_event', return_value=1): 

            response = license_client.mint_license_tokens(
                licensor_ip_id=ZERO_ADDRESS,
                license_template=ZERO_ADDRESS,
                license_terms_id=1,
                amount=1,
                receiver=ZERO_ADDRESS
            )

            assert 'tx_hash' in response
            assert response['tx_hash'] == TX_HASH[2:]
            assert isinstance(response['tx_hash'], str)

class TestLicenseTerms:
    """Tests for retrieving license terms."""

    def test_get_license_terms_success(self, license_client):
        mock_response = {
            'terms': {
                'transferable': True,
                'royaltyPolicy': ZERO_ADDRESS,
                'defaultMintingFee': 1,
                'expiration': 1,
                'commercialUse': True,
                'commercialAttribution': True,
                'commercializerChecker': ZERO_ADDRESS,
                'commercializerCheckerData': ZERO_ADDRESS,
                'commercialRevShare': 100,
                'commercialRevCeiling': 1,
                'derivativesAllowed': True,
                'derivativesAttribution': True,
                'derivativesApproval': True,
                'derivativesReciprocal': True,
                'derivativeRevCeiling': 1,
                'currency': ZERO_ADDRESS,
                'uri': "string"
            }
        }
        with patch.object(license_client.license_template_client, 'getLicenseTerms', return_value=mock_response):
            response = license_client.get_license_terms(1)
            assert response == mock_response

    def test_get_license_terms_not_exist(self, license_client):
        with patch.object(license_client.license_template_client, 'getLicenseTerms', 
                         side_effect=Exception("Given licenseTermsId is not exist.")):
            with pytest.raises(ValueError, match="Failed to get license terms: Given licenseTermsId is not exist."):
                license_client.get_license_terms(1)

class TestLicensingConfig:
    """Tests for license configuration functionality."""

    def test_set_licensing_config_missing_params(self, license_client):
        incomplete_config = {
            'isSet': True,
            'mintingFee': 0,
        }
        with pytest.raises(ValueError, match="Missing required licensing_config parameters:"):
            license_client.set_licensing_config(
                ip_id=ZERO_ADDRESS,
                license_terms_id=1,
                licensing_config=incomplete_config
            )

    def test_set_licensing_config_negative_minting_fee(self, license_client):
        config = {
            'isSet': True,
            'mintingFee': -1,
            'hookData': "0x",
            'licensingHook': ZERO_ADDRESS,
            'commercialRevShare': 0,
            'disabled': False,
            'expectMinimumGroupRewardShare': 0,
            'expectGroupRewardPool': ZERO_ADDRESS
        }
        with pytest.raises(ValueError, match="Failed to set licensing config: The minting fee must be greater than 0."):
            license_client.set_licensing_config(
                ip_id=ZERO_ADDRESS,
                license_terms_id=1,
                licensing_config=config
            )

    def test_set_licensing_config_unregistered_licensing_hook(self, license_client):
        custom_address = "0x1234567890123456789012345678901234567890"
        config = {
            'isSet': True,
            'mintingFee': 1,
            'hookData': "0x",
            'licensingHook': custom_address,
            'commercialRevShare': 0,
            'disabled': False,
            'expectMinimumGroupRewardShare': 0,
            'expectGroupRewardPool': ZERO_ADDRESS
        }
        with patch.object(license_client.ip_asset_registry_client, 'isRegistered', return_value=True), \
             patch.object(license_client.module_registry_client, 'isRegistered', return_value=False):
            with pytest.raises(ValueError, match="Failed to set licensing config: The licensing hook is not registered."):
                license_client.set_licensing_config(
                    ip_id=ZERO_ADDRESS,
                    license_terms_id=1,
                    licensing_config=config
                )

    def test_set_licensing_config_template_terms_mismatch(self, license_client):
        config = {
            'isSet': True,
            'mintingFee': 1,
            'hookData': "0x",
            'licensingHook': ZERO_ADDRESS,
            'commercialRevShare': 0,
            'disabled': False,
            'expectMinimumGroupRewardShare': 0,
            'expectGroupRewardPool': ZERO_ADDRESS
        }
        with patch.object(license_client.ip_asset_registry_client, 'isRegistered', return_value=True):
            with pytest.raises(ValueError, match="Failed to set licensing config: The license template is zero address but license terms id is not zero."):
                license_client.set_licensing_config(
                    ip_id=ZERO_ADDRESS,
                    license_terms_id=1,
                    license_template=ZERO_ADDRESS,
                    licensing_config=config
                )

    def test_set_licensing_config_zero_address_with_rev_share(self, license_client):
        config = {
            'isSet': True,
            'mintingFee': 1,
            'hookData': "0x",
            'licensingHook': ZERO_ADDRESS,
            'commercialRevShare': 10,
            'disabled': False,
            'expectMinimumGroupRewardShare': 0,
            'expectGroupRewardPool': ZERO_ADDRESS
        }
        with patch.object(license_client.ip_asset_registry_client, 'isRegistered', return_value=True):
            with pytest.raises(ValueError, match="Failed to set licensing config: The license template cannot be zero address if commercial revenue share is not zero."):
                license_client.set_licensing_config(
                    ip_id=ZERO_ADDRESS,
                    license_terms_id=0,
                    license_template=ZERO_ADDRESS,
                    licensing_config=config
                )