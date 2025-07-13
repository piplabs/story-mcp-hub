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
) -> str:
    """
    Mint license tokens for a given IP and license terms.

    Args:
        licensor_ip_id: The ID of the licensor's intellectual property
        license_terms_id: The ID of the license terms
        receiver: Optional; the recipient's address for the tokens
        amount: Optional; number of license tokens to mint (defaults to 1)
        max_minting_fee: Optional; maximum fee for minting
        max_revenue_share: Optional; maximum revenue share percentage
        license_template: Optional; address of the license template

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
        )

        return (
            f"Successfully minted license tokens:\n"
            f"Transaction Hash: {response['txHash']}\n"
            f"License Token IDs: {response['licenseTokenIds']}"
        )
    except ValueError as e:
        return f"Validation error: {str(e)}"
    except Exception as e:
        return f"Error minting license tokens: {str(e)}"


@mcp.tool()
def send_ip(to_address: str, amount: float) -> str:
    """
    Send IP tokens to another address.

    :param to_address: The recipient's wallet address
    :param amount: Amount of IP tokens to send (1 IP = 1 Ether)
    :return: Transaction result message
    """
    try:
        response = story_service.send_ip(to_address, amount)
        return f"Successfully sent {amount} IP to {to_address}. Transaction hash: {response['txHash']}"
    except Exception as e:
        return f"Error sending IP: {str(e)}"


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
) -> str:
    """
    Mint an NFT, register it as an IP Asset, and attach PIL terms.
    Automatically detects if the SPG contract requires a minting fee and handles it appropriately.

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

    Returns:
        str: Result message with transaction details
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

        # No need to use SPG_NFT_CONTRACT from env, as StoryService now has defaults
        response = story_service.mint_and_register_ip_with_terms(
            commercial_rev_share=commercial_rev_share,
            derivatives_allowed=derivatives_allowed,
            registration_metadata=registration_metadata,
            commercial_use=commercial_use,
            minting_fee=minting_fee,
            recipient=recipient,
            spg_nft_contract=spg_nft_contract,
            spg_nft_contract_max_minting_fee=spg_nft_contract_max_minting_fee,
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
            actual_fee = response['actualMintingFee']
            max_fee = response.get('maxMintingFee')
            
            if actual_fee == 0:
                fee_info = f"Minting Fee: FREE (0 wei)\n"
            else:
                fee_in_ether = story_service.web3.from_wei(actual_fee, 'ether')
                fee_info = f"Minting Fee: {actual_fee} wei ({fee_in_ether} IP)\n"
                
                if max_fee is not None:
                    max_in_ether = story_service.web3.from_wei(max_fee, 'ether')
                    fee_info += f"Your Maximum: {max_fee} wei ({max_in_ether} IP)\n"

        # Check if this was a multi-step process
        if response.get("_multi_step"):
            return (
                f"Successfully minted and registered IP asset with terms (multi-step process for paid contract):\n"
                f"Step 1 - Mint NFT: {response['_mint_txHash']}\n"
                f"Step 2 - Register IP: {response['_register_txHash']}\n"
                f"Step 3 - Attach Terms: {response['_attach_txHash']}\n\n"
                f"Final Results:\n"
                f"IP ID: {response['ipId']}\n"
                f"Token ID: {response['tokenId']}\n"
                f"License Terms IDs: {response['licenseTermsIds']}\n"
                f"{fee_info}"
                f"View the IPA here: {explorer_url}/ipa/{response['ipId']}"
            )
        else:
            return (
                f"Successfully minted and registered IP asset with terms:\n"
                f"Transaction Hash: {response['txHash']}\n"
                f"IP ID: {response['ipId']}\n"
                f"Token ID: {response['tokenId']}\n"
                f"License Terms IDs: {response['licenseTermsIds']}\n"
                f"{fee_info}"
                f"View the IPA here: {explorer_url}/ipa/{response['ipId']}"
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
        mint_fee_recipient: (OPTIONAL) Address to receive minting fees (defaults to zero address)
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
        
        fee_amount = fee_info['mintFee']
        fee_token = fee_info['mintFeeToken']
        is_native = fee_info['isNativeToken']
        
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


@mcp.tool()
def mint_nft(
    nft_contract: str,
    to_address: str,
    metadata_uri: str,
    metadata_hash: str,
    allow_duplicates: bool = False,
) -> str:
    """
    Mint an NFT from an existing SPG collection using the Story Protocol SDK.
    
    Uses the IPAsset.mint() method from the Story Protocol Python SDK to mint NFTs from SPG contracts.

    Args:
        nft_contract: The address of the SPG NFT contract to mint from
        to_address: The recipient address for the minted NFT
        metadata_uri: The metadata URI for the NFT
        metadata_hash: The metadata hash as a hex string (will be converted to bytes)
        allow_duplicates: Whether to allow minting NFTs with duplicate metadata (default: False)

    Returns:
        str: Result message with transaction details
    """
    try:
        # Convert hex string to bytes for metadata_hash
        if metadata_hash.startswith('0x'):
            metadata_hash_bytes = bytes.fromhex(metadata_hash[2:])
        else:
            metadata_hash_bytes = bytes.fromhex(metadata_hash)
        
        result = story_service.mint_nft(
            nft_contract=nft_contract,
            to_address=to_address,
            metadata_uri=metadata_uri,
            metadata_hash=metadata_hash_bytes,
            allow_duplicates=allow_duplicates
        )
        
        return (
            f"Successfully minted NFT:\n"
            f"Transaction Hash: {result['txHash']}\n"
            f"NFT Contract: {result['nftContract']}\n"
            f"Token ID: {result['tokenId']}\n"
            f"Recipient: {result['recipient']}\n"
            f"Metadata URI: {result['metadataUri']}\n"
            f"Allow Duplicates: {allow_duplicates}\n"
            f"Gas Used: {result['gasUsed']}\n\n"
            f"You can now use this NFT with the register function to create an IP without license terms."
        )
    except Exception as e:
        return f"Error minting NFT: {str(e)}"


@mcp.tool()
def mint_and_register_ip_asset(
    spg_nft_contract: str,
    recipient: Optional[str] = None,
    ip_metadata: Optional[dict] = None,
    max_minting_fee: Optional[int] = None,
) -> str:
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
                        If not specified, will accept whatever the contract requires.
                        If specified, will reject if contract requires more than this amount.

    Returns:
        str: Result message with transaction details
    """
    try:
        result = story_service.mint_and_register_ip_asset(
            spg_nft_contract=spg_nft_contract,
            recipient=recipient,
            ip_metadata=ip_metadata,
            max_minting_fee=max_minting_fee
        )
        
        # Determine which explorer URL to use based on network
        explorer_url = (
            "https://explorer.story.foundation"
            if story_service.network == "mainnet"
            else "https://aeneid.explorer.story.foundation"
        )
        
        # Format fee information for display
        fee_info = ""
        if result.get('actualMintingFee') is not None:
            actual_fee = result['actualMintingFee']
            max_fee = result.get('maxMintingFee')
            
            if actual_fee == 0:
                fee_info = f"Minting Fee: FREE (0 wei)\n"
            else:
                fee_in_ether = story_service.web3.from_wei(actual_fee, 'ether')
                fee_info = f"Minting Fee: {actual_fee} wei ({fee_in_ether} IP)\n"
                
                if max_fee is not None:
                    max_in_ether = story_service.web3.from_wei(max_fee, 'ether')
                    fee_info += f"Your Maximum: {max_fee} wei ({max_in_ether} IP)\n"
        
        return (
            f"Successfully minted NFT and registered as IP asset:\n"
            f"Transaction Hash: {result['txHash']}\n"
            f"IP ID: {result['ipId']}\n"
            f"NFT Contract: {result['nftContract']}\n"
            f"Token ID: {result['tokenId']}\n"
            f"Recipient: {recipient if recipient else 'sender'}\n"
            f"{fee_info}"
            f"View the IPA here: {explorer_url}/ipa/{result['ipId']}\n\n"
            f"This IP has no license terms attached - perfect for derivative registration!"
        )
    except Exception as e:
        return f"Error minting and registering IP asset: {str(e)}"


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
        
        if result.get('txHash'):
            return f"Successfully registered NFT as IP. Transaction hash: {result['txHash']}, IP ID: {result['ipId']}"
        else:
            return f"NFT already registered as IP. IP ID: {result['ipId']}"
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
        
        return f"Successfully attached license terms to IP. Transaction hash: {result['txHash']}"
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
    license_template: Optional[str] = None
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

    Returns:
        str: Result message with transaction hash
    """
    try:
        # Validate inputs
        if len(parent_ip_ids) != len(license_terms_ids):
            return "Error: The number of parent IP IDs must match the number of license terms IDs."
            
        result = story_service.register_derivative(
            child_ip_id=child_ip_id,
            parent_ip_ids=parent_ip_ids,
            license_terms_ids=license_terms_ids,
            max_minting_fee=max_minting_fee,
            max_rts=max_rts,
            max_revenue_share=max_revenue_share,
            license_template=license_template
        )
        
        return f"Successfully registered derivative. Transaction hash: {result['txHash']}"
    except Exception as e:
        return f"Error registering derivative: {str(e)}"


@mcp.tool()
def pay_royalty_on_behalf(
    receiver_ip_id: str,
    payer_ip_id: str,
    token: str,
    amount: int
) -> str:
    """
    Allows the function caller to pay royalties to the receiver IP asset on behalf of the payer IP asset.

    Args:
        receiver_ip_id: The IP ID that receives the royalties
        payer_ip_id: The ID of the IP asset that pays the royalties
        token: The token address to use to pay the royalties
        amount: The amount to pay

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

        return f"Successfully paid royalty on behalf. Transaction hash: {response['txHash']}"
    except Exception as e:
        return f"Error paying royalty on behalf: {str(e)}"


@mcp.tool()
def estimate_gas_for_approval(
    token: str,
    operation_type: str = "royalty",
    amount: int = 1000000000000000000000000,
    spender: Optional[str] = None
) -> str:
    """
    🔍 ADVANCED: Estimate gas costs for token approval before executing the transaction.
    
    ⚠️  WHEN TO USE: Only use this tool when:
    - You need to check gas costs before approving (for budgeting)
    - Network is congested and you want to optimize gas price
    - You're doing batch operations and need to plan gas usage
    - approve_token_for_royalty failed due to gas issues
    
    💡 NORMAL USAGE: For most cases, just use approve_token_for_royalty directly.
    It handles gas estimation automatically with smart defaults.

    Args:
        token: The token contract address to approve
        operation_type: Type of operation ("royalty", "licensing", "minting", "custom")
        amount: The amount to approve (default: large number for unlimited)
        spender: Optional manual spender address (for custom operations)

    Returns:
        str: Detailed gas estimation including price, limit, and total cost
    """
    try:
        # Auto-determine spender if not provided
        if spender is None:
            from services.story_service import StoryService
            temp_service = story_service
            
            if operation_type == "royalty":
                spender = temp_service.contracts.get("RoyaltyModule")
            elif operation_type == "licensing":
                spender = temp_service.contracts.get("LicensingModule")
            elif operation_type == "minting":
                spender = temp_service.contracts.get("SPG_NFT")
            else:
                return f"Error: For operation_type '{operation_type}', you must provide spender address manually"
            
            if not spender:
                return f"Error: Could not determine spender address for operation_type '{operation_type}'"
        
        estimate = story_service.estimate_gas_for_approval(
            token=token,
            spender=spender,
            amount=amount
        )
        
        return (
            f"⛽ Gas Estimation for Token Approval:\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Operation Type: {operation_type}\n"
            f"Token: {estimate['token']}\n"
            f"Spender: {estimate['spender']}\n"
            f"Amount: {estimate['amount']}\n\n"
            f"💰 Gas Costs:\n"
            f"Gas Price: {estimate['gasPriceGwei']:.2f} gwei\n"
            f"Estimated Gas Limit: {estimate['estimatedGasLimit']:,}\n"
            f"Total Cost: {estimate['totalCostGwei']:.4f} gwei ({estimate['totalCostIP']:.6f} IP)\n\n"
            f"💡 Use these values in approve_token_for_royalty:\n"
            f"- gas_limit: {estimate['estimatedGasLimit']} (or higher for safety)\n"
            f"- gas_price: {estimate['gasPrice']} (in wei) or {estimate['gasPriceGwei']:.0f} gwei"
        )
    except Exception as e:
        return f"Error estimating gas: {str(e)}"


@mcp.tool()
def approve_token_for_royalty(
    token: str,
    amount: int,
    operation_type: str = "royalty",
    spender: Optional[str] = None,
    gas_limit: Optional[int] = None,
    gas_price: Optional[int] = None
) -> str:
    """
    ✅ Approve a token contract to allow Story Protocol contracts to spend tokens.
    This must be called before operations that transfer tokens to avoid InsufficientAllowance errors.

    Args:
        token: The token contract address to approve
        amount: The amount to approve (use a large number like 1000000000000000000000000 for unlimited approval)
        operation_type: Type of operation - determines which contract to approve:
            - "royalty": For pay_royalty_on_behalf (uses RoyaltyModule)
            - "licensing": For mint_license_tokens (uses LicensingModule) 
            - "minting": For SPG NFT minting fees (uses SPG_NFT contract)
            - "custom": Must provide spender address manually
        spender: Optional manual spender address (only needed for custom operations or advanced use cases)
        gas_limit: Optional custom gas limit (for advanced users only)
        gas_price: Optional custom gas price in wei (for advanced users only)

    Returns:
        str: Success message with transaction and gas details
        
    Examples:
        - ✅ Recommended: approve_token_for_royalty(token, amount, "royalty")
        - ⚙️  Advanced: approve_token_for_royalty(token, amount, "royalty", gas_limit=80000, gas_price=50000000000)
        - 🔧 Custom: approve_token_for_royalty(token, amount, "custom", "0xCustomContract...")
        
    💡 This function uses smart gas defaults. Only use estimate_gas_for_approval if you need to check costs first.
    """
    try:
        response = story_service.approve_token_for_royalty(
            token=token,
            amount=amount,
            spender=spender,
            operation_type=operation_type,
            gas_limit=gas_limit,
            gas_price=gas_price
        )

        # Format gas information
        gas_info = (
            f"\n⛽ Gas Information:\n"
            f"Gas Used: {response['gasUsed']:,} / {response['gasLimit']:,}\n"
            f"Gas Price: {response['gasPriceGwei']:.2f} gwei\n"
            f"Total Cost: {response['actualCostGwei']:.4f} gwei ({response['actualCostIP']:.6f} IP)"
        )

        return (
            f"✅ Successfully approved token for {operation_type} operations!\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Transaction Hash: {response['txHash']}\n"
            f"Status: {'Success' if response['status'] == 1 else 'Failed'}\n"
            f"Approved Amount: {response['approvedAmount']}\n"
            f"Token: {response['token']}\n"
            f"Spender Contract: {response['spender']}\n"
            f"Operation Type: {response['operationType']}"
            + gas_info
        )
    except Exception as e:
        return f"Error approving token: {str(e)}"


@mcp.tool()
def check_token_allowance(
    token: str,
    owner: Optional[str] = None,
    spender: Optional[str] = None
) -> str:
    """
    Check the current allowance for a token to see if royalty payments are approved.

    Args:
        token: The token contract address
        owner: The owner address (if None, uses current account)
        spender: The spender address (if None, uses royalty contract)

    Returns:
        str: Current allowance information
    """
    try:
        response = story_service.check_token_allowance(
            token=token,
            owner=owner,
            spender=spender
        )

        return (
            f"Token Allowance Information:\n"
            f"Current Allowance: {response['allowance']}\n"
            f"Has Allowance: {'Yes' if response['hasAllowance'] else 'No'}\n"
            f"Owner: {response['owner']}\n"
            f"Spender: {response['spender']}\n"
            f"Token: {response['token']}"
        )
    except Exception as e:
        return f"Error checking token allowance: {str(e)}"


@mcp.tool()
def get_token_info(token: str) -> str:
    """
    Get detailed information about an ERC20 token including name, symbol, decimals, and total supply.

    Args:
        token: The token contract address

    Returns:
        str: Comprehensive token information
    """
    try:
        response = story_service.get_token_info(token)

        return (
            f"🪙 Token Information:\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Address: {response['address']}\n"
            f"Name: {response['name']}\n"
            f"Symbol: {response['symbol']}\n"
            f"Decimals: {response['decimals']}\n"
            f"Total Supply: {response['totalSupply']:,} ({response['totalSupplyFormatted']:,.6f} {response['symbol']})"
        )
    except Exception as e:
        return f"Error getting token info: {str(e)}"


@mcp.tool()
def get_token_balance(
    token: str,
    owner: Optional[str] = None
) -> str:
    """
    Get the token balance for a specific address.

    Args:
        token: The token contract address
        owner: The address to check balance for (if None, uses current account)

    Returns:
        str: Token balance information
    """
    try:
        response = story_service.get_token_balance(
            token_address=token,
            owner_address=owner
        )

        return (
            f"💰 Token Balance:\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Address: {response['address']}\n"
            f"Token: {response['token']}\n"
            f"Balance: {response['balanceFormatted']:,.6f} tokens\n"
            f"Raw Balance: {response['balanceRaw']:,}\n"
            f"Decimals: {response['decimals']}"
        )
    except Exception as e:
        return f"Error getting token balance: {str(e)}"


@mcp.tool()
def get_erc20_abi_info() -> str:
    """
    Get information about the ERC20 ABI being used by the system.
    This shows the available functions and demonstrates the non-hardcoded approach.

    Returns:
        str: Information about the ERC20 ABI and available functions
    """
    try:
        # Import the ERC20 ABI modules
        from services.erc20_abi import ERC20_ABI, ERC20_EXTENDED_ABI, ERC20_FUNCTIONS, get_erc20_abi
        
        # Get function counts
        standard_functions = [item for item in ERC20_ABI if item['type'] == 'function']
        standard_events = [item for item in ERC20_ABI if item['type'] == 'event']
        extended_functions = [item for item in ERC20_EXTENDED_ABI if item['type'] == 'function']
        extended_events = [item for item in ERC20_EXTENDED_ABI if item['type'] == 'event']
        
        # Get function names
        standard_function_names = [func['name'] for func in standard_functions]
        extended_function_names = [func['name'] for func in extended_functions]
        
        return (
            f"📋 ERC20 ABI Information:\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔧 Implementation: Imported from dedicated erc20_abi.py module\n"
            f"✅ Benefits: No hardcoding, easy maintenance, standardized\n\n"
            f"📊 Standard ERC20 ABI:\n"
            f"Functions: {len(standard_functions)}\n"
            f"Events: {len(standard_events)}\n"
            f"Available Functions: {', '.join(standard_function_names)}\n\n"
            f"📊 Extended ERC20 ABI (with EIP-2612 permit):\n"
            f"Functions: {len(extended_functions)}\n"
            f"Events: {len(extended_events)}\n"
            f"Additional Functions: {', '.join(set(extended_function_names) - set(standard_function_names))}\n\n"
            f"🗺️ Function Mapping Available:\n"
            f"Mapped Functions: {len(ERC20_FUNCTIONS)}\n"
            f"Example: ERC20_FUNCTIONS['balance_of'] = '{ERC20_FUNCTIONS['balance_of']}'\n\n"
            f"💡 Usage: All token operations use the imported ABI automatically\n"
            f"🔄 Maintenance: Update once in erc20_abi.py, changes apply everywhere"
        )
    except Exception as e:
        return f"Error getting ERC20 ABI info: {str(e)}"


@mcp.tool()
def claim_revenue(
    snapshot_ids: list,
    child_ip_id: str,
    token: str
) -> str:
    """
    Allows token holders to claim revenue by a list of snapshot IDs based on the token balance at certain snapshot.

    Args:
        snapshot_ids: The list of snapshot IDs
        child_ip_id: The child IP ID
        token: The token address to claim

    Returns:
        str: Result message with transaction hash and claimed amount
    """
    try:
        result = story_service.claim_revenue(
            snapshot_ids=snapshot_ids,
            child_ip_id=child_ip_id,
            token=token
        )
        
        return f"Successfully claimed revenue. Transaction hash: {result['txHash']}, Claimed amount: {result.get('claimableToken', 'Unknown')}"
    except Exception as e:
        return f"Error claiming revenue: {str(e)}"


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
    
    💰 BOND PAYMENT: The bond amount is automatically sent as native IP tokens with the transaction.
    No separate token approval needed - the SDK handles everything!

    Args:
        target_ip_id: The IP ID to dispute (must be a valid hex address starting with 0x)
        target_tag: Tag identifying the dispute type (e.g., "IMPROPER_REGISTRATION", "PLAGIARISM", "FRAUDULENT_USE")
        cid: The Content Identifier (CID) for the dispute evidence, obtained from IPFS (e.g., "QmbWqxBEKC3P8tqsKc98xmWNzrzDtRLMiMPL8wBuTGsMnR")
        bond_amount: The amount of the bond to post for the dispute, as an integer in wei (e.g., 100000000000000000 for 0.1 IP)
        liveness: The liveness of the dispute in days, must be between 30 and 365 days (defaults to 30 days)

    Returns:
        str: Result message with transaction hash and dispute ID
        
    💡 How Bond Payment Works:
    - Bond is paid in native IP tokens (not ERC20)
    - Amount is sent as transaction value (like sending ETH)
    - SDK automatically handles the payment
    - No need for separate approve/transfer steps
    
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
            liveness=liveness
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




if __name__ == "__main__":
    mcp.run()
