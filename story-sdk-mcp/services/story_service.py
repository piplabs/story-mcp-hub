from web3 import Web3
from story_protocol_python_sdk.story_client import StoryClient
import requests
import os
from typing import Union, Optional
import time
import json
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Add the parent directory to the Python path so we can import utils
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.address_resolver import create_address_resolver
from utils.contract_addresses import get_contracts_by_chain_id, CHAIN_IDS
from .erc20_abi import ERC20_ABI, ERC20_FUNCTIONS


class StoryService:

    def __init__(self, rpc_url: str, private_key: str, network: str = None):
        """
        Initialize Story Protocol service with RPC URL and private key.

        Args:
            rpc_url: RPC URL for the blockchain
            private_key: Private key for signing transactions
            network: Optional network name ('aeneid' or 'mainnet') to override auto-detection
        """
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.web3.is_connected():
            raise Exception("Failed to connect to the Web3 provider")

        self.account = self.web3.eth.account.from_key(private_key)

        # Detect chain ID
        self.chain_id = self.web3.eth.chain_id

        # If network is explicitly provided, use it instead of auto-detection
        if network:
            if network.lower() not in ["aeneid", "mainnet"]:
                raise ValueError(
                    f"Unsupported network: {network}. Must be 'aeneid' or 'mainnet'"
                )
            self.network = network.lower()
            self.chain_id = CHAIN_IDS[self.network]
        else:
            # Auto-detect network based on chain ID
            if self.chain_id == CHAIN_IDS["aeneid"]:
                self.network = "aeneid"
            elif self.chain_id == CHAIN_IDS["mainnet"]:
                self.network = "mainnet"
            else:
                raise ValueError(
                    f"Unsupported chain ID: {self.chain_id}. Must be {CHAIN_IDS['aeneid']} (Aeneid) or {CHAIN_IDS['mainnet']} (Mainnet)"
                )

        # Initialize Story client with detected chain ID
        self.client = StoryClient(
            web3=self.web3, account=self.account, chain_id=self.chain_id
        )

        # Get contract addresses for the detected network
        self.contracts = get_contracts_by_chain_id(self.chain_id)

        # Set license template from contracts
        self.LICENSE_TEMPLATE = self.contracts["PILicenseTemplate"]

        # Initialize Pinata JWT
        self.pinata_jwt = os.getenv("PINATA_JWT")
        if not self.pinata_jwt:
            self.ipfs_enabled = False
            print(
                "Warning: PINATA_JWT environment variable not found. IPFS functions will be disabled."
            )
        else:
            self.ipfs_enabled = True

        # Initialize address resolver
        self.address_resolver = create_address_resolver(
            self.web3, chain_id=CHAIN_IDS["mainnet"]
        )  # Story Protocol chain ID for .ip domains
        

    def get_license_terms(self, license_terms_id: int) -> str:
        """Get the license terms for a specific ID."""
        logger.info("love youuuuuuuuuuuuuuuuuu")
        response = self.client.License.get_license_terms(license_terms_id)
        logger.info("love you 2")

        if not response:
            raise ValueError(f"No license terms found for ID {license_terms_id}")

        return {
            "transferable": response[0],
            "royaltyPolicy": response[1],
            "defaultMintingFee": response[2],
            "expiration": response[3],
            "commercialUse": response[4],
            "commercialAttribution": response[5],
            "commercializerChecker": response[6],
            "commercializerCheckerData": response[7].hex()
            if isinstance(response[7], bytes)
            else response[7],
            "commercialRevShare": response[8],
            "commercialRevCeiling": response[9],
            "derivativesAllowed": response[10],
            "derivativesAttribution": response[11],
            "derivativesApproval": response[12],
            "derivativesReciprocal": response[13],
            "derivativeRevCeiling": response[14],
            "currency": response[15],
            "uri": response[16],
        }

    def get_license_minting_fee(self, license_terms_id: int) -> int:
        """
        Get the minting fee for a specific license terms ID.
        
        Args:
            license_terms_id: The ID of the license terms
            
        Returns:
            int: The minting fee in wei
        """
        response = self.client.License.get_license_terms(license_terms_id)
        if not response:
            raise ValueError(f"No license terms found for ID {license_terms_id}")
        
        return response[2]  # defaultMintingFee

    def get_license_revenue_share(self, license_terms_id: int) -> int:
        """
        Get the commercial revenue share percentage for a specific license terms ID.
        
        Args:
            license_terms_id: The ID of the license terms
            
        Returns:
            int: The commercial revenue share percentage (0-100)
        """
        response = self.client.License.get_license_terms(license_terms_id)
        if not response:
            raise ValueError(f"No license terms found for ID {license_terms_id}")
        
        return response[8] / (10 ** 6)  # commercialRevShare

    def mint_license_tokens(
        self,
        licensor_ip_id: str,
        license_terms_id: int,
        receiver: Optional[str] = None,
        amount: int = 1,
        max_minting_fee: Optional[int] = None,
        max_revenue_share: Optional[int] = None,
        license_template: Optional[str] = None
    ) -> dict:
        """
        Mints license tokens for the license terms attached to an IP.
        Automatically approves the exact amount of WIP tokens needed for the transaction.

        Args:
            licensor_ip_id: The licensor IP ID
            license_terms_id: The ID of the license terms
            receiver: Optional address of the receiver (defaults to sender)
            amount: Optional amount of license tokens to mint (defaults to 1)
            max_minting_fee: [Optional] maximum minting fee in wei (defaults to 0)
            max_revenue_share: [Optional] maximum revenue share percentage 0-100 (defaults to 0)
            license_template: [Optional] address of the license template (defaults to the default template)

        Returns:
            dict: Dictionary with the transaction hash and license token IDs
        """
        try:
            # Use default license template if none provided
            if license_template is None:
                license_template = self.LICENSE_TEMPLATE
            
            # Use sender address if receiver not provided
            if receiver is None:
                receiver = self.account.address
            
            # Default values for max_minting_fee and max_revenue_share
            if max_minting_fee is None:
                max_minting_fee = 0
                
            if max_revenue_share is None:
                max_revenue_share = 0
            
            # Ensure addresses are checksummed
            license_template = self.web3.to_checksum_address(license_template)
            receiver = self.web3.to_checksum_address(receiver)
            
            # Handle approve logic
            license_spender = "0xD2f60c40fEbccf6311f8B47c4f2Ec6b040400086"
            required_amount = max_minting_fee  # The amount needed for the transaction
            
            # auto-approve WIP tokens for minting license tokens
            if required_amount > 0:
                self._approve_token(
                    token_address="0x1514000000000000000000000000000000000000",  # WIP token
                    spender=license_spender, 
                    approve_amount=required_amount)
            
            # Call the SDK function
            result = self.client.License.mint_license_tokens(
                licensor_ip_id=licensor_ip_id,
                license_template=license_template,
                license_terms_id=license_terms_id,
                amount=amount,
                receiver=receiver,
                max_minting_fee=max_minting_fee,
                max_revenue_share=max_revenue_share
            )
            
            return {
                'tx_hash': result.get('tx_hash'),
                'license_token_ids': result.get('license_token_ids', [])
            }
            
        except Exception as e:
            print(f"Error minting license tokens: {str(e)}")
            raise

    # def send_ip(self, to_address: str, amount: float) -> dict:
    #     """
    #     Send IP tokens to a specified address using native token transfer.

    #     :param to_address: Recipient's address or domain name
    #     :param amount: Amount of IP tokens to send (1 IP = 1 Ether)
    #     :return: Transaction details
    #     """
    #     try:
    #         # Resolve the recipient address
    #         resolved_address = self.address_resolver.resolve_address(to_address)

    #         # Convert amount to Wei (1 IP = 1 Ether)
    #         value_in_wei = self.web3.to_wei(amount, "ether")

    #         # Set a default gas price if we can't get it from the network
    #         try:
    #             gas_price = self.web3.eth.gas_price
    #         except Exception:
    #             # Fallback gas price (50 gwei)
    #             gas_price = self.web3.to_wei(50, "gwei")

    #         # Estimate gas limit for this transaction
    #         try:
    #             gas_estimate = self.web3.eth.estimate_gas(
    #                 {
    #                     "to": resolved_address,
    #                     "from": self.account.address,
    #                     "value": value_in_wei,
    #                 }
    #             )
    #         except Exception:
    #             # Fallback gas limit
    #             gas_estimate = 21000  # Standard transfer gas limit

    #         # Build the transaction with dynamic gas settings
    #         transaction = {
    #             "to": resolved_address,
    #             "value": value_in_wei,
    #             "gas": gas_estimate,
    #             "gasPrice": gas_price,
    #             "nonce": self.web3.eth.get_transaction_count(self.account.address),
    #             "chainId": 1315,  # Story Protocol chain ID
    #         }

    #         # Sign and send the transaction
    #         signed_txn = self.account.sign_transaction(transaction)
    #         tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)

    #         # Wait for transaction receipt
    #         tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

    #         return {"tx_hash": tx_hash.hex(), "tx_receipt": tx_receipt}
    #     except Exception as e:
    #         print(f"Error details: {str(e)}")
    #         raise

    def upload_image_to_ipfs(self, image_data: Union[bytes, str]) -> str:
        """Upload an image to IPFS using Pinata API"""
        if not self.ipfs_enabled:
            raise Exception(
                "IPFS functions are disabled. Please provide PINATA_JWT environment variable."
            )

        try:
            # If image_data is a URL, download it first
            if isinstance(image_data, str) and image_data.startswith("http"):
                response = requests.get(image_data)
                image_data = response.content

            # Upload to Pinata
            headers = {"Authorization": f"Bearer {self.pinata_jwt}"}
            files = {"file": ("image.png", image_data, "image/png")}

            response = requests.post(
                "https://api.pinata.cloud/pinning/pinFileToIPFS",
                files=files,
                headers=headers,
            )

            if response.status_code != 200:
                raise Exception(f"Failed to upload to IPFS: {response.text}")

            return f"ipfs://{response.json()['IpfsHash']}"
        except Exception as e:
            print(f"Error uploading to IPFS: {str(e)}")
            raise

    # def mint_and_register_ip_asset(
    #     self,
    #     spg_nft_contract: str,
    #     recipient: Optional[str] = None,
    #     ip_metadata: Optional[dict] = None,
    #     allow_duplicates: bool = True,
    #     spg_nft_contract_max_minting_fee: Optional[int] = None,
    #     approve_amount: Optional[int] = None
    # ) -> dict:
    #     """
    #     Mint an NFT and register it as an IP asset in one transaction (without license terms).

    #     Args:
    #         spg_nft_contract: The address of the SPG NFT contract to mint from
    #         recipient: Optional recipient address (defaults to sender)
    #         ip_metadata: Optional metadata for the IP
    #             ip_metadata_uri: Optional metadata URI for the IP
    #             ip_metadata_hash: Optional metadata hash for the IP
    #             nft_metadata_uri: Optional metadata URI for the NFT
    #             nft_metadata_hash: Optional metadata hash for the NFT
    #         spg_nft_contract_max_minting_fee: Optional maximum minting fee user is willing to pay (in wei).
    #                         If not specified, will accept whatever the contract requires.
    #                         If specified, will reject if contract requires more than this amount.
    #         approve_amount: Optional amount to approve for spending WIP tokens. If None, uses the exact amount needed for the transaction.

    #     Returns:
    #         str: Result message with transaction details
    #     """
    #     try:
    #         # Validate inputs
    #         if spg_nft_contract_max_minting_fee is not None and spg_nft_contract_max_minting_fee < 0:
    #             raise ValueError("spg_nft_contract_max_minting_fee must be non-negative")

    #         # Resolve recipient address if provided
    #         resolved_recipient = (
    #             self.address_resolver.resolve_address(recipient)
    #             if recipient
    #             else self.account.address
    #         )

    #         # Use default SPG NFT contract if none provided
    #         if spg_nft_contract is None:
    #             spg_nft_contract = self.contracts["SPG_NFT"]
            
    #         # Check if the contract requires a minting fee
    #         fee_info = self.get_spg_nft_contract_minting_fee(spg_nft_contract)
    #         required_fee = fee_info['mint_fee']
            
    #         # Validate against user's maximum if specified
    #         if spg_nft_contract_max_minting_fee is not None and required_fee > spg_nft_contract_max_minting_fee:
    #             raise ValueError(
    #                 f"SPG contract requires minting fee of {required_fee} wei, "
    #                 f"but your maximum is {spg_nft_contract_max_minting_fee} wei. "
    #                 f"Increase spg_nft_contract_max_minting_fee or use a different contract."
    #             )
            
    #         # Handle approve logic
    #         mint_and_register_spender = "0xa38f42B8d33809917f23997B8423054aAB97322C"
            
    #         # approve WIP tokens for minting and registering IP asset
    #         if required_fee > 0:
    #             approve_transaction_hash = self._approve_wip(
    #                 spender=mint_and_register_spender, 
    #                 required_amount=required_fee, 
    #                 approve_amount=approve_amount)
            
    #         # Use the SDK method directly
    #         response = self.client.IPAsset.mint_and_register_ip(
    #             spg_nft_contract=spg_nft_contract,
    #             ip_metadata=ip_metadata,
    #             recipient=resolved_recipient,
    #             allow_duplicates=allow_duplicates,
    #         )
                    
    #         return {
    #             "tx_hash": response.get("tx_hash"),
    #             "ip_id": response.get("ip_id"),
    #             "token_id": response.get("token_id"),
    #             "actual_minting_fee": required_fee,
    #             "max_minting_fee": spg_nft_contract_max_minting_fee,
    #         }

    #     except Exception as e:
    #         print(f"Error minting and registering IP asset: {str(e)}")
    #         raise
    
    def create_ip_metadata(
        self, image_uri: str, name: str, description: str, attributes: list = None
    ) -> dict:
        """
        Create both NFT and IP metadata and upload to IPFS

        Args:
            image_uri: IPFS URI of the uploaded image
            name: Name of the NFT/IP
            description: Description of the NFT/IP
            attributes: Optional list of attribute dictionaries
        Returns:
            dict: Both metadata URIs and their hashes
        """
        if not self.ipfs_enabled:
            raise Exception(
                "IPFS functions are disabled. Please provide PINATA_JWT environment variable."
            )

        try:
            # Get image hash if it's a URL
            if image_uri.startswith("http"):
                image_hash = self._get_file_hash(image_uri)
            else:
                # For IPFS URIs, extract hash from URI
                image_hash = image_uri.replace("ipfs://", "")

            # Create NFT metadata (standard ERC721 format)
            nft_metadata = {
                "name": name,
                "description": description,
                "image": image_uri,
                "attributes": attributes or [],
            }

            # Create IP metadata following Story Protocol standard
            ip_metadata = {
                "title": name,
                "description": description,
                "createdAt": int(time.time()),
                "image": image_uri,
                "imageHash": f"0x{image_hash}",  # Add 0x prefix
                "mediaUrl": image_uri,
                "mediaHash": f"0x{image_hash}",  # Same as imageHash since they point to same file
                "mediaType": "image/png",  # Adjust based on actual image type
            }

            # Upload NFT metadata to IPFS
            nft_response = requests.post(
                "https://api.pinata.cloud/pinning/pinJSONToIPFS",
                json=nft_metadata,
                headers={
                    "Authorization": f"Bearer {self.pinata_jwt}",
                    "Content-Type": "application/json",
                },
            )
            if nft_response.status_code != 200:
                raise Exception(f"Failed to upload NFT metadata: {nft_response.text}")
            nft_metadata_uri = f"ipfs://{nft_response.json()['IpfsHash']}"

            # Upload IP metadata to IPFS
            ip_response = requests.post(
                "https://api.pinata.cloud/pinning/pinJSONToIPFS",
                json=ip_metadata,
                headers={
                    "Authorization": f"Bearer {self.pinata_jwt}",
                    "Content-Type": "application/json",
                },
            )
            if ip_response.status_code != 200:
                raise Exception(f"Failed to upload IP metadata: {ip_response.text}")
            ip_metadata_uri = f"ipfs://{ip_response.json()['IpfsHash']}"

            # Generate hashes of the metadata JSONs (32-byte) and convert to 0x-prefixed hex
            nft_metadata_hash_bytes = self.web3.keccak(
                text=json.dumps(nft_metadata, sort_keys=True)
            )
            ip_metadata_hash_bytes = self.web3.keccak(
                text=json.dumps(ip_metadata, sort_keys=True)
            )

            nft_metadata_hash = Web3.to_hex(nft_metadata_hash_bytes)
            ip_metadata_hash = Web3.to_hex(ip_metadata_hash_bytes)

            # Create metadata structure for registration
            registration_metadata = {
                "ip_metadata_uri": ip_metadata_uri,
                "ip_metadata_hash": ip_metadata_hash,
                "nft_metadata_uri": nft_metadata_uri,
                "nft_metadata_hash": nft_metadata_hash,
            }

            return {
                "nft_metadata": nft_metadata,
                "nft_metadata_uri": nft_metadata_uri,
                "nft_metadata_hash": nft_metadata_hash,
                "ip_metadata": ip_metadata,
                "ip_metadata_uri": ip_metadata_uri,
                "ip_metadata_hash": ip_metadata_hash,
                "registration_metadata": registration_metadata,
            }

        except Exception as e:
            print(f"Error creating metadata: {str(e)}")
            raise

    async def _get_file_hash(self, url: str) -> str:
        """
        Get hash of a file from its URL using web3's keccak

        Args:
            url: URL of the image/media file
        Returns:
            str: Hash in hex format without 0x prefix
        """
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to download file: {response.text}")

        # Hash the raw bytes using web3's keccak
        file_hash = self.web3.keccak(response.content)
        return file_hash.hex()[2:]  # Remove 0x prefix

    def mint_and_register_ip_with_terms(
        self,
        commercial_rev_share: int,
        derivatives_allowed: bool,
        registration_metadata: dict,
        commercial_use: bool = True,
        minting_fee: int = 0,
        recipient: Optional[str] = None,
        spg_nft_contract: Optional[str] = None,
        spg_nft_contract_max_minting_fee: Optional[int] = None,
        spg_nft_contract_mint_fee_token: Optional[str] = None
    ) -> dict:
        """
        Mint an NFT, register it as an IP Asset, and attach PIL terms.
        Automatically detects if the SPG contract requires a minting fee and handles it appropriately.
        Automatically approves the exact amount of tokens needed for the transaction.

        Args:
            commercial_rev_share: Percentage of revenue share (0-100)
            derivatives_allowed: Whether derivatives are allowed (if True, then derivatives_attribution=True 
                                and derivatives_reciprocal=True are automatically set, meaning derivative works 
                                must provide attribution and can create further derivatives under the same terms; 
                                if False, then derivatives_attribution=False and derivatives_reciprocal=False, 
                                meaning no derivative works can be created)
            registration_metadata: Dict containing metadata URIs and hashes from create_ip_metadata
            commercial_use: [Optional]Whether this is a commercial license (defaults to True)
            minting_fee: [Optional] Fee required to mint license tokens in wei (defaults to 0)
            recipient: [Optional] recipient address or domain name (defaults to sender)
            spg_nft_contract: [Optional] SPG NFT contract address (defaults to network-specific default)
            spg_nft_contract_max_minting_fee: [Optional] maximum minting fee user is willing to pay for SPG contract (in wei).
                                            If None, will accept whatever the contract requires.
                                            If specified, will reject if contract requires more than this amount.
            spg_nft_contract_mint_fee_token: [Optional] token address for SPG contract minting fee (e.g., WIP, MERC20).
                                              If None, will auto-detect from the SPG contract.
                                              If specified, will validate and use this token for fee payment.
        """
        try:
            # Validate inputs
            if not (0 <= commercial_rev_share <= 100):
                raise ValueError("commercial_rev_share must be between 0 and 100")
            
            if not commercial_use and commercial_rev_share > 0:
                raise ValueError("commercial_rev_share must be 0 for non-commercial use")
            
            if minting_fee < 0:
                raise ValueError("minting_fee must be non-negative")

            if spg_nft_contract_max_minting_fee is not None and spg_nft_contract_max_minting_fee < 0:
                raise ValueError("spg_nft_contract_max_minting_fee must be non-negative")

            # Validate spg_nft_contract_mint_fee_token if provided
            if spg_nft_contract_mint_fee_token is not None:
                try:
                    # Ensure it's a valid address format
                    spg_nft_contract_mint_fee_token = self.web3.to_checksum_address(spg_nft_contract_mint_fee_token)
                except Exception:
                    raise ValueError(f"spg_nft_contract_mint_fee_token must be a valid address, got: {spg_nft_contract_mint_fee_token}")

            # Resolve recipient address if provided
            resolved_recipient = (
                self.address_resolver.resolve_address(recipient)
                if recipient
                else self.account.address
            )

            # Use default SPG NFT contract if none provided
            if spg_nft_contract is None:
                spg_nft_contract = self.contracts["SPG_NFT"]
            
            fee_info = self.get_spg_nft_contract_minting_fee_and_token(spg_nft_contract)
            required_fee = fee_info['mint_fee']
            mint_fee_token = fee_info['mint_fee_token']

            # Validate that the provided token matches what the contract expects
            if spg_nft_contract_mint_fee_token and mint_fee_token.lower() != spg_nft_contract_mint_fee_token.lower():
                raise ValueError(
                    f"Token mismatch: SPG contract expects {mint_fee_token} but you provided {spg_nft_contract_mint_fee_token}. "
                    f"please either use the correct token address or set spg_nft_contract_mint_fee_token=None for auto-detection."
                )
                
            
            # Validate against user's maximum if specified
            if spg_nft_contract_max_minting_fee is not None and required_fee > spg_nft_contract_max_minting_fee:
                raise ValueError(
                    f"SPG contract requires minting fee of {required_fee} wei, "
                    f"but your maximum is {spg_nft_contract_max_minting_fee} wei. "
                    f"Increase spg_nft_contract_max_minting_fee or use a different contract."
                )
            
            # Handle approve logic - auto-approve the exact amount needed
            mint_and_register_spender = "0xa38f42B8d33809917f23997B8423054aAB97322C"
            if required_fee > 0:
                approve_transaction_hash = self._approve_token(
                    token_address=mint_fee_token,
                    spender=spg_nft_contract,
                    approve_amount=required_fee
                )
            
            # Use appropriate royalty policy based on commercial use
            royalty_policy = self.contracts["RoyaltyPolicyLAP"] if commercial_use else "0x0000000000000000000000000000000000000000"

            # Create terms matching the SDK structure
            terms = [{
                'terms': {
                    'transferable': True,
                    'royalty_policy': royalty_policy,
                    'default_minting_fee': minting_fee,
                    'expiration': 0,
                    'commercial_use': commercial_use,
                    'commercial_attribution': False,
                    'commercializer_checker': "0x0000000000000000000000000000000000000000",
                    'commercializer_checker_data': "0x0000000000000000000000000000000000000000",
                    'commercial_rev_share': commercial_rev_share,
                    'commercial_rev_ceiling': 0,
                    'derivatives_allowed': derivatives_allowed,
                    'derivatives_attribution': derivatives_allowed,  # Auto-set based on derivatives_allowed
                    'derivatives_approval': False,
                    'derivatives_reciprocal': derivatives_allowed,   # Auto-set based on derivatives_allowed
                    'derivative_rev_ceiling': 0,
                    'currency': "0x1514000000000000000000000000000000000000",
                    'uri': "",
                },
                'licensing_config': {
                    'is_set': False,
                    'minting_fee': minting_fee,
                    'hook_data': "",
                    'licensing_hook': "0x0000000000000000000000000000000000000000",
                    'commercial_rev_share': commercial_rev_share,
                    'disabled': False,
                    'expect_minimum_group_reward_share': 0,
                    'expect_group_reward_pool': "0x0000000000000000000000000000000000000000",
                }
            }]

            # Add tx_options if fee is required
            tx_options = None
            if required_fee > 0:
                tx_options = {'value': required_fee}
                fee_ether = self.web3.from_wei(required_fee, 'ether')
                print(f"SPG contract requires minting fee: {required_fee} wei ({fee_ether} IP)")
            else:
                print("SPG contract is free. Using SDK without additional fees.")

            # Use the SDK method directly
            response = self.client.IPAsset.mint_and_register_ip_asset_with_pil_terms(
                spg_nft_contract=spg_nft_contract,
                terms=terms,
                ip_metadata=registration_metadata,
                recipient=resolved_recipient,
                allow_duplicates=True,
                tx_options=None,
            )
                    
            return {
                "tx_hash": response.get("tx_hash"),
                "ip_id": response.get("ip_id"),
                "token_id": response.get("token_id"),
                "license_terms_ids": response.get("license_terms_ids"),
                "actual_minting_fee": required_fee,
                "max_minting_fee": spg_nft_contract_max_minting_fee,
            }

        except Exception as e:
            print(f"Error in mint_and_register_ip_with_terms: {str(e)}")
            raise

    def create_spg_nft_collection(
        self,
        name: str,
        symbol: str,
        is_public_minting: bool = True,
        mint_open: bool = True,
        mint_fee_recipient: Optional[str] = None,
        contract_uri: str = "",
        base_uri: str = "",
        max_supply: Optional[int] = None,
        mint_fee: Optional[int] = None,
        mint_fee_token: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> dict:
        """
        Create a new SPG NFT collection that can be used for minting and registering IP assets.

        Args:
            name: (REQUIRED) Name of the NFT collection
            symbol: (REQUIRED) Symbol for the NFT collection
            is_public_minting: (OPTIONAL, default=True) Whether anyone can mint NFTs from this collection
            mint_open: (OPTIONAL, default=True) Whether minting is currently enabled
            mint_fee_recipient: (OPTIONAL) Address to receive minting fees (defaults to sender)
            contract_uri: (OPTIONAL) URI for the collection metadata (ERC-7572 standard)
            base_uri: (OPTIONAL) Base URI for the collection. If not empty, tokenURI will be either
                     baseURI + token ID or baseURI + nftMetadataURI
            max_supply: (OPTIONAL) Maximum supply of the collection in number of tokens (defaults to unlimited)
            mint_fee: (OPTIONAL) Cost to mint a token in wei (defaults to 0)
            mint_fee_token: (OPTIONAL) Token address used for minting fees (defaults to native IP token)
            owner: (OPTIONAL) Owner address of the collection (defaults to sender)

        Returns:
            dict: Information about the created collection including:
                - tx_hash: Transaction hash
                - spg_nft_contract: Address of the created collection

        Note:
            The underlying SDK supports additional transaction options (tx_options)
            which are intentionally not exposed here as they're too low-level for agent interfaces.
        """

        try:
            # Validate mint fee recipient when there's a fee
            # if mint_fee_recipient is None and mint_fee is not None and mint_fee > 0:
            #     raise Exception("Mint fee recipient is required if mint fee is greater than 0")
            
            # Default mint_fee_recipient to zero address if not provided
            if mint_fee_recipient is None:
                mint_fee_recipient = self.account.address
            else:
                # Resolve the address if it's a domain name
                mint_fee_recipient = self.address_resolver.resolve_address(
                    mint_fee_recipient
                )

            # Resolve owner address if provided, otherwise use sender's address
            if owner:
                owner = self.address_resolver.resolve_address(owner)
            else:
                owner = self.account.address

            # Handle mint_fee_token default: if mint_fee >= 0 and mint_fee_token is None, 
            # default to zero address (native token)
            if mint_fee is not None and mint_fee >= 0 and mint_fee_token is None:
                mint_fee_token = "0x1514000000000000000000000000000000000000"

        

            # Use the SDK's built-in NFTClient with correct method name
            response = self.client.NFTClient.create_nft_collection(
                name=name,
                symbol=symbol,
                is_public_minting=is_public_minting,
                mint_open=mint_open,
                mint_fee_recipient=mint_fee_recipient,
                contract_uri=contract_uri,
                base_uri=base_uri,
                max_supply=max_supply,
                mint_fee=mint_fee,
                mint_fee_token=mint_fee_token,
                owner=owner,
                tx_options=None,  # Always use default transaction options
            )

            return {
                "tx_hash": response.get("tx_hash"),
                "spg_nft_contract": response.get("nft_contract"),
            }

        except Exception as e:
            print(f"Error creating SPG NFT collection: {str(e)}")
            raise

    # def mint_nft(
    #     self,
    #     nft_contract: str,
    #     to_address: str,
    #     metadata_uri: str,
    #     metadata_hash: bytes,
    #     allow_duplicates: bool = False,
    # ) -> dict:
    #     """
    #     Mint an NFT from an existing SPG collection using the Story Protocol SDK.
        
    #     Uses the IPAsset.mint() method from the Story Protocol Python SDK to mint NFTs from SPG contracts.

    #     Args:
    #         nft_contract: The address of the SPG NFT contract to mint from
    #         to_address: The recipient address for the minted NFT
    #         metadata_uri: The metadata URI for the NFT
    #         metadata_hash: The metadata hash as bytes
    #         allow_duplicates: Whether to allow minting NFTs with duplicate metadata (default: False)

    #     Returns:
    #         dict: Dictionary with the transaction hash, token ID, and contract address
    #     """
    #     try:
    #         # Ensure the contract address is checksummed
    #         nft_contract = self.web3.to_checksum_address(nft_contract)
    #         to_address = self.web3.to_checksum_address(to_address)
            
    #         print(f"Minting NFT from contract: {nft_contract}")
    #         print(f"To address: {to_address}")
    #         print(f"Metadata URI: {metadata_uri}")
    #         print(f"Allow duplicates: {allow_duplicates}")
            
    #         # Use the SDK's IPAsset.mint() method
    #         tx_hash = self.client.IPAsset.mint(
    #             nft_contract=nft_contract,
    #             to_address=to_address,
    #             metadata_uri=metadata_uri,
    #             metadata_hash=metadata_hash,
    #             allow_duplicates=allow_duplicates,
    #             tx_options=None  # No transaction options for now
    #         )
            
    #         # Get transaction receipt to extract token ID
    #         tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
    #         # Extract token ID from logs
    #         token_id = None
    #         try:
    #             # Look for Transfer event logs to get token ID
    #             transfer_event_signature = self.web3.keccak(text="Transfer(address,address,uint256)").hex()
    #             for log in tx_receipt['logs']:
    #                 if len(log['topics']) >= 4 and log['topics'][0].hex() == transfer_event_signature:
    #                     # Token ID is the 4th topic (index 3)
    #                     token_id = int(log['topics'][3].hex(), 16)
    #                     break
    #         except Exception as e:
    #             print(f"Warning: Could not extract token ID from logs: {e}")
    #             token_id = None
            
    #         return {
    #             'txHash': tx_hash,
    #             'tokenId': token_id,
    #             'nftContract': nft_contract,
    #             'recipient': to_address,
    #             'metadataUri': metadata_uri,
    #             'gasUsed': tx_receipt['gasUsed']
    #         }
            
    #     except Exception as e:
    #         print(f"Error minting NFT: {str(e)}")
    #         raise

    
    # def register_pil_terms(
    #     self,
    #     transferable: bool = False,
    #     commercial_use: bool = False,
    #     derivatives_allowed: bool = False,
    #     default_minting_fee: int = 92
    # ) -> dict:
    #     """Register new PIL terms with customizable parameters."""
    #     response = self.client.License.registerPILTerms(
    #         transferable=transferable,
    #         royalty_policy=self.web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
    #         default_minting_fee=default_minting_fee,
    #         expiration=0,
    #         commercial_use=commercial_use,
    #         commercial_attribution=False,
    #         commercializer_checker=self.web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
    #         commercializer_checker_data="0x",
    #         commercial_rev_share=0,
    #         commercial_rev_ceiling=0,
    #         derivatives_allowed=derivatives_allowed,
    #         derivatives_attribution=False,
    #         derivatives_approval=False,
    #         derivatives_reciprocal=False,
    #         derivative_rev_ceiling=0,
    #         currency=self.web3.to_checksum_address("0x0000000000000000000000000000000000000000"),
    #         uri=""
    #     )
    #     return response

    # def register_non_commercial_social_remixing_pil(self) -> dict:
    #     """Register a non-commercial social remixing PIL license."""
    #     return self.client.License.registerNonComSocialRemixingPIL()

    # TODO: don't need this function for now
    # def register_ip_asset(self, nft_contract: str, token_id: int, metadata: dict) -> dict:
    #     """
    #     Register an NFT as an IP Asset with metadata

    #     :param nft_contract: NFT contract address
    #     :param token_id: Token ID of the NFT
    #     :param metadata: IP Asset metadata following Story Protocol standard
    #     :return: Transaction details
    #     """
    #     try:
    #         # Using the IPAsset module from the SDK
    #         response = self.client.IPAsset.registerRootIP(
    #             nftContract=self.web3.to_checksum_address(nft_contract),
    #             tokenId=token_id,
    #             metadata=metadata
    #         )
    #         return response
    #     except Exception as e:
    #         print(f"Error registering IP asset: {str(e)}")
    #         raise

    
    # TODO: keep this function and test for now - pass in spg nft contract. image url -> upload to ipfs -> create metadata -> mint and register nft
    # def mint_and_register_nft(self, to_address: str, metadata_uri: str, ip_metadata: dict) -> dict:
    #     """
    #     Mint an NFT and register it as IP in one transaction

    #     :param to_address: Recipient's address
    #     :param metadata_uri: URI for the NFT metadata
    #     :param ip_metadata: IP Asset metadata following Story Protocol standard
    #     :return: Transaction details
    #     """
    #     try:
    #         # Using the IPAsset module's combined mint and register function
    #         response = self.client.IPAsset.mintAndRegisterRootIP(
    #             recipient=self.web3.to_checksum_address(to_address),
    #             tokenURI=metadata_uri,
    #             metadata=ip_metadata
    #         )
    #         return response
    #     except Exception as e:
    #         print(f"Error minting and registering NFT: {str(e)}")
    #         raise

    

    def get_spg_nft_contract_minting_fee_and_token(self, spg_nft_contract: str) -> dict:
        """
        Get the minting fee required by an SPG NFT contract.
        
        Args:
            spg_nft_contract: The address of the SPG NFT contract
            
        Returns:
            dict: Contains mint_fee and mint_fee_token information
        """
        try: 
            mint_fee = self.client.NFTClient.get_mint_fee(spg_nft_contract)
            mint_fee_token = self.client.NFTClient.get_mint_fee_token(spg_nft_contract)
            return {
                'mint_fee': mint_fee,
                'mint_fee_token': mint_fee_token
            }
        except Exception as e:
            print(f"Error getting minting fee: {str(e)}")
            raise

    def register(
        self,
        nft_contract: str,
        token_id: int,
        ip_metadata: Optional[dict] = None,
    ) -> dict:
        """
        Register an NFT as IP, creating a corresponding IP record.

        Args:
            nft_contract: The address of the NFT contract
            token_id: The token identifier of the NFT
            ip_metadata: Optional metadata for the IP
                ip_metadata_uri: Optional metadata URI for the IP
                ip_metadata_hash: Optional metadata hash for the IP
                nft_metadata_uri: Optional metadata URI for the NFT
                nft_metadata_hash: Optional metadata hash for the NFT

        Returns:
            dict: Dictionary with the transaction hash and IP ID
        """
        try:
            # Ensure the contract address is checksummed
            nft_contract = self.web3.to_checksum_address(nft_contract)
            
            # Prepare metadata if provided
            metadata_dict = None
            if ip_metadata:
                metadata_dict = {
                    'ip_metadata_uri': ip_metadata.get('ip_metadata_uri', ""),
                    'ip_metadata_hash': ip_metadata.get('ip_metadata_hash', "0x0000000000000000000000000000000000000000000000000000000000000000"),
                    'nft_metadata_uri': ip_metadata.get('nft_metadata_uri', ""),
                    'nft_metadata_hash': ip_metadata.get('nft_metadata_hash', "0x0000000000000000000000000000000000000000000000000000000000000000"),
                }
            
            # Call the SDK function
            result = self.client.IPAsset.register(
                nft_contract=nft_contract,
                token_id=token_id,
                ip_metadata=metadata_dict
            )
            
            return {
                'tx_hash': result.get('tx_hash'),
                'ip_id': result.get('ip_id')
            }
            
        except Exception as e:
            print(f"Error registering NFT as IP: {str(e)}")
            raise

    def attach_license_terms(
        self,
        ip_id: str,
        license_terms_id: int,
        license_template: Optional[str] = None
    ) -> dict:
        """
        Attaches license terms to an IP.

        Args:
            ip_id: The address of the IP to which the license terms are attached
            license_terms_id: The ID of the license terms
            license_template: Optional address of the license template (defaults to the default template)

        Returns:
            dict: Dictionary with the transaction hash
        """
        try:
            # Use default license template if none provided
            if license_template is None:
                license_template = self.LICENSE_TEMPLATE
            
            # Ensure the license template address is checksummed
            license_template = self.web3.to_checksum_address(license_template)
            
            # Call the SDK function
            result = self.client.License.attach_license_terms(
                ip_id=ip_id,
                license_template=license_template,
                license_terms_id=license_terms_id
            )
            
            return {
                'tx_hash': result.get('tx_hash')
            }
            
        except Exception as e:
            print(f"Error attaching license terms: {str(e)}")
            raise

    # bugs in sdk, will fix after next sdk release
    # def register_derivative(
    #     self,
    #     child_ip_id: str,
    #     parent_ip_ids: list,
    #     license_terms_ids: list,
    #     max_minting_fee: int = 0,
    #     max_rts: int = 0,
    #     max_revenue_share: int = 0,
    #     license_template: Optional[str] = None,
    #     approve_amount: Optional[int] = None
    # ) -> dict:
    #     """
    #     Registers a derivative directly with parent IP's license terms, without needing license tokens.

    #     Args:
    #         child_ip_id: The derivative IP ID
    #         parent_ip_ids: The parent IP IDs
    #         license_terms_ids: The IDs of the license terms that the parent IP supports
    #         max_minting_fee: The maximum minting fee that the caller is willing to pay in wei (default: 0 = no limit)
    #         max_rts: The maximum number of royalty tokens that can be distributed in wei (max: 100,000,000) (default: 0 = no limit)
    #         max_revenue_share: The maximum revenue share percentage allowed 0-100 (default: 0 = no limit)
    #         license_template: [Optional] address of the license template (defaults to the default template)
    #         approve_amount: [Optional] amount to approve for spending WIP tokens in wei. If None, uses the exact amount needed for the transaction.

    #     Returns:
    #         dict: Dictionary with the transaction hash
    #     """
    #     try:
    #         # Validate inputs
    #         if len(parent_ip_ids) != len(license_terms_ids):
    #             raise ValueError("The number of parent IP IDs must match the number of license terms IDs.")
            
    #         # Use default license template if none provided
    #         if license_template is None:
    #             license_template = self.LICENSE_TEMPLATE
            
    #         # Ensure the license template address is checksummed
    #         license_template = self.web3.to_checksum_address(license_template)
            
    #         register_derivative_spender = "0xD2f60c40fEbccf6311f8B47c4f2Ec6b040400086"
    #         required_fee = 0
    #         for i in range(len(license_terms_ids)):
    #             required_fee += self.get_license_terms(license_terms_id=license_terms_ids[i]).get("defaultMintingFee")

    #         # approve WIP tokens for registering derivative
    #         if required_fee > 0:
    #             approve_transaction_hash = self._approve_wip(
    #                 spender=register_derivative_spender, 
    #                 required_amount=required_fee, 
    #                 approve_amount=approve_amount)
            
    #         # Call the SDK function
    #         result = self.client.IPAsset.register_derivative(
    #             child_ip_id=child_ip_id,
    #             parent_ip_ids=parent_ip_ids,
    #             license_terms_ids=license_terms_ids,
    #             max_minting_fee=max_minting_fee,
    #             max_rts=max_rts,
    #             max_revenue_share=max_revenue_share * 10 ** 6,
    #             license_template=license_template
    #         )
            
    #         return {
    #             'tx_hash': result.get('tx_hash')
    #         }
            
    #     except Exception as e:
    #         print(f"Error registering derivative: {str(e)}")
    #         raise

    def pay_royalty_on_behalf(
        self,
        receiver_ip_id: str,
        payer_ip_id: str,
        token: str,
        amount: int
    ) -> dict:
        """
        Allows the function caller to pay royalties to the receiver IP asset on behalf of the payer IP asset.


        Args:
            receiver_ip_id: The IP ID that receives the royalties
            payer_ip_id: The ID of the IP asset that pays the royalties
            token: The token address to use to pay the royalties
            amount: The amount to pay in wei

        Returns:
            dict: Dictionary with the transaction hash
        """
        try:
            # Ensure addresses are checksummed
            receiver_ip_id = self.web3.to_checksum_address(receiver_ip_id)
            payer_ip_id = self.web3.to_checksum_address(payer_ip_id)
            token = self.web3.to_checksum_address(token)
            
            # Handle approve logic - auto-approve the exact amount needed
            royalty_spender = "0xa38f42B8d33809917f23997B8423054aAB97322C"
            required_amount = amount  # The amount needed for the transaction
            if required_amount > 0:
                approve_transaction_hash = self._approve_token(
                    token_address= token,  
                    spender=royalty_spender, 
                    approve_amount=required_amount)
            
            # Call the SDK function using the correct path
            result = self.client.Royalty.pay_royalty_on_behalf(
                receiver_ip_id,
                payer_ip_id,
                token,
                amount
            )
            
            return {
                'tx_hash': result.get('tx_hash') if isinstance(result, dict) else result
            }
            
        except Exception as e:
            print(f"Error paying royalty: {str(e)}")
            raise
    
    def claim_all_revenue(
            self, 
            ancestor_ip_id: str, 
            child_ip_ids: list, 
            license_ids: list, 
            auto_transfer: bool = True,
            claimer: Optional[str] = None,
            ) -> dict:
        """
        Claims all revenue from the child IPs of an ancestor IP, then optionally transfers tokens to the claimer.
        
        Args:
            ancestor_ip_id: The ancestor IP ID
            child_ip_ids: The list of child IP IDs (must be in same order as license_ids)
            license_ids: The list of license terms IDs 
            auto_transfer: Whether to automatically transfer the claimed tokens to the claimer
            claimer: Optional claimer address (defaults to current account)
        Returns:
            dict: A dictionary with transaction details and claimed tokens.
        """
        try:
            # Get royalty policies from license IDs
            royalty_policies = []
            currency_tokens = []
            for license_id in license_ids:
                license_terms_response = self.client.License.get_license_terms(license_id)
                if not license_terms_response:
                    raise ValueError(f"No license terms found for ID {license_id}")
                royalty_policy = license_terms_response[1]  # royaltyPolicy is at index 1
                currency_token = license_terms_response[15]  # currency is at index 15
                royalty_policies.append(royalty_policy)
                currency_tokens.append(currency_token)
            
            # Ensure addresses are checksummed
            ancestor_ip_id = self.web3.to_checksum_address(ancestor_ip_id)
            # Use current account address if claimer is not provided
            if claimer is None:
                claimer = self.account.address
            claimer = self.web3.to_checksum_address(claimer)
            child_ip_ids = [self.web3.to_checksum_address(child_id) for child_id in child_ip_ids]
            royalty_policies = [self.web3.to_checksum_address(policy) for policy in royalty_policies]
            currency_tokens = [self.web3.to_checksum_address(token) for token in currency_tokens]
            
            claim_options = {
                'auto_transfer_all_claimed_tokens_from_ip': auto_transfer,
                'auto_unwrap_ip_tokens': False
                }
            # Call the SDK function
            response = self.client.Royalty.claim_all_revenue(
                ancestor_ip_id=ancestor_ip_id,
                claimer=claimer,
                child_ip_ids=child_ip_ids,
                royalty_policies=royalty_policies,
                currency_tokens=currency_tokens,
                claim_options=claim_options
            )
            
            return {
                'receipt': response.get('tx_receipt'),
                'claimed_tokens': response.get('claimed_tokens'),
                'tx_hash': response.get('tx_hash')
            }
            
        except Exception as e:
            print(f"Error claiming revenue: {str(e)}")
            raise

    def raise_dispute(
        self,
        target_ip_id: str,
        target_tag: str,
        cid: str,
        bond_amount: int,
        liveness: int = 30
    ) -> dict:
        """
        Raises a dispute against an IP asset using the Story Protocol SDK.
        Automatically approves the exact amount of WIP tokens needed for the bond.
        
        Args:
            target_ip_id: The IP ID to dispute
            target_tag: The tag name for the dispute. Must be one of:
                       - "IMPROPER_REGISTRATION"
                       - "IMPROPER_USAGE"
                       - "IMPROPER_PAYMENT"
                       - "CONTENT_STANDARDS_VIOLATION"
                       - "IN_DISPUTE"
            cid: The Content Identifier (CID) for the dispute evidence, obtained from IPFS
            bond_amount: The amount of the bond to post for the dispute, as an integer in wei
            liveness: The liveness of the dispute in days, must be between 30 and 365 days (defaults to 30 days)
        Returns:
            dict: Dictionary with the transaction hash and dispute ID
        """
        try:
            # Validate inputs
            if not target_ip_id.lower().startswith("0x"):
                raise ValueError("target_ip_id must be a hexadecimal string.")
            if liveness < 30 or liveness > 365:
                raise ValueError("Liveness must be between 30 days and 1 year")
            if not isinstance(bond_amount, int) or bond_amount <= 0:
                raise ValueError("bond_amount must be a positive integer in wei")
            
            print(f"Debug: Bond amount {bond_amount} wei ({self.web3.from_wei(bond_amount, 'ether')} IP)")
            
            liveness = liveness * 24 * 60 * 60 # Convert days to seconds
            # Ensure target_ip_id is a checksummed address
            target_ip_id = self.web3.to_checksum_address(target_ip_id)
            
            # Handle approve logic - auto-approve the exact amount needed
            dispute_spender = "0xfFD98c3877B8789124f02C7E8239A4b0Ef11E936"
            
            # Call approve before the transaction if needed
            transaction_hash = self._approve_token(
                token_address="0x1514000000000000000000000000000000000000",  # WIP token
                spender=dispute_spender, 
                approve_amount=bond_amount)
            
            # Use the SDK's dispute functionality - it handles all the complex logic!
            response = self.client.Dispute.raise_dispute(
                target_ip_id=target_ip_id,
                target_tag=target_tag,
                cid=cid,
                liveness=liveness,
                bond=bond_amount
            )
            
            return {
                "tx_hash": response.get('tx_hash'),
                "dispute_id": response.get('dispute_id'),
                "target_ip_id": target_ip_id,
                "dispute_tag": target_tag,
                "bond_amount_wei": bond_amount,
                "bond_amount_ip": float(self.web3.from_wei(bond_amount, 'ether')),
                "liveness_days": liveness // (24 * 60 * 60),  # Convert seconds back to days
                "liveness_seconds": liveness
            }
            
        except Exception as e:
            print(f"Error raising dispute: {str(e)}")
            raise

    def _approve_wip(
        self, 
        spender: str,
        approve_amount: int
    ) -> dict:
        """
        Approve a spender to use the wallet's WIP balance.
        Simplified method that directly approves the specified amount.
        
        Args:
            spender: The address of the spender
            approve_amount: The amount of WIP to approve in base units
            
        Returns:
            dict: Dictionary containing the transaction hash
        """
        try:
            response = self.client.WIP.approve(
                spender=spender,
                amount=approve_amount,
                tx_options=None
            )
            return {'tx_hash': response.get('tx_hash')}
        except Exception as e:
            print(f"Error approving WIP: {str(e)}")
            raise
    
    def _approve_token(
        self,
        token_address: str,
        spender: str,
        approve_amount: int
    ) -> dict:
        """
        Approve a spender to use any ERC20 token from the wallet.
        
        This is a generic token approval method that works with any ERC20 token,
        including WIP, MERC20, or any other ERC20-compliant token.
        
        Args:
            token_address: The address of the ERC20 token contract
            spender: The address that will be allowed to spend the tokens
            approve_amount: The amount to approve in base units
            
        Returns:
            dict: Dictionary containing the transaction hash
            
        Example:
            # Approve MERC20 for a specific spender
            result = story_service._approve_token(
                token_address="0x1234...",  # MERC20 address
                spender="0x5678...",        # Spender address
                approve_amount=1000000000000000000  # Amount to approve in base units
            )
        """
        try:
            # Ensure addresses are checksummed
            token_address = self.web3.to_checksum_address(token_address)
            spender = self.web3.to_checksum_address(spender)
            
            # Check if this is WIP token and delegate accordingly
            if token_address == "0x1514000000000000000000000000000000000000":
                # Use WIP-specific approve method
                return self._approve_wip(
                    spender=spender,
                    approve_amount=approve_amount
                )
            else:
                # Handle other ERC20 tokens using web3
                token_contract = self.web3.eth.contract(
                    address=token_address,
                    abi=ERC20_ABI
                )
                
                # Build the approve transaction
                tx = token_contract.functions.approve(
                    spender,
                    approve_amount
                ).build_transaction({
                    'from': self.account.address,
                    'nonce': self.web3.eth.get_transaction_count(self.account.address),
                    'gas': 100000,  # Standard gas limit for approve
                    'gasPrice': self.web3.eth.gas_price,
                    'chainId': self.chain_id
                })
                
                # Sign and send the transaction
                signed_tx = self.account.sign_transaction(tx)
                tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                
                # Wait for transaction receipt
                tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
                
                print(f"Approved {approve_amount} base units of token {token_address} for spender {spender}")
                print(f"Transaction hash: {tx_hash.hex()}")
                
                return {
                    'tx_hash': tx_hash.hex(),
                    'token_address': token_address,
                    'spender': spender,
                    'amount': approve_amount
                }
            
        except Exception as e:
            print(f"Error approving token {token_address}: {str(e)}")
            raise
    
    
    def get_token_balance(
        self,
        token_address: str,
        account_address: Optional[str] = None
    ) -> dict:
        """
        Get the balance of any ERC20 token for an account.
        
        Args:
            token_address: The address of the ERC20 token contract
            account_address: The address to check balance for (defaults to wallet address)
            
        Returns:
            dict: Dictionary containing balance information
        """
        try:
            # Use wallet address if account_address not provided
            if account_address is None:
                account_address = self.account.address
                
            # Ensure addresses are checksummed
            token_address = self.web3.to_checksum_address(token_address)
            account_address = self.web3.to_checksum_address(account_address)
            
            # Create ERC20 contract instance
            token_contract = self.web3.eth.contract(
                address=token_address,
                abi=ERC20_ABI
            )
            
            # Get token details
            try:
                symbol = token_contract.functions.symbol().call()
            except:
                symbol = "UNKNOWN"
                
            try:
                decimals = token_contract.functions.decimals().call()
            except:
                decimals = 18  # Default to 18 decimals
                
            # Get balance
            balance_wei = token_contract.functions.balanceOf(account_address).call()
            balance_decimal = balance_wei / (10 ** decimals)
            
            return {
                'token_address': token_address,
                'account_address': account_address,
                'balance_wei': balance_wei,
                'balance': balance_decimal,
                'symbol': symbol,
                'decimals': decimals
            }
            
        except Exception as e:
            print(f"Error getting token balance: {str(e)}")
            raise
    
    def mint_test_token(
        self,
        token_address: str,
        amount: int,
        recipient: Optional[str] = None
    ) -> dict:
        """
        Attempt to mint test tokens if the contract has a public mint function.
        Common for testnet tokens.
        
        Args:
            token_address: The address of the ERC20 token contract
            amount: The amount to mint in wei
            recipient: The recipient address (defaults to wallet address)
            
        Returns:
            dict: Transaction result
        """
        try:
            # Use wallet address if recipient not provided
            if recipient is None:
                recipient = self.account.address
                
            # Ensure addresses are checksummed
            token_address = self.web3.to_checksum_address(token_address)
            recipient = self.web3.to_checksum_address(recipient)
            
            # Common mint function ABIs for test tokens
            mint_abis = [
                # mint(address to, uint256 amount)
                {
                    "constant": False,
                    "inputs": [
                        {"name": "to", "type": "address"},
                        {"name": "amount", "type": "uint256"}
                    ],
                    "name": "mint",
                    "outputs": [],
                    "type": "function"
                },
                # mint(uint256 amount) - mints to msg.sender
                {
                    "constant": False,
                    "inputs": [
                        {"name": "amount", "type": "uint256"}
                    ],
                    "name": "mint",
                    "outputs": [],
                    "type": "function"
                },
                # faucet() - common for test tokens
                {
                    "constant": False,
                    "inputs": [],
                    "name": "faucet",
                    "outputs": [],
                    "type": "function"
                }
            ]
            
            # Try to find and call a mint function
            for mint_abi in mint_abis:
                try:
                    # Create contract with just the mint function ABI
                    contract = self.web3.eth.contract(
                        address=token_address,
                        abi=[mint_abi] + ERC20_ABI  # Include ERC20 ABI for balance checks
                    )
                    
                    # Build the transaction based on the function signature
                    if mint_abi['name'] == 'mint' and len(mint_abi['inputs']) == 2:
                        # mint(address to, uint256 amount)
                        tx = contract.functions.mint(recipient, amount).build_transaction({
                            'from': self.account.address,
                            'nonce': self.web3.eth.get_transaction_count(self.account.address),
                            'gas': 150000,
                            'gasPrice': self.web3.eth.gas_price,
                            'chainId': self.chain_id
                        })
                    elif mint_abi['name'] == 'mint' and len(mint_abi['inputs']) == 1:
                        # mint(uint256 amount)
                        tx = contract.functions.mint(amount).build_transaction({
                            'from': self.account.address,
                            'nonce': self.web3.eth.get_transaction_count(self.account.address),
                            'gas': 150000,
                            'gasPrice': self.web3.eth.gas_price,
                            'chainId': self.chain_id
                        })
                    elif mint_abi['name'] == 'faucet':
                        # faucet() - usually gives a fixed amount
                        tx = contract.functions.faucet().build_transaction({
                            'from': self.account.address,
                            'nonce': self.web3.eth.get_transaction_count(self.account.address),
                            'gas': 150000,
                            'gasPrice': self.web3.eth.gas_price,
                            'chainId': self.chain_id
                        })
                    
                    # Sign and send the transaction
                    signed_tx = self.account.sign_transaction(tx)
                    tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                    
                    # Wait for transaction receipt
                    tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
                    
                    print(f"Successfully minted tokens using {mint_abi['name']} function")
                    print(f"Transaction hash: {tx_hash.hex()}")
                    
                    return {
                        'tx_hash': tx_hash.hex(),
                        'token_address': token_address,
                        'function_used': mint_abi['name'],
                        'recipient': recipient,
                        'amount': amount if mint_abi['name'] != 'faucet' else 'faucet default'
                    }
                    
                except Exception as e:
                    # This mint function didn't work, try the next one
                    continue
            
            # If we get here, no mint function worked
            raise Exception("No public mint function found on this token contract")
                    
        except Exception as e:
            print(f"Error minting test tokens: {str(e)}")
            raise
    
    # def pay_royalty_on_behalf_approve(self, amount: int) -> dict:
    #     """
    #     Approve a spender to use the wallet's WIP balance for royalty payments on behalf of another IP.
    #     :param amount int: The amount of WIP to approve for royalty on behalf of another IP.
    #     :return dict: A dictionary containing the transaction hash.
    #     """
    #     royalty_spender = "0xa38f42B8d33809917f23997B8423054aAB97322C"
    #     response = self.client.WIP.approve(
    #         spender=royalty_spender,
    #         amount=amount,
    #         tx_options=None
    #     )
    #     return {'tx_hash': response.get('tx_hash')}
    
    # def mint_and_register_ip_approve(self, amount: int) -> dict:
    #     """
    #     Approve a spender to use the wallet's WIP balance for minting and registering IP.
    #     :param amount int: The amount of WIP to approve for minting and registering IP.
    #     :return dict: A dictionary containing the transaction hash.
    #     """
    #     mint_and_register_spender = "0xa38f42B8d33809917f23997B8423054aAB97322C"
    #     response = self.client.WIP.approve(
    #         spender=mint_and_register_spender,
    #         amount=amount,
    #         tx_options=None
    #     )
    #     return {'tx_hash': response.get('tx_hash')}
    
    # def raise_dispute_bond_approve(self, amount: int) -> dict:
    #     """
    #     Approve a spender to use the wallet's WIP balance for raise dispute bond payments.
    #     :param amount int: The amount of WIP to approve for raise dispute bond.
    #     :return dict: A dictionary containing the transaction hash.
    #     """
    #     dispute_spender = "0xfFD98c3877B8789124f02C7E8239A4b0Ef11E936"
    #     response = self.client.WIP.approve(
    #         spender=dispute_spender,
    #         amount=amount,
    #         tx_options=None
    #     )
    #     return {'tx_hash': response.get('tx_hash')}

    # def mint_license_tokens_approve(self, amount: int) -> dict:
    #     """
    #     Approve a spender to use the wallet's WIP balance for license token minting.
    #     :param amount int: The amount of WIP to approve for license token minting.
    #     :return dict: A dictionary containing the transaction hash.
    #     """
    #     license_spender = "0xD2f60c40fEbccf6311f8B47c4f2Ec6b040400086"
    #     response = self.client.WIP.approve(
    #         spender=license_spender,
    #         amount=amount,
    #         tx_options=None
    #     )
    #     return {'tx_hash': response.get('tx_hash')}

    def deposit_wip(self, amount: int) -> dict:
        """
        Wraps the selected amount of IP to WIP.
        :param amount int: The amount of IP to wrap in wei.
        :return dict: A dictionary containing the transaction hash.
        """
        response = self.client.WIP.deposit(amount=amount)
        return {'tx_hash': response.get('tx_hash')}

    def transfer_wip(self, to: str, amount: int) -> dict:
        """
        Transfers `amount` of WIP to a recipient `to`.
        :param to str: The address of the recipient.
        :param amount int: The amount of WIP to transfer in wei.
        :param tx_options dict: [Optional] Transaction options.
        :return dict: A dictionary containing the transaction hash.
        """
        response = self.client.WIP.transfer(to=to, amount=amount)
        return {'tx_hash': response.get('tx_hash')}

    def _get_license_terms_royalty_policy_address(self, selected_license_terms_id: int) -> str:
        return self.client.License.get_license_terms(selected_license_terms_id).get('royaltyPolicy')
    
    def predict_minting_license_fee(
        self,
        licensor_ip_id: str,
        license_terms_id: int,
        amount: int,
        license_template: str | None = None,
        receiver: str | None = None,
        tx_options: dict | None = None,
    ) -> dict:
        """
        Pre-compute the minting license fee for the given IP and license terms.

        :param licensor_ip_id str: The IP ID of the licensor.
        :param license_terms_id int: The ID of the license terms.
        :param amount int: The amount of license tokens to mint.
        :param license_template str: [Optional] The address of the license template, default is Programmable IP License.
        :param receiver str: [Optional] The address of the receiver, default is your wallet address.
        :param tx_options dict: [Optional] Transaction options.
        :return dict: A dictionary containing the currency token and token amount.
        """
        response = self.client.License.predict_minting_license_fee(
            licensor_ip_id=licensor_ip_id,
            license_terms_id=license_terms_id,
            amount=amount,
            license_template=license_template,
            receiver=receiver,
            tx_options=tx_options
        )
        return response
