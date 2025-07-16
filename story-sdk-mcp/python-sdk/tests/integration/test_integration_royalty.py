# tests/integration/test_integration_royalty.py

import pytest
from web3 import Web3
import copy

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
    PIL_LICENSE_TEMPLATE,
)

class TestRoyalty:

    @pytest.fixture(scope="module")
    def setup_ips_and_licenses(self, story_client):
        """Setup parent and child IPs with proper license relationships"""
        
        parent_token_id = get_token_id(MockERC721, story_client.web3, story_client.account)
        parent_ip_response = story_client.IPAsset.register(
            nft_contract=MockERC721,
            token_id=parent_token_id
        )
        parent_ip_id = parent_ip_response['ip_id']
        
        child_token_id = get_token_id(MockERC721, story_client.web3, story_client.account)
        child_ip_response = story_client.IPAsset.register(
            nft_contract=MockERC721,
            token_id=child_token_id
        )
        child_ip_id = child_ip_response['ip_id']
        
        license_terms_response = story_client.License.register_commercial_remix_pil(
            default_minting_fee=100000,
            currency=MockERC20,
            commercial_rev_share=10,
            royalty_policy=ROYALTY_POLICY
        )
        license_terms_id = license_terms_response['license_terms_id']
        
        story_client.License.attach_license_terms(
            ip_id=parent_ip_id,
            license_template=PIL_LICENSE_TEMPLATE,
            license_terms_id=license_terms_id
        )
        
        story_client.IPAsset.register_derivative(
            child_ip_id=child_ip_id,
            parent_ip_ids=[parent_ip_id],
            license_terms_ids=[license_terms_id],
            max_minting_fee=0,
            max_rts=0,
            max_revenue_share=0,
        )
        
        mint_tokens(
            erc20_contract_address=MockERC20, 
            web3=web3, 
            account=account, 
            to_address=account.address, 
            amount=100000 * 10 ** 6
        )
        
        approve(
            erc20_contract_address=MockERC20, 
            web3=web3, 
            account=account, 
            spender_address=ROYALTY_MODULE, 
            amount=100000 * 10 ** 6
        )
        
        return {
            'parent_ip_id': parent_ip_id,
            'child_ip_id': child_ip_id,
            'license_terms_id': license_terms_id
        }

    def test_pay_royalty_on_behalf(self, story_client, setup_ips_and_licenses):
        """Test paying royalty on behalf of a payer IP to a receiver IP"""
        parent_ip_id = setup_ips_and_licenses['parent_ip_id']
        child_ip_id = setup_ips_and_licenses['child_ip_id']
        
        response = story_client.Royalty.pay_royalty_on_behalf(
            receiver_ip_id=parent_ip_id,
            payer_ip_id=child_ip_id,
            token=MockERC20,
            amount=1
        )

        assert response is not None
        assert response['tx_hash'] is not None and isinstance(response['tx_hash'], str)

    def test_claimable_revenue(self, story_client, setup_ips_and_licenses):
        """Test checking claimable revenue"""
        parent_ip_id = setup_ips_and_licenses['parent_ip_id']
        
        response = story_client.Royalty.claimable_revenue(
            royalty_vault_ip_id=parent_ip_id,
            claimer=account.address,
            token=MockERC20
        )

        assert isinstance(response, int)
    
    def test_pay_royalty_unregistered_receiver(self, story_client, setup_ips_and_licenses):
        """Test that paying royalty to unregistered IP fails appropriately"""
        child_ip_id = setup_ips_and_licenses['child_ip_id']
        unregistered_ip_id = "0x1234567890123456789012345678901234567890"
        
        with pytest.raises(ValueError, match=f"The receiver IP with id {unregistered_ip_id} is not registered"):
            story_client.Royalty.pay_royalty_on_behalf(
                receiver_ip_id=unregistered_ip_id,
                payer_ip_id=child_ip_id,
                token=MockERC20,
                amount=1000
            )

    def test_pay_royalty_invalid_amount(self, story_client, setup_ips_and_licenses):
        """Test that paying with invalid amount fails appropriately"""
        parent_ip_id = setup_ips_and_licenses['parent_ip_id']
        child_ip_id = setup_ips_and_licenses['child_ip_id']
        
        with pytest.raises(Exception):  
            story_client.Royalty.pay_royalty_on_behalf(
                receiver_ip_id=parent_ip_id,
                payer_ip_id=child_ip_id,
                token=MockERC20,
                amount=-1
            )

