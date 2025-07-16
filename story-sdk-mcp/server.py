from mcp.server.fastmcp import FastMCP
from services.story_service import StoryService
import os
from dotenv import load_dotenv
from typing import Union, Optional
import json
import sys
from pathlib import Path

# Add the parent directory to the Python path so we can import utils
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv(override=True)
print(f"RPC URL from env: {os.getenv('RPC_PROVIDER_URL')}")

# Get environment variables
private_key = os.getenv("WALLET_PRIVATE_KEY")
rpc_url = os.getenv("RPC_PROVIDER_URL")
if not private_key or not rpc_url:
    raise ValueError(
        "WALLET_PRIVATE_KEY and RPC_PROVIDER_URL environment variables are required"
    )

# Initialize Story service
story_service = StoryService(rpc_url=rpc_url, private_key=private_key)

# Initialize MCP
mcp = FastMCP("Story Protocol Server")

# Only register IPFS-related tools if IPFS is enabled
if story_service.ipfs_enabled:

    @mcp.tool()
    def upload_image_to_ipfs(image_data: Union[bytes, str]) -> str:
        """
        Upload an image to IPFS using Pinata API.

        Args:
            image_data: Either bytes of image data or URL to image

        Returns:
            str: IPFS URI of the uploaded image
        """
        try:
            ipfs_uri = story_service.upload_image_to_ipfs(image_data)
            return f"Successfully uploaded image to IPFS: {ipfs_uri}"
        except Exception as e:
            return f"Error uploading image to IPFS: {str(e)}"

    @mcp.tool()
    def create_ip_metadata(
        image_uri: str, name: str, description: str, attributes: Optional[list] = None
    ) -> str:
        """
        Create and upload both NFT and IP metadata to IPFS.

        Args:
            image_uri: IPFS URI of the uploaded image
            name: Name of the NFT/IP
            description: Description of the NFT/IP
            attributes: Optional list of attribute dictionaries

        Returns:
            str: Result message with metadata details and IPFS URIs
        """
        try:
            result = story_service.create_ip_metadata(
                image_uri=image_uri,
                name=name,
                description=description,
                attributes=attributes,
            )
            return (
                f"Successfully created and uploaded metadata:\n"
                f"NFT Metadata URI: {result['nft_metadata_uri']}\n"
                f"IP Metadata URI: {result['ip_metadata_uri']}\n"
                f"Registration metadata for minting:\n"
                f"{json.dumps(result['registration_metadata'], indent=2)}"
            )
        except Exception as e:
            return f"Error creating metadata: {str(e)}"


@mcp.tool()
def get_license_terms(license_terms_id: int) -> str:
    """Get the license terms for a specific ID."""
    try:
        terms = story_service.get_license_terms(license_terms_id)
        return f"License Terms {license_terms_id}: {terms}"
    except Exception as e:
        return f"Error retrieving license terms: {str(e)}"


@mcp.tool()
def mint_license_tokens(
    licensor_ip_id: str,
    license_terms_id: int,
    receiver: Optional[str] = None,
    amount: int = 1,
    max_minting_fee: Optional[int] = None,
    max_revenue_share: Optional[int] = None,
    license_template: Optional[str] = None,
    approve_amount: Optional[int] = None,
) -> str:
    """
    Mint license tokens for a given IP and license terms.

    💰 AUTO-APPROVE: This method automatically approves the required WIP token spending before minting.
    The approve_amount parameter controls how much WIP to approve for the spender.

    Args:
        licensor_ip_id: The ID of the licensor's intellectual property
        license_terms_id: The ID of the license terms
        receiver: Optional; the recipient's address for the tokens
        amount: Optional; number of license tokens to mint (defaults to 1)
        max_minting_fee: Optional; maximum fee for minting
        max_revenue_share: Optional; maximum revenue share percentage
        license_template: Optional; address of the license template
        approve_amount: Optional; amount to approve for spending WIP tokens (Default is exact amount needed for the transaction). 

    Returns:
        str: Success message with transaction hash and token IDs
    """
    try:
        response = story_service.mint_license_tokens(
            licensor_ip_id=licensor_ip_id,
            license_terms_id=license_terms_id,
            receiver=receiver,
            amount=amount,
            max_minting_fee=max_minting_fee,
            max_revenue_share=max_revenue_share,
            license_template=license_template,
            approve_amount=approve_amount,
        )

        return (
            f"Successfully minted license tokens:\n"
            f"Transaction Hash: {response['tx_hash']}\n"
            f"License Token IDs: {response['license_token_ids']}"
        )
    except ValueError as e:
        return f"Validation error: {str(e)}"
    except Exception as e:
        return f"Error minting license tokens: {str(e)}"


