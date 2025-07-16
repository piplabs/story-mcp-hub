# tests/integration/test_integration_group.py

import pytest
from web3 import Web3
import copy

from setup_for_integration import (
    web3,
    account, 
    story_client,
    get_token_id,
    MockERC721,
    MockERC20,
    ZERO_ADDRESS,
    PIL_LICENSE_TEMPLATE,
    EVEN_SPLIT_GROUP_POOL,
    ROYALTY_POLICY_LRP
)

# class TestGroupBasicOperations:
#     def test_register_basic_group(self, story_client):
#         response = story_client.Group.register_group(
#             group_pool=EVEN_SPLIT_GROUP_POOL
#         )
        
#         assert 'tx_hash' in response
#         assert isinstance(response['tx_hash'], str)
#         assert len(response['tx_hash']) > 0
        
#         assert 'group_id' in response
#         assert isinstance(response['group_id'], str)
#         assert response['group_id'].startswith("0x")

# class TestGroupWithLicenseOperations:
#     @pytest.fixture(scope="module")
#     def nft_collection(self, story_client):
#         tx_data = story_client.NFTClient.create_nft_collection(
#             name="test-collection",
#             symbol="TEST",
#             max_supply=100,
#             is_public_minting=True,
#             mint_open=True,
#             contract_uri="test-uri",
#             mint_fee_recipient=account.address,
#         )
#         return tx_data['nft_contract']
    
#     @pytest.fixture(scope="module")
#     def ip_with_license(self, story_client, nft_collection):
#         # Create initial IP with license terms
#         response = story_client.IPAsset.mint_and_register_ip_asset_with_pil_terms(
#             spg_nft_contract=nft_collection,
#             terms=[{
#                 'terms': {
#                     'transferable': True,
#                     'royalty_policy': ROYALTY_POLICY_LRP,
#                     'default_minting_fee': 0,
#                     'expiration': 1000,
#                     'commercial_use': True,
#                     'commercial_attribution': False,
#                     'commercializer_checker': ZERO_ADDRESS,
#                     'commercializer_checker_data': ZERO_ADDRESS,
#                     'commercial_rev_share': 0,
#                     'commercial_rev_ceiling': 0,
#                     'derivatives_allowed': True,
#                     'derivatives_attribution': True,
#                     'derivatives_approval': False,
#                     'derivatives_reciprocal': True,
#                     'derivative_rev_ceiling': 0,
#                     'currency': MockERC20,
#                     'uri': "test case"
#                 },
#                 'licensing_config': {
#                     'is_set': True,
#                     'minting_fee': 0,
#                     'hook_data': ZERO_ADDRESS,
#                     'licensing_hook': ZERO_ADDRESS,
#                     'commercial_rev_share': 0,
#                     'disabled': False,
#                     'expect_minimum_group_reward_share': 0,
#                     'expect_group_reward_pool': EVEN_SPLIT_GROUP_POOL
#                 }
#             }]
#         )
        
#         ip_id = response['ip_id']
#         license_terms_id = response['license_terms_ids'][0]

#         licensing_config = {
#             'isSet': True,
#             'mintingFee': 0,
#             'licensingHook': ZERO_ADDRESS,
#             'hookData': ZERO_ADDRESS,
#             'commercialRevShare': 0,
#             'disabled': False,
#             'expectMinimumGroupRewardShare': 0,
#             'expectGroupRewardPool': EVEN_SPLIT_GROUP_POOL
#         }
        
#         # Set licensing config
#         story_client.License.set_licensing_config(
#             ip_id=ip_id,
#             license_terms_id=license_terms_id,
#             license_template=PIL_LICENSE_TEMPLATE,
#             licensing_config=licensing_config
#         )
        
#         return {
#             'ip_id': ip_id,
#             'license_terms_id': license_terms_id
#         }
    
