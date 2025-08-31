from mcp.server.fastmcp import FastMCP
from services.storyscan_service import StoryscanService
import os
from dotenv import load_dotenv
from utils.gas_utils import (
    format_token_balance,
    gwei_to_eth,
    gwei_to_wei,
    wei_to_gwei,
    wei_to_eth,
    eth_to_wei,
    format_gas_prices,
    format_gas_amount,
)

# Load environment variables from .env file
load_dotenv()

# Initialize FastMCP
mcp = FastMCP()

# Get API endpoint from environment variables
api_endpoint = os.environ.get("STORYSCAN_API_ENDPOINT")
if not api_endpoint:
    print("STORYSCAN_API_ENDPOINT environment variable is required")
    api_endpoint = "https://www.storyscan.io/api"  # Default fallback

# Initialize StoryScan service with SSL verification disabled
story_service = StoryscanService(api_endpoint, disable_ssl_verification=True)
print(f"Initialized StoryScan service with API endpoint: {api_endpoint}")


@mcp.tool()
def get_transactions(address: str, limit: int = 10):
    """Get recent (last 5) transactions for an address. Remember its an EVM chain but the token is $IP"""
    try:
        transactions = story_service.get_transaction_history(address, limit)

        if not transactions:
            return f"No transactions found for {address}"

        formatted_transactions = []
        for tx in transactions:
            # Format timestamp to be more readable
            timestamp = tx["timestamp"]
            try:
                # Try to parse and format the timestamp if it's in ISO format
                from datetime import datetime

                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                date = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            except (ValueError, AttributeError):
                # If parsing fails, use the original timestamp
                date = timestamp

            # Format transaction value with proper decimals
            value = tx["value"]
            try:
                # Assuming value is in wei, convert to a more readable format
                value_float = float(value)
                if value_float > 0:
                    value = f"{format_token_balance(value_float)} IP"
                else:
                    value = "0 IP"
            except (ValueError, TypeError):
                value = f"{value} IP"

            # Format transaction fee
            fee = (
                tx["fee"]["value"]
                if "fee" in tx and "value" in tx["fee"]
                else "Unknown"
            )
            try:
                fee_float = float(fee)
                if fee_float > 0:
                    fee = f"{format_token_balance(fee_float)} IP"
                else:
                    fee = "0 IP"
            except (ValueError, TypeError):
                fee = f"{fee} IP"

            # Get transaction status
            status = tx.get("status", "Unknown")
            status_text = "✅ Success" if status.lower(
            ) == "ok" else f"❌ {status}"

            # Add result information if available
            if tx.get("result") and tx["result"] != "success":
                status_text += f" ({tx['result']})"

            # Add revert reason if available
            if tx.get("revert_reason") and tx["revert_reason"].get("raw"):
                status_text += f" - Revert reason: {tx['revert_reason']['raw']}"

            # Get transaction method if available
            method = tx.get("method", "")
            method_text = f" ({method})" if method else ""

            # Get transaction type
            tx_types = tx.get("transaction_types", [])
            tx_type_text = f" [{', '.join(tx_types)}]" if tx_types else ""

            # Format gas information if available
            gas_info = ""
            if tx.get("gas_used") and tx.get("gas_limit"):
                gas_used = tx["gas_used"]
                gas_limit = tx["gas_limit"]
                gas_info = f"\nGas Used/Limit: {gas_used}/{gas_limit}"

            if tx.get("gas_price"):
                gas_price = tx["gas_price"]
                # Gas price is in gwei
                gas_info += f"\nGas Price: {gas_price} gwei"

            # Add more gas information if available
            if tx.get("base_fee_per_gas"):
                gas_info += f"\nBase Fee: {tx['base_fee_per_gas']} gwei"

            if tx.get("max_fee_per_gas"):
                gas_info += f"\nMax Fee: {tx['max_fee_per_gas']} gwei"

            if tx.get("priority_fee"):
                gas_info += f"\nPriority Fee: {tx['priority_fee']}"

            if tx.get("max_priority_fee_per_gas"):
                gas_info += f"\nMax Priority Fee: {tx['max_priority_fee_per_gas']} gwei"

            # Add transaction burnt fee if available
            if tx.get("transaction_burnt_fee"):
                gas_info += f"\nBurnt Fee: {tx['transaction_burnt_fee']}"

            # Add decoded input if available
            decoded_input = ""
            if tx.get("decoded_input") and tx["decoded_input"].get("method_call"):
                decoded_input = f"\nMethod Call: {tx['decoded_input']['method_call']}"

                # Add parameters if available
                if tx["decoded_input"].get("parameters"):
                    params = tx["decoded_input"]["parameters"]
                    param_text = []
                    for param in params:
                        name = param.get("name", "")
                        type_ = param.get("type", "")
                        value_ = param.get("value", "")

                        # Format value if it's a token amount
                        if (
                            type_ == "uint256"
                            and isinstance(value_, str)
                            and value_.isdigit()
                            and len(value_) > 10
                        ):
                            try:
                                value_ = f"{format_token_balance(value_)} IP"
                            except (ValueError, TypeError):
                                pass

                        param_text.append(f"{name}: {value_}")

                    if param_text:
                        decoded_input += f"\nParameters: {', '.join(param_text)}"

            # Add raw input if available and decoded input is not
            elif tx.get("raw_input"):
                # Truncate if too long
                raw_input = tx["raw_input"]
                if len(raw_input) > 50:
                    raw_input = raw_input[:47] + "..."
                decoded_input = f"\nRaw Input: {raw_input}"

            # Add USD value if exchange rate is available
            usd_value = ""
            if tx.get("exchange_rate") and value_float > 0:
                try:
                    exchange_rate = float(tx["exchange_rate"])
                    value_eth = format_token_balance(value_float)
                    usd_amount = float(value_eth) * exchange_rate
                    usd_value = f" (${usd_amount:.2f} USD)"
                except (ValueError, TypeError):
                    pass

            # Add contract information if available
            contract_info = ""
            if tx.get("created_contract"):
                contract_info = f"\nCreated Contract: {tx['created_contract']['hash']}"

            # Add error information if available
            error_info = ""
            if tx.get("has_error_in_internal_transactions"):
                error_info = f"\nHas Error In Internal Transactions: {tx['has_error_in_internal_transactions']}"

            # Format the transaction
            formatted_tx = (
                f"Block {tx['block_number']} ({date}):\n"
                f"Hash: {tx['hash']}\n"
                f"From: {tx['from_']['hash']}\n"
                f"To: {tx['to']['hash']}{method_text}{tx_type_text}\n"
                f"Value: {value}{usd_value}\n"
                f"Fee: {fee}{gas_info}{decoded_input}{contract_info}{error_info}\n"
                f"Status: {status_text}\n"
                f"---"
            )
            formatted_transactions.append(formatted_tx)

        return f"Recent transactions for {address}:\n\n" + "\n".join(
            formatted_transactions
        )
    except Exception as e:
        return f"Error getting transactions: {str(e)}"