# @mcp.tool()
# def send_ip(to_address: str, amount: float) -> str:
#     """
#     Send IP tokens to another address.

#     :param to_address: The recipient's wallet address
#     :param amount: Amount of IP tokens to send (1 IP = 1 Ether)
#     :return: Transaction result message
#     """
#     try:
#         response = story_service.send_ip(to_address, amount)
#         return f"Successfully sent {amount} IP to {to_address}. Transaction hash: {response['txHash']}"
#     except Exception as e:
#         return f"Error sending IP: {str(e)}"


@mcp.tool()
def mint_and_register_ip_with_terms(
    commercial_rev_share: int,
    derivatives_allowed: bool,
    registration_metadata: dict,
    commercial_use: bool = True,
    minting_fee: int = 0,
    recipient: Optional[str] = None,
    spg_nft_contract: Optional[str] = None,  # Make this optional
    spg_nft_contract_max_minting_fee: Optional[int] = None,
    approve_amount: Optional[int] = None,
) -> str:
    """
    Mint an NFT, register it as an IP Asset, and attach PIL terms.
    Automatically detects if the SPG contract requires a minting fee and handles it appropriately.

    💰 AUTO-APPROVE: This method automatically approves the required WIP token spending before minting.
    The approve_amount parameter controls how much WIP to approve for the spender.

    Args:
        commercial_rev_share: Percentage of revenue share (0-100)
        derivatives_allowed: Whether derivatives are allowed
        registration_metadata: Dict containing metadata URIs and hashes from create_ip_metadata
        commercial_use: [Optional]Whether this is a commercial license (defaults to True)
        minting_fee: [Optional] Fee required to mint license tokens (defaults to 0)
        recipient: [Optional] recipient address (defaults to sender)
        spg_nft_contract: Optional SPG NFT contract address (defaults to network-specific default)
        spg_nft_contract_max_minting_fee: Optional maximum minting fee user is willing to pay for SPG contract (in wei).
                                        If None, will accept whatever the contract requires.
                                        If specified, will reject if contract requires more than this amount.
        approve_amount: Optional; amount to approve for spending WIP tokens (Default is exact amount needed for the transaction). 

    Returns:
        str: Result message with transaction details
    """
    try:
        response = story_service.mint_and_register_ip_with_terms(
            commercial_rev_share=commercial_rev_share,
            derivatives_allowed=derivatives_allowed,
            registration_metadata=registration_metadata,
            commercial_use=commercial_use,
            minting_fee=minting_fee,
            recipient=recipient,
            spg_nft_contract=spg_nft_contract,
            spg_nft_contract_max_minting_fee=spg_nft_contract_max_minting_fee,
            approve_amount=approve_amount,
        )

        # Determine which explorer URL to use based on network
        explorer_url = (
            "https://explorer.story.foundation"
            if story_service.network == "mainnet"
            else "https://aeneid.explorer.story.foundation"
        )

        # Format fee information for display
        fee_info = ""
        if response.get('actualMintingFee') is not None:
            actual_fee = response['actual_minting_fee']
            if actual_fee == 0:
                fee_info = f"SPG NFT Mint Fee: FREE (0 wei)\n"
            else:
                fee_in_ether = story_service.web3.from_wei(actual_fee, 'ether')
                fee_info = f"SPG NFT Mint Fee: {actual_fee} wei ({fee_in_ether} IP)\n"

        return (
            f"Successfully minted and registered IP asset with terms:\n"
            f"Transaction Hash: {response.get('tx_hash')}\n"
            f"IP ID: {response['ip_id']}\n"
            f"Token ID: {response['token_id']}\n"
            f"License Terms IDs: {response['license_terms_ids']}\n"
            f"{fee_info}"
            f"View the IPA here: {explorer_url}/ipa/{response['ip_id']}"
        )
    except Exception as e:
        return f"Error minting and registering IP with terms: {str(e)}"


