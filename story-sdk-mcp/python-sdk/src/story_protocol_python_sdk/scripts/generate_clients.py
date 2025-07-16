import json
import os
from jinja2 import Template

# Define the folder containing the ABI JSON files
JSONS_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'abi', 'jsons')

# Template for regular clients that read address from config
regular_class_template = Template('''
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
    def {{ function.python_name }}(self{% if function.inputs %}, {{ function.inputs | join(', ') }}{% endif %}):
        {% if function.stateMutability == 'view' or function.stateMutability == 'pure' %}
        return self.contract.functions.{{ function.name }}({% if function.inputs %}{{ function.inputs | join(', ') }}{% endif %}).call()
        {% else %}
        return self.contract.functions.{{ function.name }}({% if function.inputs %}{{ function.inputs | join(', ') }}{% endif %}).transact()
        
    def build_{{ function.python_name }}_transaction(self{% if function.inputs %}, {{ function.inputs | join(', ') }}{% endif %}, tx_params):
        return self.contract.functions.{{ function.name }}({% if function.inputs %}{{ function.inputs | join(', ') }}{% endif %}).build_transaction(tx_params)
    {% endif %}
    {% endfor %}
''')

# Template for Impl clients that require address in constructor
impl_class_template = Template('''
import json
import os
from web3 import Web3

class {{ class_name }}:
    def __init__(self, web3: Web3, contract_address=None):
        self.web3 = web3
        abi_path = os.path.join(os.path.dirname(__file__), '..', '..', 'abi', 'jsons', '{{ contract_name }}.json')
        with open(abi_path, 'r') as abi_file:
            abi = json.load(abi_file)
        self.contract = self.web3.eth.contract(address=contract_address, abi=abi)
    {% for function in functions %}
    def {{ function.python_name }}(self{% if function.inputs %}, {{ function.inputs | join(', ') }}{% endif %}):
        {% if function.stateMutability == 'view' or function.stateMutability == 'pure' %}
        return self.contract.functions.{{ function.name }}({% if function.inputs %}{{ function.inputs | join(', ') }}{% endif %}).call()
        {% else %}
        return self.contract.functions.{{ function.name }}({% if function.inputs %}{{ function.inputs | join(', ') }}{% endif %}).transact()
        
    def build_{{ function.python_name }}_transaction(self{% if function.inputs %}, {{ function.inputs | join(', ') }}{% endif %}, tx_params):
        return self.contract.functions.{{ function.name }}({% if function.inputs %}{{ function.inputs | join(', ') }}{% endif %}).build_transaction(tx_params)
    {% endif %}
    {% endfor %}
''')

def load_abi_from_file(contract_name):
    """Load ABI JSON from the jsons folder."""
    abi_path = os.path.join(JSONS_FOLDER, f"{contract_name}.json")
    if not os.path.exists(abi_path):
        raise FileNotFoundError(f"ABI file for {contract_name} not found in {JSONS_FOLDER}")
    with open(abi_path, 'r') as abi_file:
        return json.load(abi_file)

def generate_python_class_from_abi(abi, contract_name, functions, output_dir):
    """Generate a Python class for interacting with the contract."""
    class_name = contract_name + 'Client'
    
    selected_functions = []
    function_name_counts = {}
    
    for item in abi:
        if item['type'] == 'function' and item['name'] in functions:
            # Count occurrences of function names
            if item['name'] in function_name_counts:
                function_name_counts[item['name']] += 1
            else:
                function_name_counts[item['name']] = 1
                
            # Process inputs, replacing 'from' with 'from_address'
            inputs = []
            for input_param in item['inputs']:
                param_name = input_param['name']
                if param_name == 'from':
                    param_name = 'from_address'
                inputs.append(param_name)
            
            function = {
                'name': item['name'],
                'inputs': inputs,
                'stateMutability': item.get('stateMutability', 'nonpayable')
            }
            selected_functions.append(function)
    
    # Add python_name to each function, with numbering for duplicates
    function_name_seen = {}
    for function in selected_functions:
        name = function['name']
        if name in function_name_seen:
            function_name_seen[name] += 1
            function['python_name'] = f"{name}{function_name_seen[name] + 1}"
        else:
            function_name_seen[name] = 0
            function['python_name'] = name
    
    # Sort functions: transact functions first, call functions later
    selected_functions.sort(key=lambda x: x['stateMutability'] in ['view', 'pure'])
    
    # Choose template based on whether contract name ends with 'Impl'
    template = impl_class_template if contract_name.endswith('Impl') else regular_class_template
    
    rendered_class = template.render(
        class_name=class_name,
        contract_name=contract_name,
        functions=selected_functions
    )
    
    # Write the generated class to the output directory
    contract_output_dir = os.path.join(output_dir, contract_name)
    os.makedirs(contract_output_dir, exist_ok=True)

    output_file_path = os.path.join(contract_output_dir, f"{contract_name}_client.py")
    with open(output_file_path, 'w') as output_file:
        output_file.write(rendered_class)
    
    print(f"Generated {class_name} class from ABI")

def fix_client_formatting(client_dir):
    """Fix formatting issues in generated client files."""
    for root, dirs, files in os.walk(client_dir):
        for file in files:
            if file.endswith('_client.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Fix empty lines between functions (ensure exactly one empty line)
                import re
                # Replace multiple empty lines between function definitions with a single empty line
                content = re.sub(r'(\n    def [^\n]+\n)(\s*\n)+(\s+def)', r'\1\n\3', content)
                
                # Remove empty lines within function bodies
                content = re.sub(r'(\n        [^\n]+\n)(\s*\n)(\s{8})', r'\1\3', content)
                
                # Fix parameter formatting for functions with only 'self'
                content = re.sub(r'def ([a-zA-Z0-9_]+)\(self, \):', r'def \1(self):', content)
                
                # Fix empty lines in view/pure function bodies - specifically target the empty line between function definition and return statement
                content = re.sub(r'(def [a-zA-Z0-9_]+\(self(?:, [^\)]+)?\):\n\s*\n)(\s+return)', r'\1\2', content)
                
                # Remove empty lines between function definition and return statement for all functions
                content = re.sub(r'(def [a-zA-Z0-9_]+\(self(?:, [^\)]+)?\):\n)\s*\n(\s+return)', r'\1\2', content)
                
                with open(file_path, 'w') as f:
                    f.write(content)
                
                # print(f"Fixed formatting for {file_path}")

def main(config_path, output_dir):
    """Main function to generate client classes from ABIs."""
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    
    for contract in config['contracts']:
        contract_name = contract['contract_name']
        functions = contract['functions']
        try:
            abi = load_abi_from_file(contract_name)
            generate_python_class_from_abi(abi, contract_name, functions, output_dir)
        except Exception as e:
            print(f"Error generating class for {contract_name}: {e}")
    
    # Fix formatting in all generated client files
    fix_client_formatting(output_dir)

if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    output_dir = os.path.join(os.path.dirname(__file__), '../abi')
    os.makedirs(output_dir, exist_ok=True)
    main(config_path, output_dir) 