@mcp.tool()
def get_stats():
    """Get current blockchain statistics. Remember its an EVM chain but the token is $IP"""
    try:
        stats = story_service.get_blockchain_stats()
        # Convert average block time from milliseconds to seconds
        block_time_seconds = float(stats["average_block_time"]) / 1000

        # Format gas prices to show only gwei units
        gas_prices_text = (
            f"Slow: {stats['gas_prices']['slow']} gwei\n"
            f"Average: {stats['gas_prices']['average']} gwei\n"
            f"Fast: {stats['gas_prices']['fast']} gwei"
        )

        # Format market cap with proper currency symbol
        market_cap = stats.get("market_cap", "0")
        if market_cap:
            try:
                market_cap_float = float(market_cap)
                if market_cap_float >= 1_000_000_000:  # Billions
                    market_cap = f"${market_cap_float / 1_000_000_000:.2f}B"
                elif market_cap_float >= 1_000_000:  # Millions
                    market_cap = f"${market_cap_float / 1_000_000:.2f}M"
                else:
                    market_cap = f"${market_cap_float:,.2f}"
            except (ValueError, TypeError):
                market_cap = f"${market_cap}"

        # Format coin price
        coin_price = stats.get("coin_price", "0")
        if coin_price:
            try:
                coin_price = f"${float(coin_price):,.2f}"
            except (ValueError, TypeError):
                coin_price = f"${coin_price}"

        # Format gas used values for better readability
        gas_used_today_formatted = format_gas_amount(stats["gas_used_today"])
        total_gas_used_formatted = format_gas_amount(stats["total_gas_used"])

        # Create a human-readable format for when the next gas price update will occur
        gas_update_time = "Unknown"
        if stats.get("gas_prices_update_in_seconds"):
            minutes = int(stats["gas_prices_update_in_seconds"] // 60)
            seconds = int(stats["gas_prices_update_in_seconds"] % 60)
            gas_update_time = f"{minutes}m {seconds}s"

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Blockchain Statistics:\n"
                    f"Total Blocks: {stats['total_blocks']}\n"
                    f"Average Block Time: {block_time_seconds:.2f} seconds\n"
                    f"Total Transactions: {stats['total_transactions']}\n"
                    f"Transactions Today: {stats.get('transactions_today', 'N/A')}\n"
                    f"Total Addresses: {stats['total_addresses']}\n"
                    f"IP Price: {coin_price}\n"
                    f"Market Cap: {market_cap}\n"
                    f"Network Utilization: {stats['network_utilization_percentage']}%\n\n"
                    f"Gas Prices:\n{gas_prices_text}\n"
                    f"Gas Prices Update In: {gas_update_time}\n\n"
                    f"Gas Used Today: {gas_used_today_formatted}\n"
                    f"Total Gas Used: {total_gas_used_formatted}",
                }
            ],
            "raw_data": {
                "average_block_time": stats["average_block_time"],
                "coin_image": stats.get("coin_image"),
                "coin_price": stats.get("coin_price"),
                "coin_price_change_percentage": stats.get(
                    "coin_price_change_percentage"
                ),
                "gas_price_updated_at": stats.get("gas_price_updated_at"),
                "gas_prices": stats.get("gas_prices"),
                "gas_prices_update_in": stats.get("gas_prices_update_in"),
                "gas_prices_update_in_seconds": stats.get(
                    "gas_prices_update_in_seconds"
                ),
                "gas_used_today": stats.get("gas_used_today"),
                "gas_used_today_formatted": gas_used_today_formatted,
                "market_cap": stats.get("market_cap"),
                "network_utilization_percentage": stats.get(
                    "network_utilization_percentage"
                ),
                "secondary_coin_image": stats.get("secondary_coin_image"),
                "secondary_coin_price": stats.get("secondary_coin_price"),
                "static_gas_price": stats.get("static_gas_price"),
                "total_addresses": stats.get("total_addresses"),
                "total_blocks": stats.get("total_blocks"),
                "total_gas_used": stats.get("total_gas_used"),
                "total_gas_used_formatted": total_gas_used_formatted,
                "total_transactions": stats.get("total_transactions"),
                "transactions_today": stats.get("transactions_today"),
                "tvl": stats.get("tvl"),
            },
        }
    except Exception as e:
        return f"Error getting blockchain stats: {str(e)}"


