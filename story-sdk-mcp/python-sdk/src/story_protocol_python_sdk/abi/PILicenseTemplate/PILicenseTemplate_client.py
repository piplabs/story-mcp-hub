
import json
import os
from web3 import Web3

class PILicenseTemplateClient:
    def __init__(self, web3: Web3):
        self.web3 = web3
        # Assuming config.json is located at the root of the project
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'config.json'))
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        contract_address = None
        for contract in config['contracts']:
            if contract['contract_name'] == 'PILicenseTemplate':
                contract_address = contract['contract_address']
                break
        if not contract_address:
            raise ValueError(f"Contract address for PILicenseTemplate not found in config.json")
        abi_path = os.path.join(os.path.dirname(__file__), '..', '..', 'abi', 'jsons', 'PILicenseTemplate.json')
        with open(abi_path, 'r') as abi_file:
            abi = json.load(abi_file)
        self.contract = self.web3.eth.contract(address=contract_address, abi=abi)
    
    def registerLicenseTerms(self, terms):
        return self.contract.functions.registerLicenseTerms(terms).transact()
        
    def build_registerLicenseTerms_transaction(self, terms, tx_params):
        return self.contract.functions.registerLicenseTerms(terms).build_transaction(tx_params)
    
    def exists(self, licenseTermsId):
        return self.contract.functions.exists(licenseTermsId).call()
    
    def getLicenseTerms(self, selectedLicenseTermsId):
        return self.contract.functions.getLicenseTerms(selectedLicenseTermsId).call()
    
    def getLicenseTermsId(self, terms):
        return self.contract.functions.getLicenseTermsId(terms).call()
        
    