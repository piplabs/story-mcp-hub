import json
import os
from jinja2 import Template

# Load ABIs from the correct jsons folder
JSONS_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'abi', 'jsons')

class_template = Template('''
import json
import os
from web3 import Web3

class {{ class_name }}:
    def __init__(self, web3: Web3):
        self.web3 = web3
        # Assuming config.json is located at the root of the project
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'config.json'))
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        contract_address = None
        for contract in config['contracts']:
            if contract['contract_name'] == '{{ contract_name }}':
                contract_address = contract['contract_address']
                break
        if not contract_address:
            raise ValueError(f"Contract address for {{ contract_name }} not found in config.json")
        abi_path = os.path.join(os.path.dirname(__file__), '..', '..', 'abi', 'jsons', '{{ contract_name }}.json')
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

def load_abi_from_file(contract_name):
    abi_path = os.path.join(JSONS_FOLDER, f"{contract_name}.json")
    if not os.path.exists(abi_path):
        raise FileNotFoundError(f"ABI file for {contract_name} not found in {JSONS_FOLDER}")
    with open(abi_path, 'r') as abi_file:
        return json.load(abi_file)

def generate_python_classes_from_abi(abi, contract_name, functions, output_dir):
    class_name = contract_name + 'Client'
    
    selected_functions = []
    for item in abi:
        if item['type'] == 'function' and item['name'] in functions:
            function = {
                'name': item['name'],
                'inputs': [input['name'] for input in item['inputs']],
                'stateMutability': item['stateMutability'] if 'stateMutability' in item else 'nonpayable'
            }
            selected_functions.append(function)
    
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
        functions = contract['functions']
        try:
            abi = load_abi_from_file(contract_name)
            generate_python_classes_from_abi(abi, contract_name, functions, output_dir)
        except Exception as e:
            print(f"Error generating class for {contract_name}: {e}")

if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    output_dir = os.path.join(os.path.dirname(__file__), '../abi')
    os.makedirs(output_dir, exist_ok=True)
    main(config_path, output_dir)
