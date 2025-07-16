# tests/integration/test_integration_dispute.py

import pytest
from web3 import Web3

from setup_for_integration import (
    web3,
    account, 
    account_2,
    story_client,
    story_client_2,
    generate_cid,
    approve,
    wallet_address
)

class TestDispute:
    @pytest.fixture(scope="module")
    def target_ip_id(self, story_client, story_client_2):
        """Create an IP to be disputed"""
        txData = story_client.NFTClient.create_nft_collection(
            name="test-collection",
            symbol="TEST",
            max_supply=100,
            is_public_minting=True,
            mint_open=True,
            contract_uri="test-uri",
            mint_fee_recipient=account.address
        )
        
        nft_contract = txData['nft_contract']

        metadata_a = {
            'ip_metadata_uri': "test-uri-a",
            'ip_metadata_hash': web3.to_hex(web3.keccak(text="test-metadata-hash-a")),
            'nft_metadata_uri': "test-nft-uri-a",
            'nft_metadata_hash': web3.to_hex(web3.keccak(text="test-nft-metadata-hash-a"))
        }
        
        response = story_client_2.IPAsset.mint_and_register_ip(
            spg_nft_contract=nft_contract,
            ip_metadata=metadata_a
        )

        return response['ip_id']

    @pytest.fixture(scope="module")
    def dispute_id(self, story_client, target_ip_id):
        cid = generate_cid()
        bond_amount = 1000000000000000000  # 1 ETH in wei
        
        response = story_client.Dispute.raise_dispute(
            target_ip_id=target_ip_id,
            target_tag="IMPROPER_REGISTRATION",
            cid=cid,
            liveness=0x278d,  # 30 days in seconds
            bond=bond_amount
        )
        
        assert 'tx_hash' in response
        assert isinstance(response['tx_hash'], str)
        assert len(response['tx_hash']) > 0
        assert 'dispute_id' in response
        assert isinstance(response['dispute_id'], int)
        assert response['dispute_id'] > 0

        return response['dispute_id']
    
    def test_raise_dispute(self, story_client, dispute_id):
        """Test raising a dispute"""
        assert dispute_id is not None
    
    def test_counter_dispute(self, story_client_2, story_client, target_ip_id, dispute_id):
        """Test countering a dispute"""
        # Get the assertion ID from the dispute ID
        assertion_id = story_client_2.Dispute.dispute_id_to_assertion_id(dispute_id)
        
        # Generate a CID for counter evidence
        counter_evidence_cid = generate_cid()
        
        deposit_response_2 = story_client_2.WIP.deposit(
            amount=Web3.to_wei(1, 'ether') #1 IP
        )

        # Counter the dispute assertion with story_client_2 (the IP owner)
        response = story_client_2.Dispute.dispute_assertion(
            ip_id=target_ip_id,
            assertion_id=assertion_id,
            counter_evidence_cid=counter_evidence_cid
        )
        
        # Verify the response
        assert 'tx_hash' in response
        assert isinstance(response['tx_hash'], str)
        assert len(response['tx_hash']) > 0
