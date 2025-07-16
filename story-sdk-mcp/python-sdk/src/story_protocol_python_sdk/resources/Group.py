# src/story_protocol_python_sdk/resources/Group.py

from web3 import Web3

from story_protocol_python_sdk.abi.GroupingModule.GroupingModule_client import GroupingModuleClient
from story_protocol_python_sdk.abi.GroupingWorkflows.GroupingWorkflows_client import GroupingWorkflowsClient
from story_protocol_python_sdk.abi.IPAssetRegistry.IPAssetRegistry_client import IPAssetRegistryClient
from story_protocol_python_sdk.abi.CoreMetadataModule.CoreMetadataModule_client import CoreMetadataModuleClient
from story_protocol_python_sdk.abi.LicensingModule.LicensingModule_client import LicensingModuleClient
from story_protocol_python_sdk.abi.LicenseRegistry.LicenseRegistry_client import LicenseRegistryClient
from story_protocol_python_sdk.abi.PILicenseTemplate.PILicenseTemplate_client import PILicenseTemplateClient
from story_protocol_python_sdk.abi.IPAccountImpl.IPAccountImpl_client import IPAccountImplClient

from story_protocol_python_sdk.utils.license_terms import LicenseTerms
from story_protocol_python_sdk.utils.transaction_utils import build_and_send_transaction
from story_protocol_python_sdk.utils.sign import Sign
from story_protocol_python_sdk.utils.constants import ZERO_ADDRESS, ZERO_HASH


