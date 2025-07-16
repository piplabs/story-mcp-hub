# src/story_protocol_python_sdk/story_client.py

import os
import sys

# Ensure the src directory is in the Python path
current_dir = os.path.dirname(__file__)
src_path = os.path.abspath(os.path.join(current_dir, '..'))
if src_path not in sys.path:
    sys.path.append(src_path)

from story_protocol_python_sdk.resources.IPAsset import IPAsset
from story_protocol_python_sdk.resources.License import License
from story_protocol_python_sdk.resources.Royalty import Royalty
from story_protocol_python_sdk.resources.IPAccount import IPAccount
from story_protocol_python_sdk.resources.Permission import Permission
from story_protocol_python_sdk.resources.NFTClient import NFTClient
from story_protocol_python_sdk.resources.Dispute import Dispute
from story_protocol_python_sdk.resources.WIP import WIP
from story_protocol_python_sdk.resources.Group import Group

class StoryClient:
    """
    A client for interacting with Story Protocol, providing access to IPAsset, License, and Royalty resources.

    :param web3 Web3: An instance of Web3.
    :param account: The account to use for transactions.
    :param chain_id int: The ID of the blockchain network.
    """
    def __init__(self, web3, account, chain_id: int):
        """
        Initialize the StoryClient with the given web3 instance, account, and chain ID.

        :param web3 Web3: An instance of Web3.
        :param account: The account to use for transactions.
        :param chain_id int: The ID of the blockchain network.
        :raises ValueError: If web3 or account is not provided.
        """
        if not web3 or not account:
            raise ValueError("web3 and account must be provided")

        if chain_id not in [1315, 1514]:
            raise ValueError("only support story devnet")

        self.web3 = web3
        self.account = account
        self.chain_id = chain_id

        self._ip_asset = None
        self._license = None
        self._royalty = None
        self._ip_account = None
        self._permission = None
        self._nft_client = None
        self._dispute = None
        self._wip = None
        self._group = None

    @property
    def IPAsset(self) -> IPAsset:
        """
        Access the IPAsset resource.

        :return IPAsset: An instance of IPAsset.
        """
        if self._ip_asset is None:
            self._ip_asset = IPAsset(self.web3, self.account, self.chain_id)
        return self._ip_asset

    @property
    def License(self) -> License:
        """
        Access the License resource.

        :return License: An instance of License.
        """
        if self._license is None:
            self._license = License(self.web3, self.account, self.chain_id)
        return self._license
    
    @property
    def Royalty(self) -> Royalty:
        """
        Access the Royalty resource.

        :return Royalty: An instance of Royalty.
        """
        if self._royalty is None:
            self._royalty = Royalty(self.web3, self.account, self.chain_id)
        return self._royalty
    
    @property
    def IPAccount(self) -> IPAccount:
        """
        Access the IPAccount resource.

        :return IPAccount: An instance of IPAccount.
        """
        if self._ip_account is None:
            self._ip_account = IPAccount(self.web3, self.account, self.chain_id)
        return self._ip_account
    
    @property
    def Permission(self) -> Permission:
        """
        Access the Permission resource.

        :return Permission: An instance of Permission.
        """
        if self._permission is None:
            self._permission = Permission(self.web3, self.account, self.chain_id)
        return self._permission
    
    @property
    def NFTClient(self) -> NFTClient:
        """
        Access the NFTClient resource.

        :return NFTClient: An instance of NFTClient.
        """
        if self._nft_client is None:
            self._nft_client = NFTClient(self.web3, self.account, self.chain_id)
        return self._nft_client

    @property
    def Dispute(self) -> Dispute:
        """
        Access the Dispute resource.

        :return Dispute: An instance of Dispute.
        """
        if self._dispute is None:
            self._dispute = Dispute(self.web3, self.account, self.chain_id)
        return self._dispute
    
    @property
    def WIP(self) -> WIP:
        """
        Access the WIP resource.

        :return WIP: An instance of WIP.
        """
        if self._wip is None:
            self._wip = WIP(self.web3, self.account, self.chain_id)
        return self._wip
    
    @property
    def Group(self) -> Group:
        """
        Access the Group resource.
        """
        if self._group is None:
            self._group = Group(self.web3, self.account, self.chain_id)
        return self._group
    
    def get_wallet_balance(self) -> int:
        """
        Get the WIP token balance of the current wallet.

        :return int: The WIP token balance of the current wallet.
        :raises ValueError: If no account is found.
        """
        if not self.account or not hasattr(self.account, 'address'):
            raise ValueError("No account found in wallet")
        
        return self.web3.eth.get_balance(self.account.address)