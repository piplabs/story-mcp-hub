# src/story_protcol_python_sdk/resources/Permission.py

from web3 import Web3
import os, json

from story_protocol_python_sdk.abi.IPAccountImpl.IPAccountImpl_client import IPAccountImplClient
from story_protocol_python_sdk.abi.IPAssetRegistry.IPAssetRegistry_client import IPAssetRegistryClient
from story_protocol_python_sdk.abi.AccessController.AccessController_client import AccessControllerClient
from story_protocol_python_sdk.resources.IPAccount import IPAccount
from story_protocol_python_sdk.utils.transaction_utils import build_and_send_transaction
from story_protocol_python_sdk.utils.validation import validate_address
from story_protocol_python_sdk.utils.constants import DEFAULT_FUNCTION_SELECTOR
from story_protocol_python_sdk.utils.sign import Sign

class Permission:
    """
    A class to manage permissions for IP accounts.

    :param web3 Web3: An instance of Web3.
    :param account: The account to use for transactions.
    :param chain_id int: The ID of the blockchain network.
    """
    def __init__(self, web3: Web3, account, chain_id: int):
        self.web3 = web3
        self.account = account
        self.chain_id = chain_id

        self.ip_asset_registry_client = IPAssetRegistryClient(web3)
        self.ip_account = IPAccount(web3, account, chain_id)
        self.access_controller_client = AccessControllerClient(web3)
        self.sign_util = Sign(web3, self.chain_id, self.account)
        
    def set_permission(self, ip_id: str, signer: str, to: str, permission: int, func: str = DEFAULT_FUNCTION_SELECTOR, tx_options: dict = None) -> dict:
        """
        Sets the permission for a specific function call.
        Each policy is represented as a mapping from an IP account address to a signer address to a recipient
        address to a function selector to a permission level. The permission level is an enum of `AccessPermission`.
        By default, all policies are set to ABSTAIN, which means that the permission is not set.
        The owner of ipAccount by default has all permission.

        :param ip_id str: The IP ID of the IP account that grants the permission for `signer`.
        :param signer str: The address that can call `to` on behalf of the `ip_id`.
        :param to str: The address that can be called by the `signer`.
        :param permission int: The new permission level.
        :param func str: [Optional] The function selector string of `to` that can be called by the `signer` on behalf of the `ipAccount`.
        :param tx_options dict: [Optional] The transaction options.
        :return dict: A dictionary with the transaction hash and success status if waiting for transaction.
        """
        try:
            validate_address(signer)
            validate_address(to)
            
            self._check_is_registered(ip_id)
            
            data = self.access_controller_client.contract.encode_abi(
                abi_element_identifier="setPermission",
                args=[
                    self.web3.to_checksum_address(ip_id),
                    self.web3.to_checksum_address(signer),
                    self.web3.to_checksum_address(to),
                    Web3.keccak(text=func)[:4] if func else b'\x00\x00\x00\x00',
                    permission
                ]
            )
            
            response = self.ip_account.execute(
                to=self.access_controller_client.contract.address,
                value=0,
                ip_id=ip_id,
                data=data,
                tx_options=tx_options
            )
            
            return {
                'tx_hash': response['tx_hash']
            }

        except Exception as e:
            raise Exception(f"Failed to set permission for IP {ip_id}: {str(e)}")

    def set_all_permissions(self, ip_id: str, signer: str, permission: int, tx_options: dict = None) -> dict:
        """
        Sets permission to a signer for all functions across all modules.

        :param ip_id str: The IP ID of the IP account that grants the permission.
        :param signer str: The address that will receive the permissions.
        :param permission int: The new permission level.
        :param tx_options dict: [Optional] The transaction options.
        :return dict: A dictionary with the transaction hash and success status if waiting for transaction.
        """
        try:
            validate_address(signer)
            
            self._check_is_registered(ip_id)
            
            data = self.access_controller_client.contract.encode_abi(
                abi_element_identifier="setAllPermissions",
                args=[
                    self.web3.to_checksum_address(ip_id),
                    self.web3.to_checksum_address(signer),
                    permission
                ]
            )
            
            response = self.ip_account.execute(
                to=self.access_controller_client.contract.address,
                value=0,
                ip_id=ip_id,
                data=data,
                tx_options=tx_options
            )
            
            return {
                'tx_hash': response['tx_hash']
            }

        except Exception as e:
            raise Exception(f"Failed to set all permissions for IP {ip_id} and signer {signer}: {str(e)}")

    def create_set_permission_signature(self, ip_id: str, signer: str, to: str, permission: int, 
                                        func: str = DEFAULT_FUNCTION_SELECTOR, deadline: int = None, 
                                        tx_options: dict = None) -> dict:
        """
        Specific permission overrides wildcard permission with signature.

        :param ip_id str: The IP ID of the IP account that grants the permission.
        :param signer str: The address that can call `to` on behalf of the `ip_id`.
        :param to str: The address that can be called by the `signer`.
        :param permission int: The new permission level.
        :param func str: [Optional] The function selector string.
        :param deadline int: [Optional] The deadline for the signature validity.
        :param tx_options dict: [Optional] The transaction options.
        :return dict: A dictionary with the transaction hash and success status if waiting for transaction.
        """
        try:
            validate_address(signer)
            validate_address(to)
            
            self._check_is_registered(ip_id)
            
            ip_account_client = IPAccountImplClient(self.web3, contract_address=ip_id)
            
            # Convert addresses to checksum format
            ip_id = self.web3.to_checksum_address(ip_id)
            signer = self.web3.to_checksum_address(signer)
            to = self.web3.to_checksum_address(to)
            
            data = self.access_controller_client.contract.encode_abi(
                abi_element_identifier="setTransientPermission",
                args=[
                    ip_id,
                    signer,
                    to,
                    Web3.keccak(text=func)[:4] if func else b'\x00\x00\x00\x00',
                    permission
                ]
            )
            
            # Get state and calculate deadline
            state = ip_account_client.state()
            block_timestamp = self.web3.eth.get_block('latest').timestamp
            calculated_deadline = self.sign_util.get_deadline(deadline)
            
            # Get permission signature
            signature_response = self.sign_util.get_permission_signature(
                ip_id=ip_id,
                deadline=calculated_deadline,
                state=state,
                permissions=[{
                    'ipId': ip_id,
                    'signer': signer,
                    'to': to,
                    'permission': permission,
                    'func': func
                }]
            )
            
            # Extract the signature string from the response
            signature_hex = signature_response["signature"]
            
            # Create and sign the transaction
            response = self.ip_account.execute_with_sig(
                to=self.access_controller_client.contract.address,
                value=0,
                ip_id=ip_id,
                data=data,
                signer=signer,
                deadline=calculated_deadline,
                signature=self.web3.to_bytes(hexstr=signature_hex),
                tx_options=tx_options
            )
            
            return {
                'tx_hash': response['tx_hash']
            }

        except Exception as e:
            raise Exception(f"Failed to create permission signature for IP {ip_id}, signer {signer}, to {to}: {str(e)}")

    def _check_is_registered(self, ip_id: str) -> None:
        """
        Check if an IP is registered.

        :param ip_id str: The IP ID to check.
        :raises ValueError: If the IP is not registered.
        """
        if not self.ip_asset_registry_client.isRegistered(ip_id):
            raise ValueError(f"IP id with {ip_id} is not registered.")
