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

        # Manually initialize the NFTClient
        self.nft_client = NFTClient(
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

    def _get_erc20_contract(self, token_address: str):
        """
        Create an ERC20 contract instance for the given token address.
        
        Args:
            token_address: The address of the ERC20 token contract
            
        Returns:
            Contract: Web3 contract instance for the ERC20 token
        """
        token_address = self.web3.to_checksum_address(token_address)
        return self.web3.eth.contract(address=token_address, abi=ERC20_ABI)
    
    def get_token_info(self, token_address: str) -> dict:
        """
        Get basic information about an ERC20 token.
        
        Args:
            token_address: The address of the ERC20 token contract
            
        Returns:
            dict: Token information including name, symbol, decimals, and total supply
        """
        try:
            token_contract = self._get_erc20_contract(token_address)
            
            # Get token information
            name = token_contract.functions.name().call()
            symbol = token_contract.functions.symbol().call()
            decimals = token_contract.functions.decimals().call()
            total_supply = token_contract.functions.totalSupply().call()
            
            return {
                'address': token_address,
                'name': name,
                'symbol': symbol,
                'decimals': decimals,
                'totalSupply': total_supply,
                'totalSupplyFormatted': total_supply / (10 ** decimals)
            }
            
        except Exception as e:
            print(f"Error getting token info: {str(e)}")
            raise
    
    def get_token_balance(self, token_address: str, owner_address: Optional[str] = None) -> dict:
        """
        Get the token balance for a specific address.
        
        Args:
            token_address: The address of the ERC20 token contract
            owner_address: The address to check balance for (defaults to current account)
            
        Returns:
            dict: Balance information in both raw and formatted values
        """
        try:
            token_contract = self._get_erc20_contract(token_address)
            
            if owner_address is None:
                owner_address = self.account.address
            else:
                owner_address = self.web3.to_checksum_address(owner_address)
            
            # Get balance and decimals
            balance = token_contract.functions.balanceOf(owner_address).call()
            decimals = token_contract.functions.decimals().call()
            
            return {
                'address': owner_address,
                'token': token_address,
                'balanceRaw': balance,
                'balanceFormatted': balance / (10 ** decimals),
                'decimals': decimals
            }
            
        except Exception as e:
            print(f"Error getting token balance: {str(e)}")
            raise


    def get_license_terms(self, license_terms_id: int) -> dict:
        """Get the license terms for a specific ID."""
        response = self.client.License.getLicenseTerms(license_terms_id)
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
        receiver: Optional[str] = None,
        amount: int = 1,
        max_minting_fee: Optional[int] = None,
        max_revenue_share: Optional[int] = None,
        license_template: Optional[str] = None
    ) -> dict:
        """
        Mints license tokens for the license terms attached to an IP.

        Args:
            licensor_ip_id: The licensor IP ID
            license_terms_id: The ID of the license terms
            receiver: Optional address of the receiver (defaults to sender)
            amount: Optional amount of license tokens to mint (defaults to 1)
            max_minting_fee: Optional maximum minting fee (defaults to 0)
            max_revenue_share: Optional maximum revenue share percentage (defaults to 0)
            license_template: Optional address of the license template (defaults to the default template)

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
            
            # Call the SDK function
            result = self.client.License.mintLicenseTokens(
                licensor_ip_id=licensor_ip_id,
                license_template=license_template,
                license_terms_id=license_terms_id,
                amount=amount,
                receiver=receiver,
                max_minting_fee=max_minting_fee,
                max_revenue_share=max_revenue_share
            )
            
            return {
                'txHash': result.get('txHash'),
                'licenseTokenIds': result.get('licenseTokenIds', [])
            }
            
        except Exception as e:
            print(f"Error minting license tokens: {str(e)}")
            raise

    def send_ip(self, to_address: str, amount: float) -> dict:
        """
        Send IP tokens to a specified address using native token transfer.

        :param to_address: Recipient's address or domain name
        :param amount: Amount of IP tokens to send (1 IP = 1 Ether)
        :return: Transaction details
        """
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
                "chainId": 1315,  # Story Protocol chain ID
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
        commercial_use: bool = True,
        minting_fee: int = 0,
        registration_metadata: Optional[dict] = None,
        recipient: Optional[str] = None,
        spg_nft_contract: Optional[str] = None,
        spg_nft_contract_max_minting_fee: Optional[int] = None,
    ) -> dict:
        """
        Mint an NFT, register it as an IP Asset, and attach PIL terms.
        Automatically detects if the SPG contract requires a minting fee and handles it appropriately.

        Args:
            commercial_rev_share: Percentage of revenue share (0-100)
            derivatives_allowed: Whether derivatives are allowed
            commercial_use: [Optional]Whether this is a commercial license (defaults to True)
            minting_fee: [Optional] Fee required to mint license tokens (defaults to 0)
            registration_metadata: [Optional] dict containing full metadata structure
            recipient: Optional recipient address or domain name (defaults to sender)
            spg_nft_contract: Optional SPG NFT contract address (defaults to network-specific default)
            spg_nft_contract_max_minting_fee: Optional maximum minting fee user is willing to pay for SPG contract (in wei).
                                            If None, will accept whatever the contract requires.
                                            If specified, will reject if contract requires more than this amount.
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
                spg_nft_contract = self.contracts["SPG_NFT"]
            
            # Check if the contract requires a minting fee
            fee_info = self.get_spg_nft_contract_minting_fee(spg_nft_contract)
            required_fee = fee_info['mintFee']
            
            # Validate against user's maximum if specified
            if spg_nft_contract_max_minting_fee is not None and required_fee > spg_nft_contract_max_minting_fee:
                raise ValueError(
                    f"SPG contract requires minting fee of {required_fee} wei, "
                    f"but your maximum is {spg_nft_contract_max_minting_fee} wei. "
                    f"Increase spg_nft_contract_max_minting_fee or use a different contract."
                )
            
            # Use appropriate royalty policy based on commercial use
            royalty_policy = self.contracts["RoyaltyPolicyLAP"] if commercial_use else "0x0000000000000000000000000000000000000000"

            # Create terms matching our working structure
            terms = [
                {
                    "terms": {
                        "transferable": True,
                        "royalty_policy": royalty_policy,
                        "default_minting_fee": minting_fee,
                        "expiration": 0,
                        "commercial_use": commercial_use,
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
                        "is_set": False,
                        "minting_fee": minting_fee,
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

            # Add tx_options if fee is required (this is the key fix)
            if required_fee > 0:
                fee_ether = self.web3.from_wei(required_fee, 'ether')
                print(f"SPG contract requires minting fee: {required_fee} wei ({fee_ether} IP). Using alternative approach for paid contracts.")
                if spg_nft_contract_max_minting_fee is not None:
                    max_ether = self.web3.from_wei(spg_nft_contract_max_minting_fee, 'ether')
                    print(f"User's maximum: {spg_nft_contract_max_minting_fee} wei ({max_ether} IP)")
                
                # For paid SPG contracts, use separate mint and register approach
                # This avoids the SDK limitation with mintAndRegisterIpAssetWithPilTerms for paid contracts
                try:
                    # Step 1: Mint and register IP asset (without terms)
                    mint_result = self.client.IPAsset.mint_and_register_ip_asset_with_pil_terms(
                        spg_nft_contract=spg_nft_contract,
                        recipient=resolved_recipient,
                        ip_metadata=registration_metadata,
                        tx_options={'value': required_fee}
                    )
                    
                    ip_id = mint_result.get('ipId')
                    if not ip_id:
                        raise Exception("Failed to get IP ID from mint result")
                    
                    # Step 2: Register PIL terms
                    terms_data = terms[0]["terms"]  # Extract the terms from the array structure
                    pil_result = self.client.License.registerPILTerms(**terms_data)
                    license_terms_id = pil_result.get('licenseTermsId')
                    
                    if not license_terms_id:
                        raise Exception("Failed to get license terms ID from PIL registration")
                    
                    # Step 3: Attach terms to IP
                    attach_result = self.client.License.attachLicenseTerms(
                        ip_id=ip_id,
                        license_terms_id=license_terms_id
                    )
                    
                    return {
                        "txHash": mint_result.get("txHash"),
                        "ipId": ip_id,
                        "tokenId": mint_result.get("tokenId"),
                        "licenseTermsIds": [license_terms_id],
                        "actualMintingFee": required_fee,
                        "maxMintingFee": spg_nft_contract_max_minting_fee,
                        "_multiStep": True,  # Indicate this was a multi-step process
                        "_mintTxHash": mint_result.get("txHash"),
                        "_pilTxHash": pil_result.get("txHash"),
                        "_attachTxHash": attach_result.get("txHash"),
                    }
                except Exception as fallback_error:
                    print(f"Fallback approach failed: {str(fallback_error)}")
                    # If fallback fails, try the original approach anyway
                    kwargs["tx_options"] = {'value': required_fee}
            else:
                print("SPG contract is free. Using SDK without additional fees.")

            response = self.client.IPAsset.mintAndRegisterIpAssetWithPilTerms(**kwargs)

            return {
                "txHash": response.get("txHash"),
                "ipId": response.get("ipId"),
                "tokenId": response.get("tokenId"),
                "licenseTermsIds": response.get("licenseTermsIds"),
                "actualMintingFee": required_fee,  # Include actual fee paid
                "maxMintingFee": spg_nft_contract_max_minting_fee,  # Include user's limit
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
            # Validate mint fee recipient when there's a fee
            if mint_fee_recipient is None and mint_fee is not None and mint_fee > 0:
                raise Exception("Mint fee recipient is required if mint fee is greater than 0")
            
            # Default mint_fee_recipient to zero address if not provided
            if mint_fee_recipient is None:
                mint_fee_recipient = "0x0000000000000000000000000000000000000000"
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

    def mint_nft(
        self,
        nft_contract: str,
        to_address: str,
        metadata_uri: str,
        metadata_hash: bytes,
        allow_duplicates: bool = False,
    ) -> dict:
        """
        Mint an NFT from an existing SPG collection using the Story Protocol SDK.
        
        Uses the IPAsset.mint() method from the Story Protocol Python SDK to mint NFTs from SPG contracts.

        Args:
            nft_contract: The address of the SPG NFT contract to mint from
            to_address: The recipient address for the minted NFT
            metadata_uri: The metadata URI for the NFT
            metadata_hash: The metadata hash as bytes
            allow_duplicates: Whether to allow minting NFTs with duplicate metadata (default: False)

        Returns:
            dict: Dictionary with the transaction hash, token ID, and contract address
        """
        try:
            # Ensure the contract address is checksummed
            nft_contract = self.web3.to_checksum_address(nft_contract)
            to_address = self.web3.to_checksum_address(to_address)
            
            print(f"Minting NFT from contract: {nft_contract}")
            print(f"To address: {to_address}")
            print(f"Metadata URI: {metadata_uri}")
            print(f"Allow duplicates: {allow_duplicates}")
            
            # Use the SDK's IPAsset.mint() method
            tx_hash = self.client.IPAsset.mint(
                nft_contract=nft_contract,
                to_address=to_address,
                metadata_uri=metadata_uri,
                metadata_hash=metadata_hash,
                allow_duplicates=allow_duplicates,
                tx_options=None  # No transaction options for now
            )
            
            # Get transaction receipt to extract token ID
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Extract token ID from logs
            token_id = None
            try:
                # Look for Transfer event logs to get token ID
                transfer_event_signature = self.web3.keccak(text="Transfer(address,address,uint256)").hex()
                for log in tx_receipt['logs']:
                    if len(log['topics']) >= 4 and log['topics'][0].hex() == transfer_event_signature:
                        # Token ID is the 4th topic (index 3)
                        token_id = int(log['topics'][3].hex(), 16)
                        break
            except Exception as e:
                print(f"Warning: Could not extract token ID from logs: {e}")
                token_id = None
            
            return {
                'txHash': tx_hash,
                'tokenId': token_id,
                'nftContract': nft_contract,
                'recipient': to_address,
                'metadataUri': metadata_uri,
                'gasUsed': tx_receipt['gasUsed']
            }
            
        except Exception as e:
            print(f"Error minting NFT: {str(e)}")
            raise

    def mint_and_register_ip_asset(
        self,
        spg_nft_contract: str,
        recipient: Optional[str] = None,
        ip_metadata: Optional[dict] = None,
        max_minting_fee: Optional[int] = None,
    ) -> dict:
        """
        Mint an NFT and register it as an IP asset in one transaction (without license terms).

        Args:
            spg_nft_contract: The address of the SPG NFT contract to mint from
            recipient: Optional recipient address (defaults to sender)
            ip_metadata: Optional metadata for the IP
                ip_metadata_uri: Optional metadata URI for the IP
                ip_metadata_hash: Optional metadata hash for the IP
                nft_metadata_uri: Optional metadata URI for the NFT
                nft_metadata_hash: Optional metadata hash for the NFT
            max_minting_fee: Optional maximum minting fee user is willing to pay (in wei).
                           If None, will accept whatever the contract requires.
                           If specified, will reject if contract requires more than this amount.

        Returns:
            dict: Dictionary with the transaction hash, IP ID, token ID, and contract address
        """
        try:
            # Ensure the contract address is checksummed
            spg_nft_contract = self.web3.to_checksum_address(spg_nft_contract)
            
            # Use sender address if no recipient specified
            if recipient is None:
                recipient = self.account.address
            else:
                recipient = self.web3.to_checksum_address(recipient)
            
            # Check if the contract requires a minting fee
            fee_info = self.get_spg_nft_contract_minting_fee(spg_nft_contract)
            required_fee = fee_info['mintFee']
            
            # Validate against user's maximum if specified
            if max_minting_fee is not None and required_fee > max_minting_fee:
                raise ValueError(
                    f"Contract requires minting fee of {required_fee} wei, "
                    f"but your maximum is {max_minting_fee} wei. "
                    f"Increase max_minting_fee or use a different contract."
                )
            
            # Prepare metadata if provided
            
            if not ip_metadata:
                metadata_dict = {
                    'ip_metadata_uri': ip_metadata.get('ip_metadata_uri', ""),
                    'ip_metadata_hash': ip_metadata.get('ip_metadata_hash', "0x0000000000000000000000000000000000000000000000000000000000000000"),
                    'nft_metadata_uri': ip_metadata.get('nft_metadata_uri', ""),
                    'nft_metadata_hash': ip_metadata.get('nft_metadata_hash', "0x0000000000000000000000000000000000000000000000000000000000000000"),
                }
            
            # Prepare tx_options if fee is required
            tx_options = None
            if required_fee > 0:
                fee_ether = self.web3.from_wei(required_fee, 'ether')
                print(f"SPG contract requires minting fee: {required_fee} wei ({fee_ether} IP). Using SDK with tx_options.")
                if max_minting_fee is not None:
                    max_ether = self.web3.from_wei(max_minting_fee, 'ether')
                    print(f"User's maximum: {max_minting_fee} wei ({max_ether} IP)")
                tx_options = {'value': required_fee}
            else:
                print("SPG contract is free. Using SDK without additional fees.")
            
            # Call the SDK function with correct parameter names
            result = self.client.IPAsset.registration_workflows_client.mintAndRegisterIp(
                spgNftContract=spg_nft_contract,
                recipient=recipient,
                ipMetadata=metadata_dict,
                allowDuplicates=True
            )
            
            return {
                'txHash': result.get('txHash'),
                'ipId': result.get('ipId'),
                'tokenId': result.get('tokenId'),
                'nftContract': spg_nft_contract,
                'actualMintingFee': required_fee,  # Include actual fee paid
                'maxMintingFee': max_minting_fee   # Include user's limit
            }
            
        except Exception as e:
            print(f"Error minting and registering IP asset: {str(e)}")
            raise

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

    # def attach_license_terms(self, ip_id: str, license_terms_id: int) -> dict:
    #     """
    #     Attach a licensing policy to an IP Asset

    #     :param ip_id: IP Asset ID
    #     :param license_terms_id: License terms ID to attach
    #     :return: Transaction details
    #     """
    #     try:
    #         # Using the License module from the SDK
    #         response = self.client.License.addPolicyToIp(
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
    #         response = self.client.IPAsset.mintAndRegisterRootIP(
    #             recipient=self.web3.to_checksum_address(to_address),
    #             tokenURI=metadata_uri,
    #             metadata=ip_metadata
    #         )
    #         return response
    #     except Exception as e:
    #         print(f"Error minting and registering NFT: {str(e)}")
    #         raise

    

    def get_spg_nft_contract_minting_fee(self, spg_nft_contract: str) -> dict:
        """
        Get the minting fee required by an SPG NFT contract.
        
        Args:
            spg_nft_contract: The address of the SPG NFT contract
            
        Returns:
            dict: Contains mintFee and mintFeeToken information
        """
        try:
            # Ensure the contract address is checksummed
            spg_nft_contract = self.web3.to_checksum_address(spg_nft_contract)
            
            # Define the ABI for the mintFee function
            mint_fee_abi = [
                {
                    "inputs": [],
                    "name": "mintFee",
                    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "mintFeeToken",
                    "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            # Create contract instance
            contract = self.web3.eth.contract(address=spg_nft_contract, abi=mint_fee_abi)
            
            # Get mint fee and token
            mint_fee = contract.functions.mintFee().call()
            mint_fee_token = contract.functions.mintFeeToken().call()
            
            return {
                'mintFee': mint_fee,
                'mintFeeToken': mint_fee_token,
                'isNativeToken': mint_fee_token == "0x1514000000000000000000000000000000000000"
            }
            
        except Exception as e:
            print(f"Error getting SPG minting fee: {str(e)}")
            # Return defaults if unable to read
            return {
                'mintFee': 0,
                'mintFeeToken': "0x1514000000000000000000000000000000000000",
                'isNativeToken': True
            }

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
                'txHash': result.get('txHash'),
                'ipId': result.get('ipId')
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
            result = self.client.License.attachLicenseTerms(
                ip_id=ip_id,
                license_template=license_template,
                license_terms_id=license_terms_id
            )
            
            return {
                'txHash': result.get('txHash')
            }
            
        except Exception as e:
            print(f"Error attaching license terms: {str(e)}")
            raise

    def register_derivative(
        self,
        child_ip_id: str,
        parent_ip_ids: list,
        license_terms_ids: list,
        max_minting_fee: int = 0,
        max_rts: int = 0,
        max_revenue_share: int = 0,
        license_template: Optional[str] = None
    ) -> dict:
        """
        Registers a derivative directly with parent IP's license terms, without needing license tokens.

        Args:
            child_ip_id: The derivative IP ID
            parent_ip_ids: The parent IP IDs
            license_terms_ids: The IDs of the license terms that the parent IP supports
            max_minting_fee: The maximum minting fee that the caller is willing to pay (default: 0 = no limit)
            max_rts: The maximum number of royalty tokens that can be distributed (max: 100,000,000)
            max_revenue_share: The maximum revenue share percentage allowed (0-100,000,000)
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
            result = self.client.IPAsset.registerDerivative(
                child_ip_id=child_ip_id,
                parent_ip_ids=parent_ip_ids,
                license_terms_ids=license_terms_ids,
                max_minting_fee=max_minting_fee,
                max_rts=max_rts,
                max_revenue_share=max_revenue_share,
                license_template=license_template
            )
            
            return {
                'txHash': result.get('txHash')
            }
            
        except Exception as e:
            print(f"Error registering derivative: {str(e)}")
            raise

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
            amount: The amount to pay

        Returns:
            dict: Dictionary with the transaction hash
        """
        try:
            # Ensure addresses are checksummed
            receiver_ip_id = self.web3.to_checksum_address(receiver_ip_id)
            payer_ip_id = self.web3.to_checksum_address(payer_ip_id)
            token = self.web3.to_checksum_address(token)
            
            # Call the SDK function using the correct path
            result = self.client.Royalty.pay_royalty_on_behalf(
                receiver_ip_id,
                payer_ip_id,
                token,
                amount
            )
            
            return {
                'txHash': result.get('txHash') if isinstance(result, dict) else result
            }
            
        except Exception as e:
            print(f"Error paying royalty: {str(e)}")
            raise

    def estimate_gas_for_approval(
        self,
        token: str,
        spender: str,
        amount: int
    ) -> dict:
        """
        Estimate gas costs for token approval transaction.
        
        Args:
            token: Token contract address
            spender: Spender contract address  
            amount: Amount to approve
            
        Returns:
            dict: Gas estimation details including price, limit, and total cost
        """
        try:
            # Ensure addresses are checksummed
            token = self.web3.to_checksum_address(token)
            spender = self.web3.to_checksum_address(spender)
            
            # Create ERC20 contract instance using helper method
            token_contract = self._get_erc20_contract(token)
            
            # Get current gas price
            try:
                current_gas_price = self.web3.eth.gas_price
            except Exception:
                current_gas_price = self.web3.to_wei(50, "gwei")  # Fallback
            
            # Estimate gas limit
            try:
                estimated_gas = token_contract.functions.approve(spender, amount).estimate_gas({
                    'from': self.account.address
                })
                # Add 20% buffer for safety
                gas_limit = int(estimated_gas * 1.2)
            except Exception:
                gas_limit = 100000  # Fallback for approve transactions
            
            # Calculate costs in different units
            total_cost_wei = current_gas_price * gas_limit
            total_cost_gwei = self.web3.from_wei(total_cost_wei, 'gwei')
            total_cost_ip = self.web3.from_wei(total_cost_wei, 'ether')
            
            # Get gas price in gwei for display
            gas_price_gwei = self.web3.from_wei(current_gas_price, 'gwei')
            
            return {
                'gasPrice': current_gas_price,
                'gasPriceGwei': float(gas_price_gwei),
                'estimatedGasLimit': gas_limit,
                'totalCostWei': total_cost_wei,
                'totalCostGwei': float(total_cost_gwei),
                'totalCostIP': float(total_cost_ip),
                'token': token,
                'spender': spender,
                'amount': amount
            }
            
        except Exception as e:
            print(f"Error estimating gas: {str(e)}")
            raise

    def approve_token_for_royalty(
        self,
        token: str,
        amount: int,
        spender: Optional[str] = None,
        operation_type: str = "royalty",
        gas_limit: Optional[int] = None,
        gas_price: Optional[int] = None
    ) -> dict:
        """
        Approve a token contract to allow Story Protocol contracts to spend tokens.
        
        Args:
            token: The token contract address to approve
            amount: The amount to approve (use a large number for unlimited approval)
            spender: Optional spender address. If None, will auto-determine based on operation_type
            operation_type: Type of operation ("royalty", "licensing", "minting", "custom")
                          Only used when spender is None to auto-determine the correct contract
            gas_limit: Optional custom gas limit. If None, will estimate automatically
            gas_price: Optional custom gas price in wei. If None, uses network gas price
            
        Returns:
            dict: Dictionary with the transaction hash and gas information
            
        Note:
            - For most users, leave spender=None and specify operation_type
            - Only set spender manually for custom contracts or advanced use cases
            - gas_limit and gas_price are optional for advanced users who want control
            - Common operation_types:
              * "royalty" -> Uses RoyaltyModule (for pay_royalty_on_behalf)
              * "licensing" -> Uses LicensingModule (for mint_license_tokens) 
              * "minting" -> Uses default SPG_NFT contract (for minting fees)
              * "custom" -> Must provide spender address manually
        """
        try:
            # Ensure token address is checksummed
            token = self.web3.to_checksum_address(token)
            
            # Auto-determine spender based on operation type if not provided
            if spender is None:
                if operation_type == "royalty":
                    spender = self.contracts.get("RoyaltyModule")
                    if not spender:
                        raise ValueError("RoyaltyModule address not found in contracts")
                elif operation_type == "licensing":
                    spender = self.contracts.get("LicensingModule")
                    if not spender:
                        raise ValueError("LicensingModule address not found in contracts")
                elif operation_type == "minting":
                    spender = self.contracts.get("SPG_NFT")
                    if not spender:
                        raise ValueError("SPG_NFT address not found in contracts")
                elif operation_type == "custom":
                    raise ValueError("For custom operations, you must provide the spender address manually")
                else:
                    # Fallback to royalty module for backward compatibility
                    spender = self.contracts.get("RoyaltyModule")
                    if not spender:
                        # Last resort: try to get from client
                        spender = getattr(self.client.Royalty, 'address', None)
                        if not spender:
                            raise ValueError(
                                f"Unknown operation_type '{operation_type}'. "
                                f"Use 'royalty', 'licensing', 'minting', or 'custom' with manual spender address."
                            )
            
            spender = self.web3.to_checksum_address(spender)
            
            # Get gas estimation first to inform user
            gas_estimate = self.estimate_gas_for_approval(token, spender, amount)
            
            # Use provided gas parameters or fall back to estimates
            final_gas_limit = gas_limit if gas_limit is not None else gas_estimate['estimatedGasLimit']
            final_gas_price = gas_price if gas_price is not None else gas_estimate['gasPrice']
            
            # Create ERC20 contract instance using helper method
            token_contract = self._get_erc20_contract(token)
            
            # Build transaction with user-specified or estimated gas
            tx = token_contract.functions.approve(spender, amount).build_transaction({
                'from': self.account.address,
                'gas': final_gas_limit,
                'gasPrice': final_gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
            })
            
            # Calculate actual cost for reporting
            actual_cost_wei = final_gas_price * final_gas_limit
            actual_cost_gwei = self.web3.from_wei(actual_cost_wei, 'gwei')
            actual_cost_ip = self.web3.from_wei(actual_cost_wei, 'ether')
            
            # Sign and send transaction
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'txHash': receipt.transactionHash.hex(),
                'status': receipt.status,
                'approvedAmount': amount,
                'spender': spender,
                'token': token,
                'operationType': operation_type,
                'gasUsed': receipt.gasUsed,
                'gasLimit': final_gas_limit,
                'gasPrice': final_gas_price,
                'gasPriceGwei': float(self.web3.from_wei(final_gas_price, 'gwei')),
                'actualCostWei': actual_cost_wei,
                'actualCostGwei': float(actual_cost_gwei),
                'actualCostIP': float(actual_cost_ip),
                'gasEstimate': gas_estimate
            }
            
        except Exception as e:
            print(f"Error approving token: {str(e)}")
            raise

    def check_token_allowance(
        self,
        token: str,
        owner: Optional[str] = None,
        spender: Optional[str] = None
    ) -> dict:
        """
        Check the current allowance for a token.
        
        Args:
            token: The token contract address
            owner: The owner address (if None, uses current account)
            spender: The spender address (if None, uses royalty contract)
            
        Returns:
            dict: Dictionary with allowance information
        """
        try:
            # Ensure token address is checksummed
            token = self.web3.to_checksum_address(token)
            
            # Use current account as owner if not provided
            if owner is None:
                owner = self.account.address
            else:
                owner = self.web3.to_checksum_address(owner)
            
            # Get the royalty contract address if spender not provided
            if spender is None:
                try:
                    spender = self.contracts.get("RoyaltyModule")
                    if not spender:
                        spender = getattr(self.client.Royalty, 'address', None)
                        if not spender:
                            raise ValueError("Could not determine royalty contract address")
                except:
                    raise ValueError("Could not determine royalty contract address. Please provide the spender address.")
            
            spender = self.web3.to_checksum_address(spender)
            
            # Create ERC20 contract instance using helper method
            token_contract = self._get_erc20_contract(token)
            
            # Get current allowance
            allowance = token_contract.functions.allowance(owner, spender).call()
            
            return {
                'allowance': allowance,
                'owner': owner,
                'spender': spender,
                'token': token,
                'hasAllowance': allowance > 0
            }
            
        except Exception as e:
            print(f"Error checking token allowance: {str(e)}")
            raise

    def claim_revenue(
        self,
        snapshot_ids: list,
        child_ip_id: str,
        token: str
    ) -> dict:
        """
        Allows token holders to claim revenue by a list of snapshot IDs based on the token balance at certain snapshot.

        Args:
            snapshot_ids: The list of snapshot IDs
            child_ip_id: The child IP ID
            token: The token address to claim

        Returns:
            dict: Dictionary with the transaction hash and the number of claimable tokens
        """
        try:
            # Ensure the token address is checksummed
            token = self.web3.to_checksum_address(token)
            
            # Call the SDK function
            result = self.client.Royalty.claimRevenue(
                snapshot_ids=snapshot_ids,
                child_ip_id=child_ip_id,
                token=token
            )
            
            return {
                'txHash': result.get('txHash'),
                'claimableToken': result.get('claimableToken')
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
        liveness: int = 30,
    ) -> dict:
        """
        Raises a dispute against an IP asset using the Story Protocol SDK.

        Args:
            target_ip_id: The IP ID to dispute
            target_tag: The tag for the dispute (e.g., "IMPROPER_REGISTRATION", "PLAGIARISM", "FRAUDULENT_USE")
            cid: The Content Identifier (CID) for the dispute evidence, obtained from IPFS
            bond_amount: The amount of the bond to post for the dispute, as an integer in wei
            liveness: The liveness of the dispute in days (defaults to 30 days, must be between 30 and 365 days)

        Returns:
            dict: Dictionary with the transaction hash and dispute ID
        """
        try:
            # Validate inputs
            if not target_ip_id.lower().startswith("0x"):
                raise ValueError("target_ip_id must be a hexadecimal string.")
            if liveness < 30 or liveness > 365:
                raise ValueError("Liveness must be between 30 and 365 days")
            if not isinstance(bond_amount, int) or bond_amount <= 0:
                raise ValueError("bond_amount must be a positive integer in wei")
            
            # Convert liveness from days to seconds
            liveness_seconds = liveness * 24 * 60 * 60
            
            print(f"Debug: Bond amount {bond_amount} wei ({self.web3.from_wei(bond_amount, 'ether')} IP)")
            print(f"Debug: Liveness {liveness} days ({liveness_seconds} seconds)")
            
            # Ensure target_ip_id is a checksummed address
            target_ip_id = self.web3.to_checksum_address(target_ip_id)
            
            # Use the SDK's dispute functionality - it handles all the complex logic!
            response = self.client.Dispute.raise_dispute(
                target_ip_id=target_ip_id,
                target_tag=target_tag,
                cid=cid,
                liveness=liveness_seconds,
                bond=bond_amount
            )
            
            return {
                "tx_hash": response.get('txHash'),
                "dispute_id": response.get('disputeId'),
                "target_ip_id": target_ip_id,
                "bond_amount_wei": bond_amount,
                "bond_amount_ip": float(self.web3.from_wei(bond_amount, 'ether')),
                "liveness_days": liveness,
                "liveness_seconds": liveness_seconds
            }
            
        except Exception as e:
            print(f"Error raising dispute: {str(e)}")
            raise

