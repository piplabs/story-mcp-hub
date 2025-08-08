# Running the Story Protocol Specialized Agent

## Prerequisites

1. **Install Dependencies**
   ```bash
   pip3 install -e "."
   ```

2. **Set Environment Variables**
   Create a `.env` file in the project root with:
   ```
   OPENAI_API_KEY=your-openai-api-key
   
   # Optional: If you have specific RPC or wallet settings
   RPC_PROVIDER_URL=your-rpc-url
   WALLET_PRIVATE_KEY=your-wallet-private-key
   ```
   
   Or export directly:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

## Running the Agent

### Method 1: Direct Python Script
```bash
python3 run_agent.py
```

### Method 2: Make it Executable
```bash
chmod +x run_agent.py
./run_agent.py
```

## How to Chat with the Agent

Once running, you'll see:
```
=== Story Protocol Specialized Agent System ===
Following LangGraph tutorial patterns with interrupt_before confirmation

Wallet Address: 0xeC2E8ae2F6c9BE6C876629198Cc554c17e9Ff2C4

Available specialists:
  • Dispute: raise_dispute
  • IPAccount: get_erc20_token_balance, mint_test_erc20_tokens
  • IPAsset: mint_and_register_ip_with_terms, register, upload_image_to_ipfs, create_ip_metadata
  • License: get_license_terms, mint_license_tokens, attach_license_terms
  • NFTClient: create_spg_nft_collection, get_spg_nft_contract_minting_fee_and_token
  • Royalty: pay_royalty_on_behalf, claim_all_revenue
  • WIP: deposit_wip, transfer_wip

Type 'quit' to exit.

User: _
```

### Example Conversations

#### 1. Check ERC20 Token Balance (Safe Operation - No Confirmation)
```
User: What's my ERC20 token balance?
Assistant: I'll check your ERC20 token balance for you...
[Executes get_erc20_token_balance without confirmation]
```

#### 2. Register an IP Asset (Sensitive Operation - Requires Confirmation)
```
User: I want to register a new IP asset
Assistant: I'll help you register a new IP asset...
[Prepares mint_and_register_ip_with_terms]

⚠️ The agent wants to execute a sensitive blockchain operation.
Do you approve? Type 'y' to continue; otherwise, explain your requested changes.
> y
[Executes the blockchain transaction]
```

#### 3. Create NFT Collection (Sensitive Operation)
```
User: Create an NFT collection called "My Story Collection"
Assistant: I'll help you create an NFT collection...
[Routes to NFTClient specialist]

⚠️ The agent wants to execute a sensitive blockchain operation.
Do you approve? Type 'y' to continue; otherwise, explain your requested changes.
> Actually, make it "My Amazing Collection" instead
[Agent adjusts based on feedback]
```

#### 4. Query License Terms (Safe Operation)
```
User: What are the license terms for IP asset 0x123...?
Assistant: Let me look up the license terms for that IP asset...
[Executes get_license_terms without confirmation]
```

## Key Features

### 🔒 Safe vs Sensitive Operations

**Safe (No Confirmation):**
- `get_erc20_token_balance`
- `get_license_terms`
- `get_license_minting_fee`
- `get_license_revenue_share`
- `get_spg_nft_contract_minting_fee_and_token`

**Sensitive (Requires Confirmation):**
- All blockchain write operations
- Token minting and transfers
- IP registration and updates
- License minting
- Royalty payments
- Dispute raising

### 🤖 Specialized Assistants

The agent automatically routes to the appropriate specialist based on your request:
- **Dispute**: Handles IP disputes
- **IPAccount**: Manages IP account operations
- **IPAsset**: Registers and manages IP assets
- **License**: Creates and manages licenses
- **NFTClient**: Creates NFT collections
- **Royalty**: Handles royalty payments and claims
- **WIP**: Manages WIP token operations

### 🔄 Interrupt and Resume

When a sensitive operation is requested:
1. The agent prepares the transaction
2. Shows you what will be executed
3. Asks for your confirmation
4. You can:
   - Type `y` to approve
   - Provide feedback to modify the action
   - Cancel the operation

## Troubleshooting

### "OPENAI_API_KEY not set!"
```bash
export OPENAI_API_KEY="sk-..."
```
Or create a `.env` file with:
```
OPENAI_API_KEY=sk-...

### "Error initializing MCP"
Make sure the Story SDK MCP server is accessible. The agent needs access to:
- `/story-sdk-mcp/server.py`

### Import Errors
Install dependencies:
```bash
pip3 install -e "."
```

### "No module named 'langchain_openai'"
```bash
pip3 install langchain-openai langgraph langchain-core langchain-mcp-adapters python-dotenv
```

## Exit the Agent

Type any of these commands:
- `quit`
- `exit`
- `q`
- Press `Ctrl+C`