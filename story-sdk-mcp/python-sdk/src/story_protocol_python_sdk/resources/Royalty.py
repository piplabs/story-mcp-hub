#src/story_protcol_python_sdk/resources/Royalty.py

from web3 import Web3

from story_protocol_python_sdk.abi.IPAssetRegistry.IPAssetRegistry_client import IPAssetRegistryClient
from story_protocol_python_sdk.abi.IpRoyaltyVaultImpl.IpRoyaltyVaultImpl_client import IpRoyaltyVaultImplClient
from story_protocol_python_sdk.abi.RoyaltyPolicyLAP.RoyaltyPolicyLAP_client import RoyaltyPolicyLAPClient
from story_protocol_python_sdk.abi.RoyaltyModule.RoyaltyModule_client import RoyaltyModuleClient
from story_protocol_python_sdk.abi.RoyaltyWorkflows.RoyaltyWorkflows_client import RoyaltyWorkflowsClient
from story_protocol_python_sdk.abi.IPAccountImpl.IPAccountImpl_client import IPAccountImplClient
from story_protocol_python_sdk.abi.MockERC20.MockERC20_client import MockERC20Client
from story_protocol_python_sdk.abi.RoyaltyPolicyLRP.RoyaltyPolicyLRP_client import RoyaltyPolicyLRPClient

from story_protocol_python_sdk.utils.transaction_utils import build_and_send_transaction