@mcp.tool()
def create_spg_nft_collection(
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
) -> str:
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
        max_supply: (OPTIONAL) Maximum supply of the collection (defaults to unlimited)
        mint_fee: (OPTIONAL) Cost to mint a token (defaults to 0)
        mint_fee_token: (OPTIONAL) Token address used for minting fees (defaults to native token)
        owner: (OPTIONAL) Owner address of the collection (defaults to sender)

    Returns:
        str: Information about the created collection
    """
    try:
        response = story_service.create_spg_nft_collection(
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
        )

        return (
            f"Successfully created SPG NFT collection:\n"
            f"Name: {name}\n"
            f"Symbol: {symbol}\n"
            f"Transaction Hash: {response['tx_hash']}\n"
            f"SPG NFT Contract Address: {response['spg_nft_contract']}\n"
            f"Base URI: {base_uri if base_uri else 'Not set'}\n"
            f"Max Supply: {max_supply if max_supply is not None else 'Unlimited'}\n"
            f"Mint Fee: {mint_fee if mint_fee is not None else '0'}\n"
            f"Mint Fee Token: {mint_fee_token if mint_fee_token else 'Not set'}\n"
            f"Owner: {owner if owner else 'Default (sender)'}\n\n"
            f"You can now use this contract address with the mint_and_register_ip_with_terms tool."
        )
    except Exception as e:
        return f"Error creating SPG NFT collection: {str(e)}"


@mcp.tool()
def get_spg_nft_contract_minting_fee(spg_nft_contract: str) -> str:
    """
    Get the minting fee required by an SPG NFT contract.

    Args:
        spg_nft_contract: The address of the SPG NFT contract

    Returns:
        str: Information about the minting fee
    """
    try:
        fee_info = story_service.get_spg_nft_contract_minting_fee(spg_nft_contract)
        
        fee_amount = fee_info['mint_fee']
        fee_token = fee_info['mint_fee_token']
        is_native = fee_info['is_native_token']
        
        # Format the fee amount nicely
        if fee_amount == 0:
            fee_display = "FREE (0)"
        else:
            # Convert from wei to a more readable format
            fee_in_ether = story_service.web3.from_wei(fee_amount, 'ether')
            fee_display = f"{fee_amount} wei ({fee_in_ether} IP)"
        
        token_display = "Native IP token" if is_native else f"Token at {fee_token}"
        
        return (
            f"SPG NFT Minting Fee Information:\n"
            f"Contract: {spg_nft_contract}\n"
            f"Mint Fee: {fee_display}\n"
            f"Fee Token: {token_display}\n\n"
            f"When minting from this contract, you need to send {fee_amount} wei as the mint_fee parameter."
        )
    except Exception as e:
        return f"Error getting SPG minting fee: {str(e)}"


# @mcp.tool()
# def mint_nft(
#     nft_contract: str,
#     to_address: str,
#     metadata_uri: str,
#     metadata_hash: str,
#     allow_duplicates: bool = False,
# ) -> str:
#     """
#     Mint an NFT from an existing SPG collection using the Story Protocol SDK.
    
#     Uses the IPAsset.mint() method from the Story Protocol Python SDK to mint NFTs from SPG contracts.

