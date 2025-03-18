from web3 import Web3
from story_protocol_python_sdk.story_client import StoryClient
from story_protocol_python_sdk.resources.NFTClient import NFTClient
import requests
import os
from typing import Union, Optional
import time
import json
import sys
from pathlib import Path

# Add the parent directory to the Python path so we can import utils
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.address_resolver import create_address_resolver
from utils.contract_addresses import get_contracts_by_chain_id, CHAIN_IDS


class StoryService:
    def __init__(self, rpc_url: str, private_key: Optional[str] = None, network: str = None):
        """
        Initialize Story Protocol service with RPC URL and optional private key.

        Args:
            rpc_url: RPC URL for the blockchain
            private_key: Optional private key for signing transactions. If not provided,
                        transactions will need to be signed by the frontend wallet.
            network: Optional network name ('aeneid' or 'mainnet') to override auto-detection
        """
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.web3.is_connected():
            raise Exception("Failed to connect to the Web3 provider")

        self.private_key = private_key
        self.account = None
        
        # Set up account if private key is provided
        if private_key:
            self.account = self.web3.eth.account.from_key(private_key)
            print(f"Connected with account: {self.account.address}")
        else:
            print("No private key provided. Transactions will require frontend wallet signing.")

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
                    f"Unsupported chain ID: {self.chain_id}. "
                    f"Supported chain IDs: {list(CHAIN_IDS.values())}"
                )

        # Get contract addresses for the current chain ID
        self.contract_addresses = get_contracts_by_chain_id(self.chain_id)

        # Initialize the Story SDK client if private key is provided
        if private_key and self.account:
            # Use web3, account, and chain_id parameters instead of rpc_url and private_key
            self.story_client = StoryClient(
                web3=self.web3, 
                account=self.account,
                chain_id=self.chain_id
            )
            
            # Update NFTClient initialization as well
            self.nft_client = NFTClient(
                web3=self.web3,
                account=self.account,
                chain_id=self.chain_id
            )
        else:
            self.story_client = None
            self.nft_client = None

        # Initialize address resolver
        self.address_resolver = create_address_resolver(self.web3)

        # Check IPFS configuration
        self.pinata_jwt = os.getenv("PINATA_JWT", "")
        self.ipfs_enabled = bool(self.pinata_jwt)
        if not self.ipfs_enabled:
            print("IPFS functionality is disabled (PINATA_JWT not set)")
            
    def has_private_key(self) -> bool:
        """
        Check if the service has a private key for signing transactions.
        
        Returns:
            bool: True if a private key is available, False otherwise
        """
        return self.private_key is not None and self.account is not None

    def get_license_terms(self, license_terms_id: int) -> dict:
        """Get the license terms for a specific ID."""
        response = self.story_client.License.getLicenseTerms(license_terms_id)
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

    def mint_license_tokens(
        self,
        licensor_ip_id: str,
        license_terms_id: int,
        receiver: str = None,
        amount: int = 1,
        max_minting_fee: int = None,
        max_revenue_share: int = None,
    ) -> dict:
        """
        Mint license tokens for a specific IP and license terms.

        Args:
            licensor_ip_id: The IP ID to mint licenses for
            license_terms_id: The license terms ID to use
            receiver: Address or domain name to receive the license tokens (defaults to caller)
            amount: Number of license tokens to mint (defaults to 1)
            max_minting_fee: Optional maximum minting fee
            max_revenue_share: Optional maximum revenue share percentage (0-100,000,000)
        """
        try:
            # Resolve receiver address if provided
            resolved_receiver = (
                self.address_resolver.resolve_address(receiver)
                if receiver
                else self.account.address
            )

            # Build kwargs dict with only provided parameters
            kwargs = {
                "licensor_ip_id": licensor_ip_id,
                "license_template": self.contract_addresses["PILicenseTemplate"],  # Use default template
                "license_terms_id": license_terms_id,
                "amount": amount,
                "receiver": resolved_receiver,
            }

            if max_minting_fee is not None:
                kwargs["max_minting_fee"] = max_minting_fee
            if max_revenue_share is not None:
                kwargs["max_revenue_share"] = max_revenue_share

            response = self.story_client.License.mintLicenseTokens(**kwargs)
            return response

        except Exception as e:
            print(f"Error minting license tokens: {str(e)}")
            raise

    def prepare_send_ip_transaction(self, to_address: str, amount: float) -> dict:
        """
        Prepare a transaction object for sending IP tokens that can be signed by a frontend wallet.

        :param to_address: Recipient's address or domain name
        :param amount: Amount of IP tokens to send (1 IP = 1 Ether)
        :return: Transaction object ready for signing
        """
        try:
            # Resolve the recipient address
            resolved_address = self.address_resolver.resolve_address(to_address)

            # Convert amount to Wei (1 IP = 1 Ether)
            value_in_wei = self.web3.to_wei(amount, "ether")

            # Set a default gas price if we can't get it from the network
            try:
                gas_price = self.web3.eth.gas_price
            except Exception:
                # Fallback gas price (50 gwei)
                gas_price = self.web3.to_wei(50, "gwei")

            # Estimate gas (we'll use the standard transfer gas limit)
            gas_estimate = 21000  # Standard transfer gas limit

            # Build the transaction (without nonce and from address - these will be set by the frontend)
            transaction = {
                "to": resolved_address,
                "value": value_in_wei,
                "gas": gas_estimate,
                "gasPrice": gas_price,
                "chainId": self.chain_id,
                "data": "0x"  # Empty data for simple transfer
            }

            # Convert the transaction to a format that can be serialized to JSON
            tx_for_json = {
                "to": transaction["to"],
                "value": hex(transaction["value"]),
                "gas": hex(transaction["gas"]),
                "gasPrice": hex(transaction["gasPrice"]),
                "chainId": transaction["chainId"],
                "data": transaction["data"]
            }

            return tx_for_json
        except Exception as e:
            print(f"Error preparing send IP transaction: {str(e)}")
            raise

    def send_ip(self, to_address: str, amount: float) -> dict:
        """
        Send IP tokens to a specified address using native token transfer.

        :param to_address: Recipient's address or domain name
        :param amount: Amount of IP tokens to send (1 IP = 1 Ether)
        :return: Transaction details
        """
        if not self.has_private_key():
            raise ValueError("Cannot send IP tokens without a private key. Use prepare_send_ip_transaction instead.")
            
        try:
            # Resolve the recipient address
            resolved_address = self.address_resolver.resolve_address(to_address)

            # Convert amount to Wei (1 IP = 1 Ether)
            value_in_wei = self.web3.to_wei(amount, "ether")

            print(f"Debug: Account address: {self.account.address}")
            print(f"Debug: Network connected: {self.web3.eth.chain_id}")
            print(
                f"Debug: Account balance: {self.web3.eth.get_balance(self.account.address)}"
            )

            # Set a default gas price if we can't get it from the network
            try:
                gas_price = self.web3.eth.gas_price
            except Exception:
                # Fallback gas price (50 gwei)
                gas_price = self.web3.to_wei(50, "gwei")

            # Estimate gas limit for this transaction
            try:
                gas_estimate = self.web3.eth.estimate_gas(
                    {
                        "to": resolved_address,
                        "from": self.account.address,
                        "value": value_in_wei,
                    }
                )
            except Exception:
                # Fallback gas limit
                gas_estimate = 21000  # Standard transfer gas limit

            # Build the transaction with dynamic gas settings
            transaction = {
                "to": resolved_address,
                "value": value_in_wei,
                "gas": gas_estimate,
                "gasPrice": gas_price,
                "nonce": self.web3.eth.get_transaction_count(self.account.address),
                "chainId": self.chain_id,
            }

            # Sign and send the transaction
            signed_txn = self.account.sign_transaction(transaction)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)

            # Wait for transaction receipt
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

            return {"txHash": tx_hash.hex(), "txReceipt": tx_receipt}
        except Exception as e:
            print(f"Error details: {str(e)}")
            raise

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

            # Generate hashes of the metadata JSONs
            nft_metadata_hash = self.web3.keccak(
                text=json.dumps(nft_metadata, sort_keys=True)
            )
            ip_metadata_hash = self.web3.keccak(
                text=json.dumps(ip_metadata, sort_keys=True)
            )

            # Create metadata structure for registration
            registration_metadata = {
                "ip_metadata_uri": ip_metadata_uri,
                "ip_metadata_hash": ip_metadata_hash.hex(),
                "nft_metadata_uri": nft_metadata_uri,
                "nft_metadata_hash": nft_metadata_hash.hex(),
            }

            return {
                "nft_metadata": nft_metadata,
                "nft_metadata_uri": nft_metadata_uri,
                "nft_metadata_hash": nft_metadata_hash.hex(),
                "ip_metadata": ip_metadata,
                "ip_metadata_uri": ip_metadata_uri,
                "ip_metadata_hash": ip_metadata_hash.hex(),
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
        registration_metadata: dict = None,
        recipient: str = None,
        spg_nft_contract: str = None,
    ) -> dict:
        """
        Mint an NFT, register it as an IP Asset, and attach PIL terms.

        Args:
            commercial_rev_share: Percentage of revenue share (0-100)
            derivatives_allowed: Whether derivatives are allowed
            registration_metadata: Optional dict containing full metadata structure
            recipient: Optional recipient address or domain name (defaults to sender)
            spg_nft_contract: Optional SPG NFT contract address (defaults to network-specific default)
        """
        try:
            # Resolve recipient address if provided
            resolved_recipient = (
                self.address_resolver.resolve_address(recipient)
                if recipient
                else self.account.address
            )

            # Use default SPG NFT contract if none provided
            if spg_nft_contract is None:
                spg_nft_contract = self.contract_addresses["SPG_NFT"]

            # Use the royalty policy from the contracts dictionary
            royalty_policy = self.contract_addresses["RoyaltyPolicyLAP"]

            # Create terms matching our working structure
            terms = [
                {
                    "terms": {
                        "transferable": True,
                        "royalty_policy": royalty_policy,
                        "default_minting_fee": 0,
                        "expiration": 0,
                        "commercial_use": commercial_rev_share > 0,
                        "commercial_attribution": False,
                        "commercializer_checker": "0x0000000000000000000000000000000000000000",
                        "commercializer_checker_data": "0x0000000000000000000000000000000000000000",
                        "commercial_rev_share": commercial_rev_share,
                        "commercial_rev_ceiling": 0,
                        "derivatives_allowed": derivatives_allowed,
                        "derivatives_attribution": derivatives_allowed,
                        "derivatives_approval": False,
                        "derivatives_reciprocal": derivatives_allowed,
                        "derivative_rev_ceiling": 0,
                        "currency": "0x1514000000000000000000000000000000000000",
                        "uri": "",
                    },
                    "licensing_config": {
                        "is_set": True,
                        "minting_fee": 0,
                        "hook_data": "",
                        "licensing_hook": "0x0000000000000000000000000000000000000000",
                        "commercial_rev_share": commercial_rev_share,
                        "disabled": False,
                        "expect_minimum_group_reward_share": 0,
                        "expect_group_reward_pool": "0x0000000000000000000000000000000000000000",
                    },
                }
            ]

            # Build kwargs for mintAndRegisterIpAssetWithPilTerms
            kwargs = {
                "spg_nft_contract": spg_nft_contract,
                "terms": terms,
                "recipient": resolved_recipient,
                "allow_duplicates": True,
            }

            # Only add ip_metadata if registration_metadata is provided
            if registration_metadata:
                kwargs["ip_metadata"] = registration_metadata

            response = self.story_client.IPAsset.mintAndRegisterIpAssetWithPilTerms(**kwargs)

            return {
                "txHash": response.get("txHash"),
                "ipId": response.get("ipId"),
                "tokenId": response.get("tokenId"),
                "licenseTermsIds": response.get("licenseTermsIds"),
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
        mint_fee_recipient: str = None,
        contract_uri: str = "",
        base_uri: str = "",
        max_supply: int = None,
        mint_fee: int = None,
        mint_fee_token: str = None,
        owner: str = None,
    ) -> dict:
        """
        Create a new SPG NFT collection that can be used for minting and registering IP assets.

        Args:
            name: (REQUIRED) Name of the NFT collection
            symbol: (REQUIRED) Symbol for the NFT collection
            is_public_minting: (OPTIONAL, default=True) Whether anyone can mint NFTs from this collection
            mint_open: (OPTIONAL, default=True) Whether minting is currently enabled
            mint_fee_recipient: (OPTIONAL) Address to receive minting fees (defaults to zero address)
            contract_uri: (OPTIONAL) URI for the collection metadata (ERC-7572 standard)
            base_uri: (OPTIONAL) Base URI for the collection. If not empty, tokenURI will be either
                     baseURI + token ID or baseURI + nftMetadataURI
            max_supply: (OPTIONAL) Maximum supply of the collection (defaults to unlimited)
            mint_fee: (OPTIONAL) Cost to mint a token (defaults to 0)
            mint_fee_token: (OPTIONAL) Token address used for minting fees (defaults to native token)
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
            # Default mint_fee_recipient to zero address if not provided
            if mint_fee_recipient is None:
                mint_fee_recipient = "0x0000000000000000000000000000000000000000"
            else:
                # Resolve the address if it's a domain name
                mint_fee_recipient = self.address_resolver.resolve_address(
                    mint_fee_recipient
                )

            # Resolve owner address if provided
            if owner:
                owner = self.address_resolver.resolve_address(owner)

            # Use the manually initialized NFTClient instead of client.NFT
            response = self.nft_client.createNFTCollection(
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
                "tx_hash": response.get("txHash"),
                "spg_nft_contract": response.get("nftContract"),
            }

        except Exception as e:
            print(f"Error creating SPG NFT collection: {str(e)}")
            raise

    # def register_pil_terms(
    #     self,
    #     transferable: bool = False,
    #     commercial_use: bool = False,
    #     derivatives_allowed: bool = False,
    #     default_minting_fee: int = 92
    # ) -> dict:
    #     """Register new PIL terms with customizable parameters."""
    #     response = self.story_client.License.registerPILTerms(
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
    #     return self.story_client.License.registerNonComSocialRemixingPIL()

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
    #         response = self.story_client.IPAsset.registerRootIP(
    #             nftContract=self.web3.to_checksum_address(nft_contract),
    #             tokenId=token_id,
    #             metadata=metadata
    #         )
    #         return response
    #     except Exception as e:
    #         print(f"Error registering IP asset: {str(e)}")
    #         raise

    # def attach_license_terms(self, ip_id: str, license_terms_id: int) -> dict:
    #     """
    #     Attach a licensing policy to an IP Asset

    #     :param ip_id: IP Asset ID
    #     :param license_terms_id: License terms ID to attach
    #     :return: Transaction details
    #     """
    #     try:
    #         # Using the License module from the SDK
    #         response = self.story_client.License.addPolicyToIp(
    #             ipId=ip_id,
    #             licenseTermsId=license_terms_id
    #         )
    #         return response
    #     except Exception as e:
    #         print(f"Error attaching license terms: {str(e)}")
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
    #         response = self.story_client.IPAsset.mintAndRegisterRootIP(
    #             recipient=self.web3.to_checksum_address(to_address),
    #             tokenURI=metadata_uri,
    #             metadata=ip_metadata
    #         )
    #         return response
    #     except Exception as e:
    #         print(f"Error minting and registering NFT: {str(e)}")
    #         raise
