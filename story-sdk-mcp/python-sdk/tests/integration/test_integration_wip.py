# tests/integration/test_integration_wip.py

import pytest
from web3 import Web3

from setup_for_integration import (
    web3,
    story_client,
    wallet_address,
    wallet_address_2
)

class TestWIPDeposit:
    def test_deposit(self, story_client):
        """Test depositing IP to WIP"""
        ip_amt = Web3.to_wei(1, 'ether')  # or Web3.to_wei("0.01", 'ether')        
        
        # Get balances before deposit
        balance_before = story_client.get_wallet_balance()
        wip_before = story_client.WIP.balance_of(wallet_address)

        # Deposit IP to WIP
        response = story_client.WIP.deposit(
            amount=ip_amt
        )
        
        # Verify transaction hash
        assert isinstance(response['tx_hash'], str)
        
        # Get balances after deposit
        balance_after = story_client.get_wallet_balance()
        wip_after = story_client.WIP.balance_of(wallet_address)

        # Verify WIP balance increased by deposit amount
        assert wip_after == wip_before + ip_amt
        
        # Calculate gas cost
        tx_receipt = web3.eth.wait_for_transaction_receipt(response["tx_hash"], timeout=300)
        gas_cost = tx_receipt['gasUsed'] * tx_receipt['effectiveGasPrice']
        
        # Verify wallet balance decreased by deposit amount plus gas cost
        assert balance_after == balance_before - ip_amt - gas_cost


class TestWIPTransfer:
    def test_transfer(self, story_client):
        """Test transferring WIP"""
        transfer_amount = Web3.to_wei("0.01", 'ether')
        
        # Get balances before transfer
        sender_wip_before = story_client.WIP.balance_of(wallet_address)
        receiver_wip_before = story_client.WIP.balance_of(wallet_address_2)
        
        # Transfer WIP to wallet_address_2
        response = story_client.WIP.transfer(
            to=wallet_address_2,
            amount=transfer_amount,
            tx_options={"waitForTransaction": True}
        )
        
        # Verify transaction hash
        assert isinstance(response['tx_hash'], str)
        
        # Get balances after transfer
        sender_wip_after = story_client.WIP.balance_of(wallet_address)
        receiver_wip_after = story_client.WIP.balance_of(wallet_address_2)
        
        # Verify sender's WIP balance decreased by transfer amount
        assert sender_wip_after == sender_wip_before - transfer_amount
        
        # Verify receiver's WIP balance increased by transfer amount
        assert receiver_wip_after == receiver_wip_before + transfer_amount
        # Note: We're not testing transferFrom here as it requires approval
        # and the TypeScript test also skips this test for the same reason


class TestWIPWithdraw:
    def test_withdraw(self, story_client):
        """Test withdrawing WIP to IP"""
        # Get balances before withdrawal
        balance_before = story_client.get_wallet_balance()
        wip_before = story_client.WIP.balance_of(wallet_address)
        
        # Withdraw all WIP
        response = story_client.WIP.withdraw(
            amount=wip_before,
            tx_options={"waitForTransaction": True}
        )
        
        # Verify transaction hash
        assert isinstance(response['tx_hash'], str)
        
        # Get balances after withdrawal
        wip_after = story_client.WIP.balance_of(wallet_address)
        balance_after = story_client.get_wallet_balance()
        
        # Verify WIP balance is now zero
        assert wip_after == 0
        
        # Calculate gas cost
        tx_receipt = web3.eth.wait_for_transaction_receipt(response["tx_hash"], timeout=300)
        gas_cost = tx_receipt['gasUsed'] * tx_receipt['effectiveGasPrice']
        
        # Verify wallet balance increased by withdrawal amount minus gas cost
        assert balance_after == balance_before + wip_before - gas_cost
