# tests/integration/test_integration_permission.py

import pytest
from web3 import Web3

from setup_for_integration import (
    web3,
    account, 
    story_client,
    get_token_id,
    MockERC721,
    CORE_METADATA_MODULE
)

class TestPermissions:
    @pytest.fixture(scope="class")
    def ip_id(self, story_client):
        """Fixture to create an IP for testing permissions."""
        token_id = get_token_id(MockERC721, story_client.web3, story_client.account)
        response = story_client.IPAsset.register(
            nft_contract=MockERC721,
            token_id=token_id
        )
        assert 'ip_id' in response, "Failed to register IP"
        return response['ip_id']

    def test_set_permission(self, story_client, ip_id):
        """Test setting permission successfully."""
        response = story_client.Permission.set_permission(
            ip_id=ip_id,
            signer=account.address,
            to=CORE_METADATA_MODULE,
            permission=1,  # ALLOW
            func="function setAll(address,string,bytes32,bytes32)"
        )

        assert response is not None
        assert 'tx_hash' in response
        assert isinstance(response['tx_hash'], str)
        assert len(response['tx_hash']) > 0

    def test_set_all_permissions(self, story_client, ip_id):
        """Test setting all permissions successfully."""
        response = story_client.Permission.set_all_permissions(
            ip_id=ip_id,
            signer=account.address,
            permission=1  # ALLOW
        )

        assert response is not None
        assert 'tx_hash' in response
        assert isinstance(response['tx_hash'], str)
        assert len(response['tx_hash']) > 0

    def test_create_set_permission_signature(self, story_client, ip_id):
        """Test creating set permission signature."""
        deadline = web3.eth.get_block('latest')['timestamp'] + 60000
        
        response = story_client.Permission.create_set_permission_signature(
            ip_id=ip_id,
            signer=account.address,
            to=CORE_METADATA_MODULE,
            func="setAll(address,string,bytes32,bytes32)",
            permission=1,  # ALLOW
            deadline=deadline
        )

        assert response is not None
        assert 'tx_hash' in response
        assert isinstance(response['tx_hash'], str)
        assert len(response['tx_hash']) > 0

    def test_set_permission_invalid_ip(self, story_client):
        """Test setting permission for an unregistered IP."""
        unregistered_ip = "0x1234567890123456789012345678901234567890"
        
        with pytest.raises(Exception) as exc_info:
            story_client.Permission.set_permission(
                ip_id=unregistered_ip,
                signer=account.address,
                to=CORE_METADATA_MODULE,
                permission=1
            )
        
        assert f"IP id with {unregistered_ip} is not registered" in str(exc_info.value)

    def test_set_permission_invalid_addresses(self, story_client, ip_id):
        """Test that set_permission raises proper exceptions for invalid addresses."""
        invalid_signer = "0xinvalid_address"
        
        with pytest.raises(Exception) as exc_info:
            story_client.Permission.set_permission(
                ip_id=ip_id,
                signer=invalid_signer,
                to=CORE_METADATA_MODULE,
                permission=1  # ALLOW
            )
        
        assert "invalid address" in str(exc_info.value).lower()
        
        invalid_to = "not_a_hex_address"
        
        with pytest.raises(Exception) as exc_info:
            story_client.Permission.set_permission(
                ip_id=ip_id,
                signer=account.address,
                to=invalid_to,
                permission=1  # ALLOW
            )
        
        assert "invalid address" in str(exc_info.value).lower()
        
        lowercase_address = account.address.lower()
        try:
            response = story_client.Permission.set_permission(
                ip_id=ip_id,
                signer=lowercase_address,
                to=CORE_METADATA_MODULE,
                permission=1
            )
            assert 'tx_hash' in response
        except Exception as e:
            pytest.fail(f"set_permission should accept lowercase addresses, but raised: {e}")

    def test_different_permission_levels(self, story_client, ip_id):
        """Test setting and changing different permission levels."""
        DISALLOW = 0
        ALLOW = 1
        ABSTAIN = 2
        
        response = story_client.Permission.set_permission(
            ip_id=ip_id,
            signer=account.address,
            to=CORE_METADATA_MODULE,
            permission=DISALLOW,
            func="function setAll(address,string,bytes32,bytes32)"
        )
        
        assert response is not None
        assert 'tx_hash' in response
        assert isinstance(response['tx_hash'], str)
        assert len(response['tx_hash']) > 0
        
        response = story_client.Permission.set_permission(
            ip_id=ip_id,
            signer=account.address,
            to=CORE_METADATA_MODULE,
            permission=ALLOW,
            func="function setAll(address,string,bytes32,bytes32)"
        )
        
        assert response is not None
        assert 'tx_hash' in response
        
        response = story_client.Permission.set_permission(
            ip_id=ip_id,
            signer=account.address,
            to=CORE_METADATA_MODULE,
            permission=ABSTAIN,
            func="function setAll(address,string,bytes32,bytes32)"
        )
        
        assert response is not None
        assert 'tx_hash' in response
        
        response = story_client.Permission.set_all_permissions(
            ip_id=ip_id,
            signer=account.address,
            permission=DISALLOW
        )
        
        assert response is not None
        assert 'tx_hash' in response
        
        response = story_client.Permission.set_all_permissions(
            ip_id=ip_id,
            signer=account.address,
            permission=ABSTAIN
        )
        
        assert response is not None
        assert 'tx_hash' in response
    
    def test_different_function_selectors(self, story_client, ip_id):
        """Test setting permissions with different function selectors."""
        ALLOW = 1

        response = story_client.Permission.set_permission(
            ip_id=ip_id,
            signer=account.address,
            to=CORE_METADATA_MODULE,
            permission=1
            # No func parameter provided - should use default
        )
        
        assert response is not None
        assert 'tx_hash' in response
        assert isinstance(response['tx_hash'], str)
        assert len(response['tx_hash']) > 0
        
        response = story_client.Permission.set_permission(
            ip_id=ip_id,
            signer=account.address,
            to=CORE_METADATA_MODULE,
            permission=ALLOW, 
            func="setAll(address,string,bytes32,bytes32)"
        )
        
        assert response is not None
        assert 'tx_hash' in response
        
        response = story_client.Permission.set_permission(
            ip_id=ip_id,
            signer=account.address,
            to=CORE_METADATA_MODULE,
            permission=ALLOW,  
            func="setName(address,string)"
        )
        
        assert response is not None
        assert 'tx_hash' in response
        
        response = story_client.Permission.set_permission(
            ip_id=ip_id,
            signer=account.address,
            to=CORE_METADATA_MODULE,
            permission=ALLOW,
            func="setDescription(address,string)"
        )
        
        assert response is not None
        assert 'tx_hash' in response
        
        deadline = web3.eth.get_block('latest')['timestamp'] + 60000
        response = story_client.Permission.create_set_permission_signature(
            ip_id=ip_id,
            signer=account.address,
            to=CORE_METADATA_MODULE,
            permission=ALLOW,
            # No func parameter provided
            deadline=deadline
        )
        
        assert response is not None
        assert 'tx_hash' in response
    
    def test_permission_hierarchies_and_overrides(self, story_client, ip_id):
        """Test permission hierarchies and how permissions override each other."""
        DISALLOW = 0
        ALLOW = 1
        ABSTAIN = 2
        
        response = story_client.Permission.set_all_permissions(
            ip_id=ip_id,
            signer=account.address,
            permission=DISALLOW
        )
        
        assert response is not None
        assert 'tx_hash' in response
        
        specific_func = "setName(address,string)"
        response = story_client.Permission.set_permission(
            ip_id=ip_id,
            signer=account.address,
            to=CORE_METADATA_MODULE,
            permission=ALLOW,
            func=specific_func
        )
        
        assert response is not None
        assert 'tx_hash' in response
        
        alternate_signer = web3.eth.account.create()
        
        response = story_client.Permission.set_all_permissions(
            ip_id=ip_id,
            signer=alternate_signer.address,
            permission=ALLOW
        )
        
        assert response is not None
        assert 'tx_hash' in response
        
        response = story_client.Permission.set_permission(
            ip_id=ip_id,
            signer=alternate_signer.address,
            to=CORE_METADATA_MODULE,
            permission=DISALLOW,
            func=specific_func
        )
        
        assert response is not None
        assert 'tx_hash' in response
        
        deadline = web3.eth.get_block('latest')['timestamp'] + 60000
        
        response = story_client.Permission.create_set_permission_signature(
            ip_id=ip_id,
            signer=account.address,
            to=CORE_METADATA_MODULE,
            permission=ALLOW,
            func="setDescription(address,string)",
            deadline=deadline
        )
        
        assert response is not None
        assert 'tx_hash' in response
        
        response = story_client.Permission.set_all_permissions(
            ip_id=ip_id,
            signer=account.address,
            permission=ABSTAIN
        )
        
        assert response is not None
        assert 'tx_hash' in response
        
        response = story_client.Permission.set_all_permissions(
            ip_id=ip_id,
            signer=alternate_signer.address,
            permission=ABSTAIN
        )
        
        assert response is not None
        assert 'tx_hash' in response

    
