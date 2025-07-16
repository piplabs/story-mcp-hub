
import json
import os
from web3 import Web3

class WIPClient:
    def __init__(self, web3: Web3):
        self.web3 = web3
        # Assuming config.json is located at the root of the project
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'config.json'))
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        contract_address = None
        for contract in config['contracts']:
            if contract['contract_name'] == 'WIP':
                contract_address = contract['contract_address']
                break
        if not contract_address:
            raise ValueError(f"Contract address for WIP not found in config.json")
        abi_path = os.path.join(os.path.dirname(__file__), '..', '..', 'abi', 'jsons', 'WIP.json')
        with open(abi_path, 'r') as abi_file:
            abi = json.load(abi_file)
        self.contract = self.web3.eth.contract(address=contract_address, abi=abi)
    
    def approve(self, spender, amount):
        return self.contract.functions.approve(spender, amount).transact()
        
    def build_approve_transaction(self, spender, amount, tx_params):
        return self.contract.functions.approve(spender, amount).build_transaction(tx_params)
    
    def deposit(self):
        return self.contract.functions.deposit().transact()
        
    def build_deposit_transaction(self, tx_params):
        return self.contract.functions.deposit().build_transaction(tx_params)
    
    def transfer(self, to, amount):
        return self.contract.functions.transfer(to, amount).transact()
        
    def build_transfer_transaction(self, to, amount, tx_params):
        return self.contract.functions.transfer(to, amount).build_transaction(tx_params)
    
    def transferFrom(self, from_address, to, amount):
        return self.contract.functions.transferFrom(from_address, to, amount).transact()
        
    def build_transferFrom_transaction(self, from_address, to, amount, tx_params):
        return self.contract.functions.transferFrom(from_address, to, amount).build_transaction(tx_params)
    
    def withdraw(self, value):
        return self.contract.functions.withdraw(value).transact()
        
    def build_withdraw_transaction(self, value, tx_params):
        return self.contract.functions.withdraw(value).build_transaction(tx_params)
    
    def allowance(self, owner, spender):
        return self.contract.functions.allowance(owner, spender).call()
    
    def balanceOf(self, owner):
        return self.contract.functions.balanceOf(owner).call()
        
    