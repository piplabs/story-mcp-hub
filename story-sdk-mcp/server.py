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
                f"Successfully created and uploaded metadata! Here's what happened:\n\n"
                f"Your Request:\n"
                f"   • Image URI: {image_uri}\n"
                f"   • Name: {name}\n"
                f"   • Description: {description}\n"
                f"   • Attributes: {len(attributes) if attributes else 0} attributes\n\n"
                f"Generated Metadata:\n"
                f"   • NFT Metadata URI: {result['nft_metadata_uri']}\n"
                f"   • IP Metadata URI: {result['ip_metadata_uri']}\n"
                f"   • Registration metadata for minting:\n"
                f"{json.dumps(result['registration_metadata'], indent=2)}"
            )
        except Exception as e:
            return f"Error creating metadata: {str(e)}"


@mcp.tool()
def get_license_terms(license_terms_id: int) -> str:
    """Get the license terms for a specific ID."""
    try:
        terms = story_service.get_license_terms(license_terms_id)
        
        return (
            f"Successfully retrieved license terms! Here are the complete details:\n\n"
            f"Your Request:\n"
            f"   • License Terms ID: {license_terms_id}\n\n"
            f"License Terms Details:\n"
            f"   • Transferable: {terms.get('transferable', 'N/A')}\n"
            f"   • Royalty Policy: {terms.get('royaltyPolicy', 'N/A')}\n"
            f"   • Default Minting Fee: {terms.get('defaultMintingFee', 'N/A')} wei\n"
            f"   • Expiration: {terms.get('expiration', 'N/A')}\n"
            f"   • Commercial Use: {terms.get('commercialUse', 'N/A')}\n"
            f"   • Commercial Attribution: {terms.get('commercialAttribution', 'N/A')}\n"
            f"   • Commercial Revenue Share: {terms.get('commercialRevShare', 'N/A')}\n"
            f"   • Derivatives Allowed: {terms.get('derivativesAllowed', 'N/A')}\n"
            f"   • Derivatives Attribution: {terms.get('derivativesAttribution', 'N/A')}\n"
            f"   • Derivatives Reciprocal: {terms.get('derivativesReciprocal', 'N/A')}\n"
            f"   • Currency: {terms.get('currency', 'N/A')}\n"
            f"   • URI: {terms.get('uri', 'N/A')}"
        )
    except Exception as e:
        return f"❌ Error retrieving license terms for ID {license_terms_id}: {str(e)}"


@mcp.tool()
def get_license_minting_fee(license_terms_id: int) -> str:
    """
    Get the minting fee for a specific license terms ID.
    
    Args:
        license_terms_id: The ID of the license terms
        
    Returns:
        str: Information about the minting fee
    """
    try:
        minting_fee = story_service.get_license_minting_fee(license_terms_id)
        fee_in_ether = story_service.web3.from_wei(minting_fee, 'ether')
        
        return (
            f"Successfully retrieved minting fee information for License Terms ID {license_terms_id}:\n\n"
            f"Your Request:\n"
            f"   • License Terms ID: {license_terms_id}\n\n"
            f"Minting Fee Details:\n"
            f"   • Fee Amount: {minting_fee} wei ({fee_in_ether} IP)\n"
            f"   • This is the cost to mint each license token from this license terms"
        )
    except Exception as e:
        return f"❌ Error retrieving license minting fee for License Terms ID {license_terms_id}: {str(e)}"


@mcp.tool()
def get_license_revenue_share(license_terms_id: int) -> str:
    """
    Get the commercial revenue share percentage for a specific license terms ID.
    
    Args:
        license_terms_id: The ID of the license terms
        
    Returns:
        str: Information about the revenue share percentage
    """
    try:
        revenue_share = story_service.get_license_revenue_share(license_terms_id)
        
        return (
            f"Successfully retrieved revenue share information for License Terms ID {license_terms_id}:\n\n"
            f"Your Request:\n"
            f"   • License Terms ID: {license_terms_id}\n\n"
            f"Revenue Share Details:\n"
            f"   • Commercial Revenue Share: {revenue_share}%\n"
            f"   • This is the percentage of commercial revenue that must be shared"
        )
    except Exception as e:
        return f"❌ Error retrieving license revenue share for License Terms ID {license_terms_id}: {str(e)}"


