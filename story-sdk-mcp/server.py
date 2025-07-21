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

        ⚠️ IMPORTANT: This method uploads data to external services (IPFS). 
        Please double-check all parameters with the user and get their confirmation before proceeding.

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

        ⚠️ IMPORTANT: This method uploads data to external services (IPFS). 
        Please double-check all parameters with the user and get their confirmation before proceeding.

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

    ⚠️ IMPORTANT: This method makes blockchain transactions and spends tokens. 
    Please double-check all parameters with the user and get their confirmation before proceeding.

    💰 AUTO-APPROVE: This method automatically approves the required WIP token spending before minting.
    The approve_amount parameter controls how much WIP to approve for the spender.

    Args:
        licensor_ip_id: The ID of the licensor's intellectual property
        license_terms_id: The ID of the license terms
        receiver: [Optional] the recipient's address for the tokens
        amount: [Optional] number of license tokens to mint (defaults to 1)
        max_minting_fee: [Optional] maximum fee for minting in wei (defaults to 0 = no limit)
        max_revenue_share: [Optional] maximum revenue share percentage 0-100 (defaults to 0 = no limit)
        license_template: [Optional] address of the license template
        approve_amount: [Optional] amount to approve for spending WIP tokens in wei (Default is exact amount needed for the transaction). 

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

    ⚠️ IMPORTANT: This method makes blockchain transactions and spends tokens. 
    Please double-check all parameters with the user and get their confirmation before proceeding.

    💰 AUTO-APPROVE: This method automatically approves the required WIP token spending before minting.
    The approve_amount parameter controls how much WIP to approve for the spender.

    Args:
        commercial_rev_share: Percentage of revenue share (0-100)
        derivatives_allowed: Whether derivatives are allowed
        registration_metadata: Dict containing metadata URIs and hashes from create_ip_metadata
        commercial_use: [Optional]Whether this is a commercial license (defaults to True)
        minting_fee: [Optional] Fee required to mint license tokens in wei (defaults to 0)
        recipient: [Optional] recipient address (defaults to sender)
        spg_nft_contract: [Optional] SPG NFT contract address (defaults to network-specific default)
        spg_nft_contract_max_minting_fee: [Optional] maximum minting fee user is willing to pay for SPG contract in wei.
                                        If None, will accept whatever the contract requires.
                                        If specified, will reject if contract requires more than this amount.
        approve_amount: [Optional] amount to approve for spending WIP tokens in wei (Default is exact amount needed for the transaction). 

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

    ⚠️ IMPORTANT: This method makes blockchain transactions and creates contracts. 
    Please double-check all parameters with the user and get their confirmation before proceeding.

    Args:
        name: Name of the NFT collection
        symbol: Symbol for the NFT collection
        is_public_minting: [OPTIONAL] Whether anyone can mint NFTs from this collection (defaults to True)
        mint_open: [OPTIONAL] Whether minting is currently enabled (defaults to True)
        mint_fee_recipient: [OPTIONAL] Address to receive minting fees (defaults to sender)
        contract_uri: [OPTIONAL] URI for the collection metadata (ERC-7572 standard)
        base_uri: [OPTIONAL] Base URI for the collection. If not empty, tokenURI will be either
                 baseURI + token ID or baseURI + nftMetadataURI
        max_supply: [OPTIONAL] Maximum supply of the collection (defaults to unlimited)
        mint_fee: [OPTIONAL] Cost to mint a token in wei (defaults to 0)
        mint_fee_token: [OPTIONAL] Token address used for minting fees (defaults to WIP)
        owner: [OPTIONAL] Owner address of the collection (defaults to sender)

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
            f"Mint Fee Token: {mint_fee_token if mint_fee_token else 'WIP'}\n"
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

    ⚠️ IMPORTANT: This method makes blockchain transactions. 
    Please double-check all parameters with the user and get their confirmation before proceeding.

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

    ⚠️ IMPORTANT: This method makes blockchain transactions. 
    Please double-check all parameters with the user and get their confirmation before proceeding.

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

    ⚠️ IMPORTANT: This method makes blockchain transactions. 
    Please double-check all parameters with the user and get their confirmation before proceeding.

    Args:
        child_ip_id: The derivative IP ID
        parent_ip_ids: The parent IP IDs (list of IP IDs)
        license_terms_ids: The IDs of the license terms that the parent IP supports (list of term IDs)
        max_minting_fee: The maximum minting fee that the caller is willing to pay in wei (default: 0 = no limit)
        max_rts: The maximum number of royalty tokens that can be distributed (max: 100,000,000)
        max_revenue_share: The maximum revenue share percentage allowed 0-100
        license_template: [Optional] address of the license template (defaults to the default template)
        approve_amount: [Optional] amount to approve for spending WIP tokens in wei (Default is exact amount needed for the transaction). 
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

    ⚠️ IMPORTANT: This method makes blockchain transactions and spends tokens. 
    Please double-check all parameters with the user and get their confirmation before proceeding.

    💰 AUTO-APPROVE: This method automatically approves the required WIP token spending before paying royalties.
    The approve_amount parameter controls how much WIP to approve for the spender.

    Args:
        receiver_ip_id: The IP ID that receives the royalties
        payer_ip_id: The ID of the IP asset that pays the royalties
        token: The token address to use to pay the royalties
        amount: The amount to pay in wei
        approve_amount: [Optional] amount to approve for spending WIP tokens in wei (Default is exact amount needed for the transaction). 

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
    child_ip_ids: list,
    royalty_policies: list,
    currency_tokens: list,
    auto_transfer: bool = True,
    claimer: Optional[str] = None
) -> dict:
    """
    Claims all revenue from the child IPs of an ancestor IP, then optionally transfers tokens to the claimer.
    
    ⚠️ IMPORTANT: This method makes blockchain transactions and claims tokens. 
    Please double-check all parameters with the user and get their confirmation before proceeding.
    
    Args:
        ancestor_ip_id: The ancestor IP ID
        child_ip_ids: The list of child IP IDs
        royalty_policies: The list of royalty policy addresses
        currency_tokens: The list of currency tokens
        auto_transfer: Whether to automatically transfer the claimed tokens to the claimer
        claimer: Optional claimer address (defaults to current account)
    Returns:
        dict: Transaction details and claimed tokens
    """
    try:
        response = story_service.claim_all_revenue(
            ancestor_ip_id=ancestor_ip_id,
            child_ip_ids=child_ip_ids,
            royalty_policies=royalty_policies,
            currency_tokens=currency_tokens,
            auto_transfer=auto_transfer,
            claimer=claimer
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
    
    ⚠️ IMPORTANT: This method makes blockchain transactions and spends tokens. 
    Please double-check all parameters with the user and get their confirmation before proceeding.
    
    💰 AUTO-APPROVE: This method automatically approves the required WIP token spending before raising the dispute.
    The approve_amount parameter controls how much WIP to approve for the spender.

    Args:
        target_ip_id: The IP ID to dispute (must be a valid hex address starting with 0x)
        target_tag: The dispute tag name. Must be EXACTLY one of these:
                   • "IMPROPER_REGISTRATION" - IP was registered improperly
                   • "IMPROPER_USAGE" - IP is being used improperly
                   • "IMPROPER_PAYMENT" - Payment issues with the IP
                   • "CONTENT_STANDARDS_VIOLATION" - IP violates content standards
                   • "IN_DISPUTE" - General dispute status
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
    
    ⚠️ IMPORTANT: Tags must be whitelisted by protocol governance. Use EXACT tag strings above.
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
        dispute_tag = result.get('dispute_tag', 'Unknown')
        liveness_days = result.get('liveness_days', 'Unknown')
        liveness_seconds = result.get('liveness_seconds', 'Unknown')
        return f"Successfully raised dispute with tag '{dispute_tag}'. Transaction hash: {result['tx_hash']}, Dispute ID: {dispute_id}, Liveness: {liveness_days} days ({liveness_seconds} seconds)"
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
    
    ⚠️ IMPORTANT: This method makes blockchain transactions and wraps tokens. 
    Please double-check all parameters with the user and get their confirmation before proceeding.
    
    :param amount int: The amount of IP to wrap in wei.
    :return dict: A dictionary containing the transaction hash.
    """
    try:
        response = story_service.deposit_wip(amount=amount)
        return {'tx_hash': response.get('tx_hash')}
    except Exception as e:
        return {'error': str(e)}

@mcp.tool()
def approve_token_for_collection(
    collection_contract: str,
    spender: str,
    approve_amount: Optional[int] = None
) -> str:
    """
    Approve tokens for spending based on a collection's mint fee token requirements.
    This method automatically detects what token the collection uses for mint fees
    and approves the correct token type (WIP, IP, ETH, or other ERC20).

    ⚠️ IMPORTANT: This method makes blockchain transactions for token approvals. 
    Please double-check all parameters with the user and get their confirmation before proceeding.

    Args:
        collection_contract: The SPG NFT collection contract address
        spender: The address that will spend the tokens (usually a minting contract)
        approve_amount: Optional amount to approve in wei. If None, will approve the collection's mint fee amount

    Returns:
        str: Result message with approval details and transaction hash
    """
    try:
        # Get collection fee information
        fee_info = story_service.get_spg_nft_contract_minting_fee(collection_contract)
        mint_fee = fee_info['mint_fee']
        mint_fee_token = fee_info['mint_fee_token']
        is_native = fee_info['is_native_token']
        
        if mint_fee == 0:
            return f"Collection {collection_contract} has no mint fee. No approval needed."
        
        # Use collection's mint fee as default approval amount
        if approve_amount is None:
            approve_amount = mint_fee
        
        # Get token symbol for display
        token_symbol = story_service._get_token_symbol(mint_fee_token)
        
        # Approve the required token
        result = story_service._approve_token(
            token_address=mint_fee_token,
            spender=spender,
            required_amount=mint_fee,
            approve_amount=approve_amount
        )
        
        # Format amounts for display
        fee_display = story_service.web3.from_wei(mint_fee, 'ether')
        approve_display = story_service.web3.from_wei(approve_amount, 'ether')
        
        return (
            f"✅ Token approval successful!\n\n"
            f"📋 Collection Details:\n"
            f"   Contract: {collection_contract}\n"
            f"   Mint Fee: {mint_fee} wei ({fee_display} {token_symbol})\n"
            f"   Fee Token: {mint_fee_token} ({'Native IP' if is_native else 'ERC20 Token'})\n\n"
            f"💰 Approval Details:\n"
            f"   Token Approved: {token_symbol}\n"
            f"   Approved Amount: {approve_amount} wei ({approve_display} {token_symbol})\n"
            f"   Spender: {spender}\n"
            f"   Transaction Hash: {result['tx_hash']}\n\n"
            f"🎉 You can now mint from this collection using the approved tokens!"
        )
        
    except Exception as e:
        return f"❌ Error approving tokens for collection: {str(e)}"

@mcp.tool()
def check_token_compatibility(collection_contract: str) -> str:
    """
    Check what type of token a collection uses for mint fees and whether 
    the current approval system can handle it.

    Args:
        collection_contract: The SPG NFT collection contract address

    Returns:
        str: Detailed information about the collection's token requirements
    """
    try:
        # Get collection fee information
        fee_info = story_service.get_spg_nft_contract_minting_fee(collection_contract)
        mint_fee = fee_info['mint_fee']
        mint_fee_token = fee_info['mint_fee_token']
        is_native = fee_info['is_native_token']
        
        # Get token details
        token_symbol = story_service._get_token_symbol(mint_fee_token)
        is_wip = story_service._is_wip_token(mint_fee_token)
        
        # Format fee for display
        fee_display = story_service.web3.from_wei(mint_fee, 'ether') if mint_fee > 0 else "0"
        
        # Determine token type and compatibility
        if mint_fee == 0:
            token_type = "Free Collection"
            compatibility = "✅ No approval needed"
        elif is_native:
            token_type = "Native IP Token"
            compatibility = "✅ Fully supported via ERC20 interface"
        elif is_wip:
            token_type = "WIP Token"
            compatibility = "✅ Fully supported via WIP SDK interface"
        else:
            token_type = "Custom ERC20 Token"
            compatibility = "✅ Supported via generic ERC20 interface"
        
        return (
            f"🔍 Collection Token Analysis\n\n"
            f"📋 Collection: {collection_contract}\n"
            f"💰 Mint Fee: {mint_fee} wei ({fee_display} {token_symbol})\n"
            f"🏷️  Token Address: {mint_fee_token}\n"
            f"📊 Token Symbol: {token_symbol}\n"
            f"🔖 Token Type: {token_type}\n"
            f"✅ Compatibility: {compatibility}\n\n"
            f"🛠️  How to mint from this collection:\n"
            f"1. Use `approve_token_for_collection` to approve tokens\n"
            f"2. Use `mint_and_register_ip_with_terms` with this collection address\n"
            f"3. The system will automatically handle the correct token type!"
        )
        
    except Exception as e:
        return f"❌ Error checking collection compatibility: {str(e)}"

@mcp.tool()
def transfer_wip(to: str, amount: int) -> dict:
    """
    Transfers `amount` of WIP to a recipient `to`.
    
    ⚠️ IMPORTANT: This method makes blockchain transactions and transfers tokens. 
    Please double-check all parameters with the user and get their confirmation before proceeding.
    
    :param to str: The address of the recipient.
    :param amount int: The amount of WIP to transfer in wei.
    :return dict: A dictionary containing the transaction hash.
    """
    try:
        response = story_service.transfer_wip(to=to, amount=amount)
        return {'tx_hash': response.get('tx_hash')}
    except Exception as e:
        return {'error': str(e)}

# @mcp.tool()
# def get_license_terms_royalty_address(license_terms_id: int) -> str:
#     """
#     Get the royalty address for a license terms.
#     :param license_terms_id int: The ID of the license terms.
#     :return str: The royalty address.
#     """
#     try:
#         return story_service.get_license_terms_royalty_address(license_terms_id)
#     except Exception as e:
#         return {'error': str(e)}

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

@mcp.tool()
def debug_saferc20_failed_operation(
    token_address: str,
    spender_address: str,
    amount_needed: int,
    user_wallet: Optional[str] = None,
) -> str:
    """
    Debug SafeERC20FailedOperation errors by checking common causes:
    - Token existence and validity
    - User balance
    - Current allowance
    - Spender address validity
    - ERC20 interface compliance

    Args:
        token_address: The ERC20 token contract address that failed
        spender_address: The spender contract address
        amount_needed: The amount that was trying to be transferred/approved
        user_wallet: Optional user wallet address (defaults to current account)

    Returns:
        str: Detailed diagnosis of the SafeERC20FailedOperation error
    """
    try:
        if user_wallet is None:
            user_wallet = story_service.account.address

        # Check token contract existence
        try:
            code = story_service.web3.eth.get_code(token_address)
            if code == "0x":
                return (
                    f"❌ **CRITICAL ERROR: Token Contract Does Not Exist**\n\n"
                    f"🔍 Token Address: `{token_address}`\n"
                    f"❌ Contract Code: Empty (0x) - contract not deployed!\n\n"
                    f"💡 **Possible Solutions:**\n"
                    f"1. ✅ Verify the token address is correct\n"
                    f"2. ✅ Check if you're on the right network (Story testnet)\n"
                    f"3. ✅ Use a known working token:\n"
                    f"   • WIP: `0x1514000000000000000000000000000000000000000000`\n"
                    f"   • MERC20: `0xF2104833d386a2734a4eB3B8ad6FC6812F29E38E`\n"
                    f"4. ✅ Deploy the token contract if needed\n\n"
                    f"🚨 **This is the most likely cause of your SafeERC20FailedOperation error!**"
                )
        except Exception as e:
            return (
                f"❌ **ERROR: Cannot check token contract existence**\n"
                f"Error: {str(e)}\n\n"
                f"This might indicate network connectivity issues or wrong RPC endpoint."
            )

        # Check if token implements ERC20 interface
        try:
            token_contract = story_service._get_erc20_contract(token_address)
            
            # Test basic ERC20 functions calls
            token_name = token_contract.functions.name().call()
            token_symbol = token_contract.functions.symbol().call()
            token_decimals = token_contract.functions.decimals().call()
            total_supply = token_contract.functions.totalSupply().call()
            
        except Exception as e:
            return (
                f"❌ **ERROR: Token does not properly implement ERC20 interface**\n\n"
                f"🔍 Token Address: `{token_address}`\n"
                f"❌ ERC20 Interface Error: {str(e)}\n\n"
                f"💡 **Possible Solutions:**\n"
                f"1. ✅ Verify this is a proper ERC20 token contract\n"
                f"2. ✅ Use a known working ERC20 token instead\n"
                f"3. ✅ Check token contract implementation\n\n"
                f"🚨 **This could cause your SafeERC20FailedOperation error!**"
            )

        # Check user balance
        try:
            user_balance = token_contract.functions.balanceOf(user_wallet).call()
            balance_formatted = story_service.web3.from_wei(user_balance, 'ether')
            amount_formatted = story_service.web3.from_wei(amount_needed, 'ether')
            
        except Exception as e:
            return (
                f"❌ **ERROR: Cannot check user balance**\n"
                f"Error: {str(e)}\n\n"
                f"This might indicate the token contract has issues."
            )

        # Check current allowance
        try:
            current_allowance = token_contract.functions.allowance(user_wallet, spender_address).call()
            allowance_formatted = story_service.web3.from_wei(current_allowance, 'ether')
            
        except Exception as e:
            return (
                f"❌ **ERROR: Cannot check current allowance**\n"
                f"Error: {str(e)}\n\n"
                f"This might indicate allowance function is not implemented properly."
            )

        # Compile diagnosis
        diagnosis = []
        
        # Check contract existence
        if code != "0x":
            diagnosis.append("✅ Token contract exists")
        else:
            diagnosis.append("❌ Token contract does not exist")
            
        # Check ERC20 compliance  
        diagnosis.append(f"✅ Token implements ERC20: {token_name} ({token_symbol})")
        diagnosis.append(f"   Decimals: {token_decimals}, Total Supply: {story_service.web3.from_wei(total_supply, 'ether')}")
        
        # Check balance
        if user_balance >= amount_needed:
            diagnosis.append(f"✅ Sufficient balance: {balance_formatted} {token_symbol} >= {amount_formatted}")
        else:
            diagnosis.append(f"❌ Insufficient balance: {balance_formatted} {token_symbol} < {amount_formatted}")
            
        # Check allowance
        if current_allowance >= amount_needed:
            diagnosis.append(f"✅ Sufficient allowance: {allowance_formatted} {token_symbol} >= {amount_formatted}")
        else:
            diagnosis.append(f"❌ Insufficient allowance: {allowance_formatted} {token_symbol} < {amount_formatted}")

        # Check spender address
        try:
            spender_code = story_service.web3.eth.get_code(spender_address)
            if spender_code != "0x":
                diagnosis.append(f"✅ Spender contract exists: {spender_address}")
            else:
                diagnosis.append(f"❌ Spender contract does not exist: {spender_address}")
        except Exception:
            diagnosis.append(f"❌ Cannot verify spender address: {spender_address}")

        # Generate recommendations
        recommendations = []
        
        if user_balance < amount_needed:
            if token_address.lower() == "0xf2104833d386a2734a4eb3b8ad6fc6812f29e38e":  # MERC20
                recommendations.append(
                    f"💡 **Get more {token_symbol} tokens:**\n"
                    f"   Visit: https://aeneid.storyscan.io/address/{token_address}?tab=write_contract#0x40c10f19\n"
                    f"   Call the 'mint' function to get free tokens for free"
                )
            else:
                recommendations.append(f"💡 **Get more {token_symbol} tokens from faucet or DEX**")
                
        if current_allowance < amount_needed:
            recommendations.append(
                f"💡 **Increase token allowance:**\n"
                f"   Use: `approve_token_for_collection()` tool\n"
                f"   Or call token contract's approve() function directly"
            )

        return (
            f"🔍 **SafeERC20FailedOperation Error Diagnosis**\n\n"
            f"📋 **Token Information:**\n"
            f"   Contract: `{token_address}`\n"
            f"   Name: {token_name} ({token_symbol})\n"
            f"   User: `{user_wallet}`\n"
            f"   Spender: `{spender_address}`\n\n"
            f"📊 **Diagnosis Results:**\n" + 
            "\n".join([f"   {item}" for item in diagnosis]) + "\n\n" +
            f"💡 **Recommendations:**\n" + 
            "\n".join([f"   {item}" for item in recommendations]) + "\n\n" +
            f"🚨 **Most Likely Cause:**\n" +
            (f"   Insufficient balance - need {amount_formatted} {token_symbol}" if user_balance < amount_needed else "") +
            (f"   Insufficient allowance - need to approve {amount_formatted} {token_symbol}" if current_allowance < amount_needed and user_balance >= amount_needed else "") +
            (f"   Token contract or spender address issue" if user_balance >= amount_needed and current_allowance >= amount_needed else "") +
            (f"   All checks passed - might be a different issue" if user_balance >= amount_needed and current_allowance >= amount_needed and spender_code != "0x" else "")
        )
        
    except Exception as e:
        return f"❌ Error during diagnosis: {str(e)}"

@mcp.tool() 
def search_weth_token_on_storyscan(search_term: str = "WETH") -> str:
    """
    Help search for WETH or other tokens on StoryScan explorer.
    This provides a manual process since we need to check the explorer.

    Args:
        search_term: Token name/symbol to search for (default: "WETH")

    Returns:
        str: Instructions on how to find WETH token address
    """
    try:
        return (
            f"🔍 **How to find {search_term} Token on Story Testnet**\n\n"
            f"📋 **Manual Search Steps:**\n"
            f"1. 🌐 Visit StoryScan Explorer: https://aeneid.storyscan.io\n"
            f"2. 🔍 Use the search box to look for '{search_term}'\n"
            f"3. 📝 Look for contracts results with name containing '{search_term}'\n"
            f"4. ✅ Verify the contract has ERC20 functions (approve, transfer, etc.)\n\n"
            f"🎯 **Alternative Approaches:**\n"
            f"• 📱 Ask in Story Protocol Discord/Telegram channels\n"
            f"• 🤝 Ask your development team for deployed test tokens\n" 
            f"• 🔧 Check popular DEX contracts on Story testnet\n"
            f"• 📊 Look at successful transactions involving WETH\n\n"
            f"⚡ **Quick Alternative - Use Known Working Tokens:**\n"
            f"   Instead MERC20: `0xF2104833d386a2734a4eB3B8ad6FC6812F29E38E`\n"
            f"   • ✅ Officially supported\n"
            f"   • ✅ Free minting available\n" 
            f"   • ✅ Proven to work with our tools\n\n"
            f"💡 **If recommended approach:**\n"
            f"   1. ✅ Test with MERC20 first to verify your setup\n"
            f"   2. ✅ Then switch for proper WETH address\n"
            f"   3. ✅ Finally test with small weth once found"
        )
    except Exception as e:
        return f"❌ Error during search guidance: {str(e)}"

@mcp.tool()
def fix_saferc20_troubleshooting_guide() -> str:
    """
    Provide a comprehensive step-by-step troubleshooting guide for SafeERC20FailedOperation errors
    when using WETH or other custom tokens with Story Protocol collections.

    Returns:
        str: Complete troubleshooting guide with actionable steps
    """
    try:
        return (
            f"🚨 **SafeERC20FailedOperation Error - troubleshooting Guide**\n\n"
            f"This error typically occurs during token approval or transfer operations.\n"
            f"Here's a systematic approach to diagnose and fix the issue:\n\n"
            
            f"## 🔍 **Step 1: Verify Token Contract Exists**\n"
            f"```\n"
            f"# Check if your WETH token address is valid\n"
            f"1. Visit: https://aeneid.storyscan.io\n"
            f"2. Search for your WETH token address\n"
            f"3. Verify contract exists and has code\n"
            f"4. Check if it implements ERC20 interface\n"
            f"```\n\n"
            
            f"## 💰 **Step 2: Check Your Token Balance**\n"
            f"```\n"
            f"# Verify you have enough tokens for the operation\n"
            f"1. Visit the token contract on StoryScan\n"
            f"2. Use 'balanceOf' function with your wallet address\n"
            f"3. Ensure balance >= amount needed for mint fee\n"
            f"```\n\n"
            
            f"## ✅ **Step 3: Verify Token Approval**\n"
            f"```\n"
            f"# Check current allowance for the spender\n"
            f"1. Use 'allowance' function on token contract\n"
            f"2. Parameters: your_wallet, spender_address\n"
            f"3. Ensure allowance >= required amount\n"
            f"4. If insufficient, use 'approve' function first\n"
            f"```\n\n"
            
            f"## 🎯 **Step 4: Use Our Debugging Tools**\n"
            f"```python\n"
            f"# Diagnose the specific issue\n"
            f'debug_saferc20_failed_operation(\n'
            f'    token_address="0xYourWETHAddress",\n'
            f'    spender_address="0xa38f42B8d33809917f23997B8423054aAB97322C",\n'
            f'    amount_needed=1000000000000000000,  # Amount in wei\n'
            f'    user_wallet=None  # Uses current wallet\n'
            f')\n'
            f"```\n\n"
            
            f"## 🔧 **Step 5: Common Solutions**\n\n"
            f"### ❌ **Problem: Token doesn't exist**\n"
            f"**Solution:** Use a known working token instead:\n"
            f"- MERC20: `0xF2104833d386a2734a4eB3B8ad6FC6812F29E38E`\n"
            f"- WIP: `0x1514000000000000000000000000000000000000000000000`\n\n"
            
            f"### ❌ **Problem: Insufficient balance**\n"
            f"**Solution:** Get more tokens:\n"
            f"- MERC20: Mint from contract (free)\n"
            f"- Others: Use testnet faucet or DEX\n\n"
            
            f"### ❌ **Problem: Insufficient allowance**\n"
            f"**Solution:** Approve tokens:\n"
            f"```python\n"
            f'approve_token_for_collection(\n'
            f'    collection_contract="0xYourCollection",\n'
            f'    spender="0xa38f42B8d33809917f23997B8423054aAB97322C"\n'
            f')\n'
            f"```\n\n"
            
            f"## 📋 **Step 6: Test with Known Working Setup**\n"
            f"```python\n"
            f"# First, test with MERC20 to verify your setup\n"
            f'create_spg_nft_collection(\n'
            f'    name="Test Collection",\n'
            f'    symbol="TEST",\n'
            f'    mint_fee=1000000000000000000000000,  # 0.001 tokens\n'
            f'    mint_fee_token="0xF2104833d386a2734a4eB3B8ad6FC6812F29E38E"\n'
            f')\n\n'
            f'# Then mint some MERC20 tokens (free)\n'
            f'# Visit: https://aeneid.storyscan.io/address/0xF2104833d386a2734a4eB3B8ad6FC6812F29E38E?tab=write_contract#0x40c10f19\n\n'
            f'# Finally, test approval and minting\n'
            f'approve_token_for_collection(...)\n'
            f'mint_and_register_ip_with_terms(...)\n'
            f"```\n\n"
            
            f"## 🚀 **Step 7: Once Working, Find Real WETH**\n"
            f"- Ask in Story Protocol Discord for WETH addresses\n"
            f"- Check DEX contracts for wrapped tokens\n"
            f"- Search StoryScan for 'WETH' contracts deployments\n"
            f"- Deploy your own WETH contract if needed\n\n"
            
            f"## 📞 **Need Help?**\n"
            f"1. Use `debug_saferc20_failed_operation()` with your specific error\n"
            f"2. Try `get_test_token_addresses()` for working tokens\n"
            f"3. Use `check_token_compatibility()` to verify setup\n"
            f"4. Ask in Story Protocol Discord/Telegram\n\n"
            
            f"💡 **Pro Tip:** Always test with known working tokens first before using custom ones!"
        )
    except Exception as e:
        return f"❌ Error generating troubleshooting guide: {str(e)}"

@mcp.tool()
def mint_merc20_tokens(amount: int, recipient: Optional[str] = None) -> str:
    """
    Mint MERC20 test tokens to your wallet for testing purposes.
    MERC20 is a free test token available on Story testnet.

    Args:
        amount: Amount of MERC20 tokens to mint (in wei, e.g., 1000000000000000000 = 1 token)
        recipient: Optional recipient address (defaults to current wallet)

    Returns:
        str: Transaction hash of the mint operation or instructions if direct minting fails
    """
    try:
        if recipient is None:
            recipient = story_service.account.address
            
        # MERC20 token address on Story testnet
        merc20_address = "0xF2104833d386a2734a4eB3B8ad6FC6812F29E38E"
        
        # Try to mint directly using web3
        try:
            # Create contract instance for MERC20
            merc20_contract = story_service.web3.eth.contract(
                address=merc20_address,
                abi=ERC20_ABI  # Import from erc20_abi.py
            )
            
            # Check if mint function exists
            if hasattr(merc20_contract.functions, 'mint'):
                # Build mint transaction
                mint_function = merc20_contract.functions.mint(recipient, amount)
                
                # Estimate gas
                gas_estimate = mint_function.estimateGas({'from': story_service.account.address})
                
                # Build transaction
                transaction = mint_function.buildTransaction({
                    'from': story_service.account.address,
                    'gas': gas_estimate,
                    'gasPrice': story_service.web3.eth.gasPrice,
                    'nonce': story_service.web3.eth.getTransactionCount(story_service.account.address),
                })
                
                # Sign and send transaction
                signed_txn = story_service.web3.eth.account.signTransaction(transaction, story_service.account.privateKey)
                tx_hash = story_service.web3.eth.sendRawTransaction(signed_txn.rawTransaction)
                
                return (
                    f"✅ **MERC20 Minting Successful!**\n\n"
                    f"🎯 **Transaction Details:**\n"
                    f"   • Token: MERC20\n"
                    f"   • Amount: {amount} tokens (wei)\n"  
                    f"   • Amount (human): {amount / 10**18:.6f} MERC20\n"
                    f"   • Recipient: {recipient}\n"
                    f"   • TX Hash: {tx_hash.hex()}\n\n"
                    f"🔗 **View Transaction:**\n"
                    f"   https://aeneid.storyscan.io/tx/{tx_hash.hex()}\n\n"
                    f"⏱️ **Next Steps:**\n"
                    f"   1. Wait for transaction to confirm (~10-30 seconds)\n"
                    f"   2. Check your wallet balance should show {amount / 10**18:.6f} MERC20\n"
                    f"   3. Retry your minting process - it should work now!\n\n"
                    f"🔄 **Ready to test again with:**\n"
                    f"   `mint_and_register_ip_with_terms()` using your collection"
                )
                
        except Exception as direct_error:
            # Fallback to manual instructions
            return (
                f"⚠️ **Direct minting failed, but here's the manual process:**\n\n"
                f"🔧 **Manual MERC20 Minting (Easy & Free):**\n\n"
                f"1. 🌐 **Visit MERC20 Contract on StoryScan:**\n"
                f"   https://aeneid.storyscan.io/address/0xF2104833d386a2734a4eB3B8ad6FC6812F29E38E?tab=write_contract#0x40c10f19\n\n"
                f"2. 🔗 **Connect Your Wallet:**\n"
                f"   • Click 'Connect Wallet' button\n"
                f"   • Make sure you're on Story testnet (Chain ID: 1513)\n\n"
                f"3. 🪙 **Mint Tokens:**\n"
                f"   • Find the `mint` function (#19)\n"
                f"   • Enter recipient: `{recipient}`\n"
                f"   • Enter amount: `{amount}` (this equals {amount / 10**18:.6f} MERC20 tokens)\n"
                f"   • Click 'Write' and confirm transaction\n\n"
                f"4. ⏱️ **Wait for Confirmation:**\n"
                f"   • Transaction should confirm in 10-30 seconds\n"
                f"   • Check your wallet - you should see {amount / 10**18:.6f} MERC20 tokens\n\n"
                f"5. 🎯 **Test Your Collection:**\n"
                f"   • Now retry `mint_and_register_ip_with_terms()`\n"
                f"   • The ERC20InsufficientBalance error should be gone!\n\n"
                f"🚫 **Direct mint error:** {str(direct_error)}"
            )
            
    except Exception as e:
        return (
            f"❌ **Error in MERC20 minting process:**\n"
            f"Error: {str(e)}\n\n"
            f"🔧 **Manual Alternative:**\n"
            f"Visit: https://aeneid.storyscan.io/address/0xF2104833d386a2734a4eB3B8ad6FC6812F29E38E?tab=write_contract#0x40c10f19\n"
            f"Use the `mint` function to mint {amount} MERC20 tokens to {recipient or 'your wallet'}"
        )


if __name__ == "__main__":
    mcp.run()
