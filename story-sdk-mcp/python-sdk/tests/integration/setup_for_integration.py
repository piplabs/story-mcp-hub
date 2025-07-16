import os
import sys
import pytest
from dotenv import load_dotenv
from web3 import Web3

# Ensure the src directory is in the Python path
current_dir = os.path.dirname(__file__)
src_path = os.path.abspath(os.path.join(current_dir, '..', '..'))
if src_path not in sys.path:
    sys.path.append(src_path)

# Import everything from utils
from utils import (
    get_story_client_in_devnet,
    get_token_id,
    mint_tokens,
    approve,
    get_block_timestamp,
    check_event_in_tx,
    MockERC721,
    MockERC20,
    ZERO_ADDRESS,
    ROYALTY_POLICY,
    ROYALTY_MODULE,
    PIL_LICENSE_TEMPLATE,
    ARBITRATION_POLICY_UMA,
    generate_cid,
    WIP_TOKEN_ADDRESS,
    setup_royalty_vault,
    EVEN_SPLIT_GROUP_POOL,
    ROYALTY_POLICY_LRP,
    CORE_METADATA_MODULE,
    mint_by_spg
)

# Load environment variables
load_dotenv(override=True)
private_key = os.getenv('WALLET_PRIVATE_KEY')
private_key_2 = os.getenv('WALLET_PRIVATE_KEY_2')
rpc_url = os.getenv('RPC_PROVIDER_URL')
wallet_address = os.getenv('WALLET_ADDRESS')
wallet_address_2 = os.getenv('WALLET_ADDRESS_2')

if not private_key:
    raise ValueError("WALLET_PRIVATE_KEY environment variable is not set")
if not rpc_url:
    raise ValueError("RPC_PROVIDER_URL environment variable is not set")

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(rpc_url))
if not web3.is_connected():
    raise Exception("Failed to connect to Web3 provider")

# Set up the account with the private key
account = web3.eth.account.from_key(private_key)
account_2 = web3.eth.account.from_key(private_key_2)

@pytest.fixture(scope="session")
def story_client():
    return get_story_client_in_devnet(web3, account)

@pytest.fixture(scope="session")
def story_client_2():
    return get_story_client_in_devnet(web3, account_2)

# Export everything needed by test files
__all__ = [
    'web3',
    'account',
    'account_2',
    'story_client',
    'get_token_id',
    'mint_tokens',
    'approve',
    'get_block_timestamp',
    'check_event_in_tx',
    'MockERC721',
    'MockERC20',
    'ZERO_ADDRESS',
    'ROYALTY_POLICY'
    'ROYALTY_MODULE',   
    'PIL_LICENSE_TEMPLATE',
    'ARBITRATION_POLICY_UMA',
    'account_2',
    'story_client_2',
    'generate_cid',
    'setup_royalty_vault',
    'WIP_TOKEN_ADDRESS',
    'wallet_address',
    'wallet_address_2',
    'private_key',
    'private_key_2',
    'EVEN_SPLIT_GROUP_POOL',
    'ROYALTY_POLICY_LRP',
    'mint_by_spg'
]