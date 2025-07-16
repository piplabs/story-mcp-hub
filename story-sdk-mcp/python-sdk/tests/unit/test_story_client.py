import os
import sys
import pytest
from web3 import Web3
from dotenv import load_dotenv

from story_protocol_python_sdk.story_client import StoryClient
from story_protocol_python_sdk.resources.IPAsset import IPAsset
from story_protocol_python_sdk.resources.License import License
from story_protocol_python_sdk.resources.Royalty import Royalty
from story_protocol_python_sdk.resources.IPAccount import IPAccount
from story_protocol_python_sdk.resources.Permission import Permission
from tests.unit.fixtures.data import CHAIN_ID

# Load environment variables from .env file
load_dotenv()
private_key = os.getenv("WALLET_PRIVATE_KEY")
rpc_url = os.getenv("RPC_PROVIDER_URL")

# Ensure the environment variables are set
if not private_key or not rpc_url:
    raise ValueError(
        "Please set WALLET_PRIVATE_KEY and RPC_PROVIDER_URL in the .env file"
    )

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(rpc_url))

# Check if connected
if not web3.is_connected():
    raise Exception("Failed to connect to Web3 provider")

# Set up the account with the private key
account = web3.eth.account.from_key(private_key)


@pytest.fixture
def story_client():
    return StoryClient(web3, account, CHAIN_ID)


def test_story_client_constructor(story_client):
    assert story_client is not None
    assert isinstance(story_client, StoryClient)


def test_story_client_transport_error():
    with pytest.raises(ValueError):
        StoryClient(None, account, chain_id=CHAIN_ID)


def test_story_client_account_missing():
    with pytest.raises(ValueError):
        StoryClient(web3, None, chain_id=CHAIN_ID)


def test_story_client_wallet_initialization():
    client = StoryClient(web3, account, chain_id=CHAIN_ID)
    assert client is not None
    assert isinstance(client, StoryClient)


def test_ip_asset_client_getter(story_client):
    ip_asset = story_client.IPAsset
    assert ip_asset is not None
    assert isinstance(ip_asset, IPAsset)


def test_license_client_getter(story_client):
    license = story_client.License
    assert license is not None
    assert isinstance(license, License)


def test_royalty_client_getter(story_client):
    royalty = story_client.Royalty
    assert royalty is not None
    assert isinstance(royalty, Royalty)


def test_ip_account_client_getter(story_client):
    ip_account = story_client.IPAccount
    assert ip_account is not None
    assert isinstance(ip_account, IPAccount)


def test_permission_getter(story_client):
    permission = story_client.Permission
    assert permission is not None
    assert isinstance(permission, Permission)
