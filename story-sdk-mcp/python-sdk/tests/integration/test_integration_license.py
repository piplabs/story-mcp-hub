# tests/integration/test_integration_license.py

import pytest
from web3 import Web3

from setup_for_integration import (
    web3,
    account, 
    story_client,
    get_token_id,
    mint_tokens,
    approve,
    MockERC721,
    MockERC20,
    ZERO_ADDRESS,
    ROYALTY_POLICY,
    ROYALTY_MODULE,
    PIL_LICENSE_TEMPLATE
)

def test_register_pil_terms(story_client):
    response = story_client.License.register_pil_terms(
        transferable=False,
        royalty_policy=story_client.web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
        default_minting_fee=0,
        expiration=0,
        commercial_use=False,
        commercial_attribution=False,
        commercializer_checker=story_client.web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
        commercializer_checker_data="0x",
        commercial_rev_share=0,
        commercial_rev_ceiling=0,
        derivatives_allowed=False,
        derivatives_attribution=False,
        derivatives_approval=False,
        derivatives_reciprocal=False,
        derivative_rev_ceiling=0,
        currency=MockERC20,
        uri="",
    )

    assert response is not None
    assert 'license_terms_id' in response
    assert response['license_terms_id'] is not None
    assert isinstance(response['license_terms_id'], int)

def test_register_non_com_social_remixing_pil(story_client):
    response = story_client.License.register_non_com_social_remixing_pil()

    assert response is not None
    assert 'license_terms_id' in response
    assert response['license_terms_id'] is not None
    assert isinstance(response['license_terms_id'], int)

@pytest.fixture(scope="module")
def register_commercial_use_pil(story_client):
    response = story_client.License.register_commercial_use_pil(
        default_minting_fee=11,
        currency=MockERC20,
        royalty_policy=ROYALTY_POLICY
    )

    assert response is not None, "Response is None, indicating the contract interaction failed."
    assert 'license_terms_id' in response, "Response does not contain 'license_terms_id'."
    assert response['license_terms_id'] is not None, "'license_terms_id' is None."
    assert isinstance(response['license_terms_id'], int), "'license_terms_id' is not an integer."

    return response['license_terms_id']
    
def test_register_commercial_use_pil(story_client, register_commercial_use_pil):
    assert register_commercial_use_pil is not None

@pytest.fixture(scope="module")
def register_commercial_remix_pil(story_client):
    response = story_client.License.register_commercial_remix_pil(
        default_minting_fee=1,
        currency=MockERC20,
        commercial_rev_share=100,
        royalty_policy=ROYALTY_POLICY
    )

    assert response is not None, "Response is None, indicating the contract interaction failed."
    assert 'license_terms_id' in response, "Response does not contain 'license_terms_id'."
    assert response['license_terms_id'] is not None, "'license_terms_id' is None."
    assert isinstance(response['license_terms_id'], int), "'license_terms_id' is not an integer."

    return response['license_terms_id']

def test_register_commercial_remix_pil(story_client, register_commercial_remix_pil):
    assert register_commercial_remix_pil is not None

@pytest.fixture(scope="module")
def ip_id(story_client):
    token_id = get_token_id(MockERC721, story_client.web3, story_client.account)

    response = story_client.IPAsset.register(
        nft_contract=MockERC721,
        token_id=token_id
    )

    token_ids = mint_tokens(
        erc20_contract_address=MockERC20, 
        web3=web3, 
        account=account, 
        to_address=account.address, 
        amount=100000 * 10 ** 6
    )
    
    receipt = approve(
        erc20_contract_address=MockERC20, 
        web3=web3, 
        account=account, 
        spender_address=ROYALTY_MODULE, 
        amount=100000 * 10 ** 6)

    assert response is not None
    assert 'ip_id' in response
    assert response['ip_id'] is not None

    return response['ip_id']

