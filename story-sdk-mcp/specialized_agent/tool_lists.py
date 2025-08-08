# Define explicit tool lists for each specialist based on the available MCP tools

# Safe tools - read-only operations that don't modify blockchain state
dispute_safe_tools = []

ipaccount_safe_tools = [
    "get_erc20_token_balance",
]

ipasset_safe_tools = []

license_safe_tools = [
    "get_license_terms",
    "get_license_minting_fee", 
    "get_license_revenue_share",
]

nftclient_safe_tools = [
    "get_spg_nft_contract_minting_fee_and_token",
]

royalty_safe_tools = []

wip_safe_tools = []

# Sensitive tools - write operations that modify blockchain state and need confirmation
dispute_sensitive_tools = [
    "raise_dispute",
]

ipaccount_sensitive_tools = [
    "mint_test_erc20_tokens",
]

ipasset_sensitive_tools = [
    "mint_and_register_ip_with_terms",
    "register", 
    "upload_image_to_ipfs",
    "create_ip_metadata",
    "attach_license_terms",
]

license_sensitive_tools = [
    "mint_license_tokens",
]

nftclient_sensitive_tools = [
    "create_spg_nft_collection",
]

royalty_sensitive_tools = [
    "pay_royalty_on_behalf",
    "claim_all_revenue",
]

wip_sensitive_tools = [
    "deposit_wip",
    "transfer_wip",
]

# Map specialists to their tool lists
SPECIALIST_TOOL_MAPPING = {
    "dispute": {
        "safe_tools": dispute_safe_tools,
        "sensitive_tools": dispute_sensitive_tools
    },
    "ipaccount": {
        "safe_tools": ipaccount_safe_tools,
        "sensitive_tools": ipaccount_sensitive_tools
    },
    "ipasset": {
        "safe_tools": ipasset_safe_tools,
        "sensitive_tools": ipasset_sensitive_tools
    },
    "license": {
        "safe_tools": license_safe_tools,
        "sensitive_tools": license_sensitive_tools
    },
    "nftclient": {
        "safe_tools": nftclient_safe_tools,
        "sensitive_tools": nftclient_sensitive_tools
    },
    "royalty": {
        "safe_tools": royalty_safe_tools,
        "sensitive_tools": royalty_sensitive_tools
    },
    "wip": {
        "safe_tools": wip_safe_tools,
        "sensitive_tools": wip_sensitive_tools
    }
}