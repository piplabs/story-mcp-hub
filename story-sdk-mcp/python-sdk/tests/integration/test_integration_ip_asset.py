# tests/integration/test_integration_ip_asset.py

import pytest
from web3 import Web3

from setup_for_integration import (
    web3,
    account, 
    story_client,
    get_token_id,
    MockERC721,
    MockERC20,
    ZERO_ADDRESS,
    ROYALTY_POLICY,
    PIL_LICENSE_TEMPLATE,
    WIP_TOKEN_ADDRESS,
    mint_by_spg
)

class TestIPAssetRegistration:
    @pytest.fixture(scope="module")
    def child_ip_id(self, story_client):
        token_id = get_token_id(MockERC721, story_client.web3, story_client.account)

        response = story_client.IPAsset.register(
            nft_contract=MockERC721,
            token_id=token_id
        )

        assert 'tx_hash' in response
        assert isinstance(response['tx_hash'], str)

        assert response is not None
        assert 'ip_id' in response
        assert response['ip_id'] is not None
        return response['ip_id']

    def test_register_ip_asset(self, story_client, child_ip_id):
        assert child_ip_id is not None

    def test_register_ip_asset_with_metadata(self, story_client):
        token_id = get_token_id(MockERC721, story_client.web3, story_client.account)
        metadata = {
            'ip_metadata_uri': "test-uri",
            'ip_metadata_hash': web3.to_hex(web3.keccak(text="test-metadata-hash")),
            'nft_metadata_uri': "test-nft-uri",
            'nft_metadata_hash': web3.to_hex(web3.keccak(text="test-nft-metadata-hash"))
        }

        response = story_client.IPAsset.register(
            nft_contract=MockERC721,
            token_id=token_id,
            ip_metadata=metadata,
            deadline=1000
        )

        assert 'tx_hash' in response
        assert isinstance(response['tx_hash'], str)

        assert response is not None
        assert 'ip_id' in response
        assert response['ip_id'] is not None
        assert isinstance(response['ip_id'], str)

class TestIPAssetDerivatives:
    @pytest.fixture(scope="module")
    def child_ip_id(self, story_client):
        token_id = get_token_id(MockERC721, story_client.web3, story_client.account)

        response = story_client.IPAsset.register(
            nft_contract=MockERC721,
            token_id=token_id
        )

        assert 'tx_hash' in response
        assert isinstance(response['tx_hash'], str)

        assert response is not None
        assert 'ip_id' in response
        assert response['ip_id'] is not None
        return response['ip_id']
    
    @pytest.fixture(scope="module")
    def non_commercial_license(self, story_client):
        license_register_response = story_client.License.register_non_com_social_remixing_pil()
        no_commercial_license_terms_id = license_register_response['license_terms_id']
        return no_commercial_license_terms_id

    @pytest.fixture(scope="module")
    def parent_ip_id(self, story_client, non_commercial_license):
        token_id = get_token_id(MockERC721, story_client.web3, story_client.account)
        response = story_client.IPAsset.register(
            nft_contract=MockERC721,
            token_id=token_id
        )

        attach_license_response = story_client.License.attach_license_terms(response['ip_id'], PIL_LICENSE_TEMPLATE, non_commercial_license)

        return response['ip_id']

    def test_register_derivative(self, story_client, child_ip_id, parent_ip_id, non_commercial_license):
        response = story_client.IPAsset.register_derivative(
            child_ip_id=child_ip_id,
            parent_ip_ids=[parent_ip_id],
            license_terms_ids=[non_commercial_license],
            max_minting_fee=0,
            max_rts=5 * 10 ** 6,
            max_revenue_share=0,
        )
        
        assert response is not None
        assert 'tx_hash' in response
        assert response['tx_hash'] is not None
        assert isinstance(response['tx_hash'], str)
        assert len(response['tx_hash']) > 0

    def test_register_derivative_with_license_tokens(self, story_client, parent_ip_id, non_commercial_license):
        token_id = get_token_id(MockERC721, story_client.web3, story_client.account)
        child_response = story_client.IPAsset.register(
            nft_contract=MockERC721,
            token_id=token_id
        )
        child_ip_id = child_response['ip_id']

        license_token_response = story_client.License.mint_license_tokens(
            licensor_ip_id=parent_ip_id, 
            license_template=PIL_LICENSE_TEMPLATE, 
            license_terms_id=non_commercial_license, 
            amount=1,
            receiver=account.address,
            max_minting_fee=0,
            max_revenue_share=1
        )
        license_token_ids = license_token_response['license_token_ids']

        response = story_client.IPAsset.register_derivative_with_license_tokens(
            child_ip_id=child_ip_id,
            license_token_ids=license_token_ids,
            max_rts=5 * 10 ** 6
        )
        
        assert response is not None
        assert 'tx_hash' in response
        assert response['tx_hash'] is not None
        assert isinstance(response['tx_hash'], str)
        assert len(response['tx_hash']) > 0

