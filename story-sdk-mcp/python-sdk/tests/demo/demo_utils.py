# Mock ERC721 contract address
MockERC721 = "0xa1119092ea911202E0a65B743a13AE28C5CF2f21"

# Mock ERC20 contract address (same as used in TypeScript tests)
MockERC20 = "0xF2104833d386a2734a4eB3B8ad6FC6812F29E38E"

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
ROYALTY_POLICY="0xBe54FB168b3c982b7AaE60dB6CF75Bd8447b390E" #Royalty Policy LAP
ROYALTY_MODULE="0xD2f60c40fEbccf6311f8B47c4f2Ec6b040400086"
PIL_LICENSE_TEMPLATE="0x2E896b0b2Fdb7457499B56AAaA4AE55BCB4Cd316"

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
