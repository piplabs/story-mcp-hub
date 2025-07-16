# src/story_protcol_python_sdk/utils/transaction_utils.py

from web3 import Web3

TRANSACTION_TIMEOUT = 300

def build_and_send_transaction(web3: Web3, account, client_function, *client_args, tx_options: dict = None) -> dict:
    """
    Builds and sends a transaction using the provided client function and arguments.

    :param web3 Web3: An instance of Web3.
    :param account: The account to use for signing the transaction.
    :param client_function: The client function to build the transaction.
    :param client_args: Arguments to pass to the client function.
    :param tx_options dict: Optional transaction options.
    :return dict: A dictionary with the transaction hash and receipt, or encoded data if encodedTxDataOnly is True.
    :raises Exception: If there is an error during the transaction process.
    """
    try:
        tx_options = tx_options or {}

        transaction_options = {
            'from': account.address,
            'nonce': web3.eth.get_transaction_count(account.address),
        }

        # Add value if it exists in tx_options
        if 'value' in tx_options:
            transaction_options['value'] = tx_options['value']

        if 'gasPrice' in tx_options:
            transaction_options['gasPrice'] = web3.to_wei(tx_options['gasPrice'], 'gwei')
        if 'maxFeePerGas' in tx_options:
            transaction_options['maxFeePerGas'] = tx_options['maxFeePerGas']

        transaction = client_function(*client_args, transaction_options)

        # If encodedTxDataOnly is True, return the transaction data without sending
        if tx_options.get('encodedTxDataOnly'):
            return {
                'encodedTxData': transaction
            }

        signed_txn = account.sign_transaction(transaction)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=TRANSACTION_TIMEOUT)

        return {
            'tx_hash': tx_hash.hex(),
            'tx_receipt': tx_receipt
        }

    except Exception as e:
        raise e
