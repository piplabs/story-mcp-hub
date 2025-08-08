# Story Protocol Specialized Agent System

## Phase 1: LangGraph Tutorial Implementation

This implementation follows the exact patterns from the LangGraph Customer Support Bot tutorial (Parts 2-4), adapted for Story Protocol operations.

### Architecture Overview

**Key Patterns Implemented:**
- **interrupt_before**: User confirmation required before sensitive blockchain operations  
- **Dialog state tracking**: Tracks which specialist is active with `dialog_state` field
- **5-node specialist pattern**: `enter` → `assistant` → `safe_tools` → `sensitive_tools` → `leave`
- **Tool categorization**: Explicit safe vs sensitive tool lists per specialist
- **Entry nodes**: ToolMessage announcing specialist takeover
- **CompleteOrEscalate**: Return control to primary assistant

### Specialist Domains

Each specialist handles specific Story Protocol operations:

1. **Dispute**: `raise_dispute`
2. **IPAccount**: `get_erc20_token_balance`, `mint_test_erc20_tokens`  
3. **IPAsset**: `mint_and_register_ip_with_terms`, `register`, `upload_image_to_ipfs`, `create_ip_metadata`
4. **License**: `get_license_terms`, `mint_license_tokens`, `attach_license_terms`
5. **NFTClient**: `create_spg_nft_collection`, `get_spg_nft_contract_minting_fee_and_token`
6. **Royalty**: `pay_royalty_on_behalf`, `claim_all_revenue`
7. **WIP**: `deposit_wip`, `transfer_wip`

### Tool Safety Classification

**Safe Tools** (no confirmation needed):
- `get_erc20_token_balance`
- `get_license_terms` 
- `get_license_minting_fee`
- `get_license_revenue_share`
- `get_spg_nft_contract_minting_fee_and_token`

**Sensitive Tools** (require confirmation):
- All blockchain write operations (mint, register, transfer, etc.)
- All operations that spend tokens or gas

### State Configuration

```python
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: str
    wallet_address: str  # Pre-configured: 0xeC2E8ae2F6c9BE6C876629198Cc554c17e9Ff2C4
    dialog_state: Annotated[list[Literal[...]], update_dialog_stack]
```

### File Structure

```
specialized-agent/
├── __init__.py
├── README.md
├── main.py                 # Terminal test runner
├── state.py               # State management with dialog_state
├── assistant.py           # Base Assistant class  
├── tools.py              # CompleteOrEscalate tool
├── tool_lists.py         # Explicit safe/sensitive tool mappings
├── utils.py              # Entry node utility functions
├── primary_assistant.py  # Primary routing assistant
├── graph.py              # Main LangGraph assembly
└── specialists/          # Individual specialist implementations
    ├── __init__.py
    ├── dispute.py
    ├── ipaccount.py
    ├── ipasset.py
    ├── license.py
    ├── nftclient.py
    ├── royalty.py
    └── wip.py
```

### Usage (Phase 1)

```bash
# Run terminal demo
cd /Users/zizhuoliu/Desktop/Story/story-mcp-hub/story-sdk-mcp
python -m specialized-agent.main
```

### Key Features

✅ **Exact Tutorial Implementation**: Follows LangGraph docs patterns precisely  
✅ **Interrupt Before Confirmation**: All sensitive tools require user approval  
✅ **Dialog State Tracking**: Maintains context across specialist handoffs  
✅ **Explicit Tool Lists**: No pattern matching, explicit safe/sensitive categorization  
✅ **Wallet Pre-configuration**: Uses provided wallet address `0xeC2E8ae2F6c9BE6C876629198Cc554c17e9Ff2C4`  
✅ **Terminal Interface**: Phase 1 testing without API dependencies  

### Next Steps (Phase 2)

- Integrate actual MCP tool calls (currently placeholder)
- Add API endpoint integration  
- Implement wallet connection handling
- Add transaction confirmation UI
- Extend with more specialized workflows

### Technical Notes

- **Memory**: Uses `InMemorySaver` for checkpointing
- **LLM**: Claude Sonnet 3 for assistant reasoning
- **Interrupts**: `interrupt_before` on all `*_sensitive_tools` nodes
- **Routing**: Primary assistant delegates based on user intent detection
- **Error Handling**: Graceful fallback with CompleteOrEscalate

This implementation provides the foundation for a production Story Protocol assistant system with proper user confirmation flows and specialized domain handling.