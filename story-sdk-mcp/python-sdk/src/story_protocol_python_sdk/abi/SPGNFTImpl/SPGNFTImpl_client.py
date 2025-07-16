
import json
import os
from web3 import Web3

class SPGNFTImplClient:
    def __init__(self, web3: Web3, contract_address=None):
        self.web3 = web3
        abi_path = os.path.join(os.path.dirname(__file__), '..', '..', 'abi', 'jsons', 'SPGNFTImpl.json')
        with open(abi_path, 'r') as abi_file:
            abi = json.load(abi_file)
        self.contract = self.web3.eth.contract(address=contract_address, abi=abi)
    
    def mintFee(self):
        return self.contract.functions.mintFee().call()
    
    def mintFeeToken(self):
        return self.contract.functions.mintFeeToken().call()
        
    