@mcp.tool()
def mint_license_tokens(
    licensor_ip_id: str,
    license_terms_id: int,
    receiver: Optional[str] = None,
    amount: int = 1,
    max_minting_fee: Optional[int] = None,
    max_revenue_share: Optional[int] = None,
    license_template: Optional[str] = None
) -> str:
    """
    Mint license tokens for a given IP and license terms.

    ⚠️ MANDATORY WORKFLOW - DO NOT CALL THIS FUNCTION DIRECTLY ⚠️
    
    🤖 AGENT WORKFLOW - FOLLOW THESE STEPS EXACTLY:
    1. FIRST: Call get_license_minting_fee(license_terms_id) to get the required minting fee
    2. SECOND: Call get_license_revenue_share(license_terms_id) to get the revenue share percentage
    3. THIRD: Present this information to the user for confirmation:
       "This license requires a minting fee of X wei (Y IP) and has a Z% revenue share. Do you want to proceed?"
    4. FOURTH: If user confirms, call this function with the retrieved values as max_minting_fee and max_revenue_share
    
    ❌ NEVER call this function without completing steps 1-3 first!
    
    ⚠️ IMPORTANT: This method makes blockchain transactions and spends tokens. 
    Please double-check all parameters with the user and get their confirmation before proceeding.

    💰 AUTO-APPROVE: This method automatically approves the exact amount of WIP tokens needed for minting.
    The system will approve only the required fee amount to ensure the transaction succeeds.

    Args:
        licensor_ip_id: The ID of the licensor's intellectual property
        license_terms_id: The ID of the license terms
        receiver: [Optional] the recipient's address for the tokens (ask user if not provided)
        amount: [Optional] number of license tokens to mint (ask user, defaults to 1)
        max_minting_fee: [HIDDEN] DO NOT ask user - automatically set from get_license_minting_fee()
        max_revenue_share: [HIDDEN] DO NOT ask user - automatically set from get_license_revenue_share()
        license_template: [HIDDEN] DO NOT ask user - uses default template

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
            license_template=license_template
        )

        return (
            f"Successfully minted license tokens! Here's what happened:\n\n"
            f"Your Request:\n"
            f"   • Licensor IP ID: {licensor_ip_id}\n"
            f"   • License Terms ID: {license_terms_id}\n"
            f"   • Number of tokens minted: {amount}\n"
            f"   • Recipient: {receiver if receiver else 'Your wallet (default)'}\n"
            f"Result Summary:\n"
            f"   • Transaction Hash: {response['tx_hash']}\n"
            f"   • License Token IDs: {response['license_token_ids']}\n"
            f"   • Your license tokens are now ready to use"
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
    spg_nft_contract_mint_fee_token: Optional[str] = None
) -> str:
    """
    Mint an NFT, register it as an IP Asset, and attach PIL terms.
    Automatically detects if the SPG contract requires a minting fee and handles it appropriately.

    ⚠️ CONDITIONAL WORKFLOW - READ CAREFULLY ⚠️
    
    🤖 AGENT WORKFLOW - FOLLOW THESE STEPS EXACTLY:
    1. FIRST: If spg_nft_contract is provided, call get_spg_nft_contract_minting_fee_and_token(spg_nft_contract) to get fee info
    2. SECOND: Present the SPG contract fee information to the user for confirmation:
       "This SPG contract requires a minting fee of X wei (Y IP) using Z token. Do you want to proceed?"
    3. THIRD: If user confirms, call this function with the retrieved values as spg_nft_contract_max_minting_fee and spg_nft_contract_mint_fee_token
    4. NOTE: If spg_nft_contract is None, the system will use the default SPG contract (no need to check fees)
    
    ❌ NEVER call this function with a custom spg_nft_contract without completing steps 1-2 first!

    ⚠️ IMPORTANT: This method makes blockchain transactions and spends tokens. 
    Please double-check all parameters with the user and get their confirmation before proceeding.

    💰 AUTO-APPROVE: This method automatically approves the exact amount of tokens needed for minting.
    The system will approve only the required fee amount to ensure the transaction succeeds.

    Args:
        commercial_rev_share: Percentage of revenue share (0-100) (ask user)
        derivatives_allowed: Whether derivatives are allowed (ask user)
        registration_metadata: Dict containing metadata URIs and hashes from create_ip_metadata (ask user)
        commercial_use: [Optional] Whether this is a commercial license (ask user, defaults to True)
        minting_fee: [Optional] Fee required to mint license tokens in wei (ask user, defaults to 0) 
        recipient: [Optional] recipient address (ask user if not provided, defaults to sender)
        spg_nft_contract: [Optional] SPG NFT contract address (ask user if they want to use custom contract, defaults to network-specific default)
        spg_nft_contract_max_minting_fee: [HIDDEN] DO NOT ask user - automatically set from get_spg_nft_contract_minting_fee_and_token()
        spg_nft_contract_mint_fee_token: [HIDDEN] DO NOT ask user - automatically set from get_spg_nft_contract_minting_fee_and_token()

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
            spg_nft_contract_mint_fee_token=spg_nft_contract_mint_fee_token
        )

        # Determine which explorer URL to use based on network
        explorer_url = (
            "https://explorer.story.foundation"
            if story_service.network == "mainnet"
            else "https://aeneid.explorer.story.foundation"
        )

        return (
            f"Successfully minted NFT and registered as IP Asset with license terms! Here's the complete summary:\n\n"
            f"Your Configuration:\n"
            f"   • Commercial Revenue Share: {commercial_rev_share}%\n"
            f"   • Derivatives Allowed: {'Yes' if derivatives_allowed else 'No'}\n"
            f"   • Commercial Use: {'Enabled' if commercial_use else 'Disabled'}\n"
            f"   • Minting Fee: {minting_fee} WIP in wei\n"
            f"   • Recipient: {recipient if recipient else 'Your wallet (default)'}\n"
            f"   • SPG NFT Contract: {spg_nft_contract if spg_nft_contract else 'Default network contract'}\n\n"
            f"Created Assets:\n"
            f"   • IP Asset ID: {response['ip_id']}\n"
            f"   • NFT Token ID: {response['token_id']}\n"
            f"   • License Terms IDs: {response['license_terms_ids']}\n"
            f"   • Transaction Hash: {response.get('tx_hash')}\n"
            f"   • View your IP Asset: {explorer_url}/ipa/{response['ip_id']}"
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
            f"Successfully created your SPG NFT collection! Here's what was set up:\n\n"
            f"Your Collection Configuration:\n"
            f"   • Collection Name: {name}\n"
            f"   • Symbol: {symbol}\n"
            f"   • Public Minting: {'Enabled (anyone can mint)' if is_public_minting else 'Restricted (only authorized minters)'}\n"
            f"   • Minting Status: {'Open (minting allowed)' if mint_open else 'Closed (minting paused)'}\n"
            f"   • Base URI: {base_uri if base_uri else 'Not set (tokens will use individual metadata URIs)'}\n"
            f"   • Max Supply: {max_supply if max_supply is not None else 'Unlimited'}\n"
            f"   • Mint Fee: {mint_fee if mint_fee is not None else '0'} wei\n"
            f"   • Fee Token: {mint_fee_token if mint_fee_token else 'WIP (default)'}\n"
            f"   • Fee Recipient: {mint_fee_recipient if mint_fee_recipient else 'Your wallet (default)'}\n"
            f"   • Collection Owner: {owner if owner else 'Your wallet (default)'}\n\n"
            f"Result Summary:\n"
            f"   • Transaction Hash: {response['tx_hash']}\n"
            f"   • SPG NFT Contract Address: {response['spg_nft_contract']}"
        )
    except Exception as e:
        return f"Error creating SPG NFT collection: {str(e)}"


