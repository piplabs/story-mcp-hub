from mcp.server.fastmcp import FastMCP
from services.story_service import StoryService
import os
from dotenv import load_dotenv
from typing import Union
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
        image_uri: str, name: str, description: str, attributes: list = None
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
    receiver: str = None,
    amount: int = 1,
    max_minting_fee: int = None,
    max_revenue_share: int = None,
    license_template: str = None,
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
    registration_metadata: dict = None,
    recipient: str = None,
    spg_nft_contract: str = None,  # Make this optional
) -> str:
    """
    Mint an NFT, register it as an IP Asset, and attach PIL terms.

    Args:
        commercial_rev_share: Percentage of revenue share (0-100)
        derivatives_allowed: Whether derivatives are allowed
        registration_metadata: Dict containing metadata URIs and hashes from create_ip_metadata
        recipient: Optional recipient address (defaults to sender)
        spg_nft_contract: Optional SPG NFT contract address (defaults to network-specific default)

    Returns:
        str: Result message with transaction details
    """
    try:
        # Validate inputs
        if not (0 <= commercial_rev_share <= 100):
            raise ValueError("commercial_rev_share must be between 0 and 100")

        # No need to use SPG_NFT_CONTRACT from env, as StoryService now has defaults
        response = story_service.mint_and_register_ip_with_terms(
            commercial_rev_share=commercial_rev_share,
            derivatives_allowed=derivatives_allowed,
            registration_metadata=registration_metadata,
            recipient=recipient,
            spg_nft_contract=spg_nft_contract,
        )

        # Determine which explorer URL to use based on network
        explorer_url = (
            "https://explorer.story.foundation"
            if story_service.network == "mainnet"
            else "https://aeneid.explorer.story.foundation"
        )

        return (
            f"Successfully minted and registered IP asset with terms:\n"
            f"Transaction Hash: {response['txHash']}\n"
            f"IP ID: {response['ipId']}\n"
            f"Token ID: {response['tokenId']}\n"
            f"License Terms IDs: {response['licenseTermsIds']}\n"
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
    mint_fee_recipient: str = None,
    contract_uri: str = "",
    base_uri: str = "",
    max_supply: int = None,
    mint_fee: int = None,
    mint_fee_token: str = None,
    owner: str = None,
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
def register(nft_contract: str, token_id: int, ip_metadata: dict = None) -> str:
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
def attach_license_terms(ip_id: str, license_terms_id: int, license_template: str = None) -> str:
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
    license_template: str = None
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
        str: Result message with transaction hash
    """
    try:
        result = story_service.pay_royalty_on_behalf(
            receiver_ip_id=receiver_ip_id,
            payer_ip_id=payer_ip_id,
            token=token,
            amount=amount
        )
        
        return f"Successfully paid royalty. Transaction hash: {result['txHash']}"
    except Exception as e:
        return f"Error paying royalty: {str(e)}"


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
    dispute_evidence_hash: str,
    target_tag: str,
    data: str = "0x"
) -> str:
    """
    Raises a dispute against an IP asset.

    Args:
        target_ip_id: The IP ID to dispute
        dispute_evidence_hash: Hash or link to the evidence for the dispute
        target_tag: Tag identifying the dispute type (e.g., "copyright", "trademark")
        data: Optional additional data for the dispute

    Returns:
        str: Result message with transaction hash and dispute ID
    """
    try:
        result = story_service.raise_dispute(
            target_ip_id=target_ip_id,
            dispute_evidence_hash=dispute_evidence_hash,
            target_tag=target_tag,
            data=data
        )
        
        dispute_id = result.get('disputeId', 'Unknown')
        return f"Successfully raised dispute. Transaction hash: {result['txHash']}, Dispute ID: {dispute_id}"
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
