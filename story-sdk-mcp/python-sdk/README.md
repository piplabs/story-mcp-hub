# Story SDK

Welcome to the documents for Story Python SDK. The Python SDK provides the APIs for developers to build applications with Story. By using the SDK, developers can create the resources like IP assets and perform actions to interact with the resource.

## How to use Story Protocol SDK in Your Project

### Install Story Protocol core SDK

Suppose you already have a node project or created a new node project. First, you need to install `story_protocol_python_sdk` in your project. You can use one of the following command to install the package:

Use `pip`:

```
pip install story_protocol_python_sdk web3
```

Besides the Story Protocol SDK package `story_protocol_python_sdk`, we also require the package `web3` (https://pypi.org/project/web3/) to access the DeFi wallet accounts.

# Initiate SDK Client

Next we can initiate the SDK Client by first setting up our wallet and then the client itself.

## Set up your wallet

The SDK supports using `web3` for initiating SDK client. Create a Python file and write the following code to initiate the client with a private key:

> :information-source: Make sure to have WALLET_PRIVATE_KEY set up in your .env file.

```Python main.py
import os
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()
private_key = os.getenv('WALLET_PRIVATE_KEY')
rpc_url = os.getenv('RPC_PROVIDER_URL')

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(rpc_url))

# Set up the account with the private key
account = web3.eth.account.from_key(private_key)
```

The preceding code created the `account` object for creating the SDK client.

## Set up SDK client

To set up the SDK client, import `StoryClient` from `story_protocol_python_sdk`. Write the following code, utilizing the `account` we created previously.

> :information-source: Make sure to have RPC_PROVIDER_URL for your desired chain set up in your .env file. We recommend using the public default one with `RPC_PROVIDER_URL=https://aeneid.storyrpc.io`.

```Python main.py
from story_protocol_python_sdk import StoryClient

# Create StoryClient instance
aeneid_chain_id = 1315
story_client = StoryClient(web3, account, aeneid_chain_id)
```

## Running test cases

- Integration Tests

```
pytest
```

- Unit Tests

```
coverage run -m pytest tests/unit -v -ra -q
```

- Generating a Coverage Report

```
coverage report
```

## Release

| Package                         | Description                                    |
| :------------------------------ | :--------------------------------------------- |
| [story_protocol_python_sdk](./src/story_protocol_python_sdk) | A Python SDK for interacting with the Story Protocol. |

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change. Details see: [CONTRIBUTING](/CONTRIBUTING.md)

Please make sure to update tests as appropriate.

## License

[MIT License](/LICENSE.md)