class TestIPAssetMinting:
    @pytest.fixture(scope="module")
    def nft_collection(self, story_client):
        tx_data = story_client.NFTClient.create_nft_collection(
            name="test-collection",
            symbol="TEST",
            max_supply=100,
            is_public_minting=True,
            mint_open=True,
            contract_uri="test-uri",
            mint_fee_recipient=account.address,
        )
        return tx_data['nft_contract']

    def test_mint_register_attach_terms(self, story_client, nft_collection):
        metadata = {
            'ip_metadata_uri': "test-uri",
            'ip_metadata_hash': web3.to_hex(web3.keccak(text="test-metadata-hash")),
            'nft_metadata_uri': "test-nft-uri",
            'nft_metadata_hash': web3.to_hex(web3.keccak(text="test-nft-metadata-hash"))
        }

        response = story_client.IPAsset.mint_and_register_ip_asset_with_pil_terms(
            spg_nft_contract=nft_collection,
            terms=[{
                'terms': {
                    'transferable': True,
                    'royalty_policy': ROYALTY_POLICY,
                    'default_minting_fee': 1,
                    'expiration': 0,
                    'commercial_use': True,
                    'commercial_attribution': False,
                    'commercializer_checker': ZERO_ADDRESS,
                    'commercializer_checker_data': ZERO_ADDRESS,
                    'commercial_rev_share': 90,
                    'commercial_rev_ceiling': 0,
                    'derivatives_allowed': True,
                    'derivatives_attribution': True,
                    'derivatives_approval': False,
                    'derivatives_reciprocal': True,
                    'derivative_rev_ceiling': 0,
                    'currency': MockERC20,
                    'uri': ""
                },
                'licensing_config': {
                    'is_set': True,
                    'minting_fee': 1,
                    'hook_data': "",
                    'licensing_hook': ZERO_ADDRESS,
                    'commercial_rev_share': 90,
                    'disabled': False,
                    'expect_minimum_group_reward_share': 0,
                    'expect_group_reward_pool': ZERO_ADDRESS
                }
            }],
            ip_metadata=metadata
        )

        assert 'tx_hash' in response
        assert isinstance(response['tx_hash'], str)

        assert 'ip_id' in response
        assert isinstance(response['ip_id'], str)
        assert response['ip_id'].startswith("0x")

        assert 'token_id' in response
        assert isinstance(response['token_id'], int)

        assert 'license_terms_ids' in response
        assert isinstance(response['license_terms_ids'], list)
        assert all(isinstance(id, int) for id in response['license_terms_ids'])

    def test_mint_register_ip(self, story_client, nft_collection):
        metadata = {
            'ip_metadata_uri': "test-uri",
            'ip_metadata_hash': web3.to_hex(web3.keccak(text="test-metadata-hash")),
            'nft_metadata_uri': "test-nft-uri",
            'nft_metadata_hash': web3.to_hex(web3.keccak(text="test-nft-metadata-hash"))
        }
        
        response = story_client.IPAsset.mint_and_register_ip(
            spg_nft_contract=nft_collection,
            ip_metadata=metadata
        )