#     @pytest.fixture(scope="module")
#     def group_with_license(self, story_client, ip_with_license):
#         response = story_client.Group.register_group_and_attach_license(
#             group_pool=EVEN_SPLIT_GROUP_POOL,
#             license_data={
#                 'license_terms_id': ip_with_license['license_terms_id'],
#                 'licensing_config': {
#                     'is_set': True,
#                     'minting_fee': 0,
#                     'hook_data': ZERO_ADDRESS,
#                     'licensing_hook': ZERO_ADDRESS,
#                     'commercial_rev_share': 0,
#                     'disabled': False,
#                     'expect_minimum_group_reward_share': 0,
#                     'expect_group_reward_pool': ZERO_ADDRESS
#                 }
#             }
#         )

#         assert 'tx_hash' in response
#         assert isinstance(response['tx_hash'], str)

#         assert response is not None
#         assert 'group_id' in response
#         assert response['group_id'] is not None
#         return response['group_id']
    
#     def test_register_group_and_attach_license(self, group_with_license):
#         assert group_with_license is not None

#     def test_mint_register_ip_attach_license_add_to_group(self, story_client, group_with_license, ip_with_license, nft_collection):
#         response = story_client.Group.mint_and_register_ip_and_attach_license_and_add_to_group(
#             group_id=group_with_license,
#             spg_nft_contract=nft_collection,
#             license_data=[{
#                 'license_terms_id': ip_with_license['license_terms_id'],
#                 'licensing_config': {
#                     'is_set': True,
#                     'minting_fee': 0,
#                     'hook_data': ZERO_ADDRESS,
#                     'licensing_hook': ZERO_ADDRESS,
#                     'commercial_rev_share': 0,
#                     'disabled': False,
#                     'expect_minimum_group_reward_share': 0,
#                     'expect_group_reward_pool': EVEN_SPLIT_GROUP_POOL
#                 }
#             }],
#             max_allowed_reward_share=5
#         )
        
#         assert 'tx_hash' in response
#         assert isinstance(response['tx_hash'], str)
#         assert len(response['tx_hash']) > 0
        
#         assert 'ip_id' in response
#         assert isinstance(response['ip_id'], str)
#         assert response['ip_id'].startswith("0x")

# class TestAdvancedGroupOperations:
#     @pytest.fixture(scope="module")
#     def nft_collection(self, story_client):
#         tx_data = story_client.NFTClient.create_nft_collection(
#             name="test-collection",
#             symbol="TEST",
#             max_supply=100,
#             is_public_minting=True,
#             mint_open=True,
#             contract_uri="test-uri",
#             mint_fee_recipient=account.address,
#         )
#         return tx_data['nft_contract']

#     @pytest.fixture(scope="module")
#     def ip_with_license(self, story_client, nft_collection):
#         response = story_client.IPAsset.mint_and_register_ip_asset_with_pil_terms(
#             spg_nft_contract=nft_collection,
#             terms=[{
#                 'terms': {
#                     'transferable': True,
#                     'royalty_policy': ROYALTY_POLICY_LRP,
#                     'default_minting_fee': 0,
#                     'expiration': 1000,
#                     'commercial_use': True,
#                     'commercial_attribution': False,
#                     'commercializer_checker': ZERO_ADDRESS,
#                     'commercializer_checker_data': ZERO_ADDRESS,
#                     'commercial_rev_share': 0,
#                     'commercial_rev_ceiling': 0,
#                     'derivatives_allowed': True,
#                     'derivatives_attribution': True,
#                     'derivatives_approval': False,
#                     'derivatives_reciprocal': True,
#                     'derivative_rev_ceiling': 0,
#                     'currency': MockERC20,
#                     'uri': "test case"
#                 },
#                 'licensing_config': {
#                     'is_set': True,
#                     'minting_fee': 0,
#                     'hook_data': ZERO_ADDRESS,
#                     'licensing_hook': ZERO_ADDRESS,
#                     'commercial_rev_share': 0,
#                     'disabled': False,
#                     'expect_minimum_group_reward_share': 0,
#                     'expect_group_reward_pool': EVEN_SPLIT_GROUP_POOL
#                 }
#             }]
#         )
        