@mcp.tool()
def get_address_overview(address: str):
    """Get a comprehensive overview of an address including ETH balance, token info,
    and various blockchain activity indicators. Remember its an EVM chain but the token is $IP"""
    try:
        overview = story_service.get_address_overview(address)

        # Format the coin balance from wei to a human-readable value
        raw_balance = overview["coin_balance"]
        formatted_balance = format_token_balance(raw_balance)

        # Start with basic information
        result = (
            f"Address Overview for {overview['hash']}:\nBalance: {formatted_balance} IP"
        )

        # Add USD value if exchange rate is available
        if overview.get("exchange_rate"):
            try:
                exchange_rate = float(overview["exchange_rate"])
                balance_eth = float(formatted_balance)
                usd_value = balance_eth * exchange_rate
                result += f" (${usd_value:.2f} USD)"
            except (ValueError, TypeError):
                pass

        # Add block number when balance was updated
        if overview.get("block_number_balance_updated_at"):
            result += f"\nBalance Updated at Block: {overview['block_number_balance_updated_at']}"

        # Add basic address information
        result += f"\nIs Contract: {overview['is_contract']}"
        if overview.get("is_verified"):
            result += f"\nIs Verified: {overview['is_verified']}"
        if overview.get("is_scam"):
            result += f"\nIs Flagged as Scam: {overview['is_scam']}"

        # Add ENS domain name if available
        if overview.get("ens_domain_name"):
            result += f"\nENS Domain: {overview['ens_domain_name']}"

        # Add creation information if available
        if overview.get("creation_transaction_hash"):
            result += f"\nCreation Transaction: {overview['creation_transaction_hash']}"
        if overview.get("creator_address_hash"):
            result += f"\nCreator Address: {overview['creator_address_hash']}"

        # Add activity indicators
        result += f"\n\nActivity Indicators:"
        result += f"\nHas Tokens: {overview['has_tokens']}"
        result += f"\nHas Token Transfers: {overview.get('has_token_transfers', 'Unknown')}"
        result += f"\nHas Logs: {overview.get('has_logs', 'Unknown')}"
        result += f"\nHas Beacon Chain Withdrawals: {overview.get('has_beacon_chain_withdrawals', 'Unknown')}"
        result += f"\nHas Validated Blocks: {overview.get('has_validated_blocks', 'Unknown')}"
        result += f"\nHas Decompiled Code: {overview.get('has_decompiled_code', 'Unknown')}"

        # Add proxy information if available
        if overview.get("proxy_type"):
            result += f"\nProxy Type: {overview['proxy_type']}"

        if overview.get("implementations") and len(overview["implementations"]) > 0:
            impls = ", ".join([impl for impl in overview["implementations"]])
            result += f"\nImplementations: {impls}"

        # Add public tags if available
        if overview["public_tags"]:
            tags = ", ".join([tag["display_name"]
                             for tag in overview["public_tags"]])
            result += f"\n\nPublic Tags: {tags}"

        # Add private tags if available
        if overview["private_tags"]:
            tags = ", ".join([tag["display_name"]
                             for tag in overview["private_tags"]])
            result += f"\nPrivate Tags: {tags}"

        # Add watchlist names if available
        if overview["watchlist_names"]:
            names = ", ".join(
                [name["display_name"] for name in overview["watchlist_names"]]
            )
            result += f"\nWatchlist Names: {names}"

        # Add token info if this address is a token contract
        if overview.get("token"):
            token = overview["token"]
            result += "\n\nToken Information:"
            result += f"\nName: {token['name']}"
            result += f"\nSymbol: {token['symbol']}"

            # Format total supply with proper decimals
            if (
                token.get("total_supply")
                and token.get("decimals")
                and token["decimals"] != "null"
            ):
                try:
                    decimals = int(token["decimals"])
                    total_supply = format_token_balance(
                        token["total_supply"], decimals)
                    result += f"\nTotal Supply: {total_supply} {token['symbol']}"
                except (ValueError, TypeError):
                    result += f"\nTotal Supply: {token['total_supply']}"
            else:
                result += f"\nTotal Supply: {token.get('total_supply', 'Unknown')}"

            result += f"\nDecimals: {token.get('decimals', 'Unknown')}"
            result += f"\nType: {token.get('type', 'Unknown')}"
            result += f"\nHolders: {token.get('holders', 'Unknown')}"

            if token.get("exchange_rate"):
                result += f"\nExchange Rate: ${token['exchange_rate']}"

            if token.get("circulating_market_cap"):
                try:
                    market_cap = float(token["circulating_market_cap"])
                    if market_cap >= 1_000_000_000:  # Billions
                        formatted_market_cap = f"${market_cap / 1_000_000_000:.2f}B"
                    elif market_cap >= 1_000_000:  # Millions
                        formatted_market_cap = f"${market_cap / 1_000_000:.2f}M"
                    else:
                        formatted_market_cap = f"${market_cap:,.2f}"
                    result += f"\nMarket Cap: {formatted_market_cap}"
                except (ValueError, TypeError):
                    result += f"\nMarket Cap: ${token['circulating_market_cap']}"

        # Add raw data for debugging or advanced use
        result += "\n\nRaw Data:"
        result += f"\nRaw Balance: {raw_balance} wei"
        if overview.get("exchange_rate"):
            result += f"\nExchange Rate: ${overview['exchange_rate']} USD"

        return result
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
            raw_value = holding["value"]

            # Normalize common token fields from Storyscan
            token_address = token.get("address") or token.get("address_hash") or "Unknown"
            token_symbol = token.get("symbol", "UNKNOWN")
            token_name = token.get("name", "Unknown")
            token_type = token.get("type", "Unknown")
            token_decimals = token.get("decimals")
            token_holders = token.get("holders") or token.get("holders_count")

            # Get formatted value using a cleaner approach
            try:
                decimals = (
                    int(token_decimals)
                    if token_decimals and token_decimals != "null"
                    else None
                )
                formatted_value = (
                    format_token_balance(raw_value, decimals)
                    if decimals is not None
                    else raw_value
                )
            except (ValueError, TypeError):
                formatted_value = raw_value

            # Calculate USD value if available (using a cleaner approach)
            usd_display = ""
            if token.get("exchange_rate"):
                try:
                    usd_amount = float(formatted_value) * \
                        float(token["exchange_rate"])
                    usd_display = f" (${usd_amount:.2f} USD)"
                except (ValueError, TypeError):
                    pass

            # Create the display string directly
            display_value = f"{formatted_value} {token_symbol}{usd_display}"

            formatted_holding = (
                f"Token: {token_name} ({token_symbol})\n"
                f"Value: {display_value}\n"
                f"Decimals: {token_decimals if token_decimals is not None else 'Unknown'}\n"
                f"Address: {token_address}\n"
                f"Type: {token_type}"
            )

            # Add holders count if available
            if token_holders:
                formatted_holding += f"\nHolders: {token_holders}"

            # Add total supply if available
            if token.get("total_supply"):
                formatted_holding += f"\nTotal Supply: {token['total_supply']}"

            # Add market cap if available
            if token.get("circulating_market_cap"):
                formatted_holding += f"\nMarket Cap: ${token['circulating_market_cap']}"

            formatted_holding += "\n---"
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

            # Normalize token fields
            token_address = token.get("address") or token.get("address_hash") or "Unknown"
            token_symbol = token.get("symbol", "UNKNOWN")
            token_name = token.get("name", "Unknown")
            token_holders = token.get("holders") or token.get("holders_count")

            # Basic NFT information
            formatted_holding = (
                f"Collection: {token_name} ({token_symbol})\n"
                f"Token ID: {nft.get('id', 'Unknown')}\n"
                f"Token Type: {nft.get('token_type', 'Unknown')}\n"
                f"Value: {nft.get('value', 'Unknown')} (smallest unit)\n"
                f"Contract Address: {token_address}\n"
            )

            # Add token statistics if available
            if token_holders:
                formatted_holding += f"Collection Holders: {token_holders}\n"

            if token.get("total_supply"):
                formatted_holding += (
                    f"Collection Total Supply: {token['total_supply']}\n"
                )

            # Add media information if available
            if nft.get("image_url"):
                formatted_holding += f"Image URL: {nft['image_url']}\n"

            if nft.get("animation_url"):
                formatted_holding += f"Animation URL: {nft['animation_url']}\n"

            if nft.get("media_url") and nft["media_url"] != nft.get("image_url"):
                formatted_holding += f"Media URL: {nft['media_url']}\n"

            if nft.get("media_type"):
                formatted_holding += f"Media Type: {nft['media_type']}\n"

            if nft.get("external_app_url"):
                formatted_holding += f"External URL: {nft['external_app_url']}\n"

            # Add metadata summary if available
            if nft.get("metadata") and isinstance(nft["metadata"], dict):
                formatted_holding += "Metadata:\n"

                if "name" in nft["metadata"]:
                    formatted_holding += f"  Name: {nft['metadata']['name']}\n"

                if "description" in nft["metadata"] and nft["metadata"]["description"]:
                    desc = nft["metadata"]["description"]
                    # Truncate long descriptions
                    if len(desc) > 100:
                        desc = desc[:97] + "..."
                    formatted_holding += f"  Description: {desc}\n"

                if "external_url" in nft["metadata"]:
                    formatted_holding += (
                        f"  External URL: {nft['metadata']['external_url']}\n"
                    )

                # Add relationships if available
                if (
                    "relationships" in nft["metadata"]
                    and nft["metadata"]["relationships"]
                ):
                    relationships = nft["metadata"]["relationships"]
                    if relationships and len(relationships) > 0:
                        formatted_holding += "  Relationships:\n"
                        for rel in relationships:
                            rel_type = rel.get("type", "Unknown")
                            parent_id = rel.get("parentIpId", "Unknown")
                            formatted_holding += f"    - {rel_type}: {parent_id}\n"

                # Add attributes if available
                if "attributes" in nft["metadata"] and nft["metadata"]["attributes"]:
                    attrs = nft["metadata"]["attributes"]
                    if attrs and len(attrs) > 0:
                        formatted_holding += "  Attributes:\n"
                        # Limit to first 5 attributes to avoid overwhelming output
                        for i, attr in enumerate(attrs[:5]):
                            if isinstance(attr, dict):
                                trait_type = attr.get("trait_type") or attr.get(
                                    "name", "Trait"
                                )
                                value = attr.get("value", "")
                                formatted_holding += f"    - {trait_type}: {value}\n"
                        if len(attrs) > 5:
                            formatted_holding += (
                                f"    ... and {len(attrs) - 5} more attributes\n"
                            )

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
        # Get the interpretation from the service
        interpretation = story_service.get_transaction_interpretation(transaction_hash)

        # Start with a header
        result = f"Transaction Interpretation for {transaction_hash}:\n\n"

        # PART 1: EXTRACT ALL SUMMARY INFORMATION
        if "summaries" in interpretation and interpretation["summaries"]:
            result += "TRANSACTION SUMMARIES:\n"
            # Extract and format each summary
            for i, summary in enumerate(interpretation["summaries"]):
                result += f"Summary #{i+1}:\n"
                
                # Add the raw template
                if "summary_template" in summary:
                    result += f"Template: {summary['summary_template']}\n"
                
                # Process all template variables in detail
                if "summary_template_variables" in summary:
                    result += "Template Variables:\n"
                    variables = summary["summary_template_variables"]
                    
                    for key, var_data in variables.items():
                        var_type = var_data.get("type", "unknown")
                        result += f"  {key} ({var_type}):\n"
                        
                        if "value" in var_data:
                            # Handle different variable types
                            if var_type == "address" and isinstance(var_data["value"], dict):
                                addr_info = var_data["value"]
                                result += f"    Hash: {addr_info.get('hash', 'Unknown')}\n"
                                
                                # Include ALL address properties
                                for addr_key, addr_value in addr_info.items():
                                    if addr_key != "hash" and addr_value not in (None, "", [], {}):
                                        if isinstance(addr_value, dict):
                                            result += f"    {addr_key}: {str(addr_value)}\n"
                                        elif isinstance(addr_value, list) and addr_value:
                                            result += f"    {addr_key}: {str(addr_value)}\n"
                                        else:
                                            result += f"    {addr_key}: {addr_value}\n"
                            
                            elif var_type == "token" and isinstance(var_data["value"], dict):
                                token_info = var_data["value"]
                                result += f"    Name: {token_info.get('name', 'Unknown')}\n"
                                result += f"    Symbol: {token_info.get('symbol', 'Unknown')}\n"
                                
                                # Include ALL token properties
                                for token_key, token_value in token_info.items():
                                    if token_key not in ("name", "symbol") and token_value not in (None, "", [], {}):
                                        result += f"    {token_key}: {token_value}\n"
                            
                            elif var_type == "currency":
                                # Format currency with proper decimals if possible
                                try:
                                    token_info = variables.get("token", {}).get("value", {})
                                    decimals = int(token_info.get("decimals", 18))
                                    raw_value = var_data["value"]
                                    formatted_value = format_token_balance(raw_value, decimals)
                                    result += f"    Value: {formatted_value}\n"
                                    result += f"    Raw Value: {raw_value}\n"
                                except (ValueError, TypeError):
                                    result += f"    Value: {var_data['value']}\n"
                            
                            else:
                                # For all other types, just show the value
                                result += f"    Value: {var_data['value']}\n"
                
                # Add formatted summary
                try:
                    template = summary["summary_template"]
                    variables = summary["summary_template_variables"]
                    formatted_values = {}
                    
                    for key, var_data in variables.items():
                        if var_data["type"] == "address" and "value" in var_data and "hash" in var_data["value"]:
                            addr_info = var_data["value"]
                            if "name" in addr_info and addr_info["name"]:
                                formatted_values[key] = f"{addr_info['name']} ({addr_info['hash']})"
                            else:
                                formatted_values[key] = addr_info["hash"]
                        
                        elif var_data["type"] == "token" and "value" in var_data:
                            token_info = var_data["value"]
                            if "name" in token_info and "symbol" in token_info:
                                formatted_values[key] = f"{token_info['name']} ({token_info['symbol']})"
                            elif "symbol" in token_info:
                                formatted_values[key] = token_info["symbol"]
                            else:
                                formatted_values[key] = token_info.get("address", "Unknown Token")
                        
                        elif var_data["type"] == "currency" and "value" in var_data:
                            try:
                                token_info = variables.get("token", {}).get("value", {})
                                decimals = int(token_info.get("decimals", 18))
                                raw_value = var_data["value"]
                                formatted_values[key] = format_token_balance(raw_value, decimals)
                            except (ValueError, TypeError):
                                formatted_values[key] = var_data["value"]
                        
                        elif "value" in var_data:
                            formatted_values[key] = var_data["value"]
                    
                    # Replace placeholders in the template
                    formatted_summary = template
                    for key, value in formatted_values.items():
                        formatted_summary = formatted_summary.replace(f"{{{key}}}", str(value))
                    
                    result += f"Formatted Summary: {formatted_summary}\n"
                except Exception as e:
                    result += f"Could not format summary: {str(e)}\n"
                
                result += "\n"

        # PART 2: EXTRACT ALL DATA AND DEBUG DATA
        if "data" in interpretation and interpretation["data"]:
            data = interpretation["data"]
            result += "TRANSACTION DATA:\n"
            
            # Extract debug data
            if "debug_data" in data:
                debug_data = data["debug_data"]
                result += "Debug Data:\n"
                
                # Add transaction type
                if "model_classification_type" in debug_data:
                    result += f"  Transaction Type: {debug_data['model_classification_type']}\n"
                
                # Add transaction hash
                if "transaction_hash" in debug_data:
                    result += f"  Transaction Hash: {debug_data['transaction_hash']}\n"
                
                # Process summary templates in debug data
                if "summary_template" in debug_data:
                    summary_template = debug_data["summary_template"]
                    result += "  Summary Templates:\n"
                    
                    for template_type, template_data in summary_template.items():
                        result += f"    Template Type: {template_type}\n"
                        
                        if "template_name" in template_data:
                            result += f"    Template Name: {template_data['template_name']}\n"
                        
                        if "template_vars" in template_data:
                            vars_data = template_data["template_vars"]
                            result += "    Template Variables:\n"
                            
                            # Process all template variables
                            for key, value in vars_data.items():
                                if isinstance(value, dict):
                                    # Handle complex objects like tokens, addresses, etc.
                                    result += f"      {key}:\n"
                                    
                                    if key == "token":
                                        # Extract token information
                                        result += "        Token Information:\n"
                                        for token_key, token_value in value.items():
                                            if token_value not in (None, "", [], {}):
                                                result += f"          {token_key}: {token_value}\n"
                                    
                                    elif key.endswith("Address"):
                                        # Extract address information
                                        result += "        Address Information:\n"
                                        for addr_key, addr_value in value.items():
                                            if addr_value not in (None, "", [], {}):
                                                result += f"          {addr_key}: {addr_value}\n"
                                    
                                    elif key == "decodedApprovalEvent":
                                        # Extract decoded approval event information
                                        result += "        Decoded Approval Event:\n"
                                        
                                        # Process address information
                                        if "address" in value:
                                            addr = value["address"]
                                            result += "          Contract Address:\n"
                                            for addr_key, addr_value in addr.items():
                                                if addr_value not in (None, "", [], {}):
                                                    if isinstance(addr_value, (dict, list)):
                                                        result += f"            {addr_key}: {str(addr_value)}\n"
                                                    else:
                                                        result += f"            {addr_key}: {addr_value}\n"
                                        
                                        # Process block information
                                        if "block_hash" in value:
                                            result += f"          Block Hash: {value['block_hash']}\n"
                                        if "block_number" in value:
                                            result += f"          Block Number: {value['block_number']}\n"
                                        
                                        # Process data and topics
                                        if "data" in value:
                                            result += f"          Data: {value['data']}\n"
                                        if "topics" in value and value["topics"]:
                                            result += "          Topics:\n"
                                            for i, topic in enumerate(value["topics"]):
                                                if topic:
                                                    result += f"            Topic {i}: {topic}\n"
                                        
                                        # Process decoded information
                                        if "decoded" in value and isinstance(value["decoded"], dict):
                                            decoded = value["decoded"]
                                            result += "          Decoded Information:\n"
                                            result += f"            Method Call: {decoded.get('method_call', 'Unknown')}\n"
                                            result += f"            Method ID: {decoded.get('method_id', 'Unknown')}\n"
                                            
                                            # Process parameters
                                            if "parameters" in decoded and decoded["parameters"]:
                                                result += "            Parameters:\n"
                                                for param in decoded["parameters"]:
                                                    param_name = param.get("name", "Unknown")
                                                    param_type = param.get("type", "Unknown")
                                                    param_value = param.get("value", "Unknown")
                                                    param_indexed = param.get("indexed", False)
                                                    
                                                    # Format value if it's a max uint256 (unlimited approval)
                                                    if (param_type == "uint256" and 
                                                        isinstance(param_value, str) and 
                                                        param_value.startswith("115792089237316195423570985008687907853269984665640564039457584007")):
                                                        param_value = f"Unlimited ({param_value})"
                                                    
                                                    result += f"              {param_name} ({param_type}): {param_value} (Indexed: {param_indexed})\n"
                                        
                                        # Process other fields
                                        for field_key, field_value in value.items():
                                            if field_key not in ("address", "block_hash", "block_number", "data", "topics", "decoded") and field_value not in (None, "", [], {}):
                                                result += f"          {field_key}: {field_value}\n"
                                    
                                    else:
                                        # For other dictionary types, just dump all key-values
                                        for sub_key, sub_value in value.items():
                                            if sub_value not in (None, "", [], {}):
                                                result += f"        {sub_key}: {sub_value}\n"
                                
                                elif isinstance(value, list):
                                    # Handle list types
                                    if value:  # Only process non-empty lists
                                        result += f"      {key}:\n"
                                        for i, item in enumerate(value):
                                            result += f"        Item {i+1}: {str(item)}\n"
                                
                                else:
                                    # Handle simple values
                                    result += f"      {key}: {value}\n"
                
                # Process any other debug data fields
                for key, value in debug_data.items():
                    if key not in ("model_classification_type", "transaction_hash", "summary_template") and value not in (None, "", [], {}):
                        result += f"  {key}: {str(value)}\n"
            
            # Process any other data fields
            for key, value in data.items():
                if key != "debug_data" and value not in (None, "", [], {}):
                    result += f"  {key}: {str(value)}\n"

        # Return the raw JSON data as well
        result += "\n\nRAW JSON DATA:\n"
        import json
        result += json.dumps(interpretation, indent=2)
        
        return result
    except Exception as e:
        return f"Error interpreting transaction: {str(e)}"


if __name__ == "__main__":
    mcp.run()
