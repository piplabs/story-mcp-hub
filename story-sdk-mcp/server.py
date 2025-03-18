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
if not rpc_url:
    raise ValueError("RPC_PROVIDER_URL environment variable is required")

# Initialize Story service - private key is now optional
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
        Create IP metadata JSON using an IPFS image URI.

        Args:
            image_uri: IPFS URI of the image
            name: Name for the IP asset
            description: Description of the IP asset
            attributes: Optional list of attributes as key-value pairs

        Returns:
            str: IPFS URI of the uploaded metadata JSON
        """
        try:
            if not attributes:
                attributes = []

            result = story_service.create_ip_metadata(
                image_uri=image_uri, name=name, description=description, attributes=attributes
            )
            return f"Successfully created IP metadata: {json.dumps(result, indent=2)}"
        except Exception as e:
            return f"Error creating IP metadata: {str(e)}"


@mcp.tool()
def get_license_terms(license_terms_id: int) -> str:
    """
    Get details of a license terms template by ID.

    :param license_terms_id: The ID of the license terms
    :return: License terms details
    """
    try:
        license_terms = story_service.get_license_terms(license_terms_id)
        return f"License Terms Details: {json.dumps(license_terms, indent=2)}"
    except Exception as e:
        return f"Error getting license terms: {str(e)}"


@mcp.tool()
def mint_license_tokens(
    licensor_ip_id: str,
    license_terms_id: int,
    receiver: str = None,
    max_minting_fee: int = None,
    max_revenue_share: int = None,
) -> str:
    """
    Mint license tokens for a specific IP asset using a license terms template.

    :param licensor_ip_id: The IP ID that is being licensed
    :param license_terms_id: The license terms template ID to use
    :param receiver: Optional recipient address (defaults to caller)
    :param max_minting_fee: Optional maximum minting fee in wei
    :param max_revenue_share: Optional maximum revenue share percentage
    :return: Transaction result message
    """
    try:
        # Check if we have a private key for signing
        if not story_service.has_private_key():
            return "This operation requires wallet signing. Please provide transaction details to the frontend for user signing."
            
        response = story_service.mint_license_tokens(
            licensor_ip_id=licensor_ip_id,
            license_terms_id=license_terms_id,
            receiver=receiver,
            max_minting_fee=max_minting_fee,
            max_revenue_share=max_revenue_share,
        )
        
        return (
            f"Successfully minted license token. Transaction hash: {response['txHash']}\n"
            f"License Token ID: {response.get('licenseTokenId', 'Not available yet')}"
        )
    except Exception as e:
        return f"Error minting license tokens: {str(e)}"


@mcp.tool()
def send_ip(from_address: str = None, to_address: str = None, amount: float = None) -> str:
    """
    Send IP tokens to another address.

    :param from_address: The sender's wallet address (only needed for frontend-signed transactions)
    :param to_address: The recipient's wallet address
    :param amount: Amount of IP tokens to send (1 IP = 1 Ether)
    :return: Transaction details or instructions
    """
    # Input validation
    if not to_address:
        return "Please provide a recipient address (to_address)."
    if not amount or amount <= 0:
        return "Please provide a valid amount greater than 0."
    
    try:
        # Check if we're using server-side private key or frontend wallet
        if story_service.has_private_key():
            # Server-side signing
            response = story_service.send_ip(to_address, amount)
            return f"Successfully sent {amount} IP to {to_address}. Transaction hash: {response['txHash']}"
        else:
            # Frontend wallet signing
            tx_data = story_service.prepare_send_ip_transaction(to_address, amount)
            return json.dumps({
                "action": "sign_transaction",
                "transaction": tx_data,
                "message": f"Please sign the transaction to send {amount} IP to {to_address}."
            })
    except Exception as e:
        return f"Error preparing IP transaction: {str(e)}"


@mcp.tool()
def mint_and_register_ip_with_terms(
    commercial_rev_share: int,
    derivatives_allowed: bool,
    registration_metadata: dict = None,
    recipient: str = None,
    spg_nft_contract: str = None,  # Make this optional
) -> str:
    """
    Mint a new NFT representing an IP asset and register it with license terms.

    :param commercial_rev_share: Commercial revenue share percentage (e.g., 10 for 10%)
    :param derivatives_allowed: Whether derivatives are allowed under the license
    :param registration_metadata: Optional metadata for registration (dict with content fields)
    :param recipient: Optional recipient address (defaults to caller)
    :param spg_nft_contract: Optional SPG NFT contract address
    :return: Transaction result message
    """
    try:
        # Check if we have a private key for signing
        if not story_service.has_private_key():
            return "This operation requires wallet signing. Please provide transaction details to the frontend for user signing."
            
        response = story_service.mint_and_register_ip_with_terms(
            commercial_rev_share=commercial_rev_share,
            derivatives_allowed=derivatives_allowed,
            registration_metadata=registration_metadata,
            recipient=recipient,
            spg_nft_contract=spg_nft_contract,
        )
        
        return (
            f"Successfully minted and registered IP asset.\n"
            f"Transaction hash: {response['txHash']}\n"
            f"IP ID: {response.get('ipId', 'Not available yet')}\n"
            f"License Terms ID: {response.get('licenseTermsId', 'Not available yet')}"
        )
    except Exception as e:
        return f"Error minting and registering IP: {str(e)}"


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
    Create a new SPG NFT collection.

    :param name: Collection name
    :param symbol: Collection symbol
    :param is_public_minting: Whether public minting is allowed
    :param mint_open: Whether minting is currently open
    :param mint_fee_recipient: Address to receive mint fees (defaults to creator)
    :param contract_uri: Contract metadata URI
    :param base_uri: Base URI for token metadata
    :param max_supply: Maximum token supply (0 for unlimited)
    :param mint_fee: Minting fee in wei
    :param mint_fee_token: Token address for mint fee (empty for native token)
    :param owner: Owner address (defaults to creator)
    :return: Transaction result message
    """
    try:
        # Check if we have a private key for signing
        if not story_service.has_private_key():
            return "This operation requires wallet signing. Please provide transaction details to the frontend for user signing."
            
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
            f"Successfully created SPG NFT collection.\n"
            f"Transaction hash: {response['txHash']}\n"
            f"Collection address: {response.get('collectionAddress', 'Not available yet')}"
        )
    except Exception as e:
        return f"Error creating SPG NFT collection: {str(e)}"


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
