import pytest, os, sys
from unittest.mock import patch, MagicMock
from web3 import Web3

# Ensure the src directory is in the Python path
current_dir = os.path.dirname(__file__)
src_path = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
if src_path not in sys.path:
    sys.path.append(src_path)

from src.story_protocol_python_sdk.resources.Royalty import Royalty

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()
private_key = os.getenv('WALLET_PRIVATE_KEY')
rpc_url = os.getenv('RPC_PROVIDER_URL')

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(rpc_url))

# Check if connected
if not web3.is_connected():
    raise Exception("Failed to connect to Web3 provider")

# Set up the account with the private key
account = web3.eth.account.from_key(private_key)

@pytest.fixture
def royalty_client():
    chain_id = 1315
    return Royalty(web3, account, chain_id)

def test_claimable_revenue_royalty_vault_ip_id_error(royalty_client):
    with patch.object(royalty_client.ip_asset_registry_client, 'isRegistered', return_value=False):
        child_ip_id = "0xA34611b0E11Bba2b11c69864f7D36aC83D862A9c"
        account_address = account.address
        token = "0xB132A6B7AE652c974EE1557A3521D53d18F6739f"

        with pytest.raises(ValueError, match=f"The IP with id {child_ip_id} is not registered."):
            royalty_client.claimable_revenue(child_ip_id, account_address, token)

def test_claimable_revenue_success(royalty_client):
    with patch.object(royalty_client.ip_asset_registry_client, 'isRegistered', return_value=True):
        with patch.object(royalty_client, 'get_royalty_vault_address', return_value="0xA34611b0E11Bba2b11c69864f7D36aC83D862A9c"):
            with patch('story_protocol_python_sdk.abi.IpRoyaltyVaultImpl.IpRoyaltyVaultImpl_client.IpRoyaltyVaultImplClient.claimableRevenue', return_value=0):
                parent_ip_id = "0xA34611b0E11Bba2b11c69864f7D36aC83D862A9c"
                account_address = account.address
                token = "0xB132A6B7AE652c974EE1557A3521D53d18F6739f"

                response = royalty_client.claimable_revenue(parent_ip_id, account_address, token)
                assert response == 0

def test_pay_royalty_on_behalf_receiver_ip_id_error(royalty_client):
    with patch.object(royalty_client.ip_asset_registry_client, 'isRegistered', return_value=False):
        receiver_ip_id = "0xA34611b0E11Bba2b11c69864f7D36aC83D862A9c"
        payer_ip_id = "0x9C098DF37b2324aaC8792dDc7BcEF7Bb0057A9C7"
        ERC20 = "0xB132A6B7AE652c974EE1557A3521D53d18F6739f"
        amount = 1

        with pytest.raises(ValueError, match=f"The receiver IP with id {receiver_ip_id} is not registered."):
            royalty_client.pay_royalty_on_behalf(receiver_ip_id, payer_ip_id, ERC20, amount)

def test_pay_royalty_on_behalf_payer_ip_id_error(royalty_client):
    with patch.object(royalty_client.ip_asset_registry_client, 'isRegistered', side_effect=[True, False]):
        receiver_ip_id = "0xA34611b0E11Bba2b11c69864f7D36aC83D862A9c"
        payer_ip_id = "0x9C098DF37b2324aaC8792dDc7BcEF7Bb0057A9C7"
        ERC20 = "0xB132A6B7AE652c974EE1557A3521D53d18F6739f"
        amount = 1

        with pytest.raises(ValueError, match=f"The payer IP with id {payer_ip_id} is not registered."):
            royalty_client.pay_royalty_on_behalf(receiver_ip_id, payer_ip_id, ERC20, amount)

def test_pay_royalty_on_behalf_success(royalty_client):
    with patch.object(royalty_client.ip_asset_registry_client, 'isRegistered', return_value=True):
        with patch('story_protocol_python_sdk.abi.RoyaltyModule.RoyaltyModule_client.RoyaltyModuleClient.build_payRoyaltyOnBehalf_transaction', return_value={
            'data': '0x',
            'nonce': 0,
            'gas': 2000000,
            'gasPrice': Web3.to_wei('300', 'gwei')
        }):
            with patch('web3.eth.Eth.send_raw_transaction', return_value=Web3.to_bytes(hexstr='0xbadf64f2c220e27407c4d2ccbc772fb72c7dc590ac25000dc316e4dc519fbfa2')):
                with patch('web3.eth.Eth.wait_for_transaction_receipt', return_value={'status': 1, 'logs': []}):
                    receiver_ip_id = "0xA34611b0E11Bba2b11c69864f7D36aC83D862A9c"
                    payer_ip_id = "0x9C098DF37b2324aaC8792dDc7BcEF7Bb0057A9C7"
                    ERC20 = "0xB132A6B7AE652c974EE1557A3521D53d18F6739f"
                    amount = 1

                    response = royalty_client.pay_royalty_on_behalf(receiver_ip_id, payer_ip_id, ERC20, amount, tx_options={'wait_for_transaction': True})
                    assert response is not None
                    assert 'tx_hash' in response
                    assert response['tx_hash'] == 'badf64f2c220e27407c4d2ccbc772fb72c7dc590ac25000dc316e4dc519fbfa2'