def test_attach_license_terms(story_client, ip_id, register_commercial_use_pil):
    license_terms_id = register_commercial_use_pil

    response = story_client.License.attach_license_terms(ip_id, PIL_LICENSE_TEMPLATE, license_terms_id)
    
    assert response is not None, "Response is None, indicating the contract interaction failed."
    assert 'tx_hash' in response, "Response does not contain 'tx_hash'."
    assert response['tx_hash'] is not None, "'tx_hash' is None."
    assert isinstance(response['tx_hash'], str), "'tx_hash' is not a string."
    assert len(response['tx_hash']) > 0, "'tx_hash' is empty."

def test_mint_license_tokens(story_client, ip_id, register_commercial_use_pil):
    response = story_client.License.mint_license_tokens(
        licensor_ip_id=ip_id, 
        license_template=PIL_LICENSE_TEMPLATE, 
        license_terms_id=register_commercial_use_pil, 
        amount=1, 
        receiver=account.address
    )

    assert response is not None, "Response is None, indicating the contract interaction failed."
    assert 'tx_hash' in response, "Response does not contain 'tx_hash'."
    assert response['tx_hash'] is not None, "'tx_hash' is None."
    assert isinstance(response['tx_hash'], str), "'tx_hash' is not a string."
    assert len(response['tx_hash']) > 0, "'tx_hash' is empty."
    assert 'license_token_ids' in response, "Response does not contain 'license_token_ids'."
    assert response['license_token_ids'] is not None, "'license_token_ids' is None."
    assert isinstance(response['license_token_ids'], list), "'license_token_ids' is not a list."
    assert all(isinstance(i, int) for i in response['license_token_ids']), "Not all elements in 'license_token_ids' are integers."

def test_get_license_terms(story_client):
    selectedLicenseTermsId = 3

    response = story_client.License.get_license_terms(selectedLicenseTermsId)

    assert response is not None, "Response is None, indicating the call failed."

def test_predict_minting_license_fee(story_client, ip_id, register_commercial_use_pil):
    response = story_client.License.predict_minting_license_fee(
        licensor_ip_id=ip_id, 
        license_terms_id=register_commercial_use_pil, 
        amount=1
    )

    assert response is not None, "Response is None, indicating the contract interaction failed."
    assert 'currency' in response, "Response does not contain 'currency'."
    assert response['currency'] is not None, "'currency' is None."
    assert isinstance(response['currency'], str), "'currency' is not a string."
    assert len(response['currency']) > 0, "'currency' is empty."
    assert 'amount' in response, "Response does not contain 'amount'."
    assert response['amount'] is not None, "'amount' is None."
    assert isinstance(response['amount'], int), "'amount' is not an integer."

def test_set_licensing_config(story_client, ip_id, register_commercial_remix_pil):
    licensing_config = {
        'mintingFee': 1,
        'isSet': True,
        'licensingHook': "0x0000000000000000000000000000000000000000",
        'hookData': "0xFcd3243590d29B131a26B1554B0b21a5B43e622e",
        'commercialRevShare': 0,
        'disabled': False,
        'expectMinimumGroupRewardShare': 1,
        'expectGroupRewardPool': "0x0000000000000000000000000000000000000000"
    }

    response = story_client.License.set_licensing_config(
        ip_id=ip_id,
        license_terms_id=register_commercial_remix_pil,
        licensing_config=licensing_config,
        license_template=PIL_LICENSE_TEMPLATE
    )

    assert response is not None, "Response is None, indicating the contract interaction failed."
    assert 'tx_hash' in response, "Response does not contain 'tx_hash'"
    assert response['tx_hash'] is not None, "'tx_hash' is None"
    assert isinstance(response['tx_hash'], str), "'tx_hash' is not a string"
    assert len(response['tx_hash']) > 0, "'tx_hash' is empty"
    assert 'success' in response, "Response does not contain 'success'"
    assert response['success'] is True, "'success' is not True"

