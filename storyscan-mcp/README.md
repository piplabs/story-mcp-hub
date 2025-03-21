# StoryScan MCP Server

This is a Model Context Protocol (MCP) server for interacting with the StoryScan API. It provides tools for querying blockchain data, including address balances, transactions, and blockchain statistics.

## Environment Configuration

Create a `.env` file in the project root with:

```
STORYSCAN_API_ENDPOINT=https://www.storyscan.io/api
```

## Available Tools

The server provides the following tools:

- `check_balance`: Check the balance of an address
- `get_transactions`: Get recent transactions for an address
- `get_stats`: Get current blockchain statistics
- `get_address_overview`: Get a comprehensive overview of an address
- `get_token_holdings`: Get all ERC-20 token holdings for an address
- `get_nft_holdings`: Get all NFT holdings for an address
- `interpret_transaction`: Get a human-readable interpretation of a transaction
