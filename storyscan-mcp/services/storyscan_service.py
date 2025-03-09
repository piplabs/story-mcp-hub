import os
import requests
import urllib3
import logging
from typing import TypedDict, List, Optional, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, filename='storyscan_service.log', filemode='a',
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('storyscan_service')

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Type definitions (similar to TypeScript interfaces)
class GasPrices(TypedDict):
    average: float
    fast: float
    slow: float

class BlockchainStats(TypedDict):
    total_blocks: str
    total_addresses: str
    total_transactions: str
    average_block_time: float
    coin_price: Optional[str]
    transactions_today: str
    market_cap: str
    network_utilization_percentage: float
    gas_prices: GasPrices
    gas_used_today: str
    total_gas_used: str
    gas_price_updated_at: str
    gas_prices_update_in: int
    static_gas_price: Optional[str]

class Transaction(TypedDict):
    hash: str
    from_: Dict[str, str]  # Using from_ because 'from' is a Python keyword
    to: Dict[str, str]
    value: str
    timestamp: str
    block_number: int
    fee: Dict[str, str]
    status: str

class Tag(TypedDict):
    address_hash: str
    display_name: str
    label: str

class WatchlistName(TypedDict):
    display_name: str
    label: str

class TokenInfo(TypedDict):
    circulating_market_cap: Optional[str]
    icon_url: Optional[str]
    name: str
    decimals: str
    symbol: str
    address: str
    type: str
    holders: str
    exchange_rate: Optional[str]
    total_supply: str

class AddressOverview(TypedDict):
    hash: str
    coin_balance: str
    is_contract: bool
    token: Optional[TokenInfo]
    has_tokens: bool
    has_token_transfers: bool
    has_beacon_chain_withdrawals: bool
    private_tags: List[Tag]
    public_tags: List[Tag]
    watchlist_names: List[WatchlistName]
    exchange_rate: Optional[str]

class TokenHolding(TypedDict):
    token: TokenInfo
    value: str
    token_id: Optional[str]
    token_instance: Optional[dict]

class TokenHoldingsResponse(TypedDict):
    items: List[TokenHolding]
    next_page_params: Optional[dict]

class TokenInstance(TypedDict):
    is_unique: bool
    id: str
    holder_address_hash: str
    image_url: Optional[str]
    animation_url: Optional[str]
    external_app_url: Optional[str]
    metadata: dict
    token_type: str
    value: str

class NFTCollection(TypedDict):
    token: TokenInfo
    amount: str
    token_instances: List[TokenInstance]

class NFTCollectionsResponse(TypedDict):
    items: List[NFTCollection]
    next_page_params: Optional[dict]

class TransactionSummary(TypedDict):
    summary_template: str
    summary_template_variables: dict

class TransactionInterpretation(TypedDict):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    summaries: Optional[List[TransactionSummary]] = None

