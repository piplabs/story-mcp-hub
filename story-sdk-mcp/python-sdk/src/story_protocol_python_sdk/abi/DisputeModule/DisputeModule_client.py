
import json
import os
from web3 import Web3

class DisputeModuleClient:
    def __init__(self, web3: Web3):
        self.web3 = web3
        # Assuming config.json is located at the root of the project
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'config.json'))
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        contract_address = None
        for contract in config['contracts']:
            if contract['contract_name'] == 'DisputeModule':
                contract_address = contract['contract_address']
                break
        if not contract_address:
            raise ValueError(f"Contract address for DisputeModule not found in config.json")
        abi_path = os.path.join(os.path.dirname(__file__), '..', '..', 'abi', 'jsons', 'DisputeModule.json')
        with open(abi_path, 'r') as abi_file:
            abi = json.load(abi_file)
        self.contract = self.web3.eth.contract(address=contract_address, abi=abi)
    
    def cancelDispute(self, disputeId, data):
        return self.contract.functions.cancelDispute(disputeId, data).transact()
        
    def build_cancelDispute_transaction(self, disputeId, data, tx_params):
        return self.contract.functions.cancelDispute(disputeId, data).build_transaction(tx_params)
    
    def raiseDispute(self, targetIpId, disputeEvidenceHash, targetTag, data):
        return self.contract.functions.raiseDispute(targetIpId, disputeEvidenceHash, targetTag, data).transact()
        
    def build_raiseDispute_transaction(self, targetIpId, disputeEvidenceHash, targetTag, data, tx_params):
        return self.contract.functions.raiseDispute(targetIpId, disputeEvidenceHash, targetTag, data).build_transaction(tx_params)
    
    def resolveDispute(self, disputeId, data):
        return self.contract.functions.resolveDispute(disputeId, data).transact()
        
    def build_resolveDispute_transaction(self, disputeId, data, tx_params):
        return self.contract.functions.resolveDispute(disputeId, data).build_transaction(tx_params)
    
    def isWhitelistedDisputeTag(self, tag):
        return self.contract.functions.isWhitelistedDisputeTag(tag).call()
        
    