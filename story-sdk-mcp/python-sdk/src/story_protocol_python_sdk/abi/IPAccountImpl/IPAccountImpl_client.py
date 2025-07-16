
import json
import os
from web3 import Web3

class IPAccountImplClient:
    def __init__(self, web3: Web3, contract_address=None):
        self.web3 = web3
        abi_path = os.path.join(os.path.dirname(__file__), '..', '..', 'abi', 'jsons', 'IPAccountImpl.json')
        with open(abi_path, 'r') as abi_file:
            abi = json.load(abi_file)
        self.contract = self.web3.eth.contract(address=contract_address, abi=abi)
    
    def execute(self, to, value, data, operation):
        return self.contract.functions.execute(to, value, data, operation).transact()
        
    def build_execute_transaction(self, to, value, data, operation, tx_params):
        return self.contract.functions.execute(to, value, data, operation).build_transaction(tx_params)
    
    def execute2(self, to, value, data):
        return self.contract.functions.execute(to, value, data).transact()
        
    def build_execute2_transaction(self, to, value, data, tx_params):
        return self.contract.functions.execute(to, value, data).build_transaction(tx_params)
    
    def executeBatch(self, calls, operation):
        return self.contract.functions.executeBatch(calls, operation).transact()
        
    def build_executeBatch_transaction(self, calls, operation, tx_params):
        return self.contract.functions.executeBatch(calls, operation).build_transaction(tx_params)
    
    def executeWithSig(self, to, value, data, signer, deadline, signature):
        return self.contract.functions.executeWithSig(to, value, data, signer, deadline, signature).transact()
        
    def build_executeWithSig_transaction(self, to, value, data, signer, deadline, signature, tx_params):
        return self.contract.functions.executeWithSig(to, value, data, signer, deadline, signature).build_transaction(tx_params)
    
    def owner(self):
        return self.contract.functions.owner().call()
    
    def state(self):
        return self.contract.functions.state().call()
    
    def token(self):
        return self.contract.functions.token().call()
        
    