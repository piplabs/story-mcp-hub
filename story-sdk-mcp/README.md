# Story SDK MCP Server

This server provides MCP (Model Context Protocol) tools for interacting with Story's [Python SDK](https://github.com/storyprotocol/python-sdk/).

## Features

- Get license terms
- Mint and register IP Asset with PIL Terms
- Mint license tokens
- Attach license terms to IP assets
- Register derivative IP assets
- Upload image to IPFS via Pinata [External]
- Upload IP and NFT metadata via Pinata [External]
- Create SPG NFT collections
- Royalty management (pay and claim)
- Dispute management
- WIP (Wrapped IP) token operations

## Environment Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Environment variables:

- `WALLET_PRIVATE_KEY`: Your EVM wallet private key
- `RPC_PROVIDER_URL`: Your RPC provider URL. You can use the default one provided.
- `PINATA_JWT`: [optional] JWT for uploading images/metadata to pinata. You need this to upload metadata to IPFS when registering an IP. You can get this by creating a new app on [pinata](https://pinata.cloud/)

## Available Tools

### Core IP Management Tools
1. `get_license_terms`: Retrieve license terms for a specific ID
2. `mint_license_tokens`: Mint license tokens for a specific IP and license terms
3. `mint_and_register_ip_with_terms`: Mint and register an IP with terms
4. `register`: Register an IP asset
5. `attach_license_terms`: Attach license terms to an IP asset
6. `register_derivative`: Register a derivative IP asset

### IPFS Tools (only available if PINATA_JWT is configured)
7. `upload_image_to_ipfs`: Upload an image to IPFS and return the URI
8. `create_ip_metadata`: Create NFT metadata for a specific image URI

### SPG NFT Collection Tools
9. `create_spg_nft_collection`: Create a new SPG NFT collection for minting and registering IP assets
10. `get_spg_nft_contract_minting_fee`: Get the minting fee for an SPG NFT contract

### Royalty Management Tools
11. `pay_royalty_on_behalf`: Pay royalty on behalf of an IP
12. `claim_all_revenue`: Claim all revenue from an IP

### Dispute Management Tools
13. `raise_dispute`: Raise a dispute on an IP

### WIP (Wrapped IP) Token Tools
14. `deposit_wip`: Wrap IP to WIP and deposit to wallet
15. `transfer_wip`: Transfer WIP to a recipient

### Example `mint_and_register_ip_with_terms`

You can use the following parameters to test the tool:

1. `commercial_rev_share`: 5
2. `derivatives_allowed`: True
3. `registration_metadata`:

```json
{
  "ip_metadata_uri": "https://azure-wooden-quail-605.mypinata.cloud/ipfs/QmcvC23URQPKSHYB9Xy5AFswy2SKqUYPRg7iYtL5ZqEi7b",
  "ip_metadata_hash": "0xe74a304f3ca32924cef88f7445eca413ff8f80d265417bfc93d6765bb26e4dec",
  "nft_metadata_uri": "https://azure-wooden-quail-605.mypinata.cloud/ipfs/QmegKQTYSeaNgKBncYTPWMJeykHVwDgsiFf493fkXBaWcb",
  "nft_metadata_hash": "0x5c6e29420f759a5cc6497ad1d564db70e2742790f4123225a093209ad55340d7"
}
```

### Example `create_spg_nft_collection`

You can use the following parameters to create a new SPG NFT collection:

1. Required parameters:
   - `name`: "My Collection"
   - `symbol`: "MYCOL"

2. Optional parameters:
   - `is_public_minting`: true/false (default: true)
   - `mint_open`: true/false (default: true)
   - `mint_fee_recipient`: Address to receive minting fees
   - `contract_uri`: URI for collection metadata
   - `base_uri`: Base URI for the collection
   - `max_supply`: Maximum number of tokens (default: unlimited)
   - `mint_fee`: Cost to mint a token (default: 0)
   - `mint_fee_token`: Token address for minting fees
   - `owner`: Owner address (default: sender)

## Usage with MCP

You can use these tools with any MCP-compatible client. The tools are exposed through the MCP protocol and can be accessed using any AI framework of your choosing.
