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
12. `claim_all_revenue`: Claim all revenue from an IP (claimer defaults to current account)

### Dispute Management Tools
13. `raise_dispute`: Raise a dispute on an IP with specific tags

### WIP (Wrapped IP) Token Tools
14. `deposit_wip`: Wrap IP to WIP and deposit to wallet
15. `transfer_wip`: Transfer WIP to a recipient
16. `approve_token_for_collection`: **[NEW]** Approve any token type for collection minting fees
17. `check_token_compatibility`: **[NEW]** Check what token types a collection supports

## 🆕 Enhanced Token Support

### Multi-Token Approval System
The system now supports automatic approval of different token types for collection mint fees:

- **WIP Tokens**: Uses SDK's unified WIP interface
- **Native IP Tokens**: Uses standard ERC20 interface  
- **Custom ERC20 Tokens**: Generic ERC20 interface (ETH, USDC, DAI, etc.)

### How It Works

1. **Collection Creation**: When creating collections with `create_spg_nft_collection`, you can set:
   - `mint_fee`: Cost to mint in wei
   - `mint_fee_token`: Any ERC20 token address (defaults to WIP if not specified)

2. **Automatic Detection**: When minting, the system automatically:
   - Detects the collection's required token via `get_spg_nft_contract_minting_fee`
   - Approves the correct token type using the appropriate interface
   - Handles the minting transaction seamlessly

3. **Universal Compatibility**: No more limitations to WIP-only collections!

### Example Usage

```javascript
// Check what token a collection uses
check_token_compatibility("0xYourCollectionAddress")

// Approve tokens for a specific collection and spender
approve_token_for_collection(
  collection_contract="0xYourCollectionAddress", 
  spender="0xMintingContractAddress"
)

// Mint from any collection (automatically handles token approval)
mint_and_register_ip_with_terms(
  commercial_rev_share=5,
  derivatives_allowed=True,
  registration_metadata=metadata,
  spg_nft_contract="0xYourCollectionAddress"
)
```

### Supported Token Types

| Token Type | Interface Used | Example |
|------------|----------------|---------|
| **Native IP** | ERC20 Standard | `0x1514000000000000000000000000000000000000` |
| **WIP Token** | WIP SDK | `0xWIPTokenAddress` (network-specific) |
| **ETH/Other ERC20** | Generic ERC20 | `0xA0b86a33E6441be776e9D5AD52c7dAD12B8C8A9F` |

## Example Collection Creation with Different Tokens

### Create Collection with ETH Fee Token
```javascript
create_spg_nft_collection(
  name="ETH Collection",
  symbol="ETHCOL", 
  mint_fee=1000000000000000,  // 0.001 ETH in wei
  mint_fee_token="0xA0b86a33E6441be776e9D5AD52c7dAD12B8C8A9F"  // ETH token address
)
```

### Create Collection with Custom ERC20 Token
```javascript
create_spg_nft_collection(
  name="USDC Collection",
  symbol="USDCCOL",
  mint_fee=1000000,  // 1 USDC (6 decimals)
  mint_fee_token="0xUSDCTokenAddress"
)
```

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

## 🧪 Testing Different Token Types

### Testing on Story Testnet
All testing should be done on **Story Testnet (Iliad)** - you don't need to switch networks!

#### Network Configuration
- **Network Name**: Story Testnet (Iliad)  
- **Chain ID**: 1513
- **RPC URL**: `https://testnet.storyrpc.io`
- **Explorer**: https://aeneid.explorer.story.foundation

#### Available Test Tokens
Story testnet has its own ecosystem of test ERC20 tokens:

| Token Type | Description | How to Get |
|------------|-------------|------------|
| **Native IP** | Story's native token | Use testnet faucet |
| **Test ETH** | ERC20 version of ETH on Story | Request from faucet/deploy |
| **Test USDC** | Mock USDC for testing | Deploy or request |
| **Custom ERC20** | Your own test tokens | Deploy using create tools |

### Testing Workflow

#### 1. Setup Your Wallet
```bash
# Make sure you're on Story Testnet
Network: Story Testnet (Iliad)
Chain ID: 1513
```

#### 2. Get Test Tokens
```python
# Option A: Use our new inspection tools
check_token_compatibility("0xYourTestCollectionAddress")

# Option B: Create a test collection with custom token
create_spg_nft_collection(
    name="ETH Test Collection",
    symbol="ETHTEST",
    mint_fee=1000000000000000,  # 0.001 test ETH
    mint_fee_token="0xTestETHTokenAddress"  # Story testnet ETH token
)
```

#### 3. Test Token Approval
```python
# This will test the approval system with any token type
approve_token_for_collection(
    collection_contract="0xYourTestCollection",
    spender="0xa38f42B8d33809917f23997B8423054aAB97322C"  # Mint spender
)
```

#### 4. Test Minting
```python
# This will test the complete flow with your chosen token
mint_and_register_ip_with_terms(
    commercial_rev_share=5,
    derivatives_allowed=True,
    registration_metadata=your_metadata,
    spg_nft_contract="0xYourTestCollection"  # Collection using custom token
)
```

### 📋 Testing Checklist

- [ ] Wallet configured for Story Testnet (Chain ID: 1513)
- [ ] Test tokens available in wallet
- [ ] Collection created with custom `mint_fee_token`
- [ ] Token approval works with `approve_token_for_collection`
- [ ] Minting works with `mint_and_register_ip_with_terms`
- [ ] Transaction appears on Story Explorer

### 🚨 Common Testing Issues

1. **"Insufficient funds"**: Make sure you have enough test tokens in your wallet
2. **"Token not found"**: Verify the token contract exists on Story testnet  
3. **"Approval failed"**: Check if the token contract supports standard ERC20 methods
4. **"Network mismatch"**: Ensure you're connected to Story testnet, not another network

### 💡 Pro Testing Tips

- Use `check_token_compatibility()` before testing to verify token setup
- Start with small amounts for initial tests
- Monitor transactions on Story Explorer
- Keep test token contracts addresses handy for repeated testing
