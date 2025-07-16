import requests
import json
import os
from jinja2 import Template
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

# Get the API key from environment variables
api_key = os.getenv('ETHERSCAN_API_KEY')
if not api_key:
    raise ValueError("Please set ETHERSCAN_API_KEY in the .env file")

def fetch_abi(contract_address, api_key):
    url = f"https://api-sepolia.etherscan.io/api?module=contract&action=getabi&address={contract_address}&apikey={api_key}"
    response = requests.get(url)
    response_json = response.json()
    if response_json.get('status') == '1':
        abi = json.loads(response_json['result'])
        return abi
    else:
        raise Exception(f"Error fetching ABI for address {contract_address}: {response_json.get('message')}")

def save_abi(abi, output_path):
    with open(output_path, 'w') as abi_file:
        json.dump(abi, abi_file, indent=2)

class_template = Template('''
import json
import os
from web3 import Web3

class {{ class_name }}:
    def __init__(self, web3: Web3, contract_address=None):
        self.web3 = web3
        abi_path = os.path.join(os.path.dirname(__file__), '{{ contract_name }}.json')
        with open(abi_path, 'r') as abi_file:
            abi = json.load(abi_file)
        self.contract = self.web3.eth.contract(address=contract_address, abi=abi)
    {% for function in functions %}
    def {{ function.name }}(self, {% if function.inputs %}{{ function.inputs | join(', ') }}{% endif %}):
        {% if function.stateMutability == 'view' or function.stateMutability == 'pure' %}
        return self.contract.functions.{{ function.name }}({% if function.inputs %}{{ function.inputs | join(', ') }}{% endif %}).call()
        {% else %}
        return self.contract.functions.{{ function.name }}({% if function.inputs %}{{ function.inputs | join(', ') }}{% endif %}).transact()
        
    def build_{{ function.name }}_transaction(self, {% if function.inputs %}{{ function.inputs | join(', ') }}, {% endif %}tx_params):
        return self.contract.functions.{{ function.name }}({% if function.inputs %}{{ function.inputs | join(', ') }}{% endif %}).build_transaction(tx_params)
    {% endif %}
    {% endfor %}
''')

def generate_python_classes_from_abi(abi, contract_name, functions, output_dir):
    class_name = contract_name + 'Client'  # Use the contract_name directly for proper capitalization
    
    selected_functions = []
    for item in abi:
        if item['type'] == 'function' and item['name'] in functions:
            function = {
                'name': item['name'],
                'inputs': [input['name'] for input in item['inputs']],
                'stateMutability': item['stateMutability'] if 'stateMutability' in item else 'nonpayable'
            }
            selected_functions.append(function)
    
    # Sort functions to have transact functions first and call functions after
    selected_functions.sort(key=lambda x: x['stateMutability'] in ['view', 'pure'])
    
    rendered_class = class_template.render(
        class_name=class_name,
        contract_name=contract_name,
        functions=selected_functions
    )
    
    contract_output_dir = os.path.join(output_dir, contract_name)
    os.makedirs(contract_output_dir, exist_ok=True)

    output_file_path = os.path.join(contract_output_dir, f"{contract_name}_client.py")
    with open(output_file_path, 'w') as output_file:
        output_file.write(rendered_class)
    
    print(f"Generated {class_name} class from ABI")

def main(config_path, output_dir):
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    
        for contract in config['contracts']:
            contract_name = contract['contract_name']
            contract_address = contract['contract_address']
            functions = contract['functions']

            for attempt in range(3):  # Retry up to 3 times
                try:
                    abi = fetch_abi(contract_address, api_key)
                    if abi:
                        contract_output_dir = os.path.join(output_dir, contract_name)
                        os.makedirs(contract_output_dir, exist_ok=True)

                        save_abi(abi, os.path.join(contract_output_dir, f'{contract_name}.json'))
                        generate_python_classes_from_abi(abi, contract_name, functions, output_dir)
                        time.sleep(1)  # Wait for 1 second before moving to the next contract
                        break  # If successful, break out of the retry loop
                    else:
                        raise Exception("Failed to fetch ABI")
                except Exception as e:
                    print(f"Error on attempt {attempt + 1} for {contract_name}: {e}")
                    time.sleep(2)  # Wait for 2 seconds before retrying

if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), 'config_impl.json')
    output_dir = os.path.join(os.path.dirname(__file__), '../abi')
    os.makedirs(output_dir, exist_ok=True)
    main(config_path, output_dir)
