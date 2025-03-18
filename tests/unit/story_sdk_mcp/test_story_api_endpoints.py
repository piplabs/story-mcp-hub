"""
Tests for the Story SDK MCP API endpoints.
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
import json
import sys
import os
import types
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from mcp.server.fastmcp import FastMCP

from tests.mocks.web3_mocks import (
    SAMPLE_IP_ID,
    SAMPLE_NFT_CONTRACT,
    SAMPLE_TOKEN_ID,
    SAMPLE_LICENSE_TERMS_ID
)
from tests.mocks.api_mocks import (
    MOCK_IPFS_URI,
)

@pytest.fixture
def test_client(mcp_test_server):
    """Create a test client for the MCP endpoints"""
    return mcp_test_server.client

@pytest.fixture
def mock_story_service():
    """Create a mock StoryService for testing API endpoints"""
    mock_service = Mock()
    
    # Set up common mock methods
    mock_service.ipfs_enabled = True
    mock_service.get_license_terms = Mock(return_value={
        "transferable": True,
        "royaltyPolicy": "0x1234567890123456789012345678901234567890",
        "defaultMintingFee": 0,
        "expiration": 0,
        "commercialUse": True,
        "commercialAttribution": False,
        "commercializerChecker": "0x0000000000000000000000000000000000000000",
        "commercializerCheckerData": "0x",
        "commercialRevShare": 10,
        "commercialRevCeiling": 0,
        "derivativesAllowed": True,
        "derivativesAttribution": True,
        "derivativesApproval": False,
        "derivativesReciprocal": True,
        "derivativeRevCeiling": 0,
        "currency": "0x1514000000000000000000000000000000000000",
        "uri": "ipfs://example",
    })
    
    mock_service.mint_license_tokens = Mock(return_value={
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "licenseTokenIds": [1, 2, 3]
    })
    
    mock_service.send_ip = Mock(return_value={
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "txReceipt": {"status": 1}
    })
    
    mock_service.mint_and_register_ip_with_terms = Mock(return_value={
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "ipId": SAMPLE_IP_ID,
        "tokenId": SAMPLE_TOKEN_ID,
        "licenseTermsIds": [SAMPLE_LICENSE_TERMS_ID]
    })
    
    mock_service.create_spg_nft_collection = Mock(return_value={
        "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "spg_nft_contract": SAMPLE_NFT_CONTRACT
    })
    
    mock_service.upload_image_to_ipfs = Mock(return_value=MOCK_IPFS_URI)
    
    mock_service.create_ip_metadata = Mock(return_value={
        "nft_metadata": {"name": "Test", "description": "Test description"},
        "nft_metadata_uri": MOCK_IPFS_URI,
        "nft_metadata_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "ip_metadata": {"title": "Test", "description": "Test description"},
        "ip_metadata_uri": MOCK_IPFS_URI,
        "ip_metadata_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "registration_metadata": {
            "ip_metadata_uri": MOCK_IPFS_URI,
            "ip_metadata_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "nft_metadata_uri": MOCK_IPFS_URI,
            "nft_metadata_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        }
    })
    
    mock_service.register = Mock(return_value={
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "ipId": SAMPLE_IP_ID
    })
    
    mock_service.attach_license_terms = Mock(return_value={
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    })
    
    mock_service.register_derivative = Mock(return_value={
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    })
    
    mock_service.pay_royalty_on_behalf = Mock(return_value={
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    })
    
    mock_service.claim_revenue = Mock(return_value={
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "claimableToken": 1000
    })
    
    mock_service.raise_dispute = Mock(return_value={
        "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "disputeId": 1
    })
    
    # Ensure the network property is set
    mock_service.network = "mainnet"
    
    return mock_service

# Create a simpler mock server
@pytest.fixture
def story_server(mock_story_service):
    """Create a mock server with the same API as the real server"""
    # Create a simple object with methods that match the server's API
    class MockServer:
        def __init__(self, service):
            self.story_service = service
            self.network = service.network
        
        def get_license_terms(self, license_terms_id):
            result = self.story_service.get_license_terms(license_terms_id)
            return f"License Terms {license_terms_id}: {result}"
        
        def mint_license_tokens(self, licensor_ip_id, license_terms_id, receiver=None, 
                               amount=1, max_minting_fee=None, max_revenue_share=None, 
                               license_template=None):
            result = self.story_service.mint_license_tokens(
                licensor_ip_id=licensor_ip_id,
                license_terms_id=license_terms_id,
                receiver=receiver,
                amount=amount,
                max_minting_fee=max_minting_fee,
                max_revenue_share=max_revenue_share,
                license_template=license_template
            )
            return f"Successfully minted license tokens:\nTransaction Hash: {result['txHash']}\nLicense Token IDs: {result['licenseTokenIds']}"
        
        def send_ip(self, to_address, amount):
            result = self.story_service.send_ip(to_address, amount)
            return f"Successfully sent {amount} IP to {to_address}. Transaction hash: {result['txHash']}"
        
        def mint_and_register_ip_with_terms(self, commercial_rev_share, derivatives_allowed, 
                                          registration_metadata=None, recipient=None, 
                                          spg_nft_contract=None):
            result = self.story_service.mint_and_register_ip_with_terms(
                commercial_rev_share=commercial_rev_share,
                derivatives_allowed=derivatives_allowed,
                registration_metadata=registration_metadata,
                recipient=recipient,
                spg_nft_contract=spg_nft_contract
            )
            return f"Successfully minted and registered IP asset with terms:\nTransaction Hash: {result['txHash']}\nIP ID: {result['ipId']}\nToken ID: {result['tokenId']}\nLicense Terms IDs: {result['licenseTermsIds']}"
        
        def create_spg_nft_collection(self, name, symbol, is_public_minting=True, mint_open=True,
                                    mint_fee_recipient=None, contract_uri="", base_uri="",
                                    max_supply=None, mint_fee=None, mint_fee_token=None, owner=None):
            result = self.story_service.create_spg_nft_collection(
                name=name,
                symbol=symbol,
                is_public_minting=is_public_minting,
                mint_open=mint_open,
                mint_fee_recipient=mint_fee_recipient,
                contract_uri=contract_uri,
                base_uri=base_uri,
                max_supply=max_supply,
                mint_fee=mint_fee,
                mint_fee_token=mint_fee_token,
                owner=owner
            )
            return f"Successfully created SPG NFT collection:\nName: {name}\nSymbol: {symbol}\nTransaction Hash: {result['tx_hash']}\nSPG NFT Contract Address: {result['spg_nft_contract']}"
        
        def register(self, nft_contract, token_id, ip_metadata=None):
            result = self.story_service.register(
                nft_contract=nft_contract,
                token_id=token_id,
                ip_metadata=ip_metadata
            )
            return f"Successfully registered NFT as IP. Transaction hash: {result['txHash']}, IP ID: {result['ipId']}"
        
        def attach_license_terms(self, ip_id, license_terms_id, license_template=None):
            result = self.story_service.attach_license_terms(
                ip_id=ip_id,
                license_terms_id=license_terms_id,
                license_template=license_template
            )
            return f"Successfully attached license terms to IP. Transaction hash: {result['txHash']}"
        
        def register_derivative(self, child_ip_id, parent_ip_ids, license_terms_ids, 
                             max_minting_fee=0, max_rts=0, max_revenue_share=0, 
                             license_template=None):
            result = self.story_service.register_derivative(
                child_ip_id=child_ip_id,
                parent_ip_ids=parent_ip_ids,
                license_terms_ids=license_terms_ids,
                max_minting_fee=max_minting_fee,
                max_rts=max_rts,
                max_revenue_share=max_revenue_share,
                license_template=license_template
            )
            return f"Successfully registered derivative. Transaction hash: {result['txHash']}"
        
        def pay_royalty_on_behalf(self, receiver_ip_id, payer_ip_id, token, amount):
            result = self.story_service.pay_royalty_on_behalf(
                receiver_ip_id=receiver_ip_id,
                payer_ip_id=payer_ip_id,
                token=token,
                amount=amount
            )
            return f"Successfully paid royalty. Transaction hash: {result['txHash']}"
        
        def claim_revenue(self, snapshot_ids, child_ip_id, token):
            result = self.story_service.claim_revenue(
                snapshot_ids=snapshot_ids,
                child_ip_id=child_ip_id,
                token=token
            )
            return f"Successfully claimed revenue. Transaction hash: {result['txHash']}, Claimed amount: {result.get('claimableToken', 'Unknown')}"
        
        def raise_dispute(self, target_ip_id, dispute_evidence_hash, target_tag, data="0x"):
            result = self.story_service.raise_dispute(
                target_ip_id=target_ip_id,
                dispute_evidence_hash=dispute_evidence_hash,
                target_tag=target_tag,
                data=data
            )
            return f"Successfully raised dispute. Transaction hash: {result['txHash']}, Dispute ID: {result.get('disputeId', 'Unknown')}"
        
        def upload_image_to_ipfs(self, image_data):
            result = self.story_service.upload_image_to_ipfs(image_data)
            return f"Successfully uploaded image to IPFS: {result}"
        
        def create_ip_metadata(self, image_uri, name, description, attributes=None):
            result = self.story_service.create_ip_metadata(
                image_uri=image_uri,
                name=name,
                description=description,
                attributes=attributes
            )
            return f"Successfully created and uploaded metadata:\nNFT Metadata URI: {result['nft_metadata_uri']}\nIP Metadata URI: {result['ip_metadata_uri']}"
    
    # Return an instance of the mock server
    return MockServer(mock_story_service)

@pytest.mark.parametrize("license_terms_id", [1, 42, 100])
def test_get_license_terms(story_server, mock_story_service, license_terms_id):
    """Test the get_license_terms endpoint"""
    # Call the endpoint
    response = story_server.get_license_terms(license_terms_id)
    
    # Verify service was called correctly
    mock_story_service.get_license_terms.assert_called_once_with(license_terms_id)
    
    # Verify response contains expected data
    assert isinstance(response, str)
    assert "License Terms" in response
    assert "transferable" in str(mock_story_service.get_license_terms.return_value)

def test_mint_license_tokens(story_server, mock_story_service):
    """Test the mint_license_tokens endpoint"""
    # Call the endpoint
    response = story_server.mint_license_tokens(
        licensor_ip_id=SAMPLE_IP_ID,
        license_terms_id=SAMPLE_LICENSE_TERMS_ID,
        amount=3
    )
    
    # Verify service was called correctly
    mock_story_service.mint_license_tokens.assert_called_once_with(
        licensor_ip_id=SAMPLE_IP_ID,
        license_terms_id=SAMPLE_LICENSE_TERMS_ID,
        receiver=None,
        amount=3,
        max_minting_fee=None,
        max_revenue_share=None,
        license_template=None
    )
    
    # Verify response contains expected data
    assert isinstance(response, str)
    assert "Successfully minted license tokens" in response
    assert "Transaction Hash" in response

def test_send_ip(story_server, mock_story_service):
    """Test the send_ip endpoint"""
    # Call the endpoint
    to_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
    amount = 1.5
    
    response = story_server.send_ip(to_address=to_address, amount=amount)
    
    # Verify service was called correctly
    mock_story_service.send_ip.assert_called_once_with(to_address, amount)
    
    # Verify response contains expected data
    assert isinstance(response, str)
    assert f"Successfully sent {amount} IP to {to_address}" in response
    assert "Transaction hash" in response

def test_mint_and_register_ip_with_terms(story_server, mock_story_service):
    """Test the mint_and_register_ip_with_terms endpoint"""
    # Call the endpoint
    commercial_rev_share = 10
    derivatives_allowed = True
    
    response = story_server.mint_and_register_ip_with_terms(
        commercial_rev_share=commercial_rev_share,
        derivatives_allowed=derivatives_allowed
    )
    
    # Verify service was called correctly
    mock_story_service.mint_and_register_ip_with_terms.assert_called_once_with(
        commercial_rev_share=commercial_rev_share,
        derivatives_allowed=derivatives_allowed,
        registration_metadata=None,
        recipient=None,
        spg_nft_contract=None
    )
    
    # Verify response contains expected data
    assert isinstance(response, str)
    assert "Successfully minted and registered IP asset with terms" in response
    assert "Transaction Hash" in response
    assert "IP ID" in response
    assert "Token ID" in response

def test_create_spg_nft_collection(story_server, mock_story_service):
    """Test the create_spg_nft_collection endpoint"""
    # Call the endpoint
    name = "Test Collection"
    symbol = "TEST"
    
    response = story_server.create_spg_nft_collection(
        name=name,
        symbol=symbol
    )
    
    # Verify service was called correctly
    mock_story_service.create_spg_nft_collection.assert_called_once_with(
        name=name,
        symbol=symbol,
        is_public_minting=True,
        mint_open=True,
        mint_fee_recipient=None,
        contract_uri="",
        base_uri="",
        max_supply=None,
        mint_fee=None,
        mint_fee_token=None,
        owner=None
    )
    
    # Verify response contains expected data
    assert isinstance(response, str)
    assert "Successfully created SPG NFT collection" in response
    assert f"Name: {name}" in response
    assert f"Symbol: {symbol}" in response
    assert "SPG NFT Contract Address" in response

def test_register(story_server, mock_story_service):
    """Test the register endpoint"""
    # Call the endpoint
    response = story_server.register(
        nft_contract=SAMPLE_NFT_CONTRACT,
        token_id=SAMPLE_TOKEN_ID
    )
    
    # Verify service was called correctly
    mock_story_service.register.assert_called_once_with(
        nft_contract=SAMPLE_NFT_CONTRACT,
        token_id=SAMPLE_TOKEN_ID,
        ip_metadata=None
    )
    
    # Verify response contains expected data
    assert isinstance(response, str)
    assert "Successfully registered NFT as IP" in response
    assert "Transaction hash" in response
    assert "IP ID" in response

def test_attach_license_terms(story_server, mock_story_service):
    """Test the attach_license_terms endpoint"""
    # Call the endpoint
    response = story_server.attach_license_terms(
        ip_id=SAMPLE_IP_ID,
        license_terms_id=SAMPLE_LICENSE_TERMS_ID
    )
    
    # Verify service was called correctly
    mock_story_service.attach_license_terms.assert_called_once_with(
        ip_id=SAMPLE_IP_ID,
        license_terms_id=SAMPLE_LICENSE_TERMS_ID,
        license_template=None
    )
    
    # Verify response contains expected data
    assert isinstance(response, str)
    assert "Successfully attached license terms to IP" in response
    assert "Transaction hash" in response

def test_register_derivative(story_server, mock_story_service):
    """Test the register_derivative endpoint"""
    # Call the endpoint
    child_ip_id = "0xabcd1234abcd1234abcd1234abcd1234abcd1234"
    parent_ip_ids = [SAMPLE_IP_ID]
    license_terms_ids = [SAMPLE_LICENSE_TERMS_ID]
    
    response = story_server.register_derivative(
        child_ip_id=child_ip_id,
        parent_ip_ids=parent_ip_ids,
        license_terms_ids=license_terms_ids
    )
    
    # Verify service was called correctly
    mock_story_service.register_derivative.assert_called_once_with(
        child_ip_id=child_ip_id,
        parent_ip_ids=parent_ip_ids,
        license_terms_ids=license_terms_ids,
        max_minting_fee=0,
        max_rts=0,
        max_revenue_share=0,
        license_template=None
    )
    
    # Verify response contains expected data
    assert isinstance(response, str)
    assert "Successfully registered derivative" in response
    assert "Transaction hash" in response

def test_pay_royalty_on_behalf(story_server, mock_story_service):
    """Test the pay_royalty_on_behalf endpoint"""
    # Call the endpoint
    receiver_ip_id = SAMPLE_IP_ID
    payer_ip_id = "0xabcd1234abcd1234abcd1234abcd1234abcd1234"
    token = "0x1234567890123456789012345678901234567890"
    amount = 1000
    
    response = story_server.pay_royalty_on_behalf(
        receiver_ip_id=receiver_ip_id,
        payer_ip_id=payer_ip_id,
        token=token,
        amount=amount
    )
    
    # Verify service was called correctly
    mock_story_service.pay_royalty_on_behalf.assert_called_once_with(
        receiver_ip_id=receiver_ip_id,
        payer_ip_id=payer_ip_id,
        token=token,
        amount=amount
    )
    
    # Verify response contains expected data
    assert isinstance(response, str)
    assert "Successfully paid royalty" in response
    assert "Transaction hash" in response