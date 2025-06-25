"""
Tests for the StoryService class in the story-sdk-mcp module.
"""
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
from services.story_service import StoryService
import pytest
from unittest.mock import patch, Mock, MagicMock
import os
import json
from web3 import Web3
from dotenv import load_dotenv
import os.path

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

# Use a simpler approach that doesn't rely on the Python package
sys.path.append(str(project_root / "story-sdk-mcp"))
sys.path.append(str(project_root / "tests"))


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
        mock_client.License.getLicenseTerms = Mock(
            return_value=get_mock_license_terms())
        mock_client.License.mintLicenseTokens = Mock(return_value={
            "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "licenseTokenIds": [1, 2, 3]
        })
        mock_client.License.attachLicenseTerms = Mock(return_value={
            "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        })

        # Mock IPAsset module
        mock_client.IPAsset = Mock()
        mock_client.IPAsset.mintAndRegisterIpAssetWithPilTerms = Mock(
            return_value=get_mock_mint_and_register_response())
        mock_client.IPAsset.register = Mock(return_value={
            "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "ipId": SAMPLE_IP_ID
        })
        mock_client.IPAsset.registerDerivative = Mock(return_value={
            "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        })

        # Mock Royalty module
        mock_client.Royalty = Mock()
        mock_client.Royalty.payRoyaltyOnBehalf = Mock(return_value={
            "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        })
        mock_client.Royalty.claimRevenue = Mock(return_value={
            "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "claimableToken": 1000
        })

        return mock_client

    @pytest.fixture
    def mock_nft_client(self):
        """Create a mock NFTClient"""
        mock_nft_client = Mock()

        mock_nft_client.createNFTCollection = Mock(return_value={
            "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "nftContract": SAMPLE_NFT_CONTRACT
        })

        return mock_nft_client

    @pytest.fixture
    def story_service(self, mock_env, mock_web3, mock_story_client, mock_nft_client):
        """Create a StoryService instance with mocked dependencies"""
        with patch("services.story_service.Web3", return_value=mock_web3):
            with patch("services.story_service.StoryClient", return_value=mock_story_client):
                with patch("services.story_service.NFTClient", return_value=mock_nft_client):
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

                            # Get the RPC URL from environment or use fallback
                            rpc_url = os.environ.get(
                                "RPC_PROVIDER_URL", "https://aeneid.storyrpc.io")

                            service = StoryService(
                                rpc_url=rpc_url,
                                private_key=os.environ.get(
                                    "WALLET_PRIVATE_KEY"),
                                network="aeneid"  # Explicitly set network to avoid chain_id detection
                            )

                            return service

    def test_init(self, mock_env):
        """Test StoryService initialization"""
        with patch("services.story_service.Web3") as mock_web3_class:
            mock_web3 = create_mock_web3()
            mock_web3_class.return_value = mock_web3
            mock_web3_class.HTTPProvider = Mock(return_value=Mock())

            with patch("services.story_service.StoryClient") as mock_story_client_class:
                with patch("services.story_service.NFTClient") as mock_nft_client_class:
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
                            mock_nft_client_class.assert_called_once()

                            # Verify network and chain ID were set correctly
                            assert service.network == "aeneid"
                            assert service.chain_id == CHAIN_IDS["aeneid"]

                            # Verify IPFS is enabled
                            assert service.ipfs_enabled is True

    def test_get_license_terms(self, story_service, mock_story_client):
        """Test getting license terms"""
        # Setup mock response
        mock_story_client.License.getLicenseTerms.return_value = get_mock_license_terms()

        # Call the method
        result = story_service.get_license_terms(SAMPLE_LICENSE_TERMS_ID)

        # Verify the client was called correctly
        mock_story_client.License.getLicenseTerms.assert_called_once_with(
            SAMPLE_LICENSE_TERMS_ID)

        # Verify the result was correctly transformed
        assert result["transferable"] is True
        assert result["royaltyPolicy"] == "0x1234567890123456789012345678901234567890"
        assert result["commercialUse"] is True
        assert result["derivativesAllowed"] is True

    def test_mint_license_tokens(self, story_service, mock_story_client):
        """Test minting license tokens"""
        # Setup mock response
        mock_story_client.License.mintLicenseTokens.return_value = {
            "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "licenseTokenIds": [1, 2, 3]
        }

        # Call the method
        result = story_service.mint_license_tokens(
            licensor_ip_id=SAMPLE_IP_ID,
            license_terms_id=SAMPLE_LICENSE_TERMS_ID,
            amount=3
        )

        # Verify the client was called correctly
        mock_story_client.License.mintLicenseTokens.assert_called_once()
        args, kwargs = mock_story_client.License.mintLicenseTokens.call_args
        assert kwargs["licensor_ip_id"] == SAMPLE_IP_ID
        assert kwargs["license_terms_id"] == SAMPLE_LICENSE_TERMS_ID
        assert kwargs["amount"] == 3

        # Verify the result was correctly returned
        assert result["txHash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        assert result["licenseTokenIds"] == [1, 2, 3]

    def test_mint_and_register_ip_with_terms(self, story_service, mock_story_client):
        """Test minting and registering IP with terms"""
        # Setup mock response
        mock_story_client.IPAsset.mintAndRegisterIpAssetWithPilTerms.return_value = get_mock_mint_and_register_response()

        # Call the method
        result = story_service.mint_and_register_ip_with_terms(
            commercial_rev_share=10,
            derivatives_allowed=True
        )

        # Verify the client was called correctly
        mock_story_client.IPAsset.mintAndRegisterIpAssetWithPilTerms.assert_called_once()

        # Verify the result was correctly returned
        assert result["txHash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        assert result["ipId"] == SAMPLE_IP_ID
        assert result["tokenId"] == SAMPLE_TOKEN_ID
        assert result["licenseTermsIds"] == [SAMPLE_LICENSE_TERMS_ID]

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
            "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "ipId": SAMPLE_IP_ID
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
        assert result["txHash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        assert result["ipId"] == SAMPLE_IP_ID

    def test_register_with_metadata(self, story_service, mock_story_client):
        """Test registering an NFT as IP with metadata"""
        # Setup mock response
        mock_story_client.IPAsset.register.return_value = {
            "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "ipId": SAMPLE_IP_ID
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
        assert result["txHash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        assert result["ipId"] == SAMPLE_IP_ID

    def test_attach_license_terms(self, story_service, mock_story_client):
        """Test attaching license terms to an IP"""
        # Setup mock response
        mock_story_client.License.attachLicenseTerms.return_value = {
            "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        }

        # Call the method
        result = story_service.attach_license_terms(
            ip_id=SAMPLE_IP_ID,
            license_terms_id=SAMPLE_LICENSE_TERMS_ID
        )

        # Verify the client was called correctly
        mock_story_client.License.attachLicenseTerms.assert_called_once()
        args, kwargs = mock_story_client.License.attachLicenseTerms.call_args
        assert kwargs["ip_id"] == SAMPLE_IP_ID
        assert kwargs["license_terms_id"] == SAMPLE_LICENSE_TERMS_ID
        # Default LICENSE_TEMPLATE
        assert kwargs["license_template"] == "0x2E896b0b2Fdb7457499B56AAaA4AE55BCB4Cd316"

        # Verify the result
        assert result["txHash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    def test_attach_license_terms_with_custom_template(self, story_service, mock_story_client):
        """Test attaching license terms to an IP with a custom template"""
        # Setup mock response
        mock_story_client.License.attachLicenseTerms.return_value = {
            "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
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
        mock_story_client.License.attachLicenseTerms.assert_called_once()
        args, kwargs = mock_story_client.License.attachLicenseTerms.call_args
        assert kwargs["ip_id"] == SAMPLE_IP_ID
        assert kwargs["license_terms_id"] == SAMPLE_LICENSE_TERMS_ID
        assert kwargs["license_template"] == custom_template

        # Verify the result
        assert result["txHash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    def test_register_derivative(self, story_service, mock_story_client):
        """Test registering a derivative IP"""
        # Setup mock response
        mock_story_client.IPAsset.registerDerivative.return_value = {
            "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        }

        # Call the method
        child_ip_id = "0xabcd1234abcd1234abcd1234abcd1234abcd1234"
        parent_ip_ids = [SAMPLE_IP_ID]
        license_terms_ids = [SAMPLE_LICENSE_TERMS_ID]

        result = story_service.register_derivative(
            child_ip_id=child_ip_id,
            parent_ip_ids=parent_ip_ids,
            license_terms_ids=license_terms_ids
        )

        # Verify the client was called correctly
        mock_story_client.IPAsset.registerDerivative.assert_called_once()
        args, kwargs = mock_story_client.IPAsset.registerDerivative.call_args
        assert kwargs["child_ip_id"] == child_ip_id
        assert kwargs["parent_ip_ids"] == parent_ip_ids
        assert kwargs["license_terms_ids"] == license_terms_ids

        # Verify the result
        assert result["txHash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    def test_pay_royalty_on_behalf(self, story_service, mock_story_client):
        """Test paying royalty on behalf of an IP"""
        # Setup mock response
        mock_story_client.Royalty.payRoyaltyOnBehalf.return_value = {
            "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
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
        mock_story_client.Royalty.payRoyaltyOnBehalf.assert_called_once()
        args, kwargs = mock_story_client.Royalty.payRoyaltyOnBehalf.call_args
        assert kwargs["receiver_ip_id"] == receiver_ip_id
        assert kwargs["payer_ip_id"] == payer_ip_id
        assert kwargs["token"] == token
        assert kwargs["amount"] == amount

        # Verify the result
        assert result["txHash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    def test_claim_revenue(self, story_service, mock_story_client):
        """Test claiming revenue from snapshots"""
        # Setup mock response
        mock_story_client.Royalty.claimRevenue.return_value = {
            "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "claimableToken": 1000
        }

        # Test data
        snapshot_ids = [1, 2, 3]
        child_ip_id = "0xabcd1234abcd1234abcd1234abcd1234abcd1234"
        token = "0x1234567890123456789012345678901234567890"

        # Call the method
        result = story_service.claim_revenue(
            snapshot_ids=snapshot_ids,
            child_ip_id=child_ip_id,
            token=token
        )

        # Verify the client was called correctly
        mock_story_client.Royalty.claimRevenue.assert_called_once()
        args, kwargs = mock_story_client.Royalty.claimRevenue.call_args
        assert kwargs["snapshot_ids"] == snapshot_ids
        assert kwargs["child_ip_id"] == child_ip_id
        assert kwargs["token"] == token

        # Verify the result
        assert result["txHash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        assert result["claimableToken"] == 1000

    @patch("story_protocol_python_sdk.abi.DisputeModule.DisputeModule_client.DisputeModuleClient")
    @patch("story_protocol_python_sdk.utils.transaction_utils.build_and_send_transaction")
    def test_raise_dispute(self, mock_build_and_send, mock_dispute_client_class, story_service, mock_web3):
        """Test raising a dispute against an IP asset"""
        # Setup mock response for transaction
        mock_tx_receipt = {
            "txHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "txReceipt": {
                "logs": [
                    {
                        "topics": [
                            mock_web3.keccak(
                                text="DisputeRaised(uint256,address,bytes32,string)"),
                            # Mock dispute ID encoded as bytes32
                            "0x0000000000000000000000000000000000000000000000000000000000000001"
                        ]
                    }
                ]
            }
        }
        mock_build_and_send.return_value = mock_tx_receipt

        # Mock dispute client
        mock_dispute_client = Mock()
        mock_dispute_client_class.return_value = mock_dispute_client
        mock_dispute_client.build_raiseDispute_transaction = Mock()

        # Test data
        target_ip_id = SAMPLE_IP_ID
        dispute_evidence_hash = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        target_tag = "copyright"
        data = "0x1234"

        # Call the method with a patch for the _parse_dispute_id_from_logs method
        with patch.object(story_service, '_parse_dispute_id_from_logs', return_value=1):
            result = story_service.raise_dispute(
                target_ip_id=target_ip_id,
                dispute_evidence_hash=dispute_evidence_hash,
                target_tag=target_tag,
                data=data
            )

        # Verify the transaction was built and sent correctly
        mock_build_and_send.assert_called_once()

        # Verify the result
        assert result["txHash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        assert result["disputeId"] == 1

    @pytest.mark.parametrize(
        "target_tag,data,dispute_id",[
            ("0XDEADBEEF","0XCAFEBABE",42),   # hex-prefixed (upper-case) – should be converted to bytes
            ("copyright","CAFEBABE",99)        # no prefix – should remain unchanged
        ]
    )
    def test_raise_dispute_prefix_variations(self, story_service, mock_web3, target_tag, data, dispute_id):
        """Ensure raise_dispute handles different data/target_tag prefix cases correctly."""
        with patch("story_protocol_python_sdk.utils.transaction_utils.build_and_send_transaction") as mock_send, \
             patch("story_protocol_python_sdk.abi.DisputeModule.DisputeModule_client.DisputeModuleClient") as mock_dispute_client_class:
            mock_send.return_value = {
                "txHash": "0xfeedfacefeedfacefeedfacefeedfacefeedfacefeedfacefeedfacefeedface",
                "txReceipt": {"logs": []}
            }

            mock_dispute_client_class.return_value.build_raiseDispute_transaction = Mock()

            with patch.object(story_service, "_parse_dispute_id_from_logs", return_value=dispute_id):
                target_ip_id = "0xabcabcabcabcabcabcabcabcabcabcabcabcabcabcabcabcabcabcabcabcabcd"
                dispute_evidence_hash = "0xdefdefdefdefdefdefdefdefdefdefdefdefdefdefdefdefdefdefdefdefdef"

                result = story_service.raise_dispute(
                    target_ip_id=target_ip_id,
                    dispute_evidence_hash=dispute_evidence_hash,
                    target_tag=target_tag,
                    data=data
                )

        # Exactly one tx build call
        mock_send.assert_called_once()

        called_args = mock_send.call_args[0]
        forwarded_data = called_args[-1]

        if data.lower().startswith("0x"):
            # Prefixed inputs should be converted away from raw string
            assert not isinstance(forwarded_data, str)
        else:
            assert forwarded_data == data  # unchanged

        assert result["disputeId"] == dispute_id
        assert result["txHash"].lower().startswith("0x")