class TestClaimAllRevenue:
    @pytest.fixture(scope="module")
    def setup_claim_all_revenue(self, story_client):
        # Create NFT collection
        collection_response = story_client.NFTClient.create_nft_collection(
            name="free-collection",
            symbol="FREE", 
            max_supply=100,
            is_public_minting=True,
            mint_open=True,
            contract_uri="test-uri",
            mint_fee_recipient=ZERO_ADDRESS
        )
        spg_nft_contract = collection_response['nft_contract']

        # Define license terms data template
        license_terms_template = [{
            'terms': {
                'transferable': True,
                'royalty_policy': ROYALTY_POLICY,
                'default_minting_fee': 100,
                'expiration': 0,
                'commercial_use': True,
                'commercial_attribution': False,
                'commercializer_checker': ZERO_ADDRESS,
                'commercializer_checker_data': ZERO_ADDRESS,
                'commercial_rev_share': 10,
                'commercial_rev_ceiling': 0,
                'derivatives_allowed': True,
                'derivatives_attribution': True,
                'derivatives_approval': False,
                'derivatives_reciprocal': True,
                'derivative_rev_ceiling': 0,
                'currency': MockERC20,
                'uri': ''
            },
            'licensing_config': {
                'is_set': True,
                'minting_fee': 100,
                'hook_data': ZERO_ADDRESS,
                'licensing_hook': ZERO_ADDRESS,
                'commercial_rev_share': 0,
                'disabled': False,
                'expect_minimum_group_reward_share': 0,
                'expect_group_reward_pool': ZERO_ADDRESS
            }
        }]

        # Create unique metadata for each IP
        metadata_a = {
            'ip_metadata_uri': "test-uri-a",
            'ip_metadata_hash': web3.to_hex(web3.keccak(text="test-metadata-hash-a")),
            'nft_metadata_uri': "test-nft-uri-a",
            'nft_metadata_hash': web3.to_hex(web3.keccak(text="test-nft-metadata-hash-a"))
        }
        
        metadata_b = {
            'ip_metadata_uri': "test-uri-b",
            'ip_metadata_hash': web3.to_hex(web3.keccak(text="test-metadata-hash-b")),
            'nft_metadata_uri': "test-nft-uri-b",
            'nft_metadata_hash': web3.to_hex(web3.keccak(text="test-nft-metadata-hash-b"))
        }
        
        metadata_c = {
            'ip_metadata_uri': "test-uri-c",
            'ip_metadata_hash': web3.to_hex(web3.keccak(text="test-metadata-hash-c")),
            'nft_metadata_uri': "test-nft-uri-c",
            'nft_metadata_hash': web3.to_hex(web3.keccak(text="test-nft-metadata-hash-c"))
        }
        
        metadata_d = {
            'ip_metadata_uri': "test-uri-d",
            'ip_metadata_hash': web3.to_hex(web3.keccak(text="test-metadata-hash-d")),
            'nft_metadata_uri': "test-nft-uri-d",
            'nft_metadata_hash': web3.to_hex(web3.keccak(text="test-nft-metadata-hash-d"))
        }

        # Register IP A with PIL terms
        ip_a_response = story_client.IPAsset.mint_and_register_ip_asset_with_pil_terms(
            spg_nft_contract=spg_nft_contract,
            terms=copy.deepcopy(license_terms_template),
            ip_metadata=metadata_a
        )
        ip_a = ip_a_response['ip_id']
        license_terms_id = ip_a_response['license_terms_ids'][0]

        # Register IP B as derivative of A
        ip_b_response = story_client.IPAsset.mint_and_register_ip(
            spg_nft_contract=spg_nft_contract,
            ip_metadata=metadata_b
        )
        ip_b = ip_b_response['ip_id']
        story_client.IPAsset.register_derivative(
            child_ip_id=ip_b,
            parent_ip_ids=[ip_a],
            license_terms_ids=[license_terms_id]
        )

        # Register IP C as derivative of B
        ip_c_response = story_client.IPAsset.mint_and_register_ip(
            spg_nft_contract=spg_nft_contract,
            ip_metadata=metadata_c
        )
        ip_c = ip_c_response['ip_id']
        story_client.IPAsset.register_derivative( 
            child_ip_id=ip_c,
            parent_ip_ids=[ip_b],
            license_terms_ids=[license_terms_id]
        )

        # Register IP D as derivative of C
        ip_d_response = story_client.IPAsset.mint_and_register_ip(
            spg_nft_contract=spg_nft_contract,
            ip_metadata=metadata_d
        )
        ip_d = ip_d_response['ip_id']
        story_client.IPAsset.register_derivative(
            child_ip_id=ip_d,
            parent_ip_ids=[ip_c],
            license_terms_ids=[license_terms_id]
        )
    
        return {
            'ip_a': ip_a,
            'ip_b': ip_b,
            'ip_c': ip_c,
            'ip_d': ip_d
        }

    def test_claim_all_revenue(self, setup_claim_all_revenue, story_client):
        response = story_client.Royalty.claim_all_revenue(
            ancestor_ip_id=setup_claim_all_revenue['ip_a'],
            claimer=setup_claim_all_revenue['ip_a'],
            child_ip_ids=[setup_claim_all_revenue['ip_b'], setup_claim_all_revenue['ip_c']],
            royalty_policies=[ROYALTY_POLICY, ROYALTY_POLICY],
            currency_tokens=[MockERC20, MockERC20]
        ) 

        assert response is not None
        assert 'tx_hashes' in response
        assert isinstance(response['tx_hashes'], list)
        assert len(response['tx_hashes']) > 0
        assert response['claimed_tokens'][0]['amount'] == 120

    @pytest.fixture(scope="module")
    def setup_claim_all_revenue_claim_options(self, story_client):
        # Create NFT collection
        collection_response = story_client.NFTClient.create_nft_collection(
            name="free-collection",
            symbol="FREE", 
            max_supply=100,
            is_public_minting=True,
            mint_open=True,
            contract_uri="test-uri",
            mint_fee_recipient=ZERO_ADDRESS
        )
        spg_nft_contract = collection_response['nft_contract']

        # Define license terms data template
        license_terms_template = [{
            'terms': {
                'transferable': True,
                'royalty_policy': ROYALTY_POLICY,
                'default_minting_fee': 100,
                'expiration': 0,
                'commercial_use': True,
                'commercial_attribution': False,
                'commercializer_checker': ZERO_ADDRESS,
                'commercializer_checker_data': ZERO_ADDRESS,
                'commercial_rev_share': 10,
                'commercial_rev_ceiling': 0,
                'derivatives_allowed': True,
                'derivatives_attribution': True,
                'derivatives_approval': False,
                'derivatives_reciprocal': True,
                'derivative_rev_ceiling': 0,
                'currency': MockERC20,
                'uri': ''
            },
            'licensing_config': {
                'is_set': True,
                'minting_fee': 100,
                'hook_data': ZERO_ADDRESS,
                'licensing_hook': ZERO_ADDRESS,
                'commercial_rev_share': 0,
                'disabled': False,
                'expect_minimum_group_reward_share': 0,
                'expect_group_reward_pool': ZERO_ADDRESS
            }
        }]

        # Create unique metadata for each IP
        metadata_a = {
            'ip_metadata_uri': "test-uri-a",
            'ip_metadata_hash': web3.to_hex(web3.keccak(text="test-metadata-hash-a")),
            'nft_metadata_uri': "test-nft-uri-a",
            'nft_metadata_hash': web3.to_hex(web3.keccak(text="test-nft-metadata-hash-a"))
        }
        
        metadata_b = {
            'ip_metadata_uri': "test-uri-b",
            'ip_metadata_hash': web3.to_hex(web3.keccak(text="test-metadata-hash-b")),
            'nft_metadata_uri': "test-nft-uri-b",
            'nft_metadata_hash': web3.to_hex(web3.keccak(text="test-nft-metadata-hash-b"))
        }
        
        metadata_c = {
            'ip_metadata_uri': "test-uri-c",
            'ip_metadata_hash': web3.to_hex(web3.keccak(text="test-metadata-hash-c")),
            'nft_metadata_uri': "test-nft-uri-c",
            'nft_metadata_hash': web3.to_hex(web3.keccak(text="test-nft-metadata-hash-c"))
        }
        
        metadata_d = {
            'ip_metadata_uri': "test-uri-d",
            'ip_metadata_hash': web3.to_hex(web3.keccak(text="test-metadata-hash-d")),
            'nft_metadata_uri': "test-nft-uri-d",
            'nft_metadata_hash': web3.to_hex(web3.keccak(text="test-nft-metadata-hash-d"))
        }

        # Register IP A with PIL terms
        ip_a_response = story_client.IPAsset.mint_and_register_ip_asset_with_pil_terms(
            spg_nft_contract=spg_nft_contract,
            terms=copy.deepcopy(license_terms_template),
            ip_metadata=metadata_a
        )
        ip_a = ip_a_response['ip_id']
        license_terms_id = ip_a_response['license_terms_ids'][0]

        # Register IP B as derivative of A
        ip_b_response = story_client.IPAsset.mint_and_register_ip(
            spg_nft_contract=spg_nft_contract,
            ip_metadata=metadata_b
        )
        ip_b = ip_b_response['ip_id']
        ip_b_derivative_response = story_client.IPAsset.register_derivative(
            child_ip_id=ip_b,
            parent_ip_ids=[ip_a],
            license_terms_ids=[license_terms_id]
        )

        # Register IP C as derivative of B
        ip_c_response = story_client.IPAsset.mint_and_register_ip(
            spg_nft_contract=spg_nft_contract,
            ip_metadata=metadata_c
        )
        ip_c = ip_c_response['ip_id']
        story_client.IPAsset.register_derivative( 
            child_ip_id=ip_c,
            parent_ip_ids=[ip_b],
            license_terms_ids=[license_terms_id]
        )

        # Register IP D as derivative of C
        ip_d_response = story_client.IPAsset.mint_and_register_ip(
            spg_nft_contract=spg_nft_contract,
            ip_metadata=metadata_d
        )
        ip_d = ip_d_response['ip_id']
        story_client.IPAsset.register_derivative(
            child_ip_id=ip_d,
            parent_ip_ids=[ip_c],
            license_terms_ids=[license_terms_id]
        )

        return {
            'ip_a': ip_a,
            'ip_b': ip_b,
            'ip_c': ip_c,
            'ip_d': ip_d
        }

    def test_claim_all_revenue_claim_options(self, setup_claim_all_revenue_claim_options, story_client):
        """Test claiming all revenue with specific claim options"""
        response = story_client.Royalty.claim_all_revenue(
            ancestor_ip_id=setup_claim_all_revenue_claim_options['ip_a'],
            claimer=setup_claim_all_revenue_claim_options['ip_a'],
            child_ip_ids=[setup_claim_all_revenue_claim_options['ip_b'], setup_claim_all_revenue_claim_options['ip_c']],
            royalty_policies=[ROYALTY_POLICY, ROYALTY_POLICY],
            currency_tokens=[MockERC20, MockERC20],
            claim_options={
                'auto_transfer_all_claimed_tokens_from_ip': True
            }
        )

        assert response is not None
        assert 'tx_hashes' in response
        assert isinstance(response['tx_hashes'], list)
        assert len(response['tx_hashes']) > 0
        assert response['claimed_tokens'][0]['amount'] == 120