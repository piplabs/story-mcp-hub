
import json
import os
from web3 import Web3

class RegistrationWorkflowsClient:
    def __init__(self, web3: Web3):
        self.web3 = web3
        # Assuming config.json is located at the root of the project
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'config.json'))
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        contract_address = None
        for contract in config['contracts']:
            if contract['contract_name'] == 'RegistrationWorkflows':
                contract_address = contract['contract_address']
                break
        if not contract_address:
            raise ValueError(f"Contract address for RegistrationWorkflows not found in config.json")
        abi_path = os.path.join(os.path.dirname(__file__), '..', '..', 'abi', 'jsons', 'RegistrationWorkflows.json')
        with open(abi_path, 'r') as abi_file:
            abi = json.load(abi_file)
        self.contract = self.web3.eth.contract(address=contract_address, abi=abi)
    
    def createCollection(self, spgNftInitParams):
        return self.contract.functions.createCollection(spgNftInitParams).transact()
        
    def build_createCollection_transaction(self, spgNftInitParams, tx_params):
        return self.contract.functions.createCollection(spgNftInitParams).build_transaction(tx_params)
    
    def mintAndRegisterIp(self, spgNftContract, recipient, ipMetadata, allowDuplicates):
        return self.contract.functions.mintAndRegisterIp(spgNftContract, recipient, ipMetadata, allowDuplicates).transact()
        
    def build_mintAndRegisterIp_transaction(self, spgNftContract, recipient, ipMetadata, allowDuplicates, tx_params):
        return self.contract.functions.mintAndRegisterIp(spgNftContract, recipient, ipMetadata, allowDuplicates).build_transaction(tx_params)
    
    def multicall(self, data):
        return self.contract.functions.multicall(data).transact()
        
    def build_multicall_transaction(self, data, tx_params):
        return self.contract.functions.multicall(data).build_transaction(tx_params)
    
    def registerIp(self, nftContract, tokenId, ipMetadata, sigMetadata):
        return self.contract.functions.registerIp(nftContract, tokenId, ipMetadata, sigMetadata).transact()
        
    def build_registerIp_transaction(self, nftContract, tokenId, ipMetadata, sigMetadata, tx_params):
        return self.contract.functions.registerIp(nftContract, tokenId, ipMetadata, sigMetadata).build_transaction(tx_params)
    
    