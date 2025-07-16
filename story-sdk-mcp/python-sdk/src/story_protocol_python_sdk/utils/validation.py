from web3 import Web3

def validate_address(address: str) -> str:
    """
    Validates if the provided string is a valid Ethereum address.
    
    :param address str: The address to validate.
    :return str: The validated address.
    :raises ValueError: If the address is not valid.
    """
    if not Web3.is_address(address):
        raise ValueError(f"Invalid address: {address}.")
    return address