class StoryscanService:
    def __init__(self, api_endpoint: str, disable_ssl_verification=False):
        self.api_endpoint = api_endpoint.rstrip('/')
        self.disable_ssl_verification = disable_ssl_verification
        logger.info(f"Initialized StoryScan service with endpoint: {self.api_endpoint}")

    def _make_api_request(self, path: str, params: dict = None) -> dict:
        """Make a request to the Storyscan API."""
        url = f"{self.api_endpoint}/v2/{path}"
        
        # Debug log to show the exact URL being requested
        logger.info(f"Making API request to: {url}")
        
        try:
            response = requests.get(url, params=params, verify=not self.disable_ssl_verification)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to {url}: {e}")
            raise Exception(f"API request failed: {str(e)}")

    def get_address_balance(self, address: str) -> dict:
        """Get the balance of an address."""
        try:
            data = self._make_api_request(f"addresses/{address}")
            return {
                "address": data["hash"],
                "balance": data["coin_balance"]
            }
        except Exception as e:
            logger.error(f"Error in get_address_balance: {str(e)}")
            raise Exception(f"Failed to get balance: {str(e)}")

    def get_transaction_history(self, address: str, limit: int = 10) -> List[Transaction]:
        """Get transaction history for an address."""
        try:
            data = self._make_api_request(f"addresses/{address}/transactions")
            transactions = data["items"][:limit]
            return [{
                "hash": tx["hash"],
                "from_": tx["from"],
                "to": tx["to"],
                "value": tx["value"],
                "timestamp": tx["timestamp"],
                "block_number": tx["block_number"],
                "fee": tx["fee"],
                "status": tx["status"]
            } for tx in transactions]
        except Exception as e:
            logger.error(f"Error in get_transaction_history: {str(e)}")
            raise Exception(f"Failed to get transaction history: {str(e)}")

    def get_blockchain_stats(self) -> BlockchainStats:
        """Get blockchain statistics."""
        try:
            data = self._make_api_request("stats")
            return BlockchainStats(
                total_blocks=data["total_blocks"],
                total_addresses=data["total_addresses"],
                total_transactions=data["total_transactions"],
                average_block_time=data["average_block_time"],
                coin_price=data["coin_price"],
                transactions_today=data["transactions_today"],
                market_cap=data["market_cap"],
                network_utilization_percentage=data["network_utilization_percentage"],
                gas_prices=data["gas_prices"],
                gas_used_today=data["gas_used_today"],
                total_gas_used=data["total_gas_used"],
                gas_price_updated_at=data["gas_price_updated_at"],
                gas_prices_update_in=data["gas_prices_update_in"],
                static_gas_price=data["static_gas_price"]
            )
        except Exception as e:
            logger.error(f"Error in get_blockchain_stats: {str(e)}")
            raise Exception(f"Failed to get blockchain stats: {str(e)}")

    def get_address_overview(self, address: str) -> AddressOverview:
        """Get a comprehensive overview of an address including balances and token info."""
        try:
            data = self._make_api_request(f"addresses/{address}")
            return AddressOverview(
                hash=data["hash"],
                coin_balance=data["coin_balance"],
                is_contract=data["is_contract"],
                token=data.get("token"),
                has_tokens=data["has_tokens"],
                has_token_transfers=data["has_token_transfers"],
                has_beacon_chain_withdrawals=data["has_beacon_chain_withdrawals"],
                private_tags=data["private_tags"],
                public_tags=data["public_tags"],
                watchlist_names=data["watchlist_names"],
                exchange_rate=data.get("exchange_rate")
            )
        except Exception as e:
            logger.error(f"Error in get_address_overview: {str(e)}")
            raise Exception(f"Failed to get address overview: {str(e)}")

    def get_token_holdings(self, address: str) -> TokenHoldingsResponse:
        """Get token holdings for an address."""
        try:
            data = self._make_api_request(f"addresses/{address}/tokens")
            return TokenHoldingsResponse(
                items=data["items"],
                next_page_params=data.get("next_page_params")
            )
        except Exception as e:
            logger.error(f"Error in get_token_holdings: {str(e)}")
            raise Exception(f"Failed to get token holdings: {str(e)}")

    def get_nft_holdings(self, address: str) -> dict:
        """Get NFT holdings for an address."""
        try:
            # Using the correct endpoint with type parameters
            data = self._make_api_request(f"addresses/{address}/nft", 
                                         params={"type": "ERC-721,ERC-404,ERC-1155"})
            
            # Log the successful response for debugging
            logger.info(f"Successfully retrieved NFT holdings for {address}")
            
            # Simply return the raw API response as the structure matches what we need
            return data
        except Exception as e:
            logger.error(f"Error in get_nft_holdings: {str(e)}")
            raise Exception(f"Failed to get NFT holdings: {str(e)}")

    def get_transaction_interpretation(self, tx_hash: str) -> dict:
        """Get a human-readable interpretation of a transaction."""
        try:
            data = self._make_api_request(f"transactions/{tx_hash}/summary")
            
            # Log the exact response for debugging
            logger.info(f"API Response for transaction {tx_hash}: {data}")
            
            # Simply return the raw API response
            return data
        except Exception as e:
            logger.error(f"Error in get_transaction_interpretation: {str(e)}")
            raise Exception(f"Failed to get transaction interpretation: {str(e)}")
