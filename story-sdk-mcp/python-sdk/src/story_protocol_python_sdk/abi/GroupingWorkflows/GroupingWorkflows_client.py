
import json
import os
from web3 import Web3

class GroupingWorkflowsClient:
    def __init__(self, web3: Web3):
        self.web3 = web3
        # Assuming config.json is located at the root of the project
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'config.json'))
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        contract_address = None
        for contract in config['contracts']:
            if contract['contract_name'] == 'GroupingWorkflows':
                contract_address = contract['contract_address']
                break
        if not contract_address:
            raise ValueError(f"Contract address for GroupingWorkflows not found in config.json")
        abi_path = os.path.join(os.path.dirname(__file__), '..', '..', 'abi', 'jsons', 'GroupingWorkflows.json')
        with open(abi_path, 'r') as abi_file:
            abi = json.load(abi_file)
        self.contract = self.web3.eth.contract(address=contract_address, abi=abi)
    
    def collectRoyaltiesAndClaimReward(self, groupIpId, currencyTokens, memberIpIds):
        return self.contract.functions.collectRoyaltiesAndClaimReward(groupIpId, currencyTokens, memberIpIds).transact()
        
    def build_collectRoyaltiesAndClaimReward_transaction(self, groupIpId, currencyTokens, memberIpIds, tx_params):
        return self.contract.functions.collectRoyaltiesAndClaimReward(groupIpId, currencyTokens, memberIpIds).build_transaction(tx_params)
    
    def mintAndRegisterIpAndAttachLicenseAndAddToGroup(self, spgNftContract, groupId, recipient, maxAllowedRewardShare, licensesData, ipMetadata, sigAddToGroup, allowDuplicates):
        return self.contract.functions.mintAndRegisterIpAndAttachLicenseAndAddToGroup(spgNftContract, groupId, recipient, maxAllowedRewardShare, licensesData, ipMetadata, sigAddToGroup, allowDuplicates).transact()
        
    def build_mintAndRegisterIpAndAttachLicenseAndAddToGroup_transaction(self, spgNftContract, groupId, recipient, maxAllowedRewardShare, licensesData, ipMetadata, sigAddToGroup, allowDuplicates, tx_params):
        return self.contract.functions.mintAndRegisterIpAndAttachLicenseAndAddToGroup(spgNftContract, groupId, recipient, maxAllowedRewardShare, licensesData, ipMetadata, sigAddToGroup, allowDuplicates).build_transaction(tx_params)
    
    def registerGroupAndAttachLicense(self, groupPool, licenseData):
        return self.contract.functions.registerGroupAndAttachLicense(groupPool, licenseData).transact()
        
    def build_registerGroupAndAttachLicense_transaction(self, groupPool, licenseData, tx_params):
        return self.contract.functions.registerGroupAndAttachLicense(groupPool, licenseData).build_transaction(tx_params)
    
    def registerGroupAndAttachLicenseAndAddIps(self, groupPool, ipIds, maxAllowedRewardShare, licenseData):
        return self.contract.functions.registerGroupAndAttachLicenseAndAddIps(groupPool, ipIds, maxAllowedRewardShare, licenseData).transact()
        
    def build_registerGroupAndAttachLicenseAndAddIps_transaction(self, groupPool, ipIds, maxAllowedRewardShare, licenseData, tx_params):
        return self.contract.functions.registerGroupAndAttachLicenseAndAddIps(groupPool, ipIds, maxAllowedRewardShare, licenseData).build_transaction(tx_params)
    
    def registerIpAndAttachLicenseAndAddToGroup(self, nftContract, tokenId, groupId, maxAllowedRewardShare, licensesData, ipMetadata, sigMetadataAndAttachAndConfig, sigAddToGroup):
        return self.contract.functions.registerIpAndAttachLicenseAndAddToGroup(nftContract, tokenId, groupId, maxAllowedRewardShare, licensesData, ipMetadata, sigMetadataAndAttachAndConfig, sigAddToGroup).transact()
        
    def build_registerIpAndAttachLicenseAndAddToGroup_transaction(self, nftContract, tokenId, groupId, maxAllowedRewardShare, licensesData, ipMetadata, sigMetadataAndAttachAndConfig, sigAddToGroup, tx_params):
        return self.contract.functions.registerIpAndAttachLicenseAndAddToGroup(nftContract, tokenId, groupId, maxAllowedRewardShare, licensesData, ipMetadata, sigMetadataAndAttachAndConfig, sigAddToGroup).build_transaction(tx_params)
    
    