#     Args:
#         nft_contract: The address of the SPG NFT contract to mint from
#         to_address: The recipient address for the minted NFT
#         metadata_uri: The metadata URI for the NFT
#         metadata_hash: The metadata hash as a hex string (will be converted to bytes)
#         allow_duplicates: Whether to allow minting NFTs with duplicate metadata (default: False)

#     Returns:
#         str: Result message with transaction details
#     """
#     try:
#         # Convert hex string to bytes for metadata_hash
#         if metadata_hash.startswith('0x'):
#             metadata_hash_bytes = bytes.fromhex(metadata_hash[2:])
#         else:
#             metadata_hash_bytes = bytes.fromhex(metadata_hash)
        
#         result = story_service.mint_nft(
#             nft_contract=nft_contract,
#             to_address=to_address,
#             metadata_uri=metadata_uri,
#             metadata_hash=metadata_hash_bytes,
#             allow_duplicates=allow_duplicates
#         )
        
#         return (
#             f"Successfully minted NFT:\n"
#             f"Transaction Hash: {result['txHash']}\n"
#             f"NFT Contract: {result['nftContract']}\n"
#             f"Token ID: {result['tokenId']}\n"
#             f"Recipient: {result['recipient']}\n"
#             f"Metadata URI: {result['metadataUri']}\n"
#             f"Allow Duplicates: {allow_duplicates}\n"
#             f"Gas Used: {result['gasUsed']}\n\n"
#             f"You can now use this NFT with the register function to create an IP without license terms."
#         )
#     except Exception as e:
#         return f"Error minting NFT: {str(e)}"

# new added but haven't tested
# @mcp.tool()
# def mint_and_register_ip_asset(
#     spg_nft_contract: str,
#     recipient: Optional[str] = None,
#     ip_metadata: Optional[dict] = None,
#     allow_duplicates: bool = True,
#     spg_nft_contract_max_minting_fee: Optional[int] = None,
#     approve_amount: Optional[int] = None
# ) -> str:
#     """
#     Mint an NFT and register it as an IP asset in one transaction (without license terms).

#     💰 AUTO-APPROVE: This method automatically approves the required WIP token spending before minting.
#     The approve_amount parameter controls how much WIP to approve for the spender.

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
#         approve_amount: Optional; amount to approve for spending WIP tokens (Default is exact amount needed for the transaction). 

#     Returns:
#         str: Result message with transaction details
#     """
#     try:
#         response = story_service.mint_and_register_ip_asset(
#             spg_nft_contract=spg_nft_contract,
#             recipient=recipient,
#             ip_metadata=ip_metadata,
#             allow_duplicates=allow_duplicates,
#             spg_nft_contract_max_minting_fee=spg_nft_contract_max_minting_fee,
#             approve_amount=approve_amount,
#         )

#         # Determine which explorer URL to use based on network
#         explorer_url = (
#             "https://explorer.story.foundation"
#             if story_service.network == "mainnet"
#             else "https://aeneid.explorer.story.foundation"
#         )

#         # Format fee information for display
#         fee_info = ""
#         if response.get('actual_minting_fee') is not None:
#             actual_fee = response['actual_minting_fee']
#             if actual_fee == 0:
#                 fee_info = f"SPG NFT Mint Fee: FREE (0 wei)\n"
#             else:
#                 fee_in_ether = story_service.web3.from_wei(actual_fee, 'ether')
#                 fee_info = f"SPG NFT Mint Fee: {actual_fee} wei ({fee_in_ether} IP)\n"

#         return (
#             f"Successfully minted and registered IP asset with terms:\n"
#             f"Transaction Hash: {response.get('tx_hash')}\n"
#             f"IP ID: {response['ip_id']}\n"
#             f"Token ID: {response['token_id']}\n"
#             f"{fee_info}"
#             f"View the IPA here: {explorer_url}/ipa/{response['ip_id']}"
#         )
#     except Exception as e:
#         return f"Error minting and registering IP with terms: {str(e)}"


