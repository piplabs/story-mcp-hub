import pytest
from unittest.mock import Mock, patch

from story_protocol_python_sdk.resources.Permission import Permission
from tests.unit.fixtures.data import CHAIN_ID, ADDRESS, CHAIN_ID, STATE, TX_HASH
from tests.unit.fixtures.web3 import mock_web3


@pytest.fixture
def permission():
    return Permission(mock_web3, ADDRESS, CHAIN_ID)


class TestSetPermission:
    def test_unregistered_ip_account(self, permission: Permission):
        with patch.object(
            permission.ip_asset_registry_client, "isRegistered", return_value=False
        ):
            with pytest.raises(
                Exception,
                match="IP id with 0x1234567890123456789012345678901234567890 is not registered.",
            ):
                permission.set_permission(ADDRESS, ADDRESS, ADDRESS, 1)

    def test_invalid_signer_address(self, permission: Permission):
        with patch.object(
            permission.ip_asset_registry_client, "isRegistered", return_value=True
        ):
            with pytest.raises(Exception, match="Invalid address: 0xInvalidAddress."):
                permission.set_permission(ADDRESS, "0xInvalidAddress", ADDRESS, 1)

    def test_invalid_to_address(self, permission: Permission):
        with pytest.raises(Exception, match="Invalid address: 0xInvalidAddress."):
            permission.set_permission(ADDRESS, ADDRESS, "0xInvalidAddress", 1)

    def test_successful_transaction(self, permission: Permission):
        with patch.object(
            permission.ip_asset_registry_client, "isRegistered", return_value=True
        ), patch.object(
            permission.ip_account, "execute", return_value={"tx_hash": TX_HASH}
        ):
            response = permission.set_permission(ADDRESS, ADDRESS, ADDRESS, 1)
            assert response["tx_hash"] == TX_HASH

    def test_transaction_request_fails(self, permission: Permission):
        with patch.object(
            permission.ip_asset_registry_client, "isRegistered", return_value=True
        ), patch.object(
            permission.ip_account,
            "execute",
            side_effect=Exception("Transaction failed"),
        ):
            with pytest.raises(Exception, match="Transaction failed"):
                permission.set_permission(ADDRESS, ADDRESS, ADDRESS, 1)


class TestSetAllPermissions:
    def test_successful_transaction(self, permission: Permission):
        with patch.object(
            permission.ip_asset_registry_client, "isRegistered", return_value=True
        ), patch.object(
            permission.ip_account, "execute", return_value={"tx_hash": TX_HASH}
        ):
            response = permission.set_all_permissions(ADDRESS, ADDRESS, 1)
            assert response["tx_hash"] == TX_HASH

    def test_transaction_request_fails(self, permission: Permission):
        with patch.object(
            permission.ip_asset_registry_client, "isRegistered", return_value=True
        ), patch.object(
            permission.ip_account,
            "execute",
            side_effect=Exception("Transaction failed"),
        ):
            with pytest.raises(Exception, match="Transaction failed"):
                permission.set_all_permissions(ADDRESS, ADDRESS, 1)


class TestCreateSetPermissionSignature:

    def test_invalid_deadline(self, permission: Permission):
        with pytest.raises(Exception, match="Invalid deadline value."):
            permission.create_set_permission_signature(
                ADDRESS, ADDRESS, ADDRESS, 1, deadline=-1
            )

    def test_successful_signature(self, permission: Permission):
        mock_client = patch(
            "story_protocol_python_sdk.resources.Permission.IPAccountImplClient"
        ).start()
        mock_client.return_value.state.return_value = STATE
        with patch.multiple(
            permission,
            ip_account=Mock(
                execute_with_sig=Mock(return_value={"tx_hash": TX_HASH}),
            ),
            sign_util=Mock(
                get_permission_signature=Mock(
                    return_value={
                        "signature": "0x1234567890123456789012345678901234567890"
                    }
                )
            ),
        ):
            response = permission.create_set_permission_signature(
                ADDRESS, ADDRESS, ADDRESS, 1
            )
            assert response["tx_hash"] == TX_HASH
