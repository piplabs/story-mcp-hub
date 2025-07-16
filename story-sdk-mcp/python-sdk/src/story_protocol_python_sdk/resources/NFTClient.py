#src/story_protcol_python_sdk/resources/NFTClient.py

from web3 import Web3

from story_protocol_python_sdk.abi.RegistrationWorkflows.RegistrationWorkflows_client import RegistrationWorkflowsClient
from story_protocol_python_sdk.abi.SPGNFTImpl.SPGNFTImpl_client import SPGNFTImplClient

from story_protocol_python_sdk.utils.transaction_utils import build_and_send_transaction
from story_protocol_python_sdk.utils.constants import ZERO_ADDRESS, ZERO_HASH

class NFTClient:
    """
    NFTClient handles the creation of SPG NFT collections.

    :param web3 Web3: An instance of Web3.
    :param account: The account to use for transactions.
    :param chain_id int: The ID of the blockchain network.
    """    
    def __init__(self, web3: Web3, account, chain_id: int):
        self.web3 = web3
        self.account = account
        self.chain_id = chain_id

        self.registration_workflows_client = RegistrationWorkflowsClient(web3)

    def create_nft_collection(self, name: str, symbol: str, is_public_minting: bool, mint_open: bool, 
                          mint_fee_recipient: str, contract_uri: str, base_uri: str = "", max_supply: int = None, 
                          mint_fee: int = None, mint_fee_token: str = None, owner: str = None, 
                          tx_options: dict = None) -> dict:
        """
        Creates a new SPG NFT Collection.

        :param name str: The name of the collection.
        :param symbol str: The symbol of the collection.
        :param is_public_minting bool: If true, anyone can mint from the collection. If false, only addresses with minter role can mint.
        :param mint_open bool: Whether the collection is open for minting on creation.
        :param mint_fee_recipient str: The address to receive mint fees.
        :param contract_uri str: The contract URI for the collection. Follows ERC-7572 standard.
        :param base_uri str: [Optional] The base URI for the collection. If not empty, tokenURI will be either baseURI + token ID or baseURI + nftMetadataURI.
        :param max_supply int: [Optional] The maximum supply of the collection.
        :param mint_fee int: [Optional] The cost to mint a token.
        :param mint_fee_token str: [Optional] The token to mint.
        :param owner str: [Optional] The owner of the collection.
        :param tx_options dict: [Optional] The transaction options.
        :return dict: A dictionary with the transaction hash and collection address.
        """
        try:
            if mint_fee is not None and (mint_fee < 0 or not self.web3.is_address(mint_fee_token or "")):
                raise ValueError("Invalid mint fee token address, mint fee is greater than 0.")

            spg_nft_init_params = {
                'name': name,
                'symbol': symbol,
                'baseURI': base_uri or "",
                'maxSupply': max_supply if max_supply is not None else 2**32 - 1,
                'mintFee': mint_fee if mint_fee is not None else 0,
                'mintFeeToken': mint_fee_token if mint_fee_token is not None else ZERO_ADDRESS,
                'owner': owner if owner else self.account.address,
                'mintFeeRecipient': self.web3.to_checksum_address(mint_fee_recipient),
                'mintOpen': mint_open,
                'isPublicMinting': is_public_minting,
                'contractURI': contract_uri
            }

            response = build_and_send_transaction(
                self.web3,
                self.account,
                self.registration_workflows_client.build_createCollection_transaction,
                spg_nft_init_params,
                tx_options=tx_options
            )

            collection_address = self._parse_tx_collection_created_event(response['tx_receipt'])

            return {
                'tx_hash': response['tx_hash'],
                'nft_contract': collection_address
            }

        except Exception as e:
            raise e
        
    def _parse_tx_collection_created_event(self, tx_receipt: dict) -> int:
        """
        Parse the CollectionCreated event from a transaction receipt.

        :param tx_receipt dict: The transaction receipt.
        :return int: The ID of the license terms.
        """
        event_signature = self.web3.keccak(text="CollectionCreated(address)").hex()

        for log in tx_receipt['logs']:
            if log['topics'][0].hex() == event_signature:
                return self.web3.to_checksum_address('0x' + log['topics'][1].hex()[-40:])

        return None
    
    def get_mint_fee_token(self, nft_contract: str) -> str:
        """
        Returns the current mint fee token of the collection.
        
        :param nft_contract str: The address of the NFT contract.
        :return str: The address of the mint fee token.
        """
        try:
            nft_contract = self.web3.to_checksum_address(nft_contract)
            spg_nft_client = SPGNFTImplClient(self.web3, contract_address=nft_contract)
            
            return spg_nft_client.mintFeeToken()
        except Exception as e:
            raise ValueError(f"Failed to get mint fee token: {str(e)}")
    
    def get_mint_fee(self, nft_contract: str) -> int:
        """
        Returns the current mint fee of the collection.
        
        :param nft_contract str: The address of the NFT contract.
        :return int: The mint fee amount.
        """
        try:
            nft_contract = self.web3.to_checksum_address(nft_contract)
            spg_nft_client = SPGNFTImplClient(self.web3, contract_address=nft_contract)
            
            return spg_nft_client.mintFee()
        except Exception as e:
            raise ValueError(f"Failed to get mint fee: {str(e)}")