@mcp.tool()
def register(
    nft_contract: str, 
    token_id: int, 
    ip_metadata: Optional[dict] = None
    ) -> str:
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
        str: Result message with transaction hash and IP ID
    """
    try:
        result = story_service.register(
            nft_contract=nft_contract,
            token_id=token_id,
            ip_metadata=ip_metadata
        )
        
        if result.get('tx_hash'):
            return f"Successfully registered NFT as IP. Transaction hash: {result['tx_hash']}, IP ID: {result['ip_id']}"
        else:
            return f"NFT already registered as IP. IP ID: {result['ip_id']}"
    except Exception as e:
        return f"Error registering NFT as IP: {str(e)}"


@mcp.tool()
def attach_license_terms(ip_id: str, license_terms_id: int, license_template: Optional[str] = None) -> str:
    """
    Attaches license terms to an IP.

    Args:
        ip_id: The address of the IP to which the license terms are attached
        license_terms_id: The ID of the license terms
        license_template: Optional address of the license template (defaults to the default template)

    Returns:
        str: Result message with transaction hash
    """
    try:
        result = story_service.attach_license_terms(
            ip_id=ip_id,
            license_terms_id=license_terms_id,
            license_template=license_template
        )
        
        return f"Successfully attached license terms to IP. Transaction hash: {result['tx_hash']}"
    except Exception as e:
        return f"Error attaching license terms: {str(e)}"


@mcp.tool()
def register_derivative(
    child_ip_id: str,
    parent_ip_ids: list,
    license_terms_ids: list,
    max_minting_fee: int = 0,
    max_rts: int = 0,
    max_revenue_share: int = 0,
    license_template: Optional[str] = None,
    approve_amount: Optional[int] = None
) -> str:
    """
    Registers a derivative directly with parent IP's license terms, without needing license tokens.

    Args:
        child_ip_id: The derivative IP ID
        parent_ip_ids: The parent IP IDs (list of IP IDs)
        license_terms_ids: The IDs of the license terms that the parent IP supports (list of term IDs)
        max_minting_fee: The maximum minting fee that the caller is willing to pay (default: 0 = no limit)
        max_rts: The maximum number of royalty tokens that can be distributed (max: 100,000,000)
        max_revenue_share: The maximum revenue share percentage allowed (0-100,000,000)
        license_template: Optional address of the license template (defaults to the default template)
        approve_amount: Optional; amount to approve for spending WIP tokens (Default is exact amount needed for the transaction). 
    Returns:
        str: Result message with transaction hash
    """
    try:
        result = story_service.register_derivative(
            child_ip_id=child_ip_id,
            parent_ip_ids=parent_ip_ids,
            license_terms_ids=license_terms_ids,
            max_minting_fee=max_minting_fee,
            max_rts=max_rts,
            max_revenue_share=max_revenue_share,
            license_template=license_template,
            approve_amount=approve_amount
        )
        
        return f"Successfully registered derivative. Transaction hash: {result['tx_hash']}"
    except Exception as e:
        return f"Error registering derivative: {str(e)}"


@mcp.tool()
def pay_royalty_on_behalf(
    receiver_ip_id: str,
    payer_ip_id: str,
    token: str,
    amount: int,
    approve_amount: Optional[int] = None
) -> str:
    """
    Allows the function caller to pay royalties to the receiver IP asset on behalf of the payer IP asset.

    💰 AUTO-APPROVE: This method automatically approves the required WIP token spending before paying royalties.
    The approve_amount parameter controls how much WIP to approve for the spender.

    Args:
        receiver_ip_id: The IP ID that receives the royalties
        payer_ip_id: The ID of the IP asset that pays the royalties
        token: The token address to use to pay the royalties
        amount: The amount to pay
        approve_amount: Optional; amount to approve for spending WIP tokens (Default is exact amount needed for the transaction). 

    Returns:
        str: Success message with transaction hash
    """
    try:
        response = story_service.pay_royalty_on_behalf(
            receiver_ip_id=receiver_ip_id,
            payer_ip_id=payer_ip_id,
            token=token,
            amount=amount,
            approve_amount=approve_amount
        )

        return f"Successfully paid royalty on behalf. Transaction hash: {response['tx_hash']}"
    except Exception as e:
        return f"Error paying royalty on behalf: {str(e)}"



# new added but haven't tested
# @mcp.tool()
# def get_token_balance(
#     token: str,
#     owner: Optional[str] = None
# ) -> str:
#     """
#     Get the token balance for a specific address.