#         return {
#             'ip_id': response['ip_id'],
#             'license_terms_id': response['license_terms_ids'][0]
#         }
    
#     @pytest.fixture(scope="module")
#     def group_id(self, story_client, ip_with_license):
#         # Create a group with license attached
#         response = story_client.Group.register_group_and_attach_license(
#             group_pool=EVEN_SPLIT_GROUP_POOL,
#             license_data={
#                 'license_terms_id': ip_with_license['license_terms_id'],
#                 'license_template': PIL_LICENSE_TEMPLATE,
#                 'licensing_config': {
#                     'is_set': True,
#                     'minting_fee': 0,
#                     'hook_data': ZERO_ADDRESS,
#                     'licensing_hook': ZERO_ADDRESS,
#                     'commercial_rev_share': 0,
#                     'disabled': False,
#                     'expect_minimum_group_reward_share': 0,
#                     'expect_group_reward_pool': ZERO_ADDRESS
#                 }
#             }
#         )
#         return response['group_id']
    
#     def test_register_ip_and_attach_license_and_add_to_group(self, story_client, group_id, ip_with_license):
#         token_id = get_token_id(MockERC721, story_client.web3, story_client.account)
        
#         response = story_client.Group.register_ip_and_attach_license_and_add_to_group(
#             group_id=group_id,
#             nft_contract=MockERC721,
#             token_id=token_id,
#             max_allowed_reward_share=5,
#             license_data=[{
#                 'license_terms_id': ip_with_license['license_terms_id'],
#                 'licensing_config': {
#                     'is_set': True,
#                     'minting_fee': 0,
#                     'hook_data': ZERO_ADDRESS,
#                     'licensing_hook': ZERO_ADDRESS,
#                     'commercial_rev_share': 0,
#                     'disabled': False,
#                     'expect_minimum_group_reward_share': 0,
#                     'expect_group_reward_pool': EVEN_SPLIT_GROUP_POOL
#                 }
#             }]
#         )
        
#         assert 'tx_hash' in response
#         assert isinstance(response['tx_hash'], str)
#         assert len(response['tx_hash']) > 0
        
#         assert 'ip_id' in response
#         assert isinstance(response['ip_id'], str)
#         assert response['ip_id'].startswith("0x")
    
#     def test_register_group_and_attach_license_and_add_ips(self, story_client, ip_with_license):
#         response = story_client.Group.register_group_and_attach_license_and_add_ips(
#             group_pool=EVEN_SPLIT_GROUP_POOL,
#             max_allowed_reward_share=5,
#             ip_ids=[ip_with_license['ip_id']],
#             license_data={
#                 'license_terms_id': ip_with_license['license_terms_id'],
#                 'licensing_config': {
#                     'is_set': True,
#                     'minting_fee': 0,
#                     'hook_data': ZERO_ADDRESS,
#                     'licensing_hook': ZERO_ADDRESS,
#                     'commercial_rev_share': 0,
#                     'disabled': False,
#                     'expect_minimum_group_reward_share': 0,
#                     'expect_group_reward_pool': ZERO_ADDRESS
#                 }
#             }
#         )
        
#         assert 'tx_hash' in response
#         assert isinstance(response['tx_hash'], str)
#         assert len(response['tx_hash']) > 0
        
#         assert 'group_id' in response
#         assert isinstance(response['group_id'], str)
#         assert response['group_id'].startswith("0x")
    
