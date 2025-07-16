
import json
import os
from web3 import Web3

class RoyaltyModuleClient:
    def __init__(self, web3: Web3):
        self.web3 = web3
        # Assuming config.json is located at the root of the project
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'config.json'))
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        contract_address = None
        for contract in config['contracts']:
            if contract['contract_name'] == 'RoyaltyModule':
                contract_address = contract['contract_address']
                break
        if not contract_address:
            raise ValueError(f"Contract address for RoyaltyModule not found in config.json")
        abi_path = os.path.join(os.path.dirname(__file__), '..', '..', 'abi', 'jsons', 'RoyaltyModule.json')
        with open(abi_path, 'r') as abi_file:
            abi = json.load(abi_file)
        self.contract = self.web3.eth.contract(address=contract_address, abi=abi)
    
    def payRoyaltyOnBehalf(self, receiverIpId, payerIpId, token, amount):
        return self.contract.functions.payRoyaltyOnBehalf(receiverIpId, payerIpId, token, amount).transact()
        
    def build_payRoyaltyOnBehalf_transaction(self, receiverIpId, payerIpId, token, amount, tx_params):
        return self.contract.functions.payRoyaltyOnBehalf(receiverIpId, payerIpId, token, amount).build_transaction(tx_params)
    
    def ipRoyaltyVaults(self, ipId):
        return self.contract.functions.ipRoyaltyVaults(ipId).call()
    
    def isWhitelistedRoyaltyPolicy(self, royaltyPolicy):
        return self.contract.functions.isWhitelistedRoyaltyPolicy(royaltyPolicy).call()
    
    def isWhitelistedRoyaltyToken(self, token):
        return self.contract.functions.isWhitelistedRoyaltyToken(token).call()
        
    