#     Args:
#         token: The token contract address
#         owner: The address to check balance for (if None, uses current account)

#     Returns:
#         str: Token balance information
#     """
#     try:
#         response = story_service.get_token_balance(
#             token_address=token,
#             owner_address=owner
#         )

#         return (
#             f"💰 Token Balance:\n"
#             f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
#             f"Address: {response['address']}\n"
#             f"Token: {response['token']}\n"
#             f"Balance: {response['balance_formatted']:,.6f} tokens\n"
#             f"Raw Balance: {response['balance_raw']:,}\n"
#             f"Decimals: {response['decimals']}"
#         )
#     except Exception as e:
#         return f"Error getting token balance: {str(e)}"



@mcp.tool()
def claim_all_revenue(
    ancestor_ip_id: str,
    claimer: str,
    child_ip_ids: list,
    royalty_policies: list,
    currency_tokens: list,
    auto_transfer: bool = True
) -> dict:
    """
    Claims all revenue from the child IPs of an ancestor IP, then optionally transfers tokens to the claimer.
    
    Args:
        ancestor_ip_id: The ancestor IP ID
        claimer: The claimer address
        child_ip_ids: The list of child IP IDs
        royalty_policies: The list of royalty policy addresses
        currency_tokens: The list of currency tokens
        auto_transfer: Whether to automatically transfer the claimed tokens to the claimer
    Returns:
        dict: Transaction details and claimed tokens
    """
    try:
        response = story_service.claim_all_revenue(
            ancestor_ip_id=ancestor_ip_id,
            claimer=claimer,
            child_ip_ids=child_ip_ids,
            royalty_policies=royalty_policies,
            currency_tokens=currency_tokens,
            auto_transfer=auto_transfer
        )
        return response
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def raise_dispute(
    target_ip_id: str,
    target_tag: str,
    cid: str,
    bond_amount: int,
    liveness: int = 30,
    approve_amount: Optional[int] = None
) -> str:
    """
    ⚖️ Raises a dispute against an IP asset using the Story Protocol SDK.
    
    💰 AUTO-APPROVE: This method automatically approves the required WIP token spending before raising the dispute.
    The approve_amount parameter controls how much WIP to approve for the spender.

    Args:
        target_ip_id: The IP ID to dispute (must be a valid hex address starting with 0x)
        target_tag: Tag identifying the dispute type (e.g., "IMPROPER_REGISTRATION", "PLAGIARISM", "FRAUDULENT_USE")
        cid: The Content Identifier (CID) for the dispute evidence, obtained from IPFS (e.g., "QmbWqxBEKC3P8tqsKc98xmWNzrzDtRLMiMPL8wBuTGsMnR")
        bond_amount: The amount of the bond to post for the dispute, as an integer in wei (e.g., 100000000000000000 for 0.1 IP)
        liveness: The liveness of the dispute in days, must be between 30 and 365 days (defaults to 30 days)
        approve_amount: Optional; amount to approve for spending WIP tokens (Default is exact amount needed for the transaction). 

    Returns:
        str: Result message with transaction hash and dispute ID
        
    💡 Bond Amount Format:
    - Use wei (1 IP = 1,000,000,000,000,000,000 wei)
    - Example: 100000000000000000 wei = 0.1 IP
    
    💡 Liveness Period:
    - Specify in days (30-365)
    - System automatically converts to seconds for blockchain
    - Example: 30 days = 2,592,000 seconds
    """
    try:
        result = story_service.raise_dispute(
            target_ip_id=target_ip_id,
            target_tag=target_tag,
            cid=cid,
            bond_amount=bond_amount,
            liveness=liveness,
            approve_amount=approve_amount
        )
        
        if 'error' in result:
            return f"Error raising dispute: {result['error']}"
        
        dispute_id = result.get('dispute_id', 'Unknown')
        liveness_days = result.get('liveness_days', 'Unknown')
        liveness_seconds = result.get('liveness_seconds', 'Unknown')
        return f"Successfully raised dispute. Transaction hash: {result['tx_hash']}, Dispute ID: {dispute_id}, Liveness: {liveness_days} days ({liveness_seconds} seconds)"
    except Exception as e:
        return f"Error raising dispute: {str(e)}"