#     def test_fail_add_unregistered_ip_to_group(self, story_client, ip_with_license):
#         with pytest.raises(ValueError, match="Failed to register group and attach license and add IPs"):
#             story_client.Group.register_group_and_attach_license_and_add_ips(
#                 group_pool=EVEN_SPLIT_GROUP_POOL,
#                 max_allowed_reward_share=5,
#                 ip_ids=[ZERO_ADDRESS],  # Invalid IP address
#                 license_data={
#                     'license_terms_id': ip_with_license['license_terms_id'],
#                     'licensing_config': {
#                         'is_set': True,
#                         'minting_fee': 0,
#                         'hook_data': ZERO_ADDRESS,
#                         'licensing_hook': ZERO_ADDRESS,
#                         'commercial_rev_share': 0,
#                         'disabled': False,
#                         'expect_minimum_group_reward_share': 0,
#                         'expect_group_reward_pool': ZERO_ADDRESS
#                     }
#                 }
#             )

class TestCollectRoyaltyAndClaimReward:
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
    def setup_royalty_collection(self, story_client, nft_collection):
        # Create license terms data
        license_terms_data = [{
            'terms': {
                'commercial_attribution': True,
                'commercial_rev_ceiling': 10,
                'commercial_rev_share': 10,
                'commercial_use': True,
                'commercializer_checker': ZERO_ADDRESS,
                'commercializer_checker_data': ZERO_ADDRESS,
                'currency': MockERC20,
                'derivative_rev_ceiling': 0,
                'derivatives_allowed': True,
                'derivatives_approval': False,
                'derivatives_attribution': True,
                'derivatives_reciprocal': True,
                'expiration': 0,
                'default_minting_fee': 0,
                'royalty_policy': ROYALTY_POLICY_LRP,
                'transferable': True,
                'uri': "https://github.com/piplabs/pil-document/blob/ad67bb632a310d2557f8abcccd428e4c9c798db1/off-chain-terms/CommercialRemix.json"
            },
            'licensing_config': {
                'is_set': True,
                'minting_fee': 0,
                'hook_data': ZERO_ADDRESS,
                'licensing_hook': ZERO_ADDRESS,
                'commercial_rev_share': 10,
                'disabled': False,
                'expect_minimum_group_reward_share': 0,
                'expect_group_reward_pool': EVEN_SPLIT_GROUP_POOL
            }
        }]
        # Create unique metadata for each IP
        metadata_1 = {
            'ip_metadata_uri': "test-uri-1",
            'ip_metadata_hash': web3.to_hex(web3.keccak(text="test-metadata-hash-1")),
            'nft_metadata_uri': "test-nft-uri-1",
            'nft_metadata_hash': web3.to_hex(web3.keccak(text="test-nft-metadata-hash-a"))
        }
        
        metadata_2 = {
            'ip_metadata_uri': "test-uri-2",
            'ip_metadata_hash': web3.to_hex(web3.keccak(text="test-metadata-hash-2")),
            'nft_metadata_uri': "test-nft-uri-2",
            'nft_metadata_hash': web3.to_hex(web3.keccak(text="test-nft-metadata-hash-2"))
        }

        # Create two IPs
        result1 = story_client.IPAsset.mint_and_register_ip_asset_with_pil_terms(
            spg_nft_contract=nft_collection,
            terms=copy.deepcopy(license_terms_data),
            ip_metadata=metadata_1
        )
        result2 = story_client.IPAsset.mint_and_register_ip_asset_with_pil_terms(
            spg_nft_contract=nft_collection,
            terms=copy.deepcopy(license_terms_data),
            ip_metadata=metadata_2
        )
        
        ip_ids = [result1['ip_id'], result2['ip_id']]
        license_terms_id = result1['license_terms_ids'][0]
        
        # Register group and add IPs
        result3 = story_client.Group.register_group_and_attach_license_and_add_ips(
            group_pool=EVEN_SPLIT_GROUP_POOL,
            max_allowed_reward_share=100,
            ip_ids=ip_ids,
            license_data={
                'license_terms_id': license_terms_id,
                'license_template': PIL_LICENSE_TEMPLATE,
                'licensing_config': {
                    'is_set': True,
                    'minting_fee': 0,
                    'hook_data': ZERO_ADDRESS,
                    'licensing_hook': ZERO_ADDRESS,
                    'commercial_rev_share': 10,
                    'disabled': False,
                    'expect_minimum_group_reward_share': 0,
                    'expect_group_reward_pool': ZERO_ADDRESS
                }
            }
        )
        
        group_ip_id = result3['group_id']
        
        # Create derivative IPs - Step 1: Mint and register
        result4 = story_client.IPAsset.mint_and_register_ip(
            spg_nft_contract=nft_collection,
            ip_metadata={
                'ip_metadata_uri': "test-derivative-uri-4",
                'ip_metadata_hash': web3.to_hex(web3.keccak(text="test-derivative-metadata-hash-1")),
                'nft_metadata_uri': "test-derivative-nft-uri-4",
                'nft_metadata_hash': web3.to_hex(web3.keccak(text="test-derivative-nft-metadata-hash-1"))
            }
        )
        child_ip_id1 = result4['ip_id']

        # Step 2: Register as derivative
        story_client.IPAsset.register_derivative(
            child_ip_id=child_ip_id1,
            parent_ip_ids=[group_ip_id],
            license_terms_ids=[license_terms_id],
            max_minting_fee=0,
            max_rts=10,
            max_revenue_share=0
        )

        # Create second derivative IP - Step 1: Mint and register
        result5 = story_client.IPAsset.mint_and_register_ip(
            spg_nft_contract=nft_collection,
            ip_metadata={
                'ip_metadata_uri': "test-derivative-uri-5",
                'ip_metadata_hash': web3.to_hex(web3.keccak(text="test-derivative-metadata-hash-2")),
                'nft_metadata_uri': "test-derivative-nft-uri-5",
                'nft_metadata_hash': web3.to_hex(web3.keccak(text="test-derivative-nft-metadata-hash-2"))
            }
        )
        child_ip_id2 = result5['ip_id']

        # Step 2: Register as derivative
        story_client.IPAsset.register_derivative(
            child_ip_id=child_ip_id2,
            parent_ip_ids=[group_ip_id],
            license_terms_ids=[license_terms_id],
            max_minting_fee=0,
            max_rts=10,
            max_revenue_share=0
        )
        
        # Pay royalties from child IPs to group IP
        story_client.Royalty.pay_royalty_on_behalf(
            receiver_ip_id=child_ip_id1,
            payer_ip_id=group_ip_id,
            token=MockERC20,
            amount=100
        )
        
        story_client.Royalty.pay_royalty_on_behalf(
            receiver_ip_id=child_ip_id2,
            payer_ip_id=group_ip_id,
            token=MockERC20,
            amount=100
        )
    
        # Transfer to vault
        story_client.Royalty.transfer_to_vault(
            royalty_policy="LRP",
            ip_id=child_ip_id1,
            ancestor_ip_id=group_ip_id,
            token=MockERC20
        )
        
        story_client.Royalty.transfer_to_vault(
            royalty_policy="LRP",
            ip_id=child_ip_id2,
            ancestor_ip_id=group_ip_id,
            token=MockERC20
        )

        return {
            'group_ip_id': group_ip_id,
            'ip_ids': ip_ids
        }
    
    def test_collect_and_distribute_group_royalties(self, story_client, setup_royalty_collection):
        group_ip_id = setup_royalty_collection['group_ip_id']
        ip_ids = setup_royalty_collection['ip_ids']
        
        response = story_client.Group.collect_and_distribute_group_royalties(
            group_ip_id=group_ip_id,
            currency_tokens=[MockERC20],
            member_ip_ids=ip_ids
        )

        print("response is ", response)
        
        assert 'tx_hash' in response
        assert isinstance(response['tx_hash'], str)
        assert len(response['tx_hash']) > 0
        
        assert 'collected_royalties' in response

        assert len(response['collected_royalties']) > 0
        assert response['collected_royalties'][0]['amount'] == 20
        
        assert 'royalties_distributed' in response
        assert len(response['royalties_distributed']) == 2
        assert response['royalties_distributed'][0]['amount'] == 10
        assert response['royalties_distributed'][1]['amount'] == 10
