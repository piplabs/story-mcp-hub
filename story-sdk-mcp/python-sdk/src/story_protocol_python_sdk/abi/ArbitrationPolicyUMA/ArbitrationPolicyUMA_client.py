
import json
import os
from web3 import Web3

class ArbitrationPolicyUMAClient:
    def __init__(self, web3: Web3):
        self.web3 = web3
        # Assuming config.json is located at the root of the project
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'config.json'))
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        contract_address = None
        for contract in config['contracts']:
            if contract['contract_name'] == 'ArbitrationPolicyUMA':
                contract_address = contract['contract_address']
                break
        if not contract_address:
            raise ValueError(f"Contract address for ArbitrationPolicyUMA not found in config.json")
        abi_path = os.path.join(os.path.dirname(__file__), '..', '..', 'abi', 'jsons', 'ArbitrationPolicyUMA.json')
        with open(abi_path, 'r') as abi_file:
            abi = json.load(abi_file)
        self.contract = self.web3.eth.contract(address=contract_address, abi=abi)
    
    def disputeIdToAssertionId(self, disputeId):
        return self.contract.functions.disputeIdToAssertionId(disputeId).call()
    
    def maxBonds(self, token):
        return self.contract.functions.maxBonds(token).call()
    
    def maxLiveness(self):
        return self.contract.functions.maxLiveness().call()
    
    def minLiveness(self):
        return self.contract.functions.minLiveness().call()
    
    def oov3(self):
        return self.contract.functions.oov3().call()
        
    