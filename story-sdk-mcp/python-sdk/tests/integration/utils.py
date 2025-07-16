from web3 import Web3
from dotenv import load_dotenv
from src.story_protocol_python_sdk.story_client import StoryClient
import os
import hashlib
import base58

load_dotenv()

# Mock ERC721 contract address
MockERC721 = "0xa1119092ea911202E0a65B743a13AE28C5CF2f21"

# Mock ERC20 contract address (same as used in TypeScript tests)
MockERC20 = "0xF2104833d386a2734a4eB3B8ad6FC6812F29E38E"

WIP_TOKEN_ADDRESS = "0x1514000000000000000000000000000000000000";
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
ROYALTY_POLICY="0xBe54FB168b3c982b7AaE60dB6CF75Bd8447b390E" #Royalty Policy LAP
ROYALTY_MODULE="0xD2f60c40fEbccf6311f8B47c4f2Ec6b040400086"
PIL_LICENSE_TEMPLATE="0x2E896b0b2Fdb7457499B56AAaA4AE55BCB4Cd316"
ARBITRATION_POLICY_UMA="0xfFD98c3877B8789124f02C7E8239A4b0Ef11E936"
EVEN_SPLIT_GROUP_POOL="0xf96f2c30b41Cb6e0290de43C8528ae83d4f33F89"
ROYALTY_POLICY_LRP="0x9156e603C949481883B1d3355c6f1132D191fC41"
CORE_METADATA_MODULE="0x6E81a25C99C6e8430aeC7353325EB138aFE5DC16"

def get_story_client_in_sepolia(web3: Web3, account) -> StoryClient:
    chain_id = 11155111  # Sepolia chain ID
    return StoryClient(web3, account, chain_id)

def get_story_client_in_iliad(web3: Web3, account) -> StoryClient:
    chain_id = 1513  # Sepolia chain ID
    return StoryClient(web3, account, chain_id)

def get_story_client_in_odyssey(web3: Web3, account) -> StoryClient:
    chain_id = 1516  # Odyssey chain ID
    return StoryClient(web3, account, chain_id)

def get_story_client_in_devnet(web3: Web3, account) -> StoryClient:
    chain_id = 1315  # Devnet chain ID
    return StoryClient(web3, account, chain_id)

def get_token_id(nft_contract, web3, account):
    contract_abi = [
        {
            "inputs": [{"internalType": "address", "name": "to", "type": "address"}],
            "name": "mint",
            "outputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]

    contract = web3.eth.contract(address=nft_contract, abi=contract_abi)
    
    try:
        transaction = contract.functions.mint(account.address).build_transaction({
            'from': account.address,
            'nonce': web3.eth.get_transaction_count(account.address),
            'gas': 2000000
        })

        signed_txn = account.sign_transaction(transaction)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        logs = tx_receipt['logs']
        if len(logs) > 0 and len(logs[0]['topics']) > 3:
            return int(logs[0]['topics'][3].hex(), 16)
        raise ValueError(f"No token ID in logs: {tx_receipt}")
        
    except Exception as e:
        raise e

def mint_by_spg(nft_contract, web3, account, metadata_uri=""):
    contract_abi = [
        {
            "inputs": [
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "string", "name": "nftMetadataURI", "type": "string"},
                {"internalType": "bytes32", "name": "nftMetadataHash", "type": "bytes32"},
                {"internalType": "bool", "name": "allowDuplicates", "type": "bool"}
            ],
            "name": "mint",
            "outputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]

    contract = web3.eth.contract(address=nft_contract, abi=contract_abi)
    
    try:
        zero_hash = '0x' + '0' * 64
        transaction = contract.functions.mint(
            account.address,
            metadata_uri,
            zero_hash,
            True
        ).build_transaction({
            'from': account.address,
            'nonce': web3.eth.get_transaction_count(account.address),
            'gas': 2000000
        })

        signed_txn = account.sign_transaction(transaction)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        logs = tx_receipt['logs']
        if len(logs) > 0 and len(logs[0]['topics']) > 3:
            return int(logs[0]['topics'][3].hex(), 16)
        raise ValueError(f"No token ID in logs: {tx_receipt}")
        
    except Exception as e:
        raise e

def mint_tokens(erc20_contract_address, web3, account, to_address, amount):
    contract_abi = [
        {
            "inputs": [
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"}
            ],
            "name": "mint",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]

    contract = web3.eth.contract(address=erc20_contract_address, abi=contract_abi)
    transaction = contract.functions.mint(to_address, amount).build_transaction({
        'from': account.address,
        'nonce': web3.eth.get_transaction_count(account.address),
        'gas': 2000000,
        'gasPrice': web3.to_wei('300', 'gwei')
    })
    
    signed_txn = account.sign_transaction(transaction)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    
    return tx_receipt

def approve(erc20_contract_address, web3, account, spender_address, amount):
    erc20_contract_address = web3.to_checksum_address(erc20_contract_address)
    spender_address = web3.to_checksum_address(spender_address)

    contract_abi = [
        {
            "inputs": [
                {"internalType": "address", "name": "spender", "type": "address"},
                {"internalType": "uint256", "name": "value", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [
                {"internalType": "bool", "name": "", "type": "bool"}
            ],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]

    contract = web3.eth.contract(address=erc20_contract_address, abi=contract_abi)
    transaction = contract.functions.approve(spender_address, amount).build_transaction({
        'from': account.address,
        'nonce': web3.eth.get_transaction_count(account.address),
        'gas': 2000000,
        'gasPrice': web3.to_wei('300', 'gwei')
    })
    
    signed_txn = account.sign_transaction(transaction)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    
    return tx_receipt

def get_block_timestamp(web3):
    return (web3.eth.get_block('latest'))['timestamp']

def check_event_in_tx(web3, tx_hash: str, event_text: str) -> bool:
    tx_receipt = web3.eth.get_transaction_receipt(tx_hash)
    event_signature = web3.keccak(text=event_text).hex()

    for log in tx_receipt['logs']:
        if log['topics'][0].hex() == event_signature:
            return True

    return False

def generate_cid() -> str:
    """Generate a random CIDv0 for testing purposes"""
    # Generate random bytes
    random_bytes = os.urandom(32)
    # Hash using SHA-256
    sha256_hash = hashlib.sha256(random_bytes).digest()
    # Construct CIDv0 (SHA-256 + multihash prefix)
    multihash = bytes([0x12, 0x20]) + sha256_hash
    # Base58 encode
    return base58.b58encode(multihash).decode('utf-8')

def setup_royalty_vault(story_client, parent_ip_id, account):
    parent_ip_royalty_address = story_client.Royalty.getRoyaltyVaultAddress(parent_ip_id)

    transfer_data = story_client.Royalty.ip_royalty_vault_client.contract.encode_abi(
        abi_element_identifier="transfer",
        args=[account.address, 10 * 10 ** 6]
    )

    response = story_client.IPAccount.execute(
        to=parent_ip_royalty_address,
        value=0,
        ip_id=parent_ip_id,
        data=transfer_data
    )

    return response