class Group:
    """
    A class to manage groups on Story Protocol.

    :param web3 Web3: An instance of Web3.
    :param account: The account to use for transactions.
    :param chain_id int: The ID of the blockchain network.
    """
    def __init__(self, web3: Web3, account, chain_id: int):
        self.web3 = web3
        self.account = account
        self.chain_id = chain_id

        self.grouping_module_client = GroupingModuleClient(web3)
        self.grouping_workflows_client = GroupingWorkflowsClient(web3)
        self.ip_asset_registry_client = IPAssetRegistryClient(web3)
        self.core_metadata_module_client = CoreMetadataModuleClient(web3)
        self.licensing_module_client = LicensingModuleClient(web3)
        self.license_registry_client = LicenseRegistryClient(web3)
        self.pi_license_template_client = PILicenseTemplateClient(web3)

        self.license_terms_util = LicenseTerms(web3)
        self.sign_util = Sign(web3, self.chain_id, self.account)

    def register_group(self, group_pool: str, tx_options: dict = None) -> dict:
        """
        Registers a Group IPA.

        :param group_pool str: The address of the group pool.
        :param tx_options dict: [Optional] The transaction options.
        :return dict: A dictionary with the transaction hash and group ID.
        """
        try:
            if not self.web3.is_address(group_pool):
                raise ValueError(f'Address "{group_pool}" is invalid.')

            response = build_and_send_transaction(
                self.web3,
                self.account,
                self.grouping_module_client.build_registerGroup_transaction,
                group_pool,
                tx_options=tx_options
            )

            group_id = self._parse_tx_ip_group_registered_event(response['tx_receipt'])
            
            return {
                'tx_hash': response['tx_hash'],
                'group_id': group_id
            }
        
        except Exception as e:
            raise ValueError(f"Failed to register group: {str(e)}")

    def register_group_and_attach_license(
        self,
        group_pool: str,
        license_data: dict,
        tx_options: dict = None
    ) -> dict:
        """
        Register a group IP with a group reward pool and attach license terms to the group IP.

        :param group_pool str: The address of the group pool.
        :param license_data dict: License data object with terms and config.
        :param tx_options dict: [Optional] The transaction options.
        :return dict: A dictionary with the transaction hash and group ID.
        """
        try:
            if not self.web3.is_address(group_pool):
                raise ValueError(f'Group pool address "{group_pool}" is invalid.')

            # Process license data
            license_data_processed = self._get_license_data([license_data])[0]
            
            response = build_and_send_transaction(
                self.web3,
                self.account,
                self.grouping_workflows_client.build_registerGroupAndAttachLicense_transaction,
                group_pool,
                license_data_processed,
                tx_options=tx_options
            )

            group_id = self._parse_tx_ip_group_registered_event(response['tx_receipt'])

            return {
                'tx_hash': response['tx_hash'],
                'group_id': group_id
            }

        except Exception as e:
            raise ValueError(f"Failed to register group and attach license: {str(e)}")

    def mint_and_register_ip_and_attach_license_and_add_to_group(
        self,
        group_id: str,
        spg_nft_contract: str,
        license_data: list,
        max_allowed_reward_share: int,
        ip_metadata: dict = None,
        recipient: str = None,
        allow_duplicates: bool = True,
        deadline: int = None,
        tx_options: dict = None
    ) -> dict:
        """
        Mint an NFT from a SPGNFT collection, register it with metadata as an IP, 
        attach license terms to the registered IP, and add it to a group IP.

        :param group_id str: The ID of the group to add the IP to.
        :param spg_nft_contract str: The address of the SPG NFT contract.
        :param license_data list: List of license data objects with terms and config.
        :param max_allowed_reward_share int: Maximum allowed reward share percentage.
        :param ip_metadata dict: [Optional] The metadata for the IP.
        :param recipient str: [Optional] The recipient of the NFT (defaults to caller).
        :param allow_duplicates bool: [Optional] Whether to allow duplicate IPs.
        :param deadline int: [Optional] The deadline for the signature in milliseconds.
        :param tx_options dict: [Optional] The transaction options.
        :return dict: A dictionary with the transaction hash, IP ID, and token ID.
        """
        try:
            if not self.web3.is_address(group_id):
                raise ValueError(f'Group ID "{group_id}" is invalid.')
            
            if not self.web3.is_address(spg_nft_contract):
                raise ValueError(f'SPG NFT contract address "{spg_nft_contract}" is invalid.')
            
            is_registered = self.ip_asset_registry_client.isRegistered(group_id)
            if not is_registered:
                raise ValueError(f"Group IP {group_id} is not registered.")
            
            # Get IP account state
            ip_account = IPAccountImplClient(self.web3, contract_address=group_id)
            state = ip_account.state()
            
            # Calculate deadline
            calculated_deadline = self.sign_util.get_deadline(deadline=deadline)
            
            # Get permission signature for adding to group
            sig_add_to_group = self.sign_util.get_permission_signature(
                ip_id=group_id,
                deadline=calculated_deadline,
                state=state,
                permissions=[{
                    'ipId': group_id,
                    'signer': self.grouping_workflows_client.contract.address,
                    'to': self.grouping_module_client.contract.address,
                    'permission': 1,  # ALLOW
                    'func': "addIp(address,address[],uint256)",
                }]
            )

            licenses_data = self._get_license_data(license_data)
            
            metadata = self._get_ip_metadata(ip_metadata)
            
            max_allowed_reward_share = self.license_terms_util.get_revenue_share(max_allowed_reward_share)

            # Set recipient to caller if not provided
            if not recipient:
                recipient = self.account.address

            response = build_and_send_transaction(
                self.web3,
                self.account,
                self.grouping_workflows_client.build_mintAndRegisterIpAndAttachLicenseAndAddToGroup_transaction,
                spg_nft_contract,
                group_id,
                recipient,
                max_allowed_reward_share,
                licenses_data,
                metadata,
                {
                    'signer': self.account.address,
                    'deadline': calculated_deadline,
                    'signature': self.web3.to_bytes(hexstr=sig_add_to_group["signature"])
                },
                allow_duplicates,
                tx_options=tx_options
            )
            
            # Parse events to get IP ID and token ID
            registration_data = self._parse_tx_ip_registered_event(response['tx_receipt'])
            
            return {
                'tx_hash': response['tx_hash'],
                'ip_id': registration_data['ip_id'],
                'token_id': registration_data['token_id']
            }
            
        except Exception as e:
            raise ValueError(f"Failed to mint and register IP and attach license and add to group: {str(e)}")

    def register_ip_and_attach_license_and_add_to_group(
        self,
        group_id: str,
        nft_contract: str,
        token_id: int,
        license_data: list,
        max_allowed_reward_share: int,
        ip_metadata: dict = None,
        deadline: int = None,
        tx_options: dict = None
    ) -> dict:
        """
        Register an NFT as IP with metadata, attach license terms to the registered IP, 
        and add it to a group IP.

        :param group_id str: The ID of the group to add the IP to.
        :param nft_contract str: The address of the NFT contract.
        :param token_id int: The token ID of the NFT.
        :param license_data list: List of license data objects with terms and config.
        :param max_allowed_reward_share int: Maximum allowed reward share percentage.
        :param ip_metadata dict: [Optional] The metadata for the IP.
        :param deadline int: [Optional] The deadline for the signature in milliseconds.
        :param tx_options dict: [Optional] The transaction options.
        :return dict: A dictionary with the transaction hash, IP ID, and token ID.
        """
        try:
            if not self.web3.is_address(group_id):
                raise ValueError(f'Group ID "{group_id}" is invalid.')
            
            if not self.web3.is_address(nft_contract):
                raise ValueError(f'NFT contract address "{nft_contract}" is invalid.')
            
            # Check if group is registered
            is_registered = self.ip_asset_registry_client.isRegistered(group_id)
            if not is_registered:
                raise ValueError(f"Group IP {group_id} is not registered.")
            
            # Get IP ID for the NFT
            ip_id = self.ip_asset_registry_client.ipId(
                self.chain_id,
                nft_contract,
                token_id
            )
            
            # Get IP account state
            ip_account = IPAccountImplClient(self.web3, group_id)
            state = ip_account.state()
            
            # Calculate deadline
            calculated_deadline = self.sign_util.get_deadline(deadline=deadline)
            
            # Get permission signature for adding to group
            sig_add_to_group = self.sign_util.get_permission_signature(
                ip_id=group_id,
                deadline=calculated_deadline,
                state=state,
                permissions=[{
                    'ipId': group_id,
                    'signer': self.grouping_workflows_client.contract.address,
                    'to': self.grouping_module_client.contract.address,
                    'permission': 1,  # ALLOW
                    'func': "addIp(address,address[],uint256)",
                }]
            )
            
            # Get permission signature for metadata and license
            sig_metadata_and_attach = self.sign_util.get_permission_signature(
                ip_id=ip_id,
                deadline=calculated_deadline,
                state=self.web3.to_bytes(hexstr=ZERO_HASH),
                permissions=[
                    {
                        'ipId': ip_id,
                        'signer': self.grouping_workflows_client.contract.address,
                        'to': self.core_metadata_module_client.contract.address,
                        'permission': 1,  # ALLOW
                        'func': "setAll(address,string,bytes32,bytes32)"
                    },
                    {
                        'ipId': ip_id,
                        'signer': self.grouping_workflows_client.contract.address,
                        'to': self.licensing_module_client.contract.address,
                        'permission': 1,  # ALLOW
                        'func': "attachLicenseTerms(address,address,uint256)"
                    },
                    {
                        'ipId': ip_id,
                        'signer': self.grouping_workflows_client.contract.address,
                        'to': self.licensing_module_client.contract.address,
                        'permission': 1,  # ALLOW
                        'func': "setLicensingConfig(address,address,uint256,(bool,uint256,address,bytes,uint32,bool,uint32,address))"
                    }
                ]
            )
            
            # Process license data
            licenses_data = self._get_license_data(license_data)
            
            # Process IP metadata
            metadata = self._get_ip_metadata(ip_metadata)

            response = build_and_send_transaction(
                self.web3,
                self.account,
                self.grouping_workflows_client.build_registerIpAndAttachLicenseAndAddToGroup_transaction,
                nft_contract,
                token_id,
                group_id,
                self.license_terms_util.get_revenue_share(max_allowed_reward_share),
                licenses_data,
                metadata,
                {
                    'signer': self.account.address,
                    'deadline': calculated_deadline,
                    'signature': self.web3.to_bytes(hexstr=sig_metadata_and_attach['signature'])
                },
                {
                    'signer': self.account.address,
                    'deadline': calculated_deadline,
                    'signature': self.web3.to_bytes(hexstr=sig_add_to_group['signature'])
                },
                tx_options=tx_options
            )
            
            # Parse events to get IP ID and token ID
            registration_data = self._parse_tx_ip_registered_event(response['tx_receipt'])
            
            return {
                'tx_hash': response['tx_hash'],
                'ip_id': registration_data['ip_id'],
                'token_id': registration_data['token_id']
            }
            
        except Exception as e:
            raise ValueError(f"Failed to register IP and attach license and add to group: {str(e)}")

    def register_group_and_attach_license_and_add_ips(
        self,
        group_pool: str,
        ip_ids: list,
        license_data: dict,
        max_allowed_reward_share: int,
        tx_options: dict = None
    ) -> dict:
        """
        Register a group IP with a group reward pool, attach license terms to the group IP, 
        and add individual IPs to the group IP.

        :param group_pool str: The address of the group pool.
        :param ip_ids list: List of IP IDs to add to the group.
        :param license_data dict: License data object with terms and config.
        :param max_allowed_reward_share int: Maximum allowed reward share percentage.
        :param tx_options dict: [Optional] The transaction options.
        :return dict: A dictionary with the transaction hash and group ID.
        """
        try:
            if not self.web3.is_address(group_pool):
                raise ValueError(f'Group pool address "{group_pool}" is invalid.')
            
            # Validate IP IDs
            for ip_id in ip_ids:
                if not self.web3.is_address(ip_id):
                    raise ValueError(f'IP ID "{ip_id}" is invalid.')
                
                is_registered = self.ip_asset_registry_client.isRegistered(ip_id)
                if not is_registered:
                    raise ValueError(f"IP {ip_id} is not registered.")
            
            # Process license data
            license_data_processed = self._get_license_data([license_data])[0]
            
            # Check if license terms are attached to all IPs
            for ip_id in ip_ids:
                is_attached = self.license_registry_client.hasIpAttachedLicenseTerms(
                    ip_id,
                    license_data_processed['licenseTemplate'],
                    license_data_processed['licenseTermsId']
                )
                if not is_attached:
                    raise ValueError(
                        f"License terms must be attached to IP {ip_id} before adding to group."
                    )
            
            response = build_and_send_transaction(
                self.web3,
                self.account,
                self.grouping_workflows_client.build_registerGroupAndAttachLicenseAndAddIps_transaction,
                group_pool,
                ip_ids,
                self.license_terms_util.get_revenue_share(max_allowed_reward_share),
                license_data_processed,
                tx_options=tx_options
            )
            
            group_id = self._parse_tx_ip_group_registered_event(response['tx_receipt'])
            
            return {
                'tx_hash': response['tx_hash'],
                'group_id': group_id
            }
            
        except Exception as e:
            raise ValueError(f"Failed to register group and attach license and add IPs: {str(e)}")

    def collect_and_distribute_group_royalties(
        self,
        group_ip_id: str,
        currency_tokens: list,
        member_ip_ids: list,
        tx_options: dict = None
    ) -> dict:
        """
        Collect royalties for the entire group and distribute the rewards to each member IP's royalty vault.

        :param group_ip_id str: The ID of the group IP.
        :param currency_tokens list: List of currency token addresses.
        :param member_ip_ids list: List of member IP IDs.
        :param tx_options dict: [Optional] The transaction options.
        :return dict: A dictionary with the transaction hash and collected royalties.
        """
        try:
            if not self.web3.is_address(group_ip_id):
                raise ValueError(f'Group IP ID "{group_ip_id}" is invalid.')
            
            if not currency_tokens:
                raise ValueError("At least one currency token is required.")
            
            if not member_ip_ids:
                raise ValueError("At least one member IP ID is required.")
            
            # Validate currency tokens
            for token in currency_tokens:
                if not self.web3.is_address(token):
                    raise ValueError(f'Currency token address "{token}" is invalid.')
                
                if token == ZERO_ADDRESS:
                    raise ValueError("Currency token cannot be the zero address.")
            
            # Validate group IP
            is_group_registered = self.ip_asset_registry_client.isRegistered(group_ip_id)
            if not is_group_registered:
                raise ValueError(f"The group IP with ID {group_ip_id} is not registered.")
            
            # Validate member IPs
            for ip_id in member_ip_ids:
                if not self.web3.is_address(ip_id):
                    raise ValueError(f'Member IP ID "{ip_id}" is invalid.')
                
                is_member_registered = self.ip_asset_registry_client.isRegistered(ip_id)
                if not is_member_registered:
                    raise ValueError(f"Member IP with ID {ip_id} is not registered.")
            
            response = build_and_send_transaction(
                self.web3,
                self.account,
                self.grouping_workflows_client.build_collectRoyaltiesAndClaimReward_transaction,
                group_ip_id,
                currency_tokens,
                member_ip_ids,
                tx_options=tx_options
            )

            # Parse events to get collected royalties
            collected_royalties = self._parse_tx_collected_royalties_to_group_pool_event(response['tx_receipt'])
            royalties_distributed = self._parse_tx_royalty_paid_event(response['tx_receipt'])
            
            return {
                'tx_hash': response['tx_hash'],
                'collected_royalties': collected_royalties,
                'royalties_distributed': royalties_distributed
            }
            
        except Exception as e:
            raise ValueError(f"Failed to collect and distribute group royalties: {str(e)}")

    def _get_license_data(self, license_data: list) -> list:
        """
        Process license data into the format expected by the contracts.

        :param license_data list: List of license data objects.
        :return list: Processed license data.
        """
        if not license_data:
            raise ValueError("License data is required.")
        
        result = []
        for item in license_data:
            # Check if license_template is provided
            if 'license_template' in item:
                license_template = item['license_template']
            else:
                license_template = self.pi_license_template_client.contract.address
            
            if not self.web3.is_address(license_template):
                raise ValueError(f'License template address "{license_template}" is invalid.')
            
            # Validate licensing config
            licensing_config = item.get('licensing_config', {})
            
            try:
                self.license_terms_util.validate_licensing_config(licensing_config)
            except Exception as e:
                raise ValueError(f"Licensing config validation failed: {str(e)}")
            
            # Convert to camelCase for contract interaction
            camelcase_config = {
                'isSet': licensing_config.get('is_set', True),
                'mintingFee': licensing_config.get('minting_fee', 0),
                'hookData': licensing_config.get('hook_data', ZERO_ADDRESS),
                'licensingHook': licensing_config.get('licensing_hook', ZERO_ADDRESS),
                'commercialRevShare': licensing_config.get('commercial_rev_share', 0),
                'disabled': licensing_config.get('disabled', False),
                'expectMinimumGroupRewardShare': licensing_config.get('expect_minimum_group_reward_share', 0),
                'expectGroupRewardPool': licensing_config.get('expect_group_reward_pool', ZERO_ADDRESS)
            }
            
            processed_item = {
                'licenseTemplate': license_template,
                'licenseTermsId': item['license_terms_id'],
                'licensingConfig': camelcase_config
            }
            
            result.append(processed_item)
        
        return result

    def _get_ip_metadata(self, ip_metadata: dict = None) -> dict:
        """
        Process IP metadata into the format expected by the contracts.

        :param ip_metadata dict: [Optional] The metadata for the IP.
        :return dict: Processed IP metadata.
        """
        metadata = {
            'ipMetadataURI': "",
            'ipMetadataHash': ZERO_HASH,
            'nftMetadataURI': "",
            'nftMetadataHash': ZERO_HASH,
        }
        
        if ip_metadata:
            metadata.update({
                'ipMetadataURI': ip_metadata.get('ip_metadata_uri', ""),
                'ipMetadataHash': ip_metadata.get('ip_metadata_hash', ZERO_HASH),
                'nftMetadataURI': ip_metadata.get('nft_metadata_uri', ""),
                'nftMetadataHash': ip_metadata.get('nft_metadata_hash', ZERO_HASH),
            })
        
        return metadata

    def _parse_tx_ip_group_registered_event(self, tx_receipt: dict) -> str:
        """
        Parse the IPGroupRegistered event from a transaction receipt.

        :param tx_receipt dict: The transaction receipt.
        :return str: The group ID.
        :raises ValueError: If the event is not found in the transaction receipt.
        """
        event_signature = self.web3.keccak(text="IPGroupRegistered(address,address)").hex()
        
        for log in tx_receipt['logs']:
            if log['topics'][0].hex() == event_signature:
                group_id = '0x' + log['topics'][1].hex()[24:]
                return self.web3.to_checksum_address(group_id)
        
        raise ValueError("IPGroupRegistered event not found in transaction receipt")

    def _parse_tx_ip_registered_event(self, tx_receipt: dict) -> dict:
        """
        Parse the IPRegistered event from a transaction receipt.

        :param tx_receipt dict: The transaction receipt.
        :return dict: The IP ID and token ID.
        :raises ValueError: If the event is not found in the transaction receipt.
        """
        event_signature = self.web3.keccak(
            text="IPRegistered(address,uint256,address,uint256,string,string,uint256)"
        ).hex()
        
        for log in tx_receipt['logs']:
            if log['topics'][0].hex() == event_signature:
                ip_id = '0x' + log['data'].hex()[24:64]
                token_id = int(log['topics'][3].hex(), 16)
                
                return {
                    'ip_id': self.web3.to_checksum_address(ip_id),
                    'token_id': token_id
                }
        
        raise ValueError("IPRegistered event not found in transaction receipt")

    def _parse_tx_collected_royalties_to_group_pool_event(self, tx_receipt: dict) -> list:
        """
        Parse the CollectedRoyaltiesToGroupPool event from a transaction receipt.

        :param tx_receipt dict: The transaction receipt.
        :return list: List of collected royalties.
        """
        event_signature = self.web3.keccak(text="CollectedRoyaltiesToGroupPool(address,address,address,uint256)").hex()
        collected_royalties = []

        for log in tx_receipt['logs']:
            if log['topics'][0].hex() == event_signature:
                group_id = '0x' + log['topics'][1].hex()[24:]
                amount = int(log['data'][:66].hex(), 16)
                token = '0x' + log['topics'][2].hex()[24:]
                
                collected_royalties.append({
                    'group_id': self.web3.to_checksum_address(group_id),
                    'amount': amount,
                    'token': self.web3.to_checksum_address(token)
                })
        
        return collected_royalties

    def _parse_tx_royalty_paid_event(self, tx_receipt: dict) -> list:
        """
        Parse the RoyaltyPaid event from a transaction receipt.

        :param tx_receipt dict: The transaction receipt.
        :return list: List of royalties distributed.
        """
        event_signature = self.web3.keccak(text="RoyaltyPaid(address,address,address,address,uint256,uint256)").hex()
        royalties_distributed = []
        
        for log in tx_receipt['logs']:
            if log['topics'][0].hex() == event_signature:
                receiver_ip_id = '0x' + log['topics'][0].hex()[24:]
                data = log['data']
                amount = int(data[128:160].hex(), 16)
                token = '0x' + data[108:128].hex()
                amount_after_fee = int(data[160:].hex(), 16)
                
                royalties_distributed.append({
                    'ip_id': self.web3.to_checksum_address(receiver_ip_id),
                    'amount': amount,
                    'token': self.web3.to_checksum_address(token),
                    'amount_after_fee': amount_after_fee
                })
        
        return royalties_distributed
