
import json
import os
from web3 import Web3

class RoyaltyTokenDistributionWorkflowsClient:
    def __init__(self, web3: Web3):
        self.web3 = web3
        # Assuming config.json is located at the root of the project
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'config.json'))
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        contract_address = None
        for contract in config['contracts']:
            if contract['contract_name'] == 'RoyaltyTokenDistributionWorkflows':
                contract_address = contract['contract_address']
                break
        if not contract_address:
            raise ValueError(f"Contract address for RoyaltyTokenDistributionWorkflows not found in config.json")
        abi_path = os.path.join(os.path.dirname(__file__), '..', '..', 'abi', 'jsons', 'RoyaltyTokenDistributionWorkflows.json')
        with open(abi_path, 'r') as abi_file:
            abi = json.load(abi_file)
        self.contract = self.web3.eth.contract(address=contract_address, abi=abi)
    
    def distributeRoyaltyTokens(self, ipId, royaltyShares, sigApproveRoyaltyTokens):
        return self.contract.functions.distributeRoyaltyTokens(ipId, royaltyShares, sigApproveRoyaltyTokens).transact()
        
    def build_distributeRoyaltyTokens_transaction(self, ipId, royaltyShares, sigApproveRoyaltyTokens, tx_params):
        return self.contract.functions.distributeRoyaltyTokens(ipId, royaltyShares, sigApproveRoyaltyTokens).build_transaction(tx_params)
    
    def mintAndRegisterIpAndAttachPILTermsAndDistributeRoyaltyTokens(self, spgNftContract, recipient, ipMetadata, licenseTermsData, royaltyShares, allowDuplicates):
        return self.contract.functions.mintAndRegisterIpAndAttachPILTermsAndDistributeRoyaltyTokens(spgNftContract, recipient, ipMetadata, licenseTermsData, royaltyShares, allowDuplicates).transact()
        
    def build_mintAndRegisterIpAndAttachPILTermsAndDistributeRoyaltyTokens_transaction(self, spgNftContract, recipient, ipMetadata, licenseTermsData, royaltyShares, allowDuplicates, tx_params):
        return self.contract.functions.mintAndRegisterIpAndAttachPILTermsAndDistributeRoyaltyTokens(spgNftContract, recipient, ipMetadata, licenseTermsData, royaltyShares, allowDuplicates).build_transaction(tx_params)
    
    def mintAndRegisterIpAndMakeDerivativeAndDistributeRoyaltyTokens(self, spgNftContract, recipient, ipMetadata, derivData, royaltyShares, allowDuplicates):
        return self.contract.functions.mintAndRegisterIpAndMakeDerivativeAndDistributeRoyaltyTokens(spgNftContract, recipient, ipMetadata, derivData, royaltyShares, allowDuplicates).transact()
        
    def build_mintAndRegisterIpAndMakeDerivativeAndDistributeRoyaltyTokens_transaction(self, spgNftContract, recipient, ipMetadata, derivData, royaltyShares, allowDuplicates, tx_params):
        return self.contract.functions.mintAndRegisterIpAndMakeDerivativeAndDistributeRoyaltyTokens(spgNftContract, recipient, ipMetadata, derivData, royaltyShares, allowDuplicates).build_transaction(tx_params)
    
    def registerIpAndAttachPILTermsAndDeployRoyaltyVault(self, nftContract, tokenId, ipMetadata, licenseTermsData, sigMetadataAndAttachAndConfig):
        return self.contract.functions.registerIpAndAttachPILTermsAndDeployRoyaltyVault(nftContract, tokenId, ipMetadata, licenseTermsData, sigMetadataAndAttachAndConfig).transact()
        
    def build_registerIpAndAttachPILTermsAndDeployRoyaltyVault_transaction(self, nftContract, tokenId, ipMetadata, licenseTermsData, sigMetadataAndAttachAndConfig, tx_params):
        return self.contract.functions.registerIpAndAttachPILTermsAndDeployRoyaltyVault(nftContract, tokenId, ipMetadata, licenseTermsData, sigMetadataAndAttachAndConfig).build_transaction(tx_params)
    
    def registerIpAndMakeDerivativeAndDeployRoyaltyVault(self, nftContract, tokenId, ipMetadata, derivData, sigMetadataAndRegister):
        return self.contract.functions.registerIpAndMakeDerivativeAndDeployRoyaltyVault(nftContract, tokenId, ipMetadata, derivData, sigMetadataAndRegister).transact()
        
    def build_registerIpAndMakeDerivativeAndDeployRoyaltyVault_transaction(self, nftContract, tokenId, ipMetadata, derivData, sigMetadataAndRegister, tx_params):
        return self.contract.functions.registerIpAndMakeDerivativeAndDeployRoyaltyVault(nftContract, tokenId, ipMetadata, derivData, sigMetadataAndRegister).build_transaction(tx_params)
    
    