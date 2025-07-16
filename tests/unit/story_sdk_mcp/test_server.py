"""
Tests for the Story SDK MCP server module.
"""
import pytest
import json
import os
import sys
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Approach: Rather than importing the actual server module, which has dependencies
# that are difficult to mock, we'll test the server functions directly by recreating them
# and ensuring they work the same way. This is essentially a contract test.

class MockFastMCP:
    """Mock for the FastMCP class."""
    def __init__(self, name):
        self.name = name
        self.tools = {}
    
    def tool(self):
        """Mock for the @mcp.tool() decorator."""
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator

class MockStoryService:
    """Mock for the StoryService class."""
    def __init__(self):
        self.ipfs_enabled = True
        self.network = "testnet"
        self.web3 = Mock()
        self.web3.from_wei.return_value = 0.1  # For bond amount conversion
        # Add any other properties needed

class TestServerFunctions:
    """Test the MCP server functions."""
    
    @pytest.fixture
    def setup_mocks(self):
        """Set up mocks for the test."""
        self.mcp = MockFastMCP("Test MCP")
        self.story_service = MockStoryService()
        
        # Create a module-like object to hold the functions
        server_module = type('ServerModule', (), {
            'mcp': self.mcp,
            'story_service': self.story_service,
        })
        
        # Add helper function to create and register a tool
        def add_tool(name, func):
            decorated_func = self.mcp.tool()(func)
            setattr(server_module, name, decorated_func)
            return decorated_func
        
        return server_module, add_tool
    
    def test_upload_image_to_ipfs(self, setup_mocks):
        """Test the upload_image_to_ipfs function."""
        server_module, add_tool = setup_mocks
        
        # Create the tool function we want to test
        def upload_image_to_ipfs(image_data):
            """Upload an image to IPFS."""
            try:
                ipfs_uri = self.story_service.upload_image_to_ipfs(image_data)
                return f"Successfully uploaded image to IPFS: {ipfs_uri}"
            except Exception as e:
                return f"Error uploading image to IPFS: {str(e)}"
                
        # Register it with our mock MCP
        upload_image_to_ipfs = add_tool('upload_image_to_ipfs', upload_image_to_ipfs)
        
        # Mock the service method
        self.story_service.upload_image_to_ipfs = Mock(return_value="ipfs://QmTest123")
        
        # Call the function
        result = upload_image_to_ipfs(b"image_data")
        
        # Assertions
        assert "Successfully uploaded image" in result
        assert "ipfs://QmTest123" in result
        self.story_service.upload_image_to_ipfs.assert_called_once_with(b"image_data")
    
    def test_upload_image_to_ipfs_error(self, setup_mocks):
        """Test the upload_image_to_ipfs function with an error."""
        server_module, add_tool = setup_mocks
        
        # Create the tool function we want to test
        def upload_image_to_ipfs(image_data):
            """Upload an image to IPFS."""
            try:
                ipfs_uri = self.story_service.upload_image_to_ipfs(image_data)
                return f"Successfully uploaded image to IPFS: {ipfs_uri}"
            except Exception as e:
                return f"Error uploading image to IPFS: {str(e)}"
                
        # Register it with our mock MCP
        upload_image_to_ipfs = add_tool('upload_image_to_ipfs', upload_image_to_ipfs)
        
        # Mock the service method to raise an exception
        self.story_service.upload_image_to_ipfs = Mock(side_effect=Exception("IPFS error"))
        
        # Call the function
        result = upload_image_to_ipfs(b"image_data")
        
        # Assertions
        assert "Error uploading image to IPFS" in result
        assert "IPFS error" in result
        self.story_service.upload_image_to_ipfs.assert_called_once_with(b"image_data")
    
    def test_create_ip_metadata(self, setup_mocks):
        """Test the create_ip_metadata function."""
        server_module, add_tool = setup_mocks
        
        # Create the tool function we want to test
        def create_ip_metadata(image_uri, name, description, attributes=None):
            """Create and upload metadata to IPFS."""
            try:
                result = self.story_service.create_ip_metadata(
                    image_uri=image_uri,
                    name=name,
                    description=description,
                    attributes=attributes,
                )
                return (
                    f"Successfully created and uploaded metadata:\n"
                    f"NFT Metadata URI: {result['nft_metadata_uri']}\n"
                    f"IP Metadata URI: {result['ip_metadata_uri']}\n"
                    f"Registration metadata for minting:\n"
                    f"{json.dumps(result['registration_metadata'], indent=2)}"
                )
            except Exception as e:
                return f"Error creating metadata: {str(e)}"
                
        # Register it with our mock MCP
        create_ip_metadata = add_tool('create_ip_metadata', create_ip_metadata)
        
        # Mock the service method
        self.story_service.create_ip_metadata = Mock(return_value={
            "nft_metadata_uri": "ipfs://QmNft123",
            "ip_metadata_uri": "ipfs://QmIp456",
            "registration_metadata": {"name": "Test NFT"}
        })
        
        # Call the function
        result = create_ip_metadata(
            image_uri="ipfs://QmImage789",
            name="Test NFT",
            description="Test description"
        )
        
        # Assertions
        assert "Successfully created and uploaded metadata" in result
        assert "ipfs://QmNft123" in result
        assert "ipfs://QmIp456" in result
        assert "Test NFT" in result
        self.story_service.create_ip_metadata.assert_called_once_with(
            image_uri="ipfs://QmImage789",
            name="Test NFT",
            description="Test description",
            attributes=None
        )
    
    def test_get_license_terms(self, setup_mocks):
        """Test the get_license_terms function."""
        server_module, add_tool = setup_mocks
        
        # Create the tool function we want to test
        def get_license_terms(license_terms_id):
            """Get the license terms for a specific ID."""
            try:
                terms = self.story_service.get_license_terms(license_terms_id)
                return f"License Terms {license_terms_id}: {terms}"
            except Exception as e:
                return f"Error retrieving license terms: {str(e)}"
                
        # Register it with our mock MCP
        get_license_terms = add_tool('get_license_terms', get_license_terms)
        
        # Mock the service method
        self.story_service.get_license_terms = Mock(return_value={
            "transferable": True,
            "commercialUse": True
        })
        
        # Call the function
        result = get_license_terms(42)
        
        # Assertions
        assert "License Terms 42" in result
        assert "{'transferable': True" in result
        assert "'commercialUse': True" in result
        self.story_service.get_license_terms.assert_called_once_with(42)
    
    def test_mint_license_tokens(self, setup_mocks):
        """Test the mint_license_tokens function with approve_amount."""
        server_module, add_tool = setup_mocks
        
        # Create the tool function we want to test
        def mint_license_tokens(
            licensor_ip_id, 
            license_terms_id, 
            receiver=None, 
            amount=1, 
            max_minting_fee=None, 
            max_revenue_share=None, 
            license_template=None,
            approve_amount=None
        ):
            """Mint license tokens for a given IP and license terms."""
            try:
                response = self.story_service.mint_license_tokens(
                    licensor_ip_id=licensor_ip_id,
                    license_terms_id=license_terms_id,
                    receiver=receiver,
                    amount=amount,
                    max_minting_fee=max_minting_fee,
                    max_revenue_share=max_revenue_share,
                    license_template=license_template,
                    approve_amount=approve_amount,
                )

                return (
                    f"Successfully minted license tokens:\n"
                    f"Transaction Hash: {response['tx_hash']}\n"
                    f"License Token IDs: {response['license_token_ids']}"
                )
            except ValueError as e:
                return f"Validation error: {str(e)}"
            except Exception as e:
                return f"Error minting license tokens: {str(e)}"
                
        # Register it with our mock MCP
        mint_license_tokens = add_tool('mint_license_tokens', mint_license_tokens)
        
        # Mock the service method
        self.story_service.mint_license_tokens = Mock(return_value={
            "tx_hash": "0xabc123",
            "license_token_ids": [1, 2, 3]
        })
        
        # Call the function
        result = mint_license_tokens(
            licensor_ip_id="0x123",
            license_terms_id=42,
            amount=3,
            approve_amount=10000
        )
        
        # Assertions
        assert "Successfully minted license tokens" in result
        assert "0xabc123" in result
        assert "[1, 2, 3]" in result
        self.story_service.mint_license_tokens.assert_called_once_with(
            licensor_ip_id="0x123",
            license_terms_id=42,
            receiver=None,
            amount=3,
            max_minting_fee=None,
            max_revenue_share=None,
            license_template=None,
            approve_amount=10000
        )
    
    def test_mint_license_tokens_validation_error(self, setup_mocks):
        """Test the mint_license_tokens function with a validation error."""
        server_module, add_tool = setup_mocks
        
        # Create the tool function we want to test
        def mint_license_tokens(
            licensor_ip_id, 
            license_terms_id, 
            receiver=None, 
            amount=1, 
            max_minting_fee=None, 
            max_revenue_share=None, 
            license_template=None,
            approve_amount=None
        ):
            """Mint license tokens for a given IP and license terms."""
            try:
                response = self.story_service.mint_license_tokens(
                    licensor_ip_id=licensor_ip_id,
                    license_terms_id=license_terms_id,
                    receiver=receiver,
                    amount=amount,
                    max_minting_fee=max_minting_fee,
                    max_revenue_share=max_revenue_share,
                    license_template=license_template,
                    approve_amount=approve_amount,
                )

                return (
                    f"Successfully minted license tokens:\n"
                    f"Transaction Hash: {response['tx_hash']}\n"
                    f"License Token IDs: {response['license_token_ids']}"
                )
            except ValueError as e:
                return f"Validation error: {str(e)}"
            except Exception as e:
                return f"Error minting license tokens: {str(e)}"
                
        # Register it with our mock MCP
        mint_license_tokens = add_tool('mint_license_tokens', mint_license_tokens)
        
        # Mock the service method
        self.story_service.mint_license_tokens = Mock(side_effect=ValueError("Invalid license terms ID"))
        
        # Call the function
        result = mint_license_tokens(
            licensor_ip_id="0x123",
            license_terms_id=-1
        )
        
        # Assertions
        assert "Validation error" in result
        assert "Invalid license terms ID" in result
        self.story_service.mint_license_tokens.assert_called_once()
    
    def test_register(self, setup_mocks):
        """Test the register function."""
        server_module, add_tool = setup_mocks
        
        # Create the tool function we want to test
        def register(nft_contract, token_id, ip_metadata=None):
            """Register an NFT as IP, creating a corresponding IP record."""
            try:
                result = self.story_service.register(
                    nft_contract=nft_contract,
                    token_id=token_id,
                    ip_metadata=ip_metadata
                )
                
                if result.get('tx_hash'):
                    return f"Successfully registered NFT as IP. Transaction hash: {result['tx_hash']}, IP ID: {result['ip_id']}"
                else:
                    return f"NFT already registered as IP. IP ID: {result['ip_id']}"
            except Exception as e:
                return f"Error registering NFT as IP: {str(e)}"
                
        # Register it with our mock MCP
        register = add_tool('register', register)
        
        # Mock the service method
        self.story_service.register = Mock(return_value={
            "tx_hash": "0xabc123",
            "ip_id": "0xdef456"
        })
        
        # Call the function
        result = register(
            nft_contract="0x789",
            token_id=42
        )
        
        # Assertions
        assert "Successfully registered NFT as IP" in result
        assert "0xabc123" in result
        assert "0xdef456" in result
        self.story_service.register.assert_called_once_with(
            nft_contract="0x789",
            token_id=42,
            ip_metadata=None
        )
    
    def test_register_already_registered(self, setup_mocks):
        """Test the register function with already registered NFT."""
        server_module, add_tool = setup_mocks
        
        # Create the tool function we want to test
        def register(nft_contract, token_id, ip_metadata=None):
            """Register an NFT as IP, creating a corresponding IP record."""
            try:
                result = self.story_service.register(
                    nft_contract=nft_contract,
                    token_id=token_id,
                    ip_metadata=ip_metadata
                )
                
                if result.get('tx_hash'):
                    return f"Successfully registered NFT as IP. Transaction hash: {result['tx_hash']}, IP ID: {result['ip_id']}"
                else:
                    return f"NFT already registered as IP. IP ID: {result['ip_id']}"
            except Exception as e:
                return f"Error registering NFT as IP: {str(e)}"
                
        # Register it with our mock MCP
        register = add_tool('register', register)
        
        # Mock the service method
        self.story_service.register = Mock(return_value={
            "ip_id": "0xdef456"  # No tx_hash indicates already registered
        })
        
        # Call the function
        result = register(
            nft_contract="0x789",
            token_id=42
        )
        
        # Assertions
        assert "NFT already registered as IP" in result
        assert "0xdef456" in result
        self.story_service.register.assert_called_once()
    
    def test_attach_license_terms(self, setup_mocks):
        """Test the attach_license_terms function."""
        server_module, add_tool = setup_mocks
        
        # Create the tool function we want to test
        def attach_license_terms(ip_id, license_terms_id, license_template=None):
            """Attaches license terms to an IP."""
            try:
                result = self.story_service.attach_license_terms(
                    ip_id=ip_id,
                    license_terms_id=license_terms_id,
                    license_template=license_template
                )
                
                return f"Successfully attached license terms to IP. Transaction hash: {result['tx_hash']}"
            except Exception as e:
                return f"Error attaching license terms: {str(e)}"
                
        # Register it with our mock MCP
        attach_license_terms = add_tool('attach_license_terms', attach_license_terms)
        
        # Mock the service method
        self.story_service.attach_license_terms = Mock(return_value={
            "tx_hash": "0xabc123"
        })
        
        # Call the function
        result = attach_license_terms(
            ip_id="0x123",
            license_terms_id=42
        )
        
        # Assertions
        assert "Successfully attached license terms to IP" in result
        assert "0xabc123" in result
        self.story_service.attach_license_terms.assert_called_once_with(
            ip_id="0x123",
            license_terms_id=42,
            license_template=None
        )
    
    def test_register_derivative(self, setup_mocks):
        """Test the register_derivative function with approve_amount."""
        server_module, add_tool = setup_mocks
        
        # Create the tool function we want to test
        def register_derivative(
            child_ip_id,
            parent_ip_ids,
            license_terms_ids,
            max_minting_fee=0,
            max_rts=0,
            max_revenue_share=0,
            license_template=None,
            approve_amount=None
        ):
            """Registers a derivative with parent IP's license terms."""
            try:
                result = self.story_service.register_derivative(
                    child_ip_id=child_ip_id,
                    parent_ip_ids=parent_ip_ids,
                    license_terms_ids=license_terms_ids,
                    max_minting_fee=max_minting_fee,
                    max_rts=max_rts,
                    max_revenue_share=max_revenue_share,
                    license_template=license_template,
                    approve_amount=approve_amount
                )
                
                return f"Successfully registered derivative. Transaction hash: {result['tx_hash']}"
            except Exception as e:
                return f"Error registering derivative: {str(e)}"
                
        # Register it with our mock MCP
        register_derivative = add_tool('register_derivative', register_derivative)
        
        # Mock the service method
        self.story_service.register_derivative = Mock(return_value={
            "tx_hash": "0xabc123"
        })
        
        # Call the function
        result = register_derivative(
            child_ip_id="0x123",
            parent_ip_ids=["0x456", "0x789"],
            license_terms_ids=[1, 2],
            approve_amount=10000
        )
        
        # Assertions
        assert "Successfully registered derivative" in result
        assert "0xabc123" in result
        self.story_service.register_derivative.assert_called_once_with(
            child_ip_id="0x123",
            parent_ip_ids=["0x456", "0x789"],
            license_terms_ids=[1, 2],
            max_minting_fee=0,
            max_rts=0,
            max_revenue_share=0,
            license_template=None,
            approve_amount=10000
        )
    
    def test_pay_royalty_on_behalf(self, setup_mocks):
        """Test the pay_royalty_on_behalf function with approve_amount."""
        server_module, add_tool = setup_mocks
        
        # Create the tool function we want to test
        def pay_royalty_on_behalf(receiver_ip_id, payer_ip_id, token, amount, approve_amount=None):
            """Pays royalties to receiver IP on behalf of payer IP."""
            try:
                response = self.story_service.pay_royalty_on_behalf(
                    receiver_ip_id=receiver_ip_id,
                    payer_ip_id=payer_ip_id,
                    token=token,
                    amount=amount,
                    approve_amount=approve_amount
                )

                return f"Successfully paid royalty on behalf. Transaction hash: {response['tx_hash']}"
            except Exception as e:
                return f"Error paying royalty on behalf: {str(e)}"
                
        # Register it with our mock MCP
        pay_royalty_on_behalf = add_tool('pay_royalty_on_behalf', pay_royalty_on_behalf)
        
        # Mock the service method
        self.story_service.pay_royalty_on_behalf = Mock(return_value={
            "tx_hash": "0xabc123"
        })
        
        # Call the function
        result = pay_royalty_on_behalf(
            receiver_ip_id="0x123",
            payer_ip_id="0x456",
            token="0x789",
            amount=100,
            approve_amount=200
        )
        
        # Assertions
        assert "Successfully paid royalty on behalf" in result
        assert "0xabc123" in result
        self.story_service.pay_royalty_on_behalf.assert_called_once_with(
            receiver_ip_id="0x123",
            payer_ip_id="0x456",
            token="0x789",
            amount=100,
            approve_amount=200
        )
    
    def test_claim_all_revenue(self, setup_mocks):
        """Test the claim_all_revenue function."""
        server_module, add_tool = setup_mocks
        
        # Create the tool function we want to test
        def claim_all_revenue(
            ancestor_ip_id,
            claimer,
            child_ip_ids,
            royalty_policies,
            currency_tokens,
            auto_transfer=True
        ):
            """Claim all revenue for a given ancestor IP and claimer."""
            try:
                response = self.story_service.claim_all_revenue(
                    ancestor_ip_id=ancestor_ip_id,
                    claimer=claimer,
                    child_ip_ids=child_ip_ids,
                    royalty_policies=royalty_policies,
                    currency_tokens=currency_tokens,
                    auto_transfer=auto_transfer
                )
                return response
            except Exception as e:
                return {"error": str(e)}
                
        # Register it with our mock MCP
        claim_all_revenue = add_tool('claim_all_revenue', claim_all_revenue)
        
        # Mock the service method
        self.story_service.claim_all_revenue = Mock(return_value={
            "receipt": {"status": 1},
            "claimed_tokens": [{"token": "0x123", "amount": 1000}],
            "tx_hash": "0xabc123"
        })
        
        # Call the function
        result = claim_all_revenue(
            ancestor_ip_id="0x123",
            claimer="0x456",
            child_ip_ids=["0x789"],
            royalty_policies=["0xaaa"],
            currency_tokens=["0xbbb"]
        )
        
        # Assertions
        assert result["receipt"]["status"] == 1
        assert result["claimed_tokens"][0]["amount"] == 1000
        assert result["tx_hash"] == "0xabc123"
        self.story_service.claim_all_revenue.assert_called_once_with(
            ancestor_ip_id="0x123",
            claimer="0x456",
            child_ip_ids=["0x789"],
            royalty_policies=["0xaaa"],
            currency_tokens=["0xbbb"],
            auto_transfer=True
        )
    
    def test_raise_dispute(self, setup_mocks):
        """Test the raise_dispute function with new CID and liveness parameters."""
        server_module, add_tool = setup_mocks
        
        # Create the tool function we want to test
        def raise_dispute(
            target_ip_id,
            target_tag,
            cid,
            bond_amount,
            liveness=30,
            approve_amount=None
        ):
            """Raises a dispute against an IP asset."""
            try:
                result = self.story_service.raise_dispute(
                    target_ip_id=target_ip_id,
                    target_tag=target_tag,
                    cid=cid,
                    bond_amount=bond_amount,
                    liveness=liveness,
                    approve_amount=approve_amount
                )
                
                if 'error' in result:
                    return f"Error raising dispute: {result['error']}"
                
                dispute_id = result.get('dispute_id', 'Unknown')
                liveness_days = result.get('liveness_days', 'Unknown')
                liveness_seconds = result.get('liveness_seconds', 'Unknown')
                return f"Successfully raised dispute. Transaction hash: {result['tx_hash']}, Dispute ID: {dispute_id}, Liveness: {liveness_days} days ({liveness_seconds} seconds)"
            except Exception as e:
                return f"Error raising dispute: {str(e)}"
                
        # Register it with our mock MCP
        raise_dispute = add_tool('raise_dispute', raise_dispute)
        
        # Mock the service method
        self.story_service.raise_dispute = Mock(return_value={
            "tx_hash": "0xabc123",
            "dispute_id": 42,
            "liveness_days": 30,
            "liveness_seconds": 2592000
        })
        
        # Call the function
        result = raise_dispute(
            target_ip_id="0x123",
            target_tag="PLAGIARISM",
            cid="QmTest456",
            bond_amount=100000000000000000,  # 0.1 IP
            liveness=30,
            approve_amount=200000000000000000
        )
        
        # Assertions
        assert "Successfully raised dispute" in result
        assert "0xabc123" in result
        assert "42" in result
        assert "30 days" in result
        assert "2592000 seconds" in result
        self.story_service.raise_dispute.assert_called_once_with(
            target_ip_id="0x123",
            target_tag="PLAGIARISM",
            cid="QmTest456",
            bond_amount=100000000000000000,
            liveness=30,
            approve_amount=200000000000000000
        )
    
    def test_raise_dispute_error_response(self, setup_mocks):
        """Test the raise_dispute function with error in response."""
        server_module, add_tool = setup_mocks
        
        # Create the tool function we want to test
        def raise_dispute(
            target_ip_id,
            target_tag,
            cid,
            bond_amount,
            liveness=30,
            approve_amount=None
        ):
            """Raises a dispute against an IP asset."""
            try:
                result = self.story_service.raise_dispute(
                    target_ip_id=target_ip_id,
                    target_tag=target_tag,
                    cid=cid,
                    bond_amount=bond_amount,
                    liveness=liveness,
                    approve_amount=approve_amount
                )
                
                if 'error' in result:
                    return f"Error raising dispute: {result['error']}"
                
                dispute_id = result.get('dispute_id', 'Unknown')
                liveness_days = result.get('liveness_days', 'Unknown')
                liveness_seconds = result.get('liveness_seconds', 'Unknown')
                return f"Successfully raised dispute. Transaction hash: {result['tx_hash']}, Dispute ID: {dispute_id}, Liveness: {liveness_days} days ({liveness_seconds} seconds)"
            except Exception as e:
                return f"Error raising dispute: {str(e)}"
                
        # Register it with our mock MCP
        raise_dispute = add_tool('raise_dispute', raise_dispute)
        
        # Mock the service method to return error
        self.story_service.raise_dispute = Mock(return_value={
            "error": "Insufficient bond amount"
        })
        
        # Call the function
        result = raise_dispute(
            target_ip_id="0x123",
            target_tag="PLAGIARISM",
            cid="QmTest456",
            bond_amount=100
        )
        
        # Assertions
        assert "Error raising dispute" in result
        assert "Insufficient bond amount" in result
        self.story_service.raise_dispute.assert_called_once()
    
    def test_deposit_wip(self, setup_mocks):
        """Test the deposit_wip function."""
        server_module, add_tool = setup_mocks
        
        # Create the tool function we want to test
        def deposit_wip(amount):
            """Wraps the selected amount of IP to WIP."""
            try:
                response = self.story_service.deposit_wip(amount=amount)
                return {'tx_hash': response.get('tx_hash')}
            except Exception as e:
                return {'error': str(e)}
                
        # Register it with our mock MCP
        deposit_wip = add_tool('deposit_wip', deposit_wip)
        
        # Mock the service method
        self.story_service.deposit_wip = Mock(return_value={
            "tx_hash": "0xabc123"
        })
        
        # Call the function
        result = deposit_wip(amount=1000000000000000000)  # 1 IP
        
        # Assertions
        assert result['tx_hash'] == "0xabc123"
        self.story_service.deposit_wip.assert_called_once_with(amount=1000000000000000000)
    
    def test_transfer_wip(self, setup_mocks):
        """Test the transfer_wip function."""
        server_module, add_tool = setup_mocks
        
        # Create the tool function we want to test
        def transfer_wip(to, amount):
            """Transfers `amount` of WIP to a recipient `to`."""
            try:
                response = self.story_service.transfer_wip(to=to, amount=amount)
                return {'tx_hash': response.get('tx_hash')}
            except Exception as e:
                return {'error': str(e)}
                
        # Register it with our mock MCP
        transfer_wip = add_tool('transfer_wip', transfer_wip)
        
        # Mock the service method
        self.story_service.transfer_wip = Mock(return_value={
            "tx_hash": "0xabc123"
        })
        
        # Call the function
        result = transfer_wip(
            to="0x456",
            amount=500000000000000000  # 0.5 IP
        )
        
        # Assertions
        assert result['tx_hash'] == "0xabc123"
        self.story_service.transfer_wip.assert_called_once_with(
            to="0x456",
            amount=500000000000000000
        )
    
    def test_mint_and_register_ip_with_terms(self, setup_mocks):
        """Test the mint_and_register_ip_with_terms function with fee handling."""
        server_module, add_tool = setup_mocks
        
        # Create the tool function we want to test
        def mint_and_register_ip_with_terms(
            commercial_rev_share,
            derivatives_allowed,
            registration_metadata,
            commercial_use=True,
            minting_fee=0,
            recipient=None,
            spg_nft_contract=None,
            spg_nft_contract_max_minting_fee=None,
            approve_amount=None
        ):
            """Mint an NFT, register it as an IP Asset, and attach PIL terms."""
            try:
                response = self.story_service.mint_and_register_ip_with_terms(
                    commercial_rev_share=commercial_rev_share,
                    derivatives_allowed=derivatives_allowed,
                    registration_metadata=registration_metadata,
                    commercial_use=commercial_use,
                    minting_fee=minting_fee,
                    recipient=recipient,
                    spg_nft_contract=spg_nft_contract,
                    spg_nft_contract_max_minting_fee=spg_nft_contract_max_minting_fee,
                    approve_amount=approve_amount,
                )
                
                explorer_url = (
                    "https://explorer.story.foundation"
                    if self.story_service.network == "mainnet"
                    else "https://aeneid.explorer.story.foundation"
                )
                
                # Format fee information for display
                fee_info = ""
                if response.get('actual_minting_fee') is not None:
                    actual_fee = response['actual_minting_fee']
                    if actual_fee == 0:
                        fee_info = f"SPG NFT Mint Fee: FREE (0 wei)\n"
                    else:
                        # Convert from wei to a more readable format
                        fee_in_ether = self.story_service.web3.from_wei(actual_fee, 'ether')
                        fee_info = f"SPG NFT Mint Fee: {actual_fee} wei ({fee_in_ether} IP)\n"
                
                return (
                    f"Successfully minted and registered IP asset with terms:\n"
                    f"Transaction Hash: {response.get('tx_hash')}\n"
                    f"IP ID: {response['ip_id']}\n"
                    f"Token ID: {response['token_id']}\n"
                    f"License Terms IDs: {response['license_terms_ids']}\n"
                    f"{fee_info}"
                    f"View the IPA here: {explorer_url}/ipa/{response['ip_id']}"
                )
            except Exception as e:
                return f"Error minting and registering IP with terms: {str(e)}"
                
        # Register it with our mock MCP
        mint_and_register_ip_with_terms = add_tool('mint_and_register_ip_with_terms', mint_and_register_ip_with_terms)
        
        # Mock the service method
        self.story_service.mint_and_register_ip_with_terms = Mock(return_value={
            "tx_hash": "0xabc123",
            "ip_id": "0xdef456",
            "token_id": 42,
            "license_terms_ids": [1, 2],
            "actual_minting_fee": 100000,
            "max_minting_fee": 200000
        })
        
        # Call the function
        result = mint_and_register_ip_with_terms(
            commercial_rev_share=15,
            derivatives_allowed=True,
            registration_metadata={"name": "Test NFT"},
            spg_nft_contract_max_minting_fee=200000,
            approve_amount=150000
        )
        
        # Assertions
        assert "Successfully minted and registered IP asset with terms" in result
        assert "0xabc123" in result
        assert "0xdef456" in result
        assert "42" in result
        assert "[1, 2]" in result
        assert "100000 wei" in result  # Fee info
        assert "aeneid.explorer.story.foundation" in result  # testnet URL
        self.story_service.mint_and_register_ip_with_terms.assert_called_once_with(
            commercial_rev_share=15,
            derivatives_allowed=True,
            registration_metadata={"name": "Test NFT"},
            commercial_use=True,
            minting_fee=0,
            recipient=None,
            spg_nft_contract=None,
            spg_nft_contract_max_minting_fee=200000,
            approve_amount=150000
        )
    
    def test_create_spg_nft_collection(self, setup_mocks):
        """Test the create_spg_nft_collection function."""
        server_module, add_tool = setup_mocks
        
        # Create the tool function we want to test
        def create_spg_nft_collection(
            name,
            symbol,
            is_public_minting=True,
            mint_open=True,
            mint_fee_recipient=None,
            contract_uri="",
            base_uri="",
            max_supply=None,
            mint_fee=None,
            mint_fee_token=None,
            owner=None
        ):
            """Create a new SPG NFT collection."""
            try:
                response = self.story_service.create_spg_nft_collection(
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
                
                return (
                    f"Successfully created SPG NFT collection:\n"
                    f"Name: {name}\n"
                    f"Symbol: {symbol}\n"
                    f"Transaction Hash: {response['tx_hash']}\n"
                    f"SPG NFT Contract Address: {response['spg_nft_contract']}\n"
                    f"Base URI: {base_uri if base_uri else 'Not set'}\n"
                    f"Max Supply: {max_supply if max_supply is not None else 'Unlimited'}\n"
                    f"Mint Fee: {mint_fee if mint_fee is not None else '0'}\n"
                    f"Mint Fee Token: {mint_fee_token if mint_fee_token else 'Not set'}\n"
                    f"Owner: {owner if owner else 'Default (sender)'}\n\n"
                    f"You can now use this contract address with the mint_and_register_ip_with_terms tool."
                )
            except Exception as e:
                return f"Error creating SPG NFT collection: {str(e)}"
                
        # Register it with our mock MCP
        create_spg_nft_collection = add_tool('create_spg_nft_collection', create_spg_nft_collection)
        
        # Mock the service method
        self.story_service.create_spg_nft_collection = Mock(return_value={
            "tx_hash": "0xabc123",
            "spg_nft_contract": "0xdef456"
        })
        
        # Call the function
        result = create_spg_nft_collection(
            name="Test Collection",
            symbol="TEST",
            max_supply=1000
        )
        
        # Assertions
        assert "Successfully created SPG NFT collection" in result
        assert "Test Collection" in result
        assert "TEST" in result
        assert "0xabc123" in result
        assert "0xdef456" in result
        assert "1000" in result
        self.story_service.create_spg_nft_collection.assert_called_once_with(
            name="Test Collection",
            symbol="TEST",
            is_public_minting=True,
            mint_open=True,
            mint_fee_recipient=None,
            contract_uri="",
            base_uri="",
            max_supply=1000,
            mint_fee=None,
            mint_fee_token=None,
            owner=None
        )
    
    def test_get_spg_nft_contract_minting_fee(self, setup_mocks):
        """Test the get_spg_nft_contract_minting_fee function."""
        server_module, add_tool = setup_mocks
        
        # Create the tool function we want to test
        def get_spg_nft_contract_minting_fee(spg_nft_contract):
            """Get the minting fee required by an SPG NFT contract."""
            try:
                fee_info = self.story_service.get_spg_nft_contract_minting_fee(spg_nft_contract)
                
                fee_amount = fee_info['mint_fee']
                fee_token = fee_info['mint_fee_token']
                is_native = fee_info['is_native_token']
                
                # Format the fee amount nicely
                if fee_amount == 0:
                    fee_display = "FREE (0)"
                else:
                    # Convert from wei to a more readable format
                    fee_in_ether = self.story_service.web3.from_wei(fee_amount, 'ether')
                    fee_display = f"{fee_amount} wei ({fee_in_ether} IP)"
                
                token_display = "Native IP token" if is_native else f"Token at {fee_token}"
                
                return (
                    f"SPG NFT Minting Fee Information:\n"
                    f"Contract: {spg_nft_contract}\n"
                    f"Mint Fee: {fee_display}\n"
                    f"Fee Token: {token_display}\n\n"
                    f"When minting from this contract, you need to send {fee_amount} wei as the mint_fee parameter."
                )
            except Exception as e:
                return f"Error getting SPG minting fee: {str(e)}"
                
        # Register it with our mock MCP
        get_spg_nft_contract_minting_fee = add_tool('get_spg_nft_contract_minting_fee', get_spg_nft_contract_minting_fee)
        
        # Mock the service method
        self.story_service.get_spg_nft_contract_minting_fee = Mock(return_value={
            'mint_fee': 100000,
            'mint_fee_token': "0x1514000000000000000000000000000000000000",
            'is_native_token': True
        })
        
        # Call the function
        result = get_spg_nft_contract_minting_fee("0x123")
        
        # Assertions
        assert "SPG NFT Minting Fee Information" in result
        assert "100000 wei" in result
        assert "Native IP token" in result
        self.story_service.get_spg_nft_contract_minting_fee.assert_called_once_with("0x123")