
import json
import os
from web3 import Web3

class LicensingModuleClient:
    def __init__(self, web3: Web3):
        self.web3 = web3
        # Assuming config.json is located at the root of the project
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'config.json'))
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        contract_address = None
        for contract in config['contracts']:
            if contract['contract_name'] == 'LicensingModule':
                contract_address = contract['contract_address']
                break
        if not contract_address:
            raise ValueError(f"Contract address for LicensingModule not found in config.json")
        abi_path = os.path.join(os.path.dirname(__file__), '..', '..', 'abi', 'jsons', 'LicensingModule.json')
        with open(abi_path, 'r') as abi_file:
            abi = json.load(abi_file)
        self.contract = self.web3.eth.contract(address=contract_address, abi=abi)
    
    def attachLicenseTerms(self, ipId, licenseTemplate, licenseTermsId):
        return self.contract.functions.attachLicenseTerms(ipId, licenseTemplate, licenseTermsId).transact()
        
    def build_attachLicenseTerms_transaction(self, ipId, licenseTemplate, licenseTermsId, tx_params):
        return self.contract.functions.attachLicenseTerms(ipId, licenseTemplate, licenseTermsId).build_transaction(tx_params)
    
    def mintLicenseTokens(self, licensorIpId, licenseTemplate, licenseTermsId, amount, receiver, royaltyContext, maxMintingFee, maxRevenueShare):
        return self.contract.functions.mintLicenseTokens(licensorIpId, licenseTemplate, licenseTermsId, amount, receiver, royaltyContext, maxMintingFee, maxRevenueShare).transact()
        
    def build_mintLicenseTokens_transaction(self, licensorIpId, licenseTemplate, licenseTermsId, amount, receiver, royaltyContext, maxMintingFee, maxRevenueShare, tx_params):
        return self.contract.functions.mintLicenseTokens(licensorIpId, licenseTemplate, licenseTermsId, amount, receiver, royaltyContext, maxMintingFee, maxRevenueShare).build_transaction(tx_params)
    
    def registerDerivative(self, childIpId, parentIpIds, licenseTermsIds, licenseTemplate, royaltyContext, maxMintingFee, maxRts, maxRevenueShare):
        return self.contract.functions.registerDerivative(childIpId, parentIpIds, licenseTermsIds, licenseTemplate, royaltyContext, maxMintingFee, maxRts, maxRevenueShare).transact()
        
    def build_registerDerivative_transaction(self, childIpId, parentIpIds, licenseTermsIds, licenseTemplate, royaltyContext, maxMintingFee, maxRts, maxRevenueShare, tx_params):
        return self.contract.functions.registerDerivative(childIpId, parentIpIds, licenseTermsIds, licenseTemplate, royaltyContext, maxMintingFee, maxRts, maxRevenueShare).build_transaction(tx_params)
    
    def registerDerivativeWithLicenseTokens(self, childIpId, licenseTokenIds, royaltyContext, maxRts):
        return self.contract.functions.registerDerivativeWithLicenseTokens(childIpId, licenseTokenIds, royaltyContext, maxRts).transact()
        
    def build_registerDerivativeWithLicenseTokens_transaction(self, childIpId, licenseTokenIds, royaltyContext, maxRts, tx_params):
        return self.contract.functions.registerDerivativeWithLicenseTokens(childIpId, licenseTokenIds, royaltyContext, maxRts).build_transaction(tx_params)
    
    def setLicensingConfig(self, ipId, licenseTemplate, licenseTermsId, licensingConfig):
        return self.contract.functions.setLicensingConfig(ipId, licenseTemplate, licenseTermsId, licensingConfig).transact()
        
    def build_setLicensingConfig_transaction(self, ipId, licenseTemplate, licenseTermsId, licensingConfig, tx_params):
        return self.contract.functions.setLicensingConfig(ipId, licenseTemplate, licenseTermsId, licensingConfig).build_transaction(tx_params)
    
    def predictMintingLicenseFee(self, licensorIpId, licenseTemplate, licenseTermsId, amount, receiver, royaltyContext):
        return self.contract.functions.predictMintingLicenseFee(licensorIpId, licenseTemplate, licenseTermsId, amount, receiver, royaltyContext).call()
        
    