@mcp.tool()
def get_spg_nft_contract_minting_fee_and_token(spg_nft_contract: str) -> str:
    """
    Get the minting fee required by an SPG NFT contract.

    💡 USAGE: This is typically called BEFORE mint_and_register_ip_with_terms() to inform the user about SPG contract costs.

    Args:
        spg_nft_contract: The address of the SPG NFT contract

    Returns:
        str: Information about the minting fee
    """
    try:
        fee_info = story_service.get_spg_nft_contract_minting_fee_and_token(spg_nft_contract)
        
        fee_amount = fee_info['mint_fee']
        fee_token = fee_info['mint_fee_token']
        
        # Format the fee amount nicely
        if fee_amount == 0:
            fee_display = "FREE (0)"
        else:
            # Convert from wei to a more readable format
            fee_in_ether = story_service.web3.from_wei(fee_amount, 'ether')
            fee_display = f"{fee_amount} wei ({fee_in_ether} IP)"
        
        token_display = f"Token at {fee_token}"
        
        return (
            f"Successfully retrieved SPG NFT contract fee information:\n\n"
            f"Your Request:\n"
            f"   • SPG Contract Address: {spg_nft_contract}\n\n"
            f"Minting Fee Details:\n"
            f"   • Fee Amount: {fee_display}\n"
            f"   • Payment Token: {token_display}"
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
            return (
                f"Successfully registered NFT as IP Asset! Here's your registration summary:\n\n"
                f"Your Registration:\n"
                f"   • NFT Contract: {nft_contract}\n"
                f"   • Token ID: {token_id}\n"
                f"   • IP Metadata: {'Provided' if ip_metadata else 'Not provided (using defaults)'}\n\n"
                f"Result Summary:\n"
                f"   • Transaction Hash: {result['tx_hash']}\n"
                f"   • New IP Asset ID: {result['ip_id']}\n\n"
            )
        else:
            return (
                f"NFT was already registered as an IP Asset:\n\n"
                f"Your Request:\n"
                f"   • NFT Contract: {nft_contract}\n"
                f"   • Token ID: {token_id}\n\n"
                f"Registration Status:\n"
                f"   • Existing IP Asset ID: {result['ip_id']}\n"
                f"   • Status: Already registered (no transaction needed)"
            )
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
        
        return (
            f"Successfully attached license terms {license_terms_id} to IP {ip_id}\n\n"
            f"License Template: {license_template if license_template else 'Default template'}\n"
            f"Result Summary:\n"
            f"   • Transaction Hash: {result['tx_hash']}"
        )
    except Exception as e:
        return f"Error attaching license terms: {str(e)}"

# bug in sdk, will update after next sdk release
# @mcp.tool()
# def register_derivative(
#     child_ip_id: str,
#     parent_ip_ids: list,
#     license_terms_ids: list,
#     max_minting_fee: int = 0,
#     max_rts: int = 0,
#     max_revenue_share: int = 0,
#     license_template: Optional[str] = None,
#     approve_amount: Optional[int] = None
# ) -> str:
#     """
#     Registers a derivative directly with parent IP's license terms, without needing license tokens.

#     ⚠️ IMPORTANT: This method makes blockchain transactions. 
#     Please double-check all parameters with the user and get their confirmation before proceeding.

#     Args:
#         child_ip_id: The derivative IP ID
#         parent_ip_ids: The parent IP IDs (list of IP IDs)
#         license_terms_ids: The IDs of the license terms that the parent IP supports (list of term IDs)
#         max_minting_fee: The maximum minting fee that the caller is willing to pay in wei (default: 0 = no limit)
#         max_rts: The maximum number of royalty tokens that can be distributed (max: 100,000,000)
#         max_revenue_share: The maximum revenue share percentage allowed 0-100
#         license_template: [Optional] address of the license template (defaults to the default template)
#         approve_amount: [Optional] amount to approve for spending WIP tokens in wei (Default is exact amount needed for the transaction). 
#     Returns:
#         str: Result message with transaction hash
#     """
#     try:
#         result = story_service.register_derivative(
#             child_ip_id=child_ip_id,
#             parent_ip_ids=parent_ip_ids,
#             license_terms_ids=license_terms_ids,
#             max_minting_fee=max_minting_fee,
#             max_rts=max_rts,
#             max_revenue_share=max_revenue_share,
#             license_template=license_template,
#             approve_amount=approve_amount
#         )
        
#         return f"Successfully registered derivative. Transaction hash: {result['tx_hash']}"
#     except Exception as e:
#         return f"Error registering derivative: {str(e)}"


@mcp.tool()
def pay_royalty_on_behalf(
    receiver_ip_id: str,
    payer_ip_id: str,
    token: str,
    amount: int
) -> str:
    """
    Allows the function caller to pay royalties to the receiver IP asset on behalf of the payer IP asset.

    ⚠️ IMPORTANT: This method makes blockchain transactions and spends tokens. 
    Please double-check all parameters with the user and get their confirmation before proceeding.

    💰 AUTO-APPROVE: This method automatically approves the exact amount of tokens needed for paying royalties.
    The system will approve only the required amount to ensure the transaction succeeds.

    Args:
        receiver_ip_id: The IP ID that receives the royalties
        payer_ip_id: The ID of the IP asset that pays the royalties
        token: The token address to use to pay the royalties
        amount: The amount to pay in wei

    Returns:
        str: Success message with transaction hash
    """
    try:
        response = story_service.pay_royalty_on_behalf(
            receiver_ip_id=receiver_ip_id,
            payer_ip_id=payer_ip_id,
            token=token,
            amount=amount
        )

        return (
            f"Successfully paid royalty on behalf! Here's what happened:\n\n"
            f"Your Payment Details:\n"
            f"   • Receiver IP ID: {receiver_ip_id}\n"
            f"   • Payer IP ID: {payer_ip_id}\n"
            f"   • Payment Token: {token}\n"
            f"   • Amount Paid: {amount} wei\n"
            f"   • Transaction Hash: {response['tx_hash']}\n"
            f"   • You paid royalties to {receiver_ip_id} on behalf of {payer_ip_id}"
        )
    except Exception as e:
        return f"Error paying royalty on behalf: {str(e)}"



@mcp.tool()
def claim_all_revenue(
    ancestor_ip_id: str,
    child_ip_ids: list,
    license_ids: list,
    auto_transfer: bool = True,
    claimer: Optional[str] = None
) -> str:
    """
    Claims all revenue from the child IPs of an ancestor IP, then optionally transfers tokens to the claimer.
    
    ⚠️ IMPORTANT: This method makes blockchain transactions and claims tokens. 
    Please double-check all parameters with the user and get their confirmation before proceeding.
    
    Args:
        ancestor_ip_id: The ancestor IP ID
        child_ip_ids: The list of child IP IDs (must be in same order as license_ids)
        license_ids: The list of license terms IDs 
        auto_transfer: Whether to automatically transfer the claimed tokens to the claimer
        claimer: Optional claimer address (defaults to current account)
    Returns:
        str: User-friendly summary of the revenue claim process and results
    """
    try:
        response = story_service.claim_all_revenue(
            ancestor_ip_id=ancestor_ip_id,
            child_ip_ids=child_ip_ids,
            license_ids=license_ids,
            auto_transfer=auto_transfer,
            claimer=claimer
        )
        
        # Return user-friendly formatted string
        return (
            f"Successfully claimed all revenue! Here's your revenue claim summary:\n\n"
            f"Your Request:\n"
            f"   • Ancestor IP ID: {ancestor_ip_id}\n"
            f"   • Child IP IDs: {child_ip_ids}\n"
            f"   • License IDs: {license_ids}\n"
            f"   • Auto Transfer: {'Enabled' if auto_transfer else 'Disabled'}\n"
            f"   • Claimer: {claimer if claimer else 'Your wallet (default)'}\n\n"
            f"Result Summary:\n"
            f"   • Transaction Hash: {response.get('tx_hash', 'N/A')}\n"
        )
    except Exception as e:
        return (
            f"❌ Error claiming revenue: {str(e)}\n\n"
            f"📋 Your Request Details:\n"
            f"   • Ancestor IP ID: {ancestor_ip_id}\n"
            f"   • Child IP IDs: {child_ip_ids}\n"
            f"   • License IDs: {license_ids}\n"
            f"   • Auto Transfer: {'Enabled' if auto_transfer else 'Disabled'}\n"
            f"   • Claimer: {claimer if claimer else 'Your wallet (default)'}\n\n"
            f"💡 Please check your inputs and try again, or contact support if the issue persists."
        )


@mcp.tool()
def raise_dispute(
    target_ip_id: str,
    target_tag: str,
    cid: str,
    bond_amount: int,
    liveness: int = 30
) -> str:
    """
    ⚖️ Raises a dispute against an IP asset using the Story Protocol SDK.
    
    ⚠️ IMPORTANT: This method makes blockchain transactions and spends tokens. 
    Please double-check all parameters with the user and get their confirmation before proceeding.
    
    💰 AUTO-APPROVE: This method automatically approves the exact amount of WIP tokens needed for the dispute bond.
    The system will approve only the required bond amount to ensure the transaction succeeds.

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
            liveness=liveness
        )
        
        if 'error' in result:
            return f"Error raising dispute: {result['error']}"
        
        dispute_id = result.get('dispute_id', 'Unknown')
        dispute_tag = result.get('dispute_tag', 'Unknown')
        liveness_days = result.get('liveness_days', 'Unknown')
        liveness_seconds = result.get('liveness_seconds', 'Unknown')
        bond_amount_ip = result.get('bond_amount_ip', 'Unknown')
        
        return (
            f"⚖️ Successfully raised dispute! Here's your dispute summary:\n\n"
            f"📋 Your Dispute Details:\n"
            f"   • Target IP ID: {target_ip_id}\n"
            f"   • Dispute Tag: {target_tag}\n"
            f"   • Evidence CID: {cid}\n"
            f"   • Bond Amount: {bond_amount} wei ({bond_amount_ip} IP)\n"
            f"   • Liveness Period: {liveness_days} days ({liveness_seconds} seconds)\n\n"
            f"🔗 Dispute Registration:\n"
            f"   • Transaction Hash: {result['tx_hash']}\n"
            f"   • Dispute ID: {dispute_id}\n\n"
            f"💰 Auto-Approval Applied:\n"
            f"   • The system automatically approved {bond_amount} wei of WIP tokens for the dispute bond\n"
            f"   • Your bond has been locked and will be returned if the dispute is successful\n\n"
            f"🚀 What Happened:\n"
            f"   • Filed a formal dispute against IP {target_ip_id} with tag '{dispute_tag}'\n"
            f"   • Posted your dispute bond to the Story Protocol dispute system\n"
            f"   • Uploaded evidence to IPFS with identifier: {cid}\n"
            f"   • Set dispute resolution period to {liveness_days} days\n\n"
            f"⏰ What's Next:\n"
            f"   • The dispute is now active and under review\n"
            f"   • Community and validators can examine your evidence\n"
            f"   • Resolution will occur within {liveness_days} days\n"
            f"   • You'll receive your bond back if the dispute is upheld\n\n"
            f"⚠️ Important Notes:\n"
            f"   • Monitor the dispute status using Dispute ID: {dispute_id}\n"
            f"   • Ensure your evidence at {cid} remains accessible\n"
            f"   • False disputes may result in bond forfeiture"
        )
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
def deposit_wip(amount: int) -> str:
    """
    Wraps the selected amount of IP to WIP and deposits to the wallet.
    
    ⚠️ IMPORTANT: This method makes blockchain transactions and wraps tokens. 
    Please double-check all parameters with the user and get their confirmation before proceeding.
    
    :param amount int: The amount of IP to wrap in wei.
    :return str: User-friendly summary of the wrapping process and results.
    """
    try:
        response = story_service.deposit_wip(amount=amount)
        amount_in_ip = story_service.web3.from_wei(amount, 'ether')
        
        return (
            f"Successfully wrapped {amount_in_ip} IP tokens to WIP!"
        )
    except Exception as e:
        return (
            f"❌ Error wrapping IP to WIP: {str(e)}\n\n"
            f"Your Request Details:\n"
            f"   • Amount to wrap: {amount} wei ({story_service.web3.from_wei(amount, 'ether')} IP)\n"
            f"   • Action: Convert IP tokens to WIP (Wrapped IP) tokens\n\n"
            f"Please check your IP balance and try again, or contact support if the issue persists."
        )

@mcp.tool()
def get_erc20_token_balance(token_address: str, account_address: Optional[str] = None) -> str:
    """
    Get the balance of any ERC20 token for an account.
    
    Args:
        token_address: The address of the ERC20 token contract (e.g., MERC20: 0xF2104833d386a2734a4eB3B8ad6FC6812F29E38E)
        account_address: [Optional] The address to check balance for (defaults to your wallet address)
        
    Returns:
        str: Balance information including amount in both wei and decimal format
        
    Example:
        # Check MERC20 balance
        get_erc20_token_balance("0xF2104833d386a2734a4eB3B8ad6FC6812F29E38E")
    """
    try:
        balance_info = story_service.get_token_balance(
            token_address=token_address,
            account_address=account_address
        )
        
        return (
            f"✅ Successfully retrieved token balance information:\n\n"
            f"📋 Your Request:\n"
            f"   • Token Contract: {token_address}\n"
            f"   • Account: {account_address if account_address else 'Your wallet (default)'}\n\n"
            f"💰 Balance Details:\n"
            f"   • Token: {balance_info['symbol']} ({balance_info['token_address']})\n"
            f"   • Account Address: {balance_info['account_address']}\n"
            f"   • Balance: {balance_info['balance']} {balance_info['symbol']}\n"
            f"   • Balance (wei): {balance_info['balance_wei']} wei\n"
            f"   • Token Decimals: {balance_info['decimals']}\n\n"
            f"💡 Understanding Your Balance:\n"
            f"   • The balance shows how many {balance_info['symbol']} tokens you own\n"
            f"   • Wei is the smallest unit (like cents for dollars)\n"
            f"   • You can use these tokens for transactions if the contract supports them\n\n"
            f"🎉 What You Can Do:\n"
            f"   • Transfer tokens to other addresses\n"
            f"   • Use tokens in Story Protocol if they're supported (like WIP, MERC20)\n"
            f"   • Check transaction history for this token"
        )
    except Exception as e:
        return f"Error getting token balance: {str(e)}"

@mcp.tool()
def mint_test_erc20_tokens(
    token_address: str,
    amount: int,
    recipient: Optional[str] = None
) -> str:
    """
    Attempt to mint test ERC20 tokens if the contract has a public mint/faucet function.
    This is common for testnet tokens like MERC20.
    
    Args:
        token_address: The address of the ERC20 token contract (e.g., MERC20: 0xF2104833d386a2734a4eB3B8ad6FC6812F29E38E)
        amount: The amount to mint in wei (e.g., 1000000000000000000 for 1 token with 18 decimals)
        recipient: [Optional] The recipient address (defaults to your wallet)
        
    Returns:
        str: Result message with transaction details
        
    Example:
        # Mint 100 MERC20 tokens (with 18 decimals)
        mint_test_erc20_tokens("0xF2104833d386a2734a4eB3B8ad6FC6812F29E38E", 100000000000000000000)
    """
    try:
        result = story_service.mint_test_token(
            token_address=token_address,
            amount=amount,
            recipient=recipient
        )
        
        function_used = result.get('function_used', 'unknown')
        amount_display = result.get('amount', 'unknown')
        
        if amount_display != 'faucet default':
            # Try to get decimals and convert for display
            try:
                balance_info = story_service.get_token_balance(token_address)
                decimals = balance_info['decimals']
                symbol = balance_info['symbol']
                amount_decimal = amount / (10 ** decimals)
                amount_display = f"{amount_decimal} {symbol}"
            except:
                amount_display = f"{amount} wei"
        
        return (
            f"✅ Successfully minted test tokens! Here's what happened:\n\n"
            f"📋 Your Request:\n"
            f"   • Token Contract: {token_address}\n"
            f"   • Amount Requested: {amount} wei\n"
            f"   • Recipient: {result['recipient']}\n\n"
            f"🔗 Transaction Details:\n"
            f"   • Transaction Hash: {result['tx_hash']}\n"
            f"   • Function Used: {function_used}\n"
            f"   • Amount Minted: {amount_display}\n\n"
            f"🚀 What Happened:\n"
            f"   • Found a public mint function ({function_used}) on the token contract\n"
            f"   • Successfully called the mint function to create new tokens\n"
            f"   • Tokens have been added to the recipient's balance\n\n"
            f"💡 Next Steps:\n"
            f"   • Check your token balance to confirm the mint was successful\n"
            f"   • You can now use these tokens for testing Story Protocol features\n"
            f"   • Transaction may take a moment to confirm on the blockchain\n\n"
            f"⚠️ Note: These are test tokens for development/testing purposes only"
        )
    except Exception as e:
        error_msg = str(e)
        if "No public mint function found" in error_msg:
            return (
                f"Error: MERC20 at {token_address} doesn't have a public mint function.\n\n"
                f"Alternative options to get MERC20:\n"
                f"1. Ask someone with MERC20 to send you some\n"
                f"2. Check if there's a specific MERC20 faucet website\n"
                f"3. Contact the Story Protocol team on Discord/Telegram for test tokens\n"
                f"4. Use a different test token that has a public mint function"
            )
        else:
            return f"Error minting test tokens: {error_msg}"

@mcp.tool()
def transfer_wip(to: str, amount: int) -> str:
    """
    Transfers `amount` of WIP to a recipient `to`.
    
    ⚠️ IMPORTANT: This method makes blockchain transactions and transfers tokens. 
    Please double-check all parameters with the user and get their confirmation before proceeding.
    
    :param to str: The address of the recipient.
    :param amount int: The amount of WIP to transfer in wei.
    :return str: User-friendly summary of the transfer process and results.
    """
    try:
        response = story_service.transfer_wip(to=to, amount=amount)
        amount_in_ip = story_service.web3.from_wei(amount, 'ether')
        
        return (
            f"✅ Successfully transferred WIP tokens! Here's what happened:\n\n"
            f"📋 Your Transfer Details:\n"
            f"   • Recipient: {to}\n"
            f"   • Amount: {amount} wei ({amount_in_ip} WIP)\n"
            f"   • Token Type: WIP (Wrapped IP)\n\n"
            f"🔗 Transaction Details:\n"
            f"   • Transaction Hash: {response.get('tx_hash')}\n\n"
            f"💸 Transfer Process:\n"
            f"   • {amount_in_ip} WIP tokens have been sent from your wallet\n"
            f"   • The recipient will receive the tokens once the transaction confirms\n"
            f"   • Your WIP balance has been reduced by {amount_in_ip} WIP\n\n"
            f"🚀 What Happened:\n"
            f"   • Initiated a WIP token transfer on the Story Protocol network\n"
            f"   • Used the ERC-20 transfer function for secure token movement\n"
            f"   • Transaction is now being processed by the blockchain\n\n"
            f"💡 Next Steps:\n"
            f"   • Monitor the transaction hash for confirmation status\n"
            f"   • The recipient can check their WIP balance after confirmation\n"
            f"   • You can verify your updated balance in your wallet\n\n"
            f"🎉 Transfer initiated successfully!"
        )
    except Exception as e:
        return (
            f"❌ Error transferring WIP tokens: {str(e)}\n\n"
            f"📋 Your Transfer Details:\n"
            f"   • Recipient: {to}\n"
            f"   • Amount: {amount} wei ({story_service.web3.from_wei(amount, 'ether')} WIP)\n"
            f"   • Token Type: WIP (Wrapped IP)\n\n"
            f"💡 Please check your WIP balance and recipient address, then try again."
        )

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



if __name__ == "__main__":
    mcp.run()