class TestSPGNFTOperations:
    @pytest.fixture(scope="module")
    def nft_collection(self, story_client):
        tx_data = story_client.NFTClient.create_nft_collection(
            name="test-collection",
            symbol="TEST",
            max_supply=100,
            is_public_minting=True,
            mint_open=True,
            contract_uri="test-uri",
            mint_fee_recipient=account.address,
        )
        return tx_data['nft_contract']

    @pytest.fixture(scope="module")
    def parent_ip_and_license_terms(self, story_client, nft_collection):
        response = story_client.IPAsset.mint_and_register_ip_asset_with_pil_terms(
            spg_nft_contract=nft_collection,
            terms=[{
                'terms': {
                    'transferable': True,
                    'royalty_policy': ROYALTY_POLICY,
                    'default_minting_fee': 0,
                    'expiration': 0,
                    'commercial_use': True,
                    'commercial_attribution': False,
                    'commercializer_checker': ZERO_ADDRESS,
                    'commercializer_checker_data': ZERO_ADDRESS,
                    'commercial_rev_share': 90,
                    'commercial_rev_ceiling': 0,
                    'derivatives_allowed': True,
                    'derivatives_attribution': True,
                    'derivatives_approval': False,
                    'derivatives_reciprocal': True,
                    'derivative_rev_ceiling': 0,
                    'currency': MockERC20,
                    'uri': ""
                },
                'licensing_config': {
                    'is_set': True,
                    'minting_fee': 0,
                    'hook_data': ZERO_ADDRESS,
                    'licensing_hook': ZERO_ADDRESS,
                    'commercial_rev_share': 0,
                    'disabled': False,
                    'expect_minimum_group_reward_share': 0,
                    'expect_group_reward_pool': ZERO_ADDRESS
                }
            }]
        )

        return {
            'parent_ip_id': response['ip_id'],
            'license_terms_id': response['license_terms_ids'][0]
        }
    # def test_register_ip_asset_with_metadata(self, story_client, nft_collection):
    #     token_id = mint_by_spg(nft_collection, story_client.web3, story_client.account, "test-metadata")

    #     response = story_client.IPAsset.register(
    #         nft_contract=nft_collection,
    #         token_id=token_id,
    #         ip_metadata={
    #             'ip_metadata_uri': "test-uri",
    #             'ip_metadata_hash': web3.to_hex(web3.keccak(text="test-metadata-hash")),
    #             'nft_metadata_hash': web3.to_hex(web3.keccak(text="test-nft-metadata-hash"))
    #         },
    #         deadline=1000
    #     )

    #     assert 'ip_id' in response
    #     assert isinstance(response['ip_id'], str)
    #     assert response['ip_id'] != ''

    # def test_register_derivative_ip(self, story_client, parent_ip_id, license_terms_id):
    #     token_child_id = mint_by_spg(MockERC721, story_client.web3, story_client.account)
        
    #     result = story_client.IPAsset.register_derivative_ip(
    #         nft_contract=MockERC721,
    #         token_id=token_child_id,
    #         deriv_data={
    #             'parentIpIds': [parent_ip_id],
    #             'licenseTermsIds': [license_terms_id],
    #             'maxMintingFee': 0,
    #             'maxRts': 5 * 10**6,
    #             'maxRevenueShare': 0
    #         },
    #         deadline=1000,
    #         tx_options={'waitForTransaction': True}
    #     )

    #     assert isinstance(result['tx_hash'], str) and result['tx_hash']
    #     assert isinstance(result['ip_id'], str) and result['ip_id']

    def test_register_ip_and_attach_pil_terms(self, story_client, nft_collection, parent_ip_and_license_terms):
        token_id = mint_by_spg(nft_collection, story_client.web3, story_client.account)

        # Register IP and attach PIL terms
        result = story_client.IPAsset.register_ip_and_attach_pil_terms(
            nft_contract=nft_collection,
            token_id=token_id,
            deadline=1000,
            license_terms_data=[
                {
                    'terms': {
                        'transferable': True,
                        'royalty_policy': ZERO_ADDRESS,
                        'default_minting_fee': 0,
                        'expiration': 0,
                        'commercial_use': False,
                        'commercial_attribution': False,
                        'commercializer_checker': ZERO_ADDRESS,
                        'commercializer_checker_data': ZERO_ADDRESS,
                        'commercial_rev_share': 0,
                        'commercial_rev_ceiling': 0,
                        'derivatives_allowed': True,
                        'derivatives_attribution': True,
                        'derivatives_approval': False,
                        'derivatives_reciprocal': True,
                        'derivative_rev_ceiling': 0,
                        'currency': WIP_TOKEN_ADDRESS,
                        'uri': '',
                    },
                    'licensing_config': {
                        'is_set': True,
                        'minting_fee': 0,
                        'licensing_hook': ZERO_ADDRESS,
                        'hook_data': ZERO_ADDRESS,
                        'commercial_rev_share': 0,
                        'disabled': False,
                        'expect_minimum_group_reward_share': 0,
                        'expect_group_reward_pool': ZERO_ADDRESS,
                    }
                },
                {
                    'terms': {
                        'transferable': True,
                        'royalty_policy': ROYALTY_POLICY,
                        'default_minting_fee': 10000,
                        'expiration': 1000,
                        'commercial_use': True,
                        'commercial_attribution': False,
                        'commercializer_checker': ZERO_ADDRESS,
                        'commercializer_checker_data': ZERO_ADDRESS,
                        'commercial_rev_share': 0,
                        'commercial_rev_ceiling': 0,
                        'derivatives_allowed': True,
                        'derivatives_attribution': True,
                        'derivatives_approval': False,
                        'derivatives_reciprocal': True,
                        'derivative_rev_ceiling': 0,
                        'currency': WIP_TOKEN_ADDRESS,
                        'uri': 'test case',
                    },
                    'licensing_config': {
                        'is_set': True,
                        'minting_fee': 10000,
                        'licensing_hook': ZERO_ADDRESS,
                        'hook_data': ZERO_ADDRESS,
                        'commercial_rev_share': 0,
                        'disabled': False,
                        'expect_minimum_group_reward_share': 0,
                        'expect_group_reward_pool': ZERO_ADDRESS,
                    }
                }
            ]
        )

        assert isinstance(result['tx_hash'], str) and result['tx_hash']
        assert isinstance(result['ip_id'], str) and result['ip_id']
        assert isinstance(result['license_terms_ids'], list) and result['license_terms_ids']
        
