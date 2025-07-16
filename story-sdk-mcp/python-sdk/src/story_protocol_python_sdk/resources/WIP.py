"""Module for handling Wrapped IP (WIP) token operations."""

from web3 import Web3

from story_protocol_python_sdk.abi.WIP.WIP_client import WIPClient
from story_protocol_python_sdk.utils.transaction_utils import build_and_send_transaction

class WIP:
    """
    A class to manage Wrapped IP (WIP) token operations.

    :param web3 Web3: An instance of Web3.
    :param account: The account to use for transactions.
    :param chain_id int: The ID of the blockchain network.
    """
    def __init__(self, web3: Web3, account, chain_id: int):
        self.web3 = web3
        self.account = account
        self.chain_id = chain_id

        self.wip_client = WIPClient(web3)

    def deposit(self, amount: int, tx_options: dict = None) -> dict:
        """
        Wraps the selected amount of IP to WIP.
        The WIP will be deposited to the wallet that transferred the IP.

        :param amount int: The amount of IP to wrap.
        :param tx_options dict: [Optional] Transaction options.
        :return dict: A dictionary containing the transaction hash.
        """
        try:
            if amount <= 0:
                raise ValueError("WIP deposit amount must be greater than 0.")

            # Prepare transaction options
            transaction_options = tx_options or {}
            transaction_options.update({
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'value': amount
            })
            
            response = build_and_send_transaction(
                self.web3,
                self.account,
                self.wip_client.build_deposit_transaction,
                tx_options=transaction_options
            )

            return {'tx_hash': response['tx_hash']}

        except Exception as e:
            raise ValueError(f"Failed to deposit IP for WIP: {str(e)}")

    def withdraw(self, amount: int, tx_options: dict = None) -> dict:
        """
        Unwraps the selected amount of WIP to IP.

        :param amount int: The amount of WIP to unwrap.
        :param tx_options dict: [Optional] Transaction options.
        :return dict: A dictionary containing the transaction hash.
        """
        try:
            if amount <= 0:
                raise ValueError("WIP withdraw amount must be greater than 0.")

            response = build_and_send_transaction(
                self.web3,
                self.account,
                self.wip_client.build_withdraw_transaction,
                amount,
                tx_options=tx_options
            )

            return {'tx_hash': response['tx_hash']}

        except Exception as e:
            raise ValueError(f"Failed to withdraw WIP: {str(e)}")

    def approve(self, spender: str, amount: int, tx_options: dict = None) -> dict:
        """
        Approve a spender to use the wallet's WIP balance.

        :param spender str: The address of the spender.
        :param amount int: The amount of WIP to approve.
        :param tx_options dict: [Optional] Transaction options.
        :return dict: A dictionary containing the transaction hash.
        """
        try:
            if amount <= 0:
                raise ValueError("WIP approve amount must be greater than 0.")

            if not self.web3.is_address(spender):
                raise ValueError(f"The spender address {spender} is not valid.")

            spender = self.web3.to_checksum_address(spender)

            response = build_and_send_transaction(
                self.web3,
                self.account,
                self.wip_client.build_approve_transaction,
                spender,
                amount,
                tx_options=tx_options
            )

            return {'tx_hash': response['tx_hash']}

        except Exception as e:
            raise ValueError(f"Failed to approve WIP: {str(e)}")

    def balance_of(self, address: str) -> int:
        """
        Returns the balance of WIP for an address.

        :param address str: The address to check the balance of.
        :return int: The WIP balance of the address.
        """
        try:
            if not self.web3.is_address(address):
                raise ValueError(f"The address {address} is not valid.")

            address = self.web3.to_checksum_address(address)
            return self.wip_client.balanceOf(address)

        except Exception as e:
            raise ValueError(f"Failed to get WIP balance: {str(e)}")

    def transfer(self, to: str, amount: int, tx_options: dict = None) -> dict:
        """
        Transfers `amount` of WIP to a recipient `to`.

        :param to str: The address of the recipient.
        :param amount int: The amount of WIP to transfer.
        :param tx_options dict: [Optional] Transaction options.
        :return dict: A dictionary containing the transaction hash.
        """
        try:
            if amount <= 0:
                raise ValueError("WIP transfer amount must be greater than 0.")

            if not self.web3.is_address(to):
                raise ValueError(f"The recipient address {to} is not valid.")

            to = self.web3.to_checksum_address(to)

            response = build_and_send_transaction(
                self.web3,
                self.account,
                self.wip_client.build_transfer_transaction,
                to,
                amount,
                tx_options=tx_options
            )

            return {'tx_hash': response['tx_hash']}

        except Exception as e:
            raise ValueError(f"Failed to transfer WIP: {str(e)}")

    def transfer_from(self, from_address: str, to: str, amount: int, tx_options: dict = None) -> dict:
        """
        Transfers `amount` of WIP from `from_address` to a recipient `to`.

        :param from_address str: The address to transfer from.
        :param to str: The address of the recipient.
        :param amount int: The amount of WIP to transfer.
        :param tx_options dict: [Optional] Transaction options.
        :return dict: A dictionary containing the transaction hash.
        """
        try:
            if amount <= 0:
                raise ValueError("WIP transfer amount must be greater than 0.")

            if not self.web3.is_address(from_address):
                raise ValueError(f"The from address {from_address} is not valid.")

            if not self.web3.is_address(to):
                raise ValueError(f"The recipient address {to} is not valid.")

            from_address = self.web3.to_checksum_address(from_address)
            to = self.web3.to_checksum_address(to)

            response = build_and_send_transaction(
                self.web3,
                self.account,
                self.wip_client.build_transferFrom_transaction,
                from_address,
                to,
                amount,
                tx_options=tx_options
            )

            return {'tx_hash': response['tx_hash']}

        except Exception as e:
            raise ValueError(f"Failed to transfer WIP from another address: {str(e)}")
    
    def allowance(self, owner: str, spender: str) -> int:
        """
        Returns the amount of WIP tokens that `spender` is allowed to spend on behalf of `owner`.

        :param owner str: The address of the token owner.
        :param spender str: The address of the spender.
        :return int: The amount of WIP tokens the spender is allowed to spend.
        """
        try:
            if not self.web3.is_address(owner):
                raise ValueError(f"The owner address {owner} is not valid.")

            if not self.web3.is_address(spender):
                raise ValueError(f"The spender address {spender} is not valid.")

            owner = self.web3.to_checksum_address(owner)
            spender = self.web3.to_checksum_address(spender)

            return self.wip_client.allowance(owner, spender)

        except Exception as e:
            raise ValueError(f"Failed to get allowance: {str(e)}")
