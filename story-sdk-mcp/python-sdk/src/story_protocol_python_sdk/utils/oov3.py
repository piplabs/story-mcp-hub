# Define the ABI for the getAssertion function
# Load the ABI from the JSON file
import json
import os
from web3 import Web3
from story_protocol_python_sdk.abi.ArbitrationPolicyUMA.ArbitrationPolicyUMA_client import ArbitrationPolicyUMAClient

abi_path = os.path.join(os.path.dirname(__file__), '..', 'abi', 'jsons', 'ASSERTION_ABI.json')
with open(abi_path, 'r') as abi_file:
    ASSERTION_ABI = json.load(abi_file)

def get_oov3_contract(arbitration_policy_uma_client: ArbitrationPolicyUMAClient) -> str:
    """
    Get the OOv3 contract address.
    
    :param arbitration_policy_uma_client: The ArbitrationPolicyUMA client instance.
    :return str: The OOv3 contract address.
    """
    return arbitration_policy_uma_client.oov3()

def get_assertion_bond(web3: Web3, arbitration_policy_uma_client: ArbitrationPolicyUMAClient, assertion_id: str) -> int:
    """
    Get assertion details to determine bond amount.
    
    :param web3: The Web3 instance.
    :param arbitration_policy_uma_client: The ArbitrationPolicyUMA client instance.
    :param assertion_id str: The ID of the assertion.
    :return int: The bond amount.
    """
    try:
        oov3_contract_address = get_oov3_contract(arbitration_policy_uma_client)
        
        oov3_contract = web3.eth.contract(address=oov3_contract_address, abi=ASSERTION_ABI)
        
        assertion_data = oov3_contract.functions.getAssertion(assertion_id).call()
        
        return assertion_data[9]
    except Exception as e:
        raise ValueError(f"Failed to get assertion details: {str(e)}")