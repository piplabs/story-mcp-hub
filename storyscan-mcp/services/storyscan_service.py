import os
import requests
import urllib3
import logging
import sys
from pathlib import Path
from typing import TypedDict, List, Optional, Dict, Any

# Add the parent directory to the Python path so we can import utils
sys.path.append(str(Path(__file__).parent.parent.parent))

# Now import the gas utilities with the correct path
from utils.gas_utils import format_gas_prices, wei_to_gwei, gwei_to_eth, format_token_balance

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
    gas_prices_update_in_seconds: float
    static_gas_price: Optional[str]

class Transaction(TypedDict):
    hash: str
    from_: Dict[str, Any]  # Using from_ because 'from' is a Python keyword
    to: Dict[str, Any]
    value: str
    timestamp: str
    block_number: int
    fee: Dict[str, str]
    status: str
    gas_used: Optional[str]
    gas_price: Optional[str]
    gas_limit: Optional[str]
    method: Optional[str]
    decoded_input: Optional[Dict[str, Any]]
    token_transfers: Optional[Any]
    nonce: Optional[int]
    transaction_types: Optional[List[str]]
    exchange_rate: Optional[str]
    result: Optional[str]
    type: Optional[int]
    confirmations: Optional[int]
    position: Optional[int]
    priority_fee: Optional[str]
    tx_burnt_fee: Optional[str]
    raw_input: Optional[str]
    revert_reason: Optional[Dict[str, str]]
    confirmation_duration: Optional[List[float]]
    transaction_burnt_fee: Optional[str]
    max_fee_per_gas: Optional[str]
    max_priority_fee_per_gas: Optional[str]
    transaction_tag: Optional[Any]
    created_contract: Optional[Any]
    base_fee_per_gas: Optional[str]
    has_error_in_internal_transactions: Optional[bool]
    actions: Optional[List[Any]]
    authorization_list: Optional[List[Any]]

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
    block_number_balance_updated_at: Optional[int]
    creation_transaction_hash: Optional[str]
    creator_address_hash: Optional[str]
    ens_domain_name: Optional[str]
    has_decompiled_code: bool
    has_logs: bool
    has_validated_blocks: bool
    implementations: List[Any]
    is_scam: bool
    is_verified: bool
    metadata: Optional[Any]
    name: Optional[str]
    proxy_type: Optional[str]
    watchlist_address_id: Optional[str]

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

    def get_transaction_history(self, address: str, limit: int = 5) -> List[Transaction]:
        """Get transaction history for an address."""
        try:
            data = self._make_api_request(f"addresses/{address}/transactions")
            transactions = data["items"][:limit]
            
            result = []
            for tx in transactions:
                # Get the fee from the API response
                fee = tx.get('fee', {})
                
                # Create a transaction object with all available fields
                transaction = {
                    "hash": tx["hash"],
                    "from_": tx["from"],
                    "to": tx["to"],
                    "value": tx["value"],
                    "timestamp": tx["timestamp"],
                    "block_number": tx["block_number"],
                    "fee": fee,
                    "status": tx["status"],
                    "gas_used": tx.get("gas_used"),
                    "gas_price": tx.get("gas_price"),
                    "gas_limit": tx.get("gas_limit"),
                    "method": tx.get("method"),
                    "decoded_input": tx.get("decoded_input"),
                    "token_transfers": tx.get("token_transfers"),
                    "nonce": tx.get("nonce"),
                    "transaction_types": tx.get("transaction_types"),
                    "exchange_rate": tx.get("exchange_rate"),
                    "result": tx.get("result"),
                    "type": tx.get("type"),
                    "confirmations": tx.get("confirmations"),
                    "position": tx.get("position"),
                    "priority_fee": tx.get("priority_fee"),
                    "tx_burnt_fee": tx.get("tx_burnt_fee"),
                    "raw_input": tx.get("raw_input"),
                    "revert_reason": tx.get("revert_reason"),
                    "confirmation_duration": tx.get("confirmation_duration"),
                    "transaction_burnt_fee": tx.get("transaction_burnt_fee"),
                    "max_fee_per_gas": tx.get("max_fee_per_gas"),
                    "max_priority_fee_per_gas": tx.get("max_priority_fee_per_gas"),
                    "transaction_tag": tx.get("transaction_tag"),
                    "created_contract": tx.get("created_contract"),
                    "base_fee_per_gas": tx.get("base_fee_per_gas"),
                    "has_error_in_internal_transactions": tx.get("has_error_in_internal_transactions"),
                    "actions": tx.get("actions"),
                    "authorization_list": tx.get("authorization_list")
                }
                
                result.append(transaction)
            
            return result
        except Exception as e:
            logger.error(f"Error in get_transaction_history: {str(e)}")
            raise Exception(f"Failed to get transaction history: {str(e)}")

    def get_blockchain_stats(self) -> BlockchainStats:
        """Get blockchain statistics."""
        try:
            data = self._make_api_request("stats")
            
            # The gas prices from the API are already in gwei, no need to convert
            # No ETH conversion needed as per requirements
            
            # Convert gas_prices_update_in from milliseconds to seconds
            if 'gas_prices_update_in' in data:
                data['gas_prices_update_in_seconds'] = data['gas_prices_update_in'] / 1000
            
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
                gas_prices_update_in_seconds=data.get("gas_prices_update_in_seconds", 0),
                static_gas_price=data["static_gas_price"]
            )
        except Exception as e:
            logger.error(f"Error in get_blockchain_stats: {str(e)}")
            raise Exception(f"Failed to get blockchain stats: {str(e)}")

    def get_address_overview(self, address: str) -> AddressOverview:
        """Get a comprehensive overview of an address including balances and token info."""
        try:
            data = self._make_api_request(f"addresses/{address}")
            
            # Return the raw coin balance without formatting
            # Formatting will be done in the server.py file
            
            return AddressOverview(
                hash=data["hash"],
                coin_balance=data["coin_balance"],  # Keep the raw balance
                is_contract=data["is_contract"],
                token=data.get("token"),
                has_tokens=data["has_tokens"],
                has_token_transfers=data["has_token_transfers"],
                has_beacon_chain_withdrawals=data["has_beacon_chain_withdrawals"],
                private_tags=data["private_tags"],
                public_tags=data["public_tags"],
                watchlist_names=data["watchlist_names"],
                exchange_rate=data.get("exchange_rate"),
                block_number_balance_updated_at=data.get("block_number_balance_updated_at"),
                creation_transaction_hash=data.get("creation_transaction_hash"),
                creator_address_hash=data.get("creator_address_hash"),
                ens_domain_name=data.get("ens_domain_name"),
                has_decompiled_code=data["has_decompiled_code"],
                has_logs=data["has_logs"],
                has_validated_blocks=data["has_validated_blocks"],
                implementations=data["implementations"],
                is_scam=data["is_scam"],
                is_verified=data["is_verified"],
                metadata=data.get("metadata"),
                name=data.get("name"),
                proxy_type=data.get("proxy_type"),
                watchlist_address_id=data.get("watchlist_address_id")
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