# @mcp.tool()
# def pay_royalty_on_behalf_approve(amount: int) -> dict:
#     """
#     Approve a spender to use the wallet's WIP balance for royalty payments.

#     :param amount int: The amount of WIP to approve for royalty.
#     :return dict: A dictionary containing the transaction hash.
#     """
#     try:
#         response = story_service.pay_royalty_on_behalf_approve(amount=amount)
#         return {
#             'tx_hash': response.get('tx_hash')
#         }
#     except Exception as e:
#         return f"Error approving royalty: {str(e)}"

# @mcp.tool()
# def mint_and_register_ip_approve(amount: int) -> dict:
#     """
#     Approve a spender to use the wallet's WIP balance for minting and registering IP.

#     :param amount int: The amount of WIP to approve for minting and registering IP.
#     :return dict: A dictionary containing the transaction hash.
#     """
#     try:
#         response = story_service.mint_and_register_ip_approve(amount=amount)
#         return {
#             'tx_hash': response.get('tx_hash')
#         }
#     except Exception as e:
#         return f"Error approving mint and register IP: {str(e)}"

# @mcp.tool()
# def raise_dispute_bond_approve(amount: int) -> dict:
#     """
#     Approve a spender to use the wallet's WIP balance for raise dispute bond payments.
#     :param amount int: The amount of WIP to approve for raise dispute bond.
#     :return dict: A dictionary containing the transaction hash.
#     """
#     try:
#         response = story_service.raise_dispute_bond_approve(amount=amount)
#         return {
#             'tx_hash': response.get('tx_hash')
#         }
#     except Exception as e:
#         return f"Error approving raise dispute bond: {str(e)}"
    
# @mcp.tool()
# def mint_license_tokens_approve(amount: int) -> dict:
#     """
#     Approve a spender to use the wallet's WIP balance for license token minting.
#     :param amount int: The amount of WIP to approve for license token minting.
#     :return dict: A dictionary containing the transaction hash.
#     """
#     try:
#         response = story_service.mint_license_tokens_approve(amount=amount)
#         return {
#             'tx_hash': response.get('tx_hash')
#         }
#     except Exception as e:
#         return f"Error approving mint license tokens: {str(e)}"

@mcp.tool()
def deposit_wip(amount: int) -> dict:
    """
    Wraps the selected amount of IP to WIP and deposits to the wallet.
    :param amount int: The amount of IP to wrap.
    :return dict: A dictionary containing the transaction hash.
    """
    try:
        response = story_service.deposit_wip(amount=amount)
        return {'tx_hash': response.get('tx_hash')}
    except Exception as e:
        return {'error': str(e)}

@mcp.tool()
def transfer_wip(to: str, amount: int) -> dict:
    """
    Transfers `amount` of WIP to a recipient `to`.
    :param to str: The address of the recipient.
    :param amount int: The amount of WIP to transfer.
    :return dict: A dictionary containing the transaction hash.
    """
    try:
        response = story_service.transfer_wip(to=to, amount=amount)
        return {'tx_hash': response.get('tx_hash')}
    except Exception as e:
        return {'error': str(e)}


