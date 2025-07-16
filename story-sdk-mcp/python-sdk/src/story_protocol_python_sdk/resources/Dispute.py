from web3 import Web3
from eth_abi.abi import encode

from story_protocol_python_sdk.resources.WIP import WIP
from story_protocol_python_sdk.abi.DisputeModule.DisputeModule_client import DisputeModuleClient
from story_protocol_python_sdk.abi.ArbitrationPolicyUMA.ArbitrationPolicyUMA_client import ArbitrationPolicyUMAClient
from story_protocol_python_sdk.abi.IPAccountImpl.IPAccountImpl_client import IPAccountImplClient
from story_protocol_python_sdk.abi.WIP.WIP_client import WIPClient

from story_protocol_python_sdk.utils.transaction_utils import build_and_send_transaction
from story_protocol_python_sdk.utils.ipfs import convert_cid_to_hash_ipfs
from story_protocol_python_sdk.utils.constants import ZERO_ADDRESS
from story_protocol_python_sdk.utils.oov3 import get_assertion_bond

class Dispute:
    """
    A class to manage disputes on Story Protocol.

    :param web3 Web3: An instance of Web3.
    :param account: The account to use for transactions.
    :param chain_id int: The ID of the blockchain network.
    """
    def __init__(self, web3: Web3, account, chain_id: int):
        self.web3 = web3
        self.account = account
        self.chain_id = chain_id

        self.dispute_module_client = DisputeModuleClient(web3)
        self.arbitration_policy_uma_client = ArbitrationPolicyUMAClient(web3)
        self.wip = WIP(web3, account, chain_id)
        self.wip_client = WIPClient(web3)

    def _validate_address(self, address: str) -> str:
        """
        Validates if a string is a valid Ethereum address.
        
        :param address str: The address to validate
        :return str: The validated address
        :raises ValueError: If the address is invalid
        """
        if not self.web3.is_address(address):
            raise ValueError(f"Invalid address: {address}.")
        return address

    def raise_dispute(self, target_ip_id: str, target_tag: str, cid: str, liveness: int, bond: int, tx_options: dict = None) -> dict:
        """
        Raises a dispute on a given IP ID.

        :param target_ip_id str: The IP ID being disputed.
        :param target_tag str: The tag to be applied to the IP.
        :param cid str: The IPFS CID containing dispute evidence.
        :param liveness int: The liveness period for the dispute.
        :param bond int: The bond amount for the dispute.
        :param tx_options dict: [Optional] Transaction options.
        :return dict: A dictionary containing the transaction hash and dispute ID.
        """
        try:
            # Validate target IP address
            target_ip_id = self._validate_address(target_ip_id)

            # Convert tag to bytes32
            tag_bytes = self.web3.to_hex(text=target_tag).ljust(66, '0')

            # Check if tag is whitelisted
            is_whitelisted = self.dispute_module_client.isWhitelistedDisputeTag(tag_bytes)
            if not is_whitelisted:
                raise ValueError(f"The target tag {target_tag} is not whitelisted.")

            # Get liveness bounds
            min_liveness = self.arbitration_policy_uma_client.minLiveness()
            max_liveness = self.arbitration_policy_uma_client.maxLiveness()
            if liveness < min_liveness or liveness > max_liveness:
                raise ValueError(f"Liveness must be between {min_liveness} and {max_liveness}.")

            # Check bond amount
            max_bonds = self.arbitration_policy_uma_client.maxBonds(
                token=self.web3.to_checksum_address("0x1514000000000000000000000000000000000000")
            )
            if bond > max_bonds:
                raise ValueError(f"Bond must be less than {max_bonds}.")

            deposit_response = self.wip.deposit(
                amount=bond
            )

            # Convert CID to IPFS hash
            dispute_evidence_hash = convert_cid_to_hash_ipfs(cid)

            # Encode the data for the arbitration policy
            data = encode(
                ["uint64", "address", "uint256"],
                [
                    liveness,
                    "0x1514000000000000000000000000000000000000", 
                    bond
                ]
            )
            
            response = build_and_send_transaction(
                self.web3,
                self.account,
                self.dispute_module_client.build_raiseDispute_transaction,
                target_ip_id,
                dispute_evidence_hash,
                tag_bytes,
                data,
                tx_options=tx_options
            )

            dispute_id = self._parse_tx_dispute_raised_event(response['tx_receipt'])

            return {
                'tx_hash': response['tx_hash'],
                'dispute_id': dispute_id if dispute_id else None
            }

        except Exception as e:
            raise ValueError(f"Failed to raise dispute: {str(e)}")

    def cancel_dispute(self, dispute_id: int, data: str = "0x", tx_options: dict = None) -> dict:
        """
        Cancels an ongoing dispute.

        :param dispute_id int: The ID of the dispute to cancel.
        :param data str: [Optional] Additional data for the cancellation.
        :param tx_options dict: [Optional] Transaction options.
        :return dict: A dictionary containing the transaction hash.
        """
        try:
            response = build_and_send_transaction(
                self.web3,
                self.account,
                self.dispute_module_client.build_cancelDispute_transaction,
                dispute_id,
                data,
                tx_options=tx_options
            )

            return {
                'tx_hash': response['tx_hash']
            }

        except Exception as e:
            raise ValueError(f"Failed to cancel dispute: {str(e)}")

    def resolve_dispute(self, dispute_id: int, data: str, tx_options: dict = None) -> dict:
        """
        Resolves a dispute after it has been judged.

        :param dispute_id int: The ID of the dispute to resolve.
        :param data str: The resolution data.
        :param tx_options dict: [Optional] Transaction options.
        :return dict: A dictionary containing the transaction hash.
        """
        try:
            response = build_and_send_transaction(
                self.web3,
                self.account,
                self.dispute_module_client.build_resolveDispute_transaction,
                dispute_id,
                data,
                tx_options=tx_options
            )

            return {
                'tx_hash': response['tx_hash']
            }

        except Exception as e:
            raise ValueError(f"Failed to resolve dispute: {str(e)}")

    def tag_if_related_ip_infringed(self, infringement_tags: list, tx_options: dict = None) -> list:
        """
        Tags a derivative if a parent has been tagged with an infringement tag.

        :param infringement_tags list: List of dictionaries containing IP IDs and dispute IDs.
            :param ip_id str: The IP ID to tag.
            :param dispute_id int: The ID of the dispute.
        :param tx_options dict: [Optional] Transaction options.
        :return list: A list of transaction hashes.
        """
        try:
            tx_hashes = []
            
            for tag in infringement_tags:
                ip_id = self._validate_address(tag['ip_id'])
                
                response = build_and_send_transaction(
                    self.web3,
                    self.account,
                    self.dispute_module_client.build_tagIfRelatedIpInfringed_transaction,
                    ip_id,
                    tag['dispute_id'],
                    tx_options=tx_options
                )
                
                tx_hashes.append(response['tx_hash'])

            return tx_hashes

        except Exception as e:
            raise ValueError(f"Failed to tag related IP infringed: {str(e)}")

    def _parse_tx_dispute_raised_event(self, tx_receipt: dict) -> int:
        """
        Parse the DisputeRaised event from a transaction receipt.

        :param tx_receipt dict: The transaction receipt.
        :return int: The dispute ID from the event.
        """
        event_signature = self.web3.keccak(
            text="DisputeRaised(uint256,address,address,uint256,address,bytes32,bytes32,bytes)"
        ).hex()

        for log in tx_receipt['logs']:
            if log['topics'][0].hex() == event_signature:
                data = log['data']
                dispute_id = int.from_bytes(data[:32], byteorder='big')
                return dispute_id
        return None

    def dispute_assertion(self, assertion_id: str, counter_evidence_cid: str, ip_id: str, tx_options: dict = None) -> dict:
        """
        Counters a dispute that was raised by another party on an IP using counter evidence.
        The counter evidence (e.g., documents, images) should be uploaded to IPFS,
        and its corresponding CID is converted to a hash for the request.

        The liveness period is split in two parts:
        - the first part of the liveness period in which only the IP's owner can be called the method.
        - a second part in which any address can be called the method.

        If you only have a disputeId, call dispute_id_to_assertion_id to get the assertionId needed here.

        :param assertion_id str: The ID of the assertion to dispute.
        :param counter_evidence_cid str: The IPFS CID of the counter evidence.
        :param ip_id str: The IP ID related to the dispute.
        :param tx_options dict: [Optional] Transaction options.
        :return dict: Transaction response containing tx_hash and receipt.
        """
        try:
            # Validate IP ID
            ip_id = self._validate_address(ip_id)
            
            # Create IP Account client
            ip_account = IPAccountImplClient(self.web3, contract_address=ip_id)
            
            # Get assertion details to determine bond amount
            bond = get_assertion_bond(self.web3, self.arbitration_policy_uma_client, assertion_id)

            # Check if user has enough WIP tokens
            user_balance = self.wip.balance_of(address=self.account.address)
            
            if user_balance < bond:
                raise ValueError(f"Insufficient WIP balance. Required: {bond}, Available: {user_balance}")
            
            # Convert CID to IPFS hash
            counter_evidence_hash = convert_cid_to_hash_ipfs(counter_evidence_cid)
            
            # Get encoded data for dispute assertion
            encoded_data = self.arbitration_policy_uma_client.contract.encode_abi(
                abi_element_identifier="disputeAssertion",
                args= [
                    assertion_id,
                    counter_evidence_hash
                ]
            )

            # Check allowance
            allowance = self.wip.allowance(
                owner=self.account.address,
                spender=ip_account.contract.address
            )
                        
            # Approve IP Account to transfer WrappedIP tokens if needed
            if allowance < bond:
                approve_tx = self.wip.approve(
                    spender=ip_account.contract.address,
                    amount=2**256 - 1  # maxUint256
                )
            
            # Prepare calls for executeBatch
            calls = []
            
            if bond > 0:
                # Transfer tokens from wallet to IP Account
                transfer_data = self.wip_client.contract.encode_abi(
                    abi_element_identifier="transferFrom",
                    args=[
                        self.account.address,
                        ip_account.contract.address,
                        bond
                    ]
                )
                calls.append({
                    'target': self.wip_client.contract.address,
                    'value': 0,
                    'data': transfer_data
                })
                
                # Approve arbitration policy to spend tokens
                approve_data = self.wip_client.contract.encode_abi(
                    abi_element_identifier="approve",
                    args=[
                        self.arbitration_policy_uma_client.contract.address,
                        2**256 - 1  # maxUint256
                    ]
                )
                calls.append({
                    'target': self.wip_client.contract.address,
                    'value': 0,
                    'data': approve_data
                })
            
            # Add dispute assertion call
            calls.append({
                'target': self.arbitration_policy_uma_client.contract.address,
                'value': 0,
                'data': encoded_data
            })
            
            # Execute batch transaction
            response = build_and_send_transaction(
                self.web3,
                self.account,
                ip_account.build_executeBatch_transaction,
                calls,
                0,
                tx_options=tx_options
            )

            return {
                'tx_hash': response['tx_hash'],
                'receipt': response.get('tx_receipt')
            }
            
        except Exception as e:
            raise ValueError(f"Failed to dispute assertion: {str(e)}")

    def dispute_id_to_assertion_id(self, dispute_id: int) -> str:
        """
        Converts a dispute ID to its corresponding assertion ID.

        :param dispute_id int: The dispute ID to convert.
        :return str: The corresponding assertion ID as a hex string.
        :raises ValueError: If there is an error during the conversion.
        """
        try:
            assertion_id = self.arbitration_policy_uma_client.disputeIdToAssertionId(dispute_id)
            return assertion_id
        except Exception as e:
            raise ValueError(f"Failed to convert dispute ID to assertion ID: {str(e)}")
    
    def get_assertion_bond(self, assertion_id: str) -> int:
        """
        Get the bond amount for a given assertion ID.
        """
        return get_assertion_bond(self.web3, self.arbitration_policy_uma_client, assertion_id)