def test_register_pil_terms_with_no_minting_fee(story_client):
    """Test registering PIL terms with no minting fee."""
    response = story_client.License.register_pil_terms(
        transferable=False,
        royalty_policy=story_client.web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
        default_minting_fee=0,  # Minimal minting fee
        expiration=0,
        commercial_use=False,
        commercial_attribution=False,
        commercializer_checker=story_client.web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
        commercializer_checker_data="0x",
        commercial_rev_share=0,
        commercial_rev_ceiling=0,
        derivatives_allowed=False,
        derivatives_attribution=False,
        derivatives_approval=False,
        derivatives_reciprocal=False,
        derivative_rev_ceiling=0,
        currency=MockERC20,
        uri=""
    )

    assert response is not None
    assert 'license_terms_id' in response
    assert response['license_terms_id'] is not None
    assert isinstance(response['license_terms_id'], int)

def test_register_commercial_use_pil_without_royalty_policy(story_client):
    """Test registering commercial use PIL without specifying royalty policy."""
    response = story_client.License.register_commercial_use_pil(
        default_minting_fee=1,
        currency=MockERC20
    )

    assert response is not None
    assert 'license_terms_id' in response
    assert response['license_terms_id'] is not None
    assert isinstance(response['license_terms_id'], int)

@pytest.fixture(scope="module")
def setup_license_terms(story_client, ip_id):
    """Fixture to set up license terms for testing."""
    response = story_client.License.register_commercial_remix_pil(
        default_minting_fee=1,
        currency=MockERC20,
        commercial_rev_share=100,
        royalty_policy=ROYALTY_POLICY
    )
    license_id = response['license_terms_id']

    # Attach the license terms
    story_client.License.attach_license_terms(
        ip_id=ip_id,
        license_template=PIL_LICENSE_TEMPLATE,
        license_terms_id=license_id
    )

    return license_id

def test_multi_token_minting(story_client, ip_id, setup_license_terms):
    """Test minting multiple license tokens at once."""
    response = story_client.License.mint_license_tokens(
        licensor_ip_id=ip_id,
        license_template=PIL_LICENSE_TEMPLATE,
        license_terms_id=setup_license_terms,
        amount=3,  # Mint multiple tokens
        receiver=account.address
    )

    assert response is not None
    assert 'tx_hash' in response
    assert response['tx_hash'] is not None
    assert isinstance(response['tx_hash'], str)
    assert len(response['tx_hash']) > 0
    assert 'license_token_ids' in response
    assert isinstance(response['license_token_ids'], list)
    assert len(response['license_token_ids']) > 0

def test_set_licensing_config_with_hooks(story_client, ip_id, register_commercial_remix_pil):
    """Test setting licensing configuration with hooks enabled."""
    licensing_config = {
        'mintingFee': 100,
        'isSet': True,
        'licensingHook': "0x0000000000000000000000000000000000000000",
        'hookData': "0x1234567890",  # Different hook data
        'commercialRevShare': 100,  # 50% revenue share
        'disabled': False,
        'expectMinimumGroupRewardShare': 10,  # 10% minimum group reward
        'expectGroupRewardPool': "0x0000000000000000000000000000000000000000"
    }

    response = story_client.License.set_licensing_config(
        ip_id=ip_id,
        license_terms_id=register_commercial_remix_pil,
        licensing_config=licensing_config,
        license_template=PIL_LICENSE_TEMPLATE
    )

    assert response is not None
    assert 'tx_hash' in response
    assert response['tx_hash'] is not None
    assert isinstance(response['tx_hash'], str)
    assert len(response['tx_hash']) > 0
    assert 'success' in response
    assert response['success'] is True

def test_predict_minting_fee_with_multiple_tokens(story_client, ip_id, setup_license_terms):
    """Test predicting minting fee for multiple tokens."""
    response = story_client.License.predict_minting_license_fee(
        licensor_ip_id=ip_id,
        license_terms_id=setup_license_terms,
        amount=5  # Predict for 5 tokens
    )

    assert response is not None
    assert 'currency' in response
    assert response['currency'] is not None
    assert isinstance(response['currency'], str)
    assert len(response['currency']) > 0
    assert 'amount' in response
    assert response['amount'] is not None
    assert isinstance(response['amount'], int)
    assert response['amount'] > 0  # Amount should be positive for multiple tokens
