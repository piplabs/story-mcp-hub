"""
Tests for the StoryService class in the story-sdk-mcp module.
"""
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.mocks.api_mocks import (
    MockResponse,
    MOCK_IPFS_HASH,
    MOCK_IPFS_URI,
    mock_pinata_upload_response
)
from tests.mocks.web3_mocks import (
    create_mock_web3,
    get_mock_license_terms,
    get_mock_mint_and_register_response,
    SAMPLE_IP_ID,
    SAMPLE_NFT_CONTRACT,
    SAMPLE_TOKEN_ID,
    SAMPLE_LICENSE_TERMS_ID
)
from utils.contract_addresses import CHAIN_IDS
sys.path.insert(0, str(project_root / "story-sdk-mcp"))
from services.story_service import StoryService
import pytest
from unittest.mock import patch, Mock, MagicMock
import os
import json
from web3 import Web3
from dotenv import load_dotenv
import os.path

# Additional imports
import os


class TestStoryService:
    """Test suite for StoryService class"""

    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Set up environment variables for testing"""
        # Load environment variables from .env.test file
        env_file = os.path.join(project_root, '.env.test')
        load_dotenv(env_file)

        # Use monkeypatch to ensure variables are set even if .env.test is missing some
        if not os.environ.get("WALLET_PRIVATE_KEY"):
            monkeypatch.setenv(
                "WALLET_PRIVATE_KEY", "mock_private_key")
        if not os.environ.get("RPC_PROVIDER_URL"):
            monkeypatch.setenv("RPC_PROVIDER_URL",
                               "https://aeneid.storyrpc.io")
        if not os.environ.get("PINATA_JWT"):
            monkeypatch.setenv("PINATA_JWT", "mock_pinata_jwt")

    @pytest.fixture
    def mock_story_client(self):
        """Create a mock StoryClient"""
        mock_client = Mock()

        # Mock License module
        mock_client.License = Mock()
        mock_client.License.get_license_terms = Mock(
            return_value=get_mock_license_terms())
        mock_client.License.mint_license_tokens = Mock(return_value={
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "license_token_ids": [1, 2, 3]
        })
        mock_client.License.attach_license_terms = Mock(return_value={
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        })

        # Mock IPAsset module
        mock_client.IPAsset = Mock()
        mock_client.IPAsset.mint_and_register_ip_asset_with_pil_terms = Mock(
            return_value=get_mock_mint_and_register_response())
        mock_client.IPAsset.register = Mock(return_value={
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "ip_id": SAMPLE_IP_ID
        })
        mock_client.IPAsset.register_derivative = Mock(return_value={
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        })

        # Mock Royalty module
        mock_client.Royalty = Mock()
        mock_client.Royalty.pay_royalty_on_behalf = Mock(return_value={
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        })
        mock_client.Royalty.claim_all_revenue = Mock(return_value={
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "tx_receipt": {"status": 1},
            "claimed_tokens": [{"token": "0x123", "amount": 1000}]
        })

        # Mock NFTClient module
        mock_client.NFTClient = Mock()
        mock_client.NFTClient.create_nft_collection = Mock(return_value={
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "nft_contract": SAMPLE_NFT_CONTRACT
        })

        # Mock Dispute module
        mock_client.Dispute = Mock()
        mock_client.Dispute.raise_dispute = Mock(return_value={
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "dispute_id": 42
        })

        # Mock WIP module
        mock_client.WIP = Mock()
        mock_client.WIP.approve = Mock(return_value={
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        })
        mock_client.WIP.allowance = Mock(return_value=1000000)
        mock_client.WIP.deposit = Mock(return_value={
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        })
        mock_client.WIP.transfer = Mock(return_value={
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        })

        return mock_client

    @pytest.fixture
    def story_service(self, mock_env, mock_web3, mock_story_client):
        """Create a StoryService instance with mocked dependencies"""
        with patch("services.story_service.Web3", return_value=mock_web3):
            with patch("services.story_service.StoryClient", return_value=mock_story_client):
                with patch("services.story_service.create_address_resolver") as mock_resolver_fn:
                    # Return a mock address resolver
                    address_resolver_mock = Mock()
                    address_resolver_mock.resolve_address = lambda addr: addr
                    mock_resolver_fn.return_value = address_resolver_mock

                    # Mock get_contracts_by_chain_id to return a contracts dictionary with LICENSE_TEMPLATE
                    with patch("services.story_service.get_contracts_by_chain_id") as mock_contracts_fn:
                        mock_contracts_fn.return_value = {
                            "PILicenseTemplate": "0x2E896b0b2Fdb7457499B56AAaA4AE55BCB4Cd316",
                            "SPG_NFT": SAMPLE_NFT_CONTRACT,
                            "RoyaltyPolicyLAP": "0xBe54FB168b3c982b7AaE60dB6CF75Bd8447b390E",
                            "DisputeModule": "0x9b7A9c70AFF961C799110954fc06F3093aeb94C5"
                        }

                        # We need to skip the web3 validation and fix the to_checksum_address functionality
                        mock_web3.is_connected.return_value = True
                        # Use the real Web3.to_checksum_address to avoid validation errors
                        mock_web3.to_checksum_address = Web3.to_checksum_address
                        mock_web3.from_wei = Web3.from_wei

                        # Get the RPC URL from environment or use fallback
                        rpc_url = os.environ.get(
                            "RPC_PROVIDER_URL", "https://aeneid.storyrpc.io")

                        service = StoryService(
                            rpc_url=rpc_url,
                            private_key=os.environ.get(
                                "WALLET_PRIVATE_KEY"),
                            network="aeneid"  # Explicitly set network to avoid chain_id detection
                        )

                        # Set the mocked client
                        service.client = mock_story_client

                        return service

    def test_init(self, mock_env):
        """Test StoryService initialization"""
        with patch("services.story_service.Web3") as mock_web3_class:
            mock_web3 = create_mock_web3()
            mock_web3_class.return_value = mock_web3
            mock_web3_class.HTTPProvider = Mock(return_value=Mock())

            with patch("services.story_service.StoryClient") as mock_story_client_class:
                with patch("services.story_service.create_address_resolver") as mock_resolver_fn:
                    # Return a mock address resolver
                    address_resolver_mock = Mock()
                    address_resolver_mock.resolve_address = lambda addr: addr
                    mock_resolver_fn.return_value = address_resolver_mock

                    # Mock get_contracts_by_chain_id to return a contracts dictionary with LICENSE_TEMPLATE
                    with patch("services.story_service.get_contracts_by_chain_id") as mock_contracts_fn:
                        mock_contracts_fn.return_value = {
                            "PILicenseTemplate": "0x2E896b0b2Fdb7457499B56AAaA4AE55BCB4Cd316",
                            "SPG_NFT": SAMPLE_NFT_CONTRACT,
                            "RoyaltyPolicyLAP": "0xBe54FB168b3c982b7AaE60dB6CF75Bd8447b390E",
                            "DisputeModule": "0x9b7A9c70AFF961C799110954fc06F3093aeb94C5"
                        }

                        # Get the RPC URL from environment or use fallback
                        rpc_url = os.environ.get(
                            "RPC_PROVIDER_URL", "https://aeneid.storyrpc.io")

                        # Test initialization
                        service = StoryService(
                            rpc_url=rpc_url,
                            private_key=os.environ.get(
                                "WALLET_PRIVATE_KEY"),
                            network="aeneid"  # Explicitly set network to avoid auto-detection
                        )

                        # Verify web3 was initialized correctly
                        mock_web3_class.HTTPProvider.assert_called_once_with(
                            rpc_url)
                        assert service.web3 is mock_web3

                        # Verify Story clients were initialized
                        mock_story_client_class.assert_called_once()

                        # Verify network and chain ID were set correctly
                        assert service.network == "aeneid"
                        assert service.chain_id == CHAIN_IDS["aeneid"]

                        # Verify IPFS is enabled
                        assert service.ipfs_enabled is True

    def test_get_license_terms(self, story_service, mock_story_client):
        """Test getting license terms"""
        # Setup mock response
        mock_story_client.License.get_license_terms.return_value = get_mock_license_terms()

        # Call the method
        result = story_service.get_license_terms(SAMPLE_LICENSE_TERMS_ID)

        # Verify the client was called correctly
        mock_story_client.License.get_license_terms.assert_called_once_with(
            SAMPLE_LICENSE_TERMS_ID)

        # Verify the result was correctly transformed
        assert result["transferable"] is True
        assert result["royaltyPolicy"] == "0x1234567890123456789012345678901234567890"
        assert result["commercialUse"] is True
        assert result["derivativesAllowed"] is True

    def test_get_license_minting_fee(self, story_service, mock_story_client):
        """Test getting license minting fee"""
        # Setup mock response
        mock_story_client.License.get_license_terms.return_value = get_mock_license_terms()

        # Call the method
        result = story_service.get_license_minting_fee(SAMPLE_LICENSE_TERMS_ID)

        # Verify the client was called correctly
        mock_story_client.License.get_license_terms.assert_called_once_with(SAMPLE_LICENSE_TERMS_ID)

        # Verify the result (defaultMintingFee is at index 2)
        assert result == 0  # From mock data

    def test_get_license_revenue_share(self, story_service, mock_story_client):
        """Test getting license revenue share"""
        # Setup mock response
        mock_story_client.License.get_license_terms.return_value = get_mock_license_terms()

        # Call the method
        result = story_service.get_license_revenue_share(SAMPLE_LICENSE_TERMS_ID)

        # Verify the client was called correctly
        mock_story_client.License.get_license_terms.assert_called_once_with(SAMPLE_LICENSE_TERMS_ID)

        # Verify the result (commercialRevShare is at index 8, divided by 10^6)
        assert result == 10 / (10 ** 6)  # 10 / 10^6 = 0.00001

    def test_mint_license_tokens(self, story_service, mock_story_client):
        """Test minting license tokens"""
        # Setup mock response
        mock_story_client.License.mint_license_tokens.return_value = {
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "license_token_ids": [1, 2, 3]
        }

        # Mock get_license_terms to return defaultMintingFee
        story_service.get_license_terms = Mock(return_value={"defaultMintingFee": 0})

        # Call the method
        result = story_service.mint_license_tokens(
            licensor_ip_id=SAMPLE_IP_ID,
            license_terms_id=SAMPLE_LICENSE_TERMS_ID,
            amount=3
        )

        # Verify the client was called correctly
        mock_story_client.License.mint_license_tokens.assert_called_once()
        args, kwargs = mock_story_client.License.mint_license_tokens.call_args
        assert kwargs["licensor_ip_id"] == SAMPLE_IP_ID
        assert kwargs["license_terms_id"] == SAMPLE_LICENSE_TERMS_ID
        assert kwargs["amount"] == 3

        # Verify the result was correctly returned
        assert result["tx_hash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        assert result["license_token_ids"] == [1, 2, 3]

        # Test with non-zero minting fee
        story_service.get_license_terms = Mock(return_value={"defaultMintingFee": 1000})
        result = story_service.mint_license_tokens(
            licensor_ip_id=SAMPLE_IP_ID,
            license_terms_id=SAMPLE_LICENSE_TERMS_ID,
            amount=1,
            max_minting_fee=2000
        )
        # Should call WIP.approve since fee > 0
        mock_story_client.WIP.approve.assert_called()

    def test_mint_and_register_ip_with_terms(self, story_service, mock_story_client):
        """Test minting and registering IP with terms including fee handling"""
        # Setup mock response
        mock_story_client.IPAsset.mint_and_register_ip_asset_with_pil_terms.return_value = get_mock_mint_and_register_response()

        # Mock get_spg_nft_minting_token to return a fee
        story_service.get_spg_nft_minting_token = Mock(return_value={
            'mint_fee': 100000,
            'mint_fee_token': "0x1514000000000000000000000000000000000000"
        })

        # Call the method with fee validation
        result = story_service.mint_and_register_ip_with_terms(
            commercial_rev_share=10,
            derivatives_allowed=True,
            registration_metadata={
                "ip_metadata_uri": "ipfs://test",
                "ip_metadata_hash": "0xabc123",
                "nft_metadata_uri": "ipfs://test",
                "nft_metadata_hash": "0xdef456"
            },
            spg_nft_contract_max_minting_fee=200000  # Higher than required fee
        )

        # Verify the client was called correctly
        mock_story_client.IPAsset.mint_and_register_ip_asset_with_pil_terms.assert_called_once()

        # Verify the result was correctly returned
        assert result["tx_hash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        assert result["ip_id"] == SAMPLE_IP_ID
        assert result["token_id"] == SAMPLE_TOKEN_ID
        assert result["license_terms_ids"] == [SAMPLE_LICENSE_TERMS_ID]
        assert result["actual_minting_fee"] == 100000
        assert result["max_minting_fee"] == 200000

        # Test validation error when max fee is too low
        with pytest.raises(ValueError) as exc_info:
            story_service.mint_and_register_ip_with_terms(
                commercial_rev_share=10,
                derivatives_allowed=True,
                registration_metadata={},
                spg_nft_contract_max_minting_fee=50000  # Lower than required fee
            )
        assert "SPG contract requires minting fee" in str(exc_info.value)

    @patch("requests.post")
    def test_upload_image_to_ipfs(self, mock_post, story_service):
        """Test uploading an image to IPFS"""
        # Setup mock response
        mock_post.return_value = mock_pinata_upload_response()

        # Call the method with bytes
        image_data = b"test image data"
        result = story_service.upload_image_to_ipfs(image_data)

        # Verify the request was made correctly
        mock_post.assert_called_once()
        assert mock_post.call_args[0][0] == "https://api.pinata.cloud/pinning/pinFileToIPFS"

        # Verify the result
        assert result == f"ipfs://{MOCK_IPFS_HASH}"

    @patch("requests.get")
    @patch("requests.post")
    def test_upload_image_to_ipfs_from_url(self, mock_post, mock_get, story_service):
        """Test uploading an image to IPFS from a URL"""
        # Setup mock responses
        mock_get.return_value = MockResponse(content=b"image data from url")
        mock_post.return_value = mock_pinata_upload_response()

        # Call the method with a URL
        image_url = "https://example.com/image.png"
        result = story_service.upload_image_to_ipfs(image_url)

        # Verify the requests were made correctly
        mock_get.assert_called_once_with(image_url)
        mock_post.assert_called_once()

        # Verify the result
        assert result == f"ipfs://{MOCK_IPFS_HASH}"

    @patch("requests.post")
    def test_create_ip_metadata(self, mock_post, story_service):
        """Test creating IP metadata"""
        # Setup mock responses
        mock_responses = [
            mock_pinata_upload_response(),  # For NFT metadata
            mock_pinata_upload_response()   # For IP metadata
        ]
        mock_post.side_effect = mock_responses

        # Call the method
        result = story_service.create_ip_metadata(
            image_uri=MOCK_IPFS_URI,
            name="Test NFT",
            description="A test NFT",
            attributes=[{"trait_type": "Rarity", "value": "Legendary"}]
        )

        # Verify the requests were made correctly
        assert mock_post.call_count == 2

        # Verify the result structure
        assert "nft_metadata" in result
        assert "ip_metadata" in result
        assert "registration_metadata" in result
        assert result["nft_metadata_uri"] == MOCK_IPFS_URI
        assert result["ip_metadata_uri"] == MOCK_IPFS_URI

    def test_register(self, story_service, mock_story_client):
        """Test registering an NFT as IP"""
        # Setup mock response
        mock_story_client.IPAsset.register.return_value = {
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "ip_id": SAMPLE_IP_ID
        }

        # Call the method
        result = story_service.register(
            nft_contract=SAMPLE_NFT_CONTRACT,
            token_id=SAMPLE_TOKEN_ID
        )

        # Verify the client was called correctly
        mock_story_client.IPAsset.register.assert_called_once()
        args, kwargs = mock_story_client.IPAsset.register.call_args
        assert kwargs["nft_contract"] == SAMPLE_NFT_CONTRACT
        assert kwargs["token_id"] == SAMPLE_TOKEN_ID

        # Verify the result
        assert result["tx_hash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        assert result["ip_id"] == SAMPLE_IP_ID

    def test_register_with_metadata(self, story_service, mock_story_client):
        """Test registering an NFT as IP with metadata"""
        # Setup mock response
        mock_story_client.IPAsset.register.return_value = {
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "ip_id": SAMPLE_IP_ID
        }

        # Create test metadata
        ip_metadata = {
            "ip_metadata_uri": MOCK_IPFS_URI,
            "ip_metadata_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "nft_metadata_uri": MOCK_IPFS_URI,
            "nft_metadata_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        }

        # Call the method
        result = story_service.register(
            nft_contract=SAMPLE_NFT_CONTRACT,
            token_id=SAMPLE_TOKEN_ID,
            ip_metadata=ip_metadata
        )

        # Verify the client was called correctly
        mock_story_client.IPAsset.register.assert_called_once()
        args, kwargs = mock_story_client.IPAsset.register.call_args
        assert kwargs["nft_contract"] == SAMPLE_NFT_CONTRACT
        assert kwargs["token_id"] == SAMPLE_TOKEN_ID
        assert kwargs["ip_metadata"]["ip_metadata_uri"] == MOCK_IPFS_URI
        assert kwargs["ip_metadata"]["ip_metadata_hash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

        # Verify the result
        assert result["tx_hash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        assert result["ip_id"] == SAMPLE_IP_ID

    def test_attach_license_terms(self, story_service, mock_story_client):
        """Test attaching license terms to an IP"""
        # Setup mock response
        mock_story_client.License.attach_license_terms.return_value = {
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        }

        # Call the method
        result = story_service.attach_license_terms(
            ip_id=SAMPLE_IP_ID,
            license_terms_id=SAMPLE_LICENSE_TERMS_ID
        )

        # Verify the client was called correctly
        mock_story_client.License.attach_license_terms.assert_called_once()
        args, kwargs = mock_story_client.License.attach_license_terms.call_args
        assert kwargs["ip_id"] == SAMPLE_IP_ID
        assert kwargs["license_terms_id"] == SAMPLE_LICENSE_TERMS_ID
        # Default LICENSE_TEMPLATE
        assert kwargs["license_template"] == "0x2E896b0b2Fdb7457499B56AAaA4AE55BCB4Cd316"

        # Verify the result
        assert result["tx_hash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    def test_attach_license_terms_with_custom_template(self, story_service, mock_story_client):
        """Test attaching license terms to an IP with a custom template"""
        # Setup mock response
        mock_story_client.License.attach_license_terms.return_value = {
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        }

        # Custom license template
        custom_template = "0x1234567890123456789012345678901234567890"

        # Call the method
        result = story_service.attach_license_terms(
            ip_id=SAMPLE_IP_ID,
            license_terms_id=SAMPLE_LICENSE_TERMS_ID,
            license_template=custom_template
        )

        # Verify the client was called correctly
        mock_story_client.License.attach_license_terms.assert_called_once()
        args, kwargs = mock_story_client.License.attach_license_terms.call_args
        assert kwargs["ip_id"] == SAMPLE_IP_ID
        assert kwargs["license_terms_id"] == SAMPLE_LICENSE_TERMS_ID
        assert kwargs["license_template"] == custom_template

        # Verify the result
        assert result["tx_hash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    # def test_register_derivative(self, story_service, mock_story_client):
    #     """Test registering a derivative IP with approve_amount"""
    #     # Setup mock response
    #     mock_story_client.IPAsset.register_derivative.return_value = {
    #         "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    #     }

    #     # Mock get_license_terms to return fees
    #     story_service.get_license_terms = Mock(return_value={"defaultMintingFee": 1000})

    #     # Call the method
    #     child_ip_id = "0xabcd1234abcd1234abcd1234abcd1234abcd1234"
    #     parent_ip_ids = [SAMPLE_IP_ID]
    #     license_terms_ids = [SAMPLE_LICENSE_TERMS_ID]

    #     result = story_service.register_derivative(
    #         child_ip_id=child_ip_id,
    #         parent_ip_ids=parent_ip_ids,
    #         license_terms_ids=license_terms_ids,
    #         approve_amount=2000
    #     )

    #     # Verify the client was called correctly
    #     mock_story_client.IPAsset.register_derivative.assert_called_once()
    #     args, kwargs = mock_story_client.IPAsset.register_derivative.call_args
    #     assert kwargs["child_ip_id"] == child_ip_id
    #     assert kwargs["parent_ip_ids"] == parent_ip_ids
    #     assert kwargs["license_terms_ids"] == license_terms_ids

    #     # Verify WIP approval was called since fee > 0
    #     mock_story_client.WIP.approve.assert_called()

    #     # Verify the result
    #     assert result["tx_hash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    #     # Test validation error for mismatched lists
    #     with pytest.raises(ValueError) as exc_info:
    #         story_service.register_derivative(
    #             child_ip_id=child_ip_id,
    #             parent_ip_ids=[SAMPLE_IP_ID, "0x123"],
    #             license_terms_ids=[SAMPLE_LICENSE_TERMS_ID]  # Only one ID
    #         )
    #     assert "must match" in str(exc_info.value)

    def test_pay_royalty_on_behalf(self, story_service, mock_story_client):
        """Test paying royalty on behalf of an IP"""
        # Setup mock response
        mock_story_client.Royalty.pay_royalty_on_behalf.return_value = {
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        }

        # Test data
        receiver_ip_id = SAMPLE_IP_ID
        payer_ip_id = "0xabcd1234abcd1234abcd1234abcd1234abcd1234"
        token = "0x1234567890123456789012345678901234567890"
        amount = 1000

        # Call the method
        result = story_service.pay_royalty_on_behalf(
            receiver_ip_id=receiver_ip_id,
            payer_ip_id=payer_ip_id,
            token=token,
            amount=amount
        )

        # Verify the client was called correctly
        mock_story_client.Royalty.pay_royalty_on_behalf.assert_called_once()
        args, kwargs = mock_story_client.Royalty.pay_royalty_on_behalf.call_args
        # Compare with checksummed addresses since the service checksums them
        assert args == (
            Web3.to_checksum_address(receiver_ip_id),
            Web3.to_checksum_address(payer_ip_id),
            Web3.to_checksum_address(token),
            amount
        )

        # Note: Since we're using a non-WIP token (0x1234...),
        # _approve_token will use ERC20 contract approval, not WIP.approve

        # Verify the result
        assert result["tx_hash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    def test_claim_all_revenue(self, story_service, mock_story_client):
        """Test claiming all revenue"""
        # Setup mock response
        mock_story_client.Royalty.claim_all_revenue.return_value = {
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "tx_receipt": {"status": 1},
            "claimed_tokens": [{"token": "0x123", "amount": 1000}]
        }

        # Mock get_license_terms to return royalty policy and currency
        mock_story_client.License.get_license_terms.return_value = [
            True,  # transferable
            "0xaaaa567890123456789012345678901234567890",  # royaltyPolicy
            0,  # defaultMintingFee
            0,  # expiration
            True,  # commercialUse
            False,  # commercialAttribution
            "0x0000000000000000000000000000000000000000",  # commercializerChecker
            b"",  # commercializerCheckerData
            10,  # commercialRevShare
            0,  # commercialRevCeiling
            True,  # derivativesAllowed
            True,  # derivativesAttribution
            False,  # derivativesApproval
            True,  # derivativesReciprocal
            0,  # derivativeRevCeiling
            "0xcccc567890123456789012345678901234567890",  # currency
            ""  # uri
        ]

        # Test data
        ancestor_ip_id = SAMPLE_IP_ID
        child_ip_ids = ["0x1234567890123456789012345678901234567890", "0x5678901234567890123456789012345678901234"]
        license_ids = [1, 2]

        # Call the method
        result = story_service.claim_all_revenue(
            ancestor_ip_id=ancestor_ip_id,
            child_ip_ids=child_ip_ids,
            license_ids=license_ids,
            auto_transfer=True,
            claimer=None
        )

        # Verify get_license_terms was called for each license_id
        assert mock_story_client.License.get_license_terms.call_count == 2
        mock_story_client.License.get_license_terms.assert_any_call(1)
        mock_story_client.License.get_license_terms.assert_any_call(2)

        # Verify the client was called correctly
        mock_story_client.Royalty.claim_all_revenue.assert_called_once()
        args, kwargs = mock_story_client.Royalty.claim_all_revenue.call_args
        assert kwargs["ancestor_ip_id"] == Web3.to_checksum_address(ancestor_ip_id)
        assert kwargs["claimer"] == story_service.account.address  # Should use default claimer
        assert kwargs["child_ip_ids"] == [Web3.to_checksum_address(child_id) for child_id in child_ip_ids]
        assert len(kwargs["royalty_policies"]) == 2
        assert len(kwargs["currency_tokens"]) == 2
        assert kwargs["claim_options"]["auto_transfer_all_claimed_tokens_from_ip"] == True

        # Verify the result
        assert result["receipt"]["status"] == 1
        assert result["claimed_tokens"][0]["token"] == "0x123"
        assert result["claimed_tokens"][0]["amount"] == 1000
        assert result["tx_hash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    def test_raise_dispute(self, story_service, mock_story_client):
        """Test raising a dispute with new CID and liveness parameters"""
        # Setup mock response
        mock_story_client.Dispute.raise_dispute.return_value = {
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "dispute_id": 42
        }

        # Test data
        target_ip_id = SAMPLE_IP_ID
        target_tag = "PLAGIARISM"
        cid = "QmbWqxBEKC3P8tqsKc98xmWNzrzDtRLMiMPL8wBuTGsMnR"
        bond_amount = 100000000000000000  # 0.1 IP in wei
        liveness = 45  # 45 days

        # Call the method
        result = story_service.raise_dispute(
            target_ip_id=target_ip_id,
            target_tag=target_tag,
            cid=cid,
            bond_amount=bond_amount,
            liveness=liveness
        )

        # Verify the client was called correctly
        mock_story_client.Dispute.raise_dispute.assert_called_once()
        args, kwargs = mock_story_client.Dispute.raise_dispute.call_args
        assert kwargs["target_ip_id"] == Web3.to_checksum_address(target_ip_id)
        assert kwargs["target_tag"] == target_tag
        assert kwargs["cid"] == cid
        assert kwargs["liveness"] == 45 * 24 * 60 * 60  # Converted to seconds
        assert kwargs["bond"] == bond_amount

        # Verify WIP approval was called since bond > 0
        mock_story_client.WIP.approve.assert_called()

        # Verify the result
        assert result["tx_hash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        assert result["dispute_id"] == 42
        assert result["bond_amount_wei"] == bond_amount
        assert result["bond_amount_ip"] == 0.1
        assert result["liveness_days"] == 45
        assert result["liveness_seconds"] == 45 * 24 * 60 * 60

        # Test validation errors
        with pytest.raises(ValueError) as exc_info:
            story_service.raise_dispute(
                target_ip_id="invalid_ip_id",  # Not a hex string
                target_tag=target_tag,
                cid=cid,
                bond_amount=bond_amount
            )
        assert "must be a hexadecimal string" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            story_service.raise_dispute(
                target_ip_id=target_ip_id,
                target_tag=target_tag,
                cid=cid,
                bond_amount=bond_amount,
                liveness=400  # > 365 days
            )
        assert "between 30 days and 1 year" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            story_service.raise_dispute(
                target_ip_id=target_ip_id,
                target_tag=target_tag,
                cid=cid,
                bond_amount=-100  # Negative amount
            )
        assert "positive integer" in str(exc_info.value)

    def test_deposit_wip(self, story_service, mock_story_client):
        """Test depositing IP to WIP"""
        # Setup mock response
        mock_story_client.WIP.deposit.return_value = {
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        }

        # Call the method
        amount = 1000000000000000000  # 1 IP in wei
        result = story_service.deposit_wip(amount=amount)

        # Verify the client was called correctly
        mock_story_client.WIP.deposit.assert_called_once_with(amount=amount)

        # Verify the result
        assert result["tx_hash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    def test_transfer_wip(self, story_service, mock_story_client):
        """Test transferring WIP tokens"""
        # Setup mock response
        mock_story_client.WIP.transfer.return_value = {
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        }

        # Test data
        to_address = "0xabcd1234abcd1234abcd1234abcd1234abcd1234"
        amount = 500000000000000000  # 0.5 IP in wei

        # Call the method
        result = story_service.transfer_wip(to=to_address, amount=amount)

        # Verify the client was called correctly
        mock_story_client.WIP.transfer.assert_called_once_with(to=to_address, amount=amount)

        # Verify the result
        assert result["tx_hash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    def test_create_spg_nft_collection(self, story_service, mock_story_client):
        """Test creating an SPG NFT collection"""
        # Setup mock response
        mock_story_client.NFTClient.create_nft_collection.return_value = {
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "nft_contract": SAMPLE_NFT_CONTRACT
        }

        # Call the method
        result = story_service.create_spg_nft_collection(
            name="Test Collection",
            symbol="TEST",
            is_public_minting=True,
            mint_open=True,
            mint_fee_recipient="0x1234567890123456789012345678901234567890",
            base_uri="https://api.example.com/metadata/",
            max_supply=10000,
            mint_fee=100000,
            mint_fee_token="0x1514000000000000000000000000000000000000",
            owner="0xabcd1234abcd1234abcd1234abcd1234abcd1234"
        )

        # Verify the client was called correctly
        mock_story_client.NFTClient.create_nft_collection.assert_called_once()
        args, kwargs = mock_story_client.NFTClient.create_nft_collection.call_args
        assert kwargs["name"] == "Test Collection"
        assert kwargs["symbol"] == "TEST"
        assert kwargs["is_public_minting"] == True
        assert kwargs["mint_open"] == True
        assert kwargs["max_supply"] == 10000
        assert kwargs["mint_fee"] == 100000

        # Verify the result
        assert result["tx_hash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        assert result["spg_nft_contract"] == SAMPLE_NFT_CONTRACT

    def test_get_spg_nft_minting_token(self, story_service):
        """Test getting SPG NFT contract minting fee and token"""
        # Mock the client method
        story_service.client.NFTClient.get_mint_fee = Mock(return_value=100000)
        story_service.client.NFTClient.get_mint_fee_token = Mock(return_value="0x1514000000000000000000000000000000000000")
        
        result = story_service.get_spg_nft_minting_token(SAMPLE_NFT_CONTRACT)
        
        # Verify the result
        assert result['mint_fee'] == 100000
        assert result['mint_fee_token'] == "0x1514000000000000000000000000000000000000"
        
        # Verify the client methods were called
        story_service.client.NFTClient.get_mint_fee.assert_called_once_with(SAMPLE_NFT_CONTRACT)
        story_service.client.NFTClient.get_mint_fee_token.assert_called_once_with(SAMPLE_NFT_CONTRACT)

    def test_approve_wip(self, story_service, mock_story_client):
        """Test the _approve_wip helper method"""
        # Setup mock response
        mock_story_client.WIP.approve.return_value = {
            "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        }
        mock_story_client.WIP.allowance.return_value = 0

        # Test with approve amount
        spender = "0x1234567890123456789012345678901234567890"
        approve_amount = 1000
        result = story_service._approve_wip(spender=spender, approve_amount=approve_amount)
        
        mock_story_client.WIP.approve.assert_called_once_with(
            spender=spender,
            amount=approve_amount,
            tx_options=None
        )
        assert result["tx_hash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    def test_predict_minting_license_fee(self, story_service, mock_story_client):
        """Test predicting minting license fee with various parameter combinations"""
        # Test case 1: Basic call with required parameters only
        mock_story_client.License.predict_minting_license_fee.return_value = {
            "currencyToken": "0x1514000000000000000000000000000000000000",
            "tokenAmount": 1000000000000000000
        }

        result = story_service.predict_minting_license_fee(
            licensor_ip_id=SAMPLE_IP_ID,
            license_terms_id=SAMPLE_LICENSE_TERMS_ID,
            amount=1
        )

        # Verify the client was called correctly
        mock_story_client.License.predict_minting_license_fee.assert_called_with(
            licensor_ip_id=SAMPLE_IP_ID,
            license_terms_id=SAMPLE_LICENSE_TERMS_ID,
            amount=1,
            license_template=None,
            receiver=None,
            tx_options=None
        )

        # Verify the result (should return SDK response directly)
        assert result["currencyToken"] == "0x1514000000000000000000000000000000000000"
        assert result["tokenAmount"] == 1000000000000000000

        # Test case 2: Call with all optional parameters
        mock_story_client.License.predict_minting_license_fee.reset_mock()
        mock_story_client.License.predict_minting_license_fee.return_value = {
            "currencyToken": "0x2514000000000000000000000000000000000000",
            "tokenAmount": 2000000000000000000
        }

        custom_template = "0x1234567890123456789012345678901234567890"
        custom_receiver = "0xabcd1234abcd1234abcd1234abcd1234abcd1234"
        tx_options = {"gasLimit": 200000}

        result = story_service.predict_minting_license_fee(
            licensor_ip_id=SAMPLE_IP_ID,
            license_terms_id=SAMPLE_LICENSE_TERMS_ID,
            amount=5,
            license_template=custom_template,
            receiver=custom_receiver,
            tx_options=tx_options
        )

        # Verify the client was called with all parameters
        mock_story_client.License.predict_minting_license_fee.assert_called_with(
            licensor_ip_id=SAMPLE_IP_ID,
            license_terms_id=SAMPLE_LICENSE_TERMS_ID,
            amount=5,
            license_template=custom_template,
            receiver=custom_receiver,
            tx_options=tx_options
        )

        # Verify the result (should return SDK response directly)
        assert result["currencyToken"] == "0x2514000000000000000000000000000000000000"
        assert result["tokenAmount"] == 2000000000000000000

        # Test case 3: Call with different amounts and license terms
        mock_story_client.License.predict_minting_license_fee.reset_mock()
        mock_story_client.License.predict_minting_license_fee.return_value = {
            "currencyToken": "0x3514000000000000000000000000000000000000",
            "tokenAmount": 5000000000000000000
        }

        result = story_service.predict_minting_license_fee(
            licensor_ip_id="0x9876543210987654321098765432109876543210",
            license_terms_id=99,
            amount=10
        )

        # Verify the client was called correctly
        mock_story_client.License.predict_minting_license_fee.assert_called_with(
            licensor_ip_id="0x9876543210987654321098765432109876543210",
            license_terms_id=99,
            amount=10,
            license_template=None,
            receiver=None,
            tx_options=None
        )

        # Verify the result (should return SDK response directly)
        assert result["currencyToken"] == "0x3514000000000000000000000000000000000000"
        assert result["tokenAmount"] == 5000000000000000000

        # Test case 4: Response with missing fields (edge case)
        mock_story_client.License.predict_minting_license_fee.reset_mock()
        mock_story_client.License.predict_minting_license_fee.return_value = {
            "currencyToken": "0x4514000000000000000000000000000000000000"
            # Missing tokenAmount
        }

        result = story_service.predict_minting_license_fee(
            licensor_ip_id=SAMPLE_IP_ID,
            license_terms_id=SAMPLE_LICENSE_TERMS_ID,
            amount=1
        )

        # Verify the response is returned as-is (no transformation)
        assert result["currencyToken"] == "0x4514000000000000000000000000000000000000"
        assert "tokenAmount" not in result

        # Test case 5: Empty response (edge case)
        mock_story_client.License.predict_minting_license_fee.reset_mock()
        mock_story_client.License.predict_minting_license_fee.return_value = {}

        result = story_service.predict_minting_license_fee(
            licensor_ip_id=SAMPLE_IP_ID,
            license_terms_id=SAMPLE_LICENSE_TERMS_ID,
            amount=1
        )

        # Verify the empty response is returned as-is
        assert result == {}

        # Test case 6: Large amounts
        mock_story_client.License.predict_minting_license_fee.reset_mock()
        mock_story_client.License.predict_minting_license_fee.return_value = {
            "currencyToken": "0x5514000000000000000000000000000000000000",
            "tokenAmount": 1000000000000000000000  # Large amount
        }

        result = story_service.predict_minting_license_fee(
            licensor_ip_id=SAMPLE_IP_ID,
            license_terms_id=SAMPLE_LICENSE_TERMS_ID,
            amount=1000
        )

        # Verify the client was called correctly with large amount
        mock_story_client.License.predict_minting_license_fee.assert_called_with(
            licensor_ip_id=SAMPLE_IP_ID,
            license_terms_id=SAMPLE_LICENSE_TERMS_ID,
            amount=1000,
            license_template=None,
            receiver=None,
            tx_options=None
        )

        # Verify the result with large token amount (should return SDK response directly)
        assert result["currencyToken"] == "0x5514000000000000000000000000000000000000"
        assert result["tokenAmount"] == 1000000000000000000000