# @mcp.tool()
# def register_ip_asset(nft_contract: str, token_id: int, metadata: dict) -> str:
#     """
#     Register an NFT as an IP Asset.

#     :param nft_contract: NFT contract address
#     :param token_id: Token ID of the NFT
#     :param metadata: IP Asset metadata following Story Protocol standard
#     :return: Registration result message
#     """
#     try:
#         response = story_service.register_ip_asset(nft_contract, token_id, metadata)
#         return f"Successfully registered IP asset. IP ID: {response.get('ipId')}"
#     except Exception as e:
#         return f"Error registering IP asset: {str(e)}"

# @mcp.tool()
# def attach_license_terms(ip_id: str, license_terms_id: int) -> str:
#     """
#     Attach a licensing policy to an IP Asset.

#     :param ip_id: IP Asset ID
#     :param license_terms_id: License terms ID to attach
#     :return: Result message
#     """
#     try:
#         response = story_service.attach_license_terms(ip_id, license_terms_id)
#         return f"Successfully attached license terms {license_terms_id} to IP {ip_id}. Response: {response}"
#     except Exception as e:
#         return f"Error attaching license terms: {str(e)}"

# @mcp.tool()
# def mint_and_register_nft(to_address: str, metadata_uri: str, ip_metadata: dict) -> str:
#     """
#     Mint an NFT and register it as IP in one transaction.

#     :param to_address: Recipient's wallet address
#     :param metadata_uri: URI for the NFT metadata
#     :param ip_metadata: IP Asset metadata following Story Protocol standard
#     :return: Minting result message
#     """
#     try:
#         response = story_service.mint_and_register_nft(to_address, metadata_uri, ip_metadata)
#         return f"Successfully minted and registered NFT to {to_address}. Transaction details: {response}"
#     except Exception as e:
#         return f"Error minting and registering NFT: {str(e)}"

# @mcp.tool()
# def mint_generated_image(
#     image_data: Union[bytes, str],
#     name: str,
#     description: str,
#     recipient_address: str,
#     attributes: list = None,
#     ip_metadata: dict = None
# ) -> str:
#     """
#     Upload a generated image, mint it as an NFT, and register it as IP.

#     :param image_data: Either bytes of image data or URL to image
#     :param name: Name for the NFT
#     :param description: Description for the NFT
#     :param recipient_address: Address to receive the NFT
#     :param attributes: Optional list of NFT attributes
#     :param ip_metadata: Optional IP Asset metadata
#     :return: Result message with URIs and transaction details
#     """
#     try:
#         response = story_service.mint_generated_image(
#             image_data=image_data,
#             name=name,
#             description=description,
#             recipient_address=recipient_address,
#             attributes=attributes,
#             ip_metadata=ip_metadata
#         )
#         return (
#             f"Successfully processed generated image:\n"
#             f"Image URI: {response['image_uri']}\n"
#             f"Metadata URI: {response['metadata_uri']}\n"
#             f"Transaction Details: {response['transaction_details']}"
#         )
#     except Exception as e:
#         return f"Error processing generated image: {str(e)}"

# @mcp.tool()
# def register_non_commercial_social_remixing_pil() -> str:
#     """Register a non-commercial social remixing PIL license."""
#     try:
#         response = story_service.register_non_commercial_social_remixing_pil()
#         return f"Non-commercial social remixing PIL registered: {response}"
#     except Exception as e:
#         return f"Error registering non-commercial PIL: {str(e)}"

# @mcp.tool()
# def get_license_terms_test(selected_license_terms_id: int) -> dict:
#     """
#     Get license terms test.
#     :param selected_license_terms_id int: The ID of the license terms.
#     :return dict: A dictionary containing the license terms.
#     """
#     try:
#         return story_service.get_license_terms_test(selected_license_terms_id)
#     except Exception as e:
#         return {'error': str(e)}


if __name__ == "__main__":
    mcp.run()