class Royalty:
    """
    A class to claim and pay royalties on Story Protocol.

    :param web3 Web3: An instance of Web3.
    :param account: The account to use for transactions.
    :param chain_id int: The ID of the blockchain network.
    """
    def __init__(self, web3: Web3, account, chain_id: int):
        self.web3 = web3
        self.account = account
        self.chain_id = chain_id

        self.ip_asset_registry_client = IPAssetRegistryClient(web3)
        self.royalty_policy_lap_client = RoyaltyPolicyLAPClient(web3)
        self.royalty_module_client = RoyaltyModuleClient(web3)
        self.ip_royalty_vault_client = IpRoyaltyVaultImplClient(web3)
        self.royalty_workflows_client = RoyaltyWorkflowsClient(web3)
        self.ip_account_impl_client = IPAccountImplClient(web3)
        self.mock_erc20_client = MockERC20Client(web3)
        self.royalty_policy_lrp_client = RoyaltyPolicyLRPClient(web3)

    def get_royalty_vault_address(self, ip_id: str) -> str:
        """
        Get the royalty vault address for a given IP ID.

        :param ip_id str: The IP ID.
        :return str: The respective royalty vault address.
        """
        is_registered = self.ip_asset_registry_client.isRegistered(ip_id)
        if not is_registered:
            raise ValueError(f"The IP with id {ip_id} is not registered.")

        return self.royalty_module_client.ipRoyaltyVaults(ip_id)

    def claimable_revenue(self, royalty_vault_ip_id: str, claimer: str, token: str) -> int:
        """
        Calculates the amount of revenue token claimable by a token holder.

        :param royalty_vault_ip_id str: The id of the royalty vault.
        :param claimer str: The address of the royalty token holder.
        :param token str: The revenue token to claim.
        :return int: The claimable revenue amount.
        """
        try:
            proxy_address = self.get_royalty_vault_address(royalty_vault_ip_id)
            ip_royalty_vault_client = IpRoyaltyVaultImplClient(self.web3, contract_address=proxy_address)

            claimable_revenue = ip_royalty_vault_client.claimableRevenue(
                claimer=claimer,
                token=token
            )

            return claimable_revenue

        except Exception as e:
            raise e
        
    def pay_royalty_on_behalf(self, receiver_ip_id: str, payer_ip_id: str, token: str, amount: int, tx_options: dict = None) -> dict:
        """
        Allows the function caller to pay royalties to the receiver IP asset on behalf of the payer IP asset.

        :param receiver_ip_id str: The IP ID that receives the royalties.
        :param payer_ip_id str: The ID of the IP asset that pays the royalties.
        :param token str: The token to use to pay the royalties.
        :param amount int: The amount to pay.
        :param tx_options dict: [Optional] The transaction options.
        :return dict: A dictionary with the transaction hash.
        """
        try:
            is_receiver_registered = self.ip_asset_registry_client.isRegistered(receiver_ip_id)
            if not is_receiver_registered:
                raise ValueError(f"The receiver IP with id {receiver_ip_id} is not registered.")

            is_payer_registered = self.ip_asset_registry_client.isRegistered(payer_ip_id)
            if not is_payer_registered:
                raise ValueError(f"The payer IP with id {payer_ip_id} is not registered.")
                
            response = build_and_send_transaction(
                self.web3,
                self.account,
                self.royalty_module_client.build_payRoyaltyOnBehalf_transaction,
                receiver_ip_id,
                payer_ip_id,
                token,
                amount,
                tx_options=tx_options
            )

            return {'tx_hash': response['tx_hash']}
        
        except Exception as e:
            raise e
    
    def claim_all_revenue(self, ancestor_ip_id: str, claimer: str, child_ip_ids: list, royalty_policies: list, currency_tokens: list, claim_options: dict = None, tx_options: dict = None) -> dict:
        """
        Claims all revenue from the child IPs of an ancestor IP, then optionally transfers and unwraps tokens.

        :param ancestor_ip_id str: The IP ID of the ancestor.
        :param claimer str: The address of the claimer.
        :param child_ip_ids list: List of child IP IDs.
        :param royalty_policies list: List of royalty policy addresses.
        :param currency_tokens list: List of currency token addresses.
        :param claim_options dict: [Optional] Options for auto-transfer and unwrapping.
        :param tx_options dict: [Optional] The transaction options.
        :return dict: A dictionary with transaction details and claimed tokens.
        """
        try:
            # Validate addresses
            if not self.web3.is_address(ancestor_ip_id):
                raise ValueError("Invalid ancestor IP ID address")
            if not self.web3.is_address(claimer):
                raise ValueError("Invalid claimer address") 
            if not all(self.web3.is_address(addr) for addr in child_ip_ids):
                raise ValueError("Invalid child IP ID address")
            if not all(self.web3.is_address(addr) for addr in royalty_policies):
                raise ValueError("Invalid royalty policy address")
            if not all(self.web3.is_address(addr) for addr in currency_tokens):
                raise ValueError("Invalid currency token address")

            # Claim revenue
            response = build_and_send_transaction(
                self.web3,
                self.account,
                self.royalty_workflows_client.build_claimAllRevenue_transaction,
                ancestor_ip_id,
                claimer, 
                child_ip_ids,
                royalty_policies,
                currency_tokens,
                tx_options=tx_options
            )

            tx_hashes = [response['tx_hash']]
            
            # Determine if the claimer is an IP owned by the wallet.
            owns_claimer, is_claimer_ip, ip_account = self._get_claimer_info(claimer)

            # If wallet does not own the claimer then we cannot auto claim.
            # If owns_claimer is false, it means the claimer is neither an IP owned by the wallet nor the wallet address itself.
            if not owns_claimer:
                return {
                    'receipt': response['tx_receipt'],
                    'tx_hashes': tx_hashes
                }
            
            claimed_tokens = self._parse_tx_revenue_token_claimed_event(response['tx_receipt'])

            auto_transfer = claim_options.get('auto_transfer_all_claimed_tokens_from_ip', True) if claim_options else True
            # auto_unwrap = claim_options['auto_unwrap_ip_tokens']

            # transfer claimed tokens from IP to wallet if wallet owns IP
            if auto_transfer and is_claimer_ip and owns_claimer:
                hashes = self._transfer_claimed_tokens_from_ip_to_wallet(
                    ancestor_ip_id,
                    ip_account,
                    claimed_tokens
                )
                tx_hashes.extend(hashes)

            return {
                'receipt': response['tx_receipt'],
                'claimed_tokens': claimed_tokens,
                'tx_hashes': tx_hashes
            }

        except Exception as e:
            raise ValueError(f"Failed to claim all revenue: {str(e)}")
    
    def transfer_to_vault(
        self,
        ip_id: str,
        ancestor_ip_id: str,
        token: str,
        royalty_policy: str = "LAP",
        tx_options: dict = None
    ) -> dict:
        """
        Transfers to vault an amount of revenue tokens claimable via a royalty policy.

        :param ip_id str: The IP ID.
        :param ancestor_ip_id str: The ancestor IP ID.
        :param token str: The token address.
        :param royalty_policy str: The royalty policy to use ("LAP" or "LRP").
        :param tx_options dict: [Optional] Transaction options.
        :return dict: A dictionary with the transaction hash and receipt.
        """
        try:
            if not self.web3.is_address(token):
                raise ValueError(f'Token address "{token}" is invalid.')
            
            # Determine which royalty policy to use
            if royalty_policy == "LAP":
                royalty_policy_client = self.royalty_policy_lap_client
            elif royalty_policy == "LRP":
                royalty_policy_client = self.royalty_policy_lrp_client
            else:
                # If it's a custom address
                if not self.web3.is_address(royalty_policy):
                    raise ValueError(f'Royalty policy address "{royalty_policy}" is invalid.')
                royalty_policy_client = self.royalty_policy_lap_client  # Same ABI for all royalty policies
                royalty_policy_client.contract.address = self.web3.to_checksum_address(royalty_policy)

            response = build_and_send_transaction(
                self.web3,
                self.account,
                royalty_policy_client.build_transferToVault_transaction,
                ip_id,
                ancestor_ip_id,
                token,
                tx_options=tx_options
            )

            return {
                'tx_hash': response['tx_hash'],
                'receipt': response['tx_receipt']
            }

        except Exception as e:
            raise ValueError(f"Failed to transfer to vault: {str(e)}")

    def _get_claimer_info(self, claimer):
        """
        Get information about the claimer address.
        
        :param claimer str: The claimer address to check
        :return dict: Dictionary containing:
            - owns_claimer (bool): Whether the wallet owns the claimer
            - is_claimer_ip (bool): Whether the claimer is an IP
            - ip_account (IpAccountImplClient): IP account client if claimer is an IP
        """
        is_claimer_ip = self.ip_asset_registry_client.isRegistered(claimer)
        owns_claimer = claimer == self.account.address

        ip_account = None
        if is_claimer_ip:
            ip_account = IPAccountImplClient(self.web3, contract_address=claimer)
            ip_owner = ip_account.owner()
            owns_claimer = ip_owner == self.account.address

        return owns_claimer, is_claimer_ip, ip_account
    
    def _transfer_claimed_tokens_from_ip_to_wallet(self, ancestor_ip_id: str, ip_account, claimed_tokens: list) -> list:
        """
        Transfer claimed tokens from an IP account to the wallet.

        :param ancestor_ip_id str: The IP ID of the ancestor.
        :param ip_account IpAccountImplClient: The IP account to transfer from
        :param claimed_tokens list: List of claimed tokens, each containing token address and amount
        :return list: List of transaction hashes
        """
        tx_hashes = []

        for claimed_token in claimed_tokens:
            token = claimed_token['token'] 
            amount = claimed_token['amount']

            if amount <= 0:
                continue

            # Build ERC20 transfer function data
            transfer_data = self.mock_erc20_client.contract.encode_abi(
                abi_element_identifier="transfer", 
                args=[self.account.address, amount]
            )

        # Execute transfer through IP account - use build_and_send_transaction to properly sign with account
        response = build_and_send_transaction(
            self.web3,
            self.account,
            ip_account.build_execute_transaction,
            self.web3.to_checksum_address(token),
            0,
            transfer_data,
            0
        )
        tx_hashes.append(response['tx_hash'])

        return tx_hashes

    def _parse_tx_revenue_token_claimed_event(self, tx_receipt: dict) -> list:
        """
        Parse the RevenueTokenClaimed events from a transaction receipt.

        :param tx_receipt dict: The transaction receipt.
        :return list: List of claimed tokens with claimer address, token address and amount.
        """
        event_signature = self.web3.keccak(text="RevenueTokenClaimed(address,address,uint256)").hex()
        claimed_tokens = []
        
        for log in tx_receipt.get('logs', []):
            if log['topics'][0].hex() == event_signature:
                data = log['data']
                
                # Convert HexBytes to hex string without '0x' prefix
                data_hex = data.hex() if hasattr(data, 'hex') else data[2:] if isinstance(data, str) and data.startswith('0x') else data
                
                # Each parameter is 32 bytes (64 hex chars)
                claimer = "0x" + data_hex[24:64]  # First 20 bytes of the first parameter
                token = "0x" + data_hex[88:128]   # First 20 bytes of the second parameter
                amount = int(data_hex[128:], 16)  # Third parameter
                
                claimed_tokens.append({
                    'claimer': claimer,
                    'token': token,
                    'amount': amount
                })

        return claimed_tokens
