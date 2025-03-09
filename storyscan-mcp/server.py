from mcp.server.fastmcp import FastMCP
from services.storyscan_service import StoryscanService
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize FastMCP
mcp = FastMCP()

# Get API endpoint from environment variables
api_endpoint = os.environ.get("STORYSCAN_API_ENDPOINT")
if not api_endpoint:
    print("STORYSCAN_API_ENDPOINT environment variable is required")
    api_endpoint = "https://www.storyscan.xyz/api"  # Default fallback

# Initialize StoryScan service with SSL verification disabled
story_service = StoryscanService(api_endpoint, disable_ssl_verification=True)
print(f"Initialized StoryScan service with API endpoint: {api_endpoint}")

@mcp.tool()
def check_balance(address: str):
    """Check the balance of an address. Remember its an EVM chain but the token is $IP"""
    try:
        balance = story_service.get_address_balance(address)
        return f"Address: {balance['address']}\nBalance: {balance['balance']} IP"
    except Exception as e:
        return f"Error checking balance: {str(e)}"

@mcp.tool()
def get_transactions(address: str, limit: int = 10):
    """Get recent transactions for an address. Remember its an EVM chain but the token is $IP"""
    try:
        transactions = story_service.get_transaction_history(address, limit)
        
        if not transactions:
            return f"No transactions found for {address}"
        
        formatted_transactions = []
        for tx in transactions:
            date = tx["timestamp"]  # Could format this better if needed
            formatted_tx = (
                f"Block {tx['block_number']} ({date}):\n"
                f"Hash: {tx['hash']}\n"
                f"From: {tx['from_']['hash']}\n"
                f"To: {tx['to']['hash']}\n"
                f"Value: {tx['value']} IP\n"
                f"Fee: {tx['fee']['value']} IP\n"
                f"---"
            )
            formatted_transactions.append(formatted_tx)
        
        return f"Recent transactions for {address}:\n\n" + "\n".join(formatted_transactions)
    except Exception as e:
        return f"Error getting transactions: {str(e)}"

@mcp.tool()
def get_stats():
    """Get current blockchain statistics. Remember its an EVM chain but the token is $IP"""
    try:
        stats = story_service.get_blockchain_stats()
        return (
            f"Blockchain Statistics:\n"
            f"Total Blocks: {stats['total_blocks']}\n"
            f"Average Block Time: {stats['average_block_time']}\n"
            f"Total Transactions: {stats['total_transactions']}\n"
            f"Total Addresses: {stats['total_addresses']}\n"
            f"Current Gas Price: {stats['gas_prices']['average']} IP"
        )
    except Exception as e:
        return f"Error getting blockchain stats: {str(e)}"

@mcp.tool()
def get_address_overview(address: str):
    """Get a comprehensive overview of an address including ETH balance, token info,
    and various blockchain activity indicators. Remember its an EVM chain but the token is $IP"""
    try:
        overview = story_service.get_address_overview(address)
        return (
            f"Address Overview for {overview['hash']}:\n"
            f"Balance: {overview['coin_balance']} IP\n"
            f"Is Contract: {overview['is_contract']}\n"
            f"Has Tokens: {overview['has_tokens']}\n"
            f"Has Token Transfers: {overview['has_token_transfers']}"
        )
    except Exception as e:
        return f"Error getting address overview: {str(e)}"

@mcp.tool()
def get_token_holdings(address: str):
    """Get all ERC-20 token holdings for an address, including detailed token information
    and balances. Remember its an EVM chain but the token is $IP"""
    try:
        holdings = story_service.get_token_holdings(address)
        
        if not holdings["items"]:
            return f"No token holdings found for {address}"
        
        formatted_holdings = []
        for holding in holdings["items"]:
            token = holding["token"]
            formatted_holding = (
                f"Token: {token['name']} ({token['symbol']})\n"
                f"Value: {holding['value']}\n"
                f"Address: {token['address']}\n"
                f"Type: {token['type']}\n"
                f"---"
            )
            formatted_holdings.append(formatted_holding)
        
        return f"Token holdings for {address}:\n\n" + "\n".join(formatted_holdings)
    except Exception as e:
        return f"Error getting token holdings: {str(e)}"

@mcp.tool()
def get_nft_holdings(address: str):
    """Get all NFT holdings for an address, including collection information and
    individual token metadata. Remember its an EVM chain but the token is $IP"""
    try:
        # Use the correct endpoint with type parameters
        nft_holdings = story_service.get_nft_holdings(address)
        
        if not nft_holdings["items"]:
            return f"No NFT holdings found for {address}"
        
        formatted_holdings = []
        for nft in nft_holdings["items"]:
            token = nft["token"]
            formatted_holding = (
                f"Collection: {token['name']} ({token['symbol']})\n"
                f"Token ID: {nft['id']}\n"
                f"Token Type: {nft['token_type']}\n"
            )
            
            # Add image URL if available
            if nft['image_url']:
                formatted_holding += f"Image: {nft['image_url']}\n"
                
            # Add external URL if available
            if nft['external_app_url']:
                formatted_holding += f"External URL: {nft['external_app_url']}\n"
                
            # Add metadata summary if available
            if nft['metadata'] and isinstance(nft['metadata'], dict):
                if 'name' in nft['metadata']:
                    formatted_holding += f"Name: {nft['metadata']['name']}\n"
                if 'description' in nft['metadata'] and nft['metadata']['description']:
                    desc = nft['metadata']['description']
                    # Truncate long descriptions
                    if len(desc) > 100:
                        desc = desc[:97] + "..."
                    formatted_holding += f"Description: {desc}\n"
            
            formatted_holding += "---\n"
            formatted_holdings.append(formatted_holding)
        
        return f"NFT holdings for {address}:\n\n" + "\n".join(formatted_holdings)
    except Exception as e:
        return f"Error getting NFT holdings: {str(e)}"

@mcp.tool()
def interpret_transaction(transaction_hash: str) -> str:
    """
    Get a human-readable interpretation of a blockchain transaction.
    
    Args:
        transaction_hash: The hash of the transaction to interpret
        
    Returns:
        str: A human-readable summary of the transaction
    """
    try:
        interpretation = story_service.get_transaction_interpretation(transaction_hash)
        # Just return the raw response
        return str(interpretation)
    except Exception as e:
        return f"Error interpreting transaction: {str(e)}"

if __name__ == "__main__":
    mcp.run()