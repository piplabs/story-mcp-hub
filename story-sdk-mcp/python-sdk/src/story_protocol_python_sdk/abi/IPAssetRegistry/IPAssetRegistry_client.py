
import json
import os
from web3 import Web3

class IPAssetRegistryClient:
    def __init__(self, web3: Web3):
        self.web3 = web3
        # Assuming config.json is located at the root of the project
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'config.json'))
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        contract_address = None
        for contract in config['contracts']:
            if contract['contract_name'] == 'IPAssetRegistry':
                contract_address = contract['contract_address']
                break
        if not contract_address:
            raise ValueError(f"Contract address for IPAssetRegistry not found in config.json")
        abi_path = os.path.join(os.path.dirname(__file__), '..', '..', 'abi', 'jsons', 'IPAssetRegistry.json')
        with open(abi_path, 'r') as abi_file:
            abi = json.load(abi_file)
        self.contract = self.web3.eth.contract(address=contract_address, abi=abi)
    
    def register(self, chainid, tokenContract, tokenId):
        return self.contract.functions.register(chainid, tokenContract, tokenId).transact()
        
    def build_register_transaction(self, chainid, tokenContract, tokenId, tx_params):
        return self.contract.functions.register(chainid, tokenContract, tokenId).build_transaction(tx_params)
    
    def ipId(self, chainId, tokenContract, tokenId):
        return self.contract.functions.ipId(chainId, tokenContract, tokenId).call()
    
    def isRegistered(self, id):
        return self.contract.functions.isRegistered(id).call()
        
    