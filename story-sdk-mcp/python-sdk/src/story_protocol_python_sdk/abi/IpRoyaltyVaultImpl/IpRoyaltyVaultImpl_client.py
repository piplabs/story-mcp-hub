
import json
import os
from web3 import Web3

class IpRoyaltyVaultImplClient:
    def __init__(self, web3: Web3, contract_address=None):
        self.web3 = web3
        abi_path = os.path.join(os.path.dirname(__file__), '..', '..', 'abi', 'jsons', 'IpRoyaltyVaultImpl.json')
        with open(abi_path, 'r') as abi_file:
            abi = json.load(abi_file)
        self.contract = self.web3.eth.contract(address=contract_address, abi=abi)
    
    def balanceOf(self, account):
        return self.contract.functions.balanceOf(account).call()
    
    def claimableRevenue(self, claimer, token):
        return self.contract.functions.claimableRevenue(claimer, token).call()
    
    def ipId(self):
        return self.contract.functions.ipId().call()
        
    