# Add this test class to your existing test_integration_ip_asset.py file

class TestIPAssetMint:
    @pytest.fixture(scope="module")
    def nft_collection(self, story_client):
        tx_data = story_client.NFTClient.create_nft_collection(
            name="test-mint-collection",
            symbol="MINT",
            max_supply=100,
            is_public_minting=True,
            mint_open=True,
            contract_uri="test-mint-uri",
            mint_fee_recipient=account.address,
        )
        return tx_data['nft_contract']

    def test_mint_basic(self, story_client, nft_collection):
        """Test basic minting functionality"""
        metadata_uri = "https://example.com/metadata/1.json"
        metadata_hash = web3.keccak(text="test-metadata-content")
        
        response = story_client.IPAsset.mint(
            nft_contract=nft_collection,
            to_address=account.address,
            metadata_uri=metadata_uri,
            metadata_hash=metadata_hash,
            allow_duplicates=False
        )
        
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert response.startswith("0x")
        
        # Wait for transaction confirmation to verify it was successful
        receipt = story_client.web3.eth.wait_for_transaction_receipt(response)
        assert receipt.status == 1

    def test_mint_with_duplicates_allowed(self, story_client, nft_collection):
        """Test minting with duplicate metadata allowed"""
        metadata_uri = "https://example.com/metadata/duplicate.json"
        metadata_hash = web3.keccak(text="duplicate-metadata-content")
        
        # First mint
        response1 = story_client.IPAsset.mint(
            nft_contract=nft_collection,
            to_address=account.address,
            metadata_uri=metadata_uri,
            metadata_hash=metadata_hash,
            allow_duplicates=True
        )
        
        assert response1 is not None
        receipt1 = story_client.web3.eth.wait_for_transaction_receipt(response1)
        assert receipt1.status == 1
        
        # Second mint with same metadata (should succeed with allow_duplicates=True)
        response2 = story_client.IPAsset.mint(
            nft_contract=nft_collection,
            to_address=account.address,
            metadata_uri=metadata_uri,
            metadata_hash=metadata_hash,
            allow_duplicates=True
        )
        
        assert response2 is not None
        receipt2 = story_client.web3.eth.wait_for_transaction_receipt(response2)
        assert receipt2.status == 1
        
        # Verify different transaction hashes
        assert response1 != response2

    def test_mint_to_different_address(self, story_client, nft_collection):
        """Test minting to a different recipient address"""
        # Create a different recipient address for testing
        different_account = story_client.web3.eth.account.create()
        recipient_address = different_account.address
        
        metadata_uri = "https://example.com/metadata/different-recipient.json"
        metadata_hash = web3.keccak(text="different-recipient-metadata")
        
        response = story_client.IPAsset.mint(
            nft_contract=nft_collection,
            to_address=recipient_address,
            metadata_uri=metadata_uri,
            metadata_hash=metadata_hash,
            allow_duplicates=False
        )
        
        assert response is not None
        receipt = story_client.web3.eth.wait_for_transaction_receipt(response)
        assert receipt.status == 1

    def test_mint_with_various_metadata_formats(self, story_client, nft_collection):
        """Test minting with different metadata URI formats"""
        test_cases = [
            {
                "uri": "ipfs://QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG",
                "content": "ipfs-metadata"
            },
            {
                "uri": "https://gateway.pinata.cloud/ipfs/QmTest123",
                "content": "pinata-gateway-metadata"
            },
            {
                "uri": "ar://abc123def456",
                "content": "arweave-metadata"
            },
            {
                "uri": "",  # Empty URI
                "content": "empty-uri-metadata"
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            metadata_hash = web3.keccak(text=f"{test_case['content']}-{i}")
            
            response = story_client.IPAsset.mint(
                nft_contract=nft_collection,
                to_address=account.address,
                metadata_uri=test_case["uri"],
                metadata_hash=metadata_hash,
                allow_duplicates=False
            )
            
            assert response is not None
            receipt = story_client.web3.eth.wait_for_transaction_receipt(response)
            assert receipt.status == 1

    def test_mint_with_zero_hash(self, story_client, nft_collection):
        """Test minting with zero hash"""
        metadata_uri = "https://example.com/metadata/zero-hash.json"
        zero_hash = b'\x00' * 32  # 32 bytes of zeros
        
        response = story_client.IPAsset.mint(
            nft_contract=nft_collection,
            to_address=account.address,
            metadata_uri=metadata_uri,
            metadata_hash=zero_hash,
            allow_duplicates=False
        )
        
        assert response is not None
        receipt = story_client.web3.eth.wait_for_transaction_receipt(response)
        assert receipt.status == 1


    def test_mint_error_cases(self, story_client, nft_collection):
        """Test various error cases for minting"""
        metadata_uri = "https://example.com/metadata/error-test.json"
        metadata_hash = web3.keccak(text="error-test-metadata")
        
        # Test with invalid address format (not a valid hex address)
        with pytest.raises(Exception):
            story_client.IPAsset.mint(
                nft_contract=nft_collection,
                to_address="invalid-address-format",
                metadata_uri=metadata_uri,
                metadata_hash=metadata_hash,
                allow_duplicates=False
            )
        
        # Test with invalid metadata hash format (wrong length - too short)
        with pytest.raises(Exception):
            story_client.IPAsset.mint(
                nft_contract=nft_collection,
                to_address=account.address,
                metadata_uri=metadata_uri,
                metadata_hash=b"too_short",  # bytes32 should be 32 bytes
                allow_duplicates=False
            )
        
        # Test with invalid metadata hash format (wrong length - too long)
        with pytest.raises(Exception):
            story_client.IPAsset.mint(
                nft_contract=nft_collection,
                to_address=account.address,
                metadata_uri=metadata_uri,
                metadata_hash=b"this_is_way_too_long_for_bytes32_format_and_should_fail",
                allow_duplicates=False
            )

    def test_mint_with_existing_metadata_hash_no_duplicates(self, story_client, nft_collection):
        """Test that minting with existing metadata hash fails when duplicates not allowed"""
        metadata_uri = "https://example.com/metadata/no-duplicates.json"
        metadata_hash = web3.keccak(text="no-duplicates-metadata")
        
        # First mint should succeed
        response1 = story_client.IPAsset.mint(
            nft_contract=nft_collection,
            to_address=account.address,
            metadata_uri=metadata_uri,
            metadata_hash=metadata_hash,
            allow_duplicates=False
        )
        
        assert response1 is not None
        receipt1 = story_client.web3.eth.wait_for_transaction_receipt(response1)
        assert receipt1.status == 1
        
        # Second mint with same metadata hash should fail when allow_duplicates=False
        with pytest.raises(Exception):
            story_client.IPAsset.mint(
                nft_contract=nft_collection,
                to_address=account.address,
                metadata_uri=metadata_uri,
                metadata_hash=metadata_hash,
                allow_duplicates=False
            )
