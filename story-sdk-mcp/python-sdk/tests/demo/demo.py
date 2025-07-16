import os
from dotenv import load_dotenv
from web3 import Web3

from story_protocol_python_sdk import StoryClient
from demo_utils import get_token_id, MockERC721, MockERC20, mint_tokens, ROYALTY_POLICY, ROYALTY_MODULE, PIL_LICENSE_TEMPLATE

def main():
    # 1. Set up your Story Config
    load_dotenv()
    private_key = os.getenv('WALLET_PRIVATE_KEY')
    rpc_url = os.getenv('RPC_PROVIDER_URL')

    if not private_key:
        raise ValueError("WALLET_PRIVATE_KEY environment variable is not set")
    if not rpc_url:
        raise ValueError("RPC_PROVIDER_URL environment variable is not set")

    # Initialize Web3
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    if not web3.is_connected():
        raise Exception("Failed to connect to Web3 provider")

    # Set up the account with the private key
    account = web3.eth.account.from_key(private_key)

    # Create StoryClient instance
    story_client = StoryClient(web3, account, 1315)

    # 2. Register an IP Asset
    token_id = get_token_id(MockERC721, story_client.web3, story_client.account)

    registered_ip_asset_response = story_client.IPAsset.register(
        nft_contract=MockERC721,
        token_id=token_id
    )
    print(f"Root IPA created at transaction hash {registered_ip_asset_response['txHash']}, IPA ID: {registered_ip_asset_response['ipId']}")

    # 3. Register PIL Terms
    register_pil_terms_response = story_client.License.registerCommercialUsePIL(
        default_minting_fee=1,
        currency=MockERC20,
        royalty_policy=ROYALTY_POLICY
    )
    if 'txHash' in register_pil_terms_response:
        print(f"PIL Terms registered at transaction hash {register_pil_terms_response['txHash']}, License Terms ID: {register_pil_terms_response['licenseTermsId']}")
    else:
        print(f"License Terms ID: {register_pil_terms_response['licenseTermsId']}, already registered.")

    # 4. Attach License Terms to IP
    try:
        attach_license_terms_response = story_client.License.attachLicenseTerms(
            ip_id=registered_ip_asset_response['ipId'],
            license_template=PIL_LICENSE_TEMPLATE,
            license_terms_id=register_pil_terms_response['licenseTermsId']
        )
        print(f"Attached License Terms to IP at transaction hash {attach_license_terms_response['txHash']}")
    except Exception as e:
        print(f"License Terms ID {register_pil_terms_response['licenseTermsId']} already attached to this IPA.")

    #Before you mint make sure you have enough ERC20 tokens according to the minting fee above
    token_ids = mint_tokens(MockERC20, web3, account, account.address, 10000)

    # 5. Mint License
    mint_license_response = story_client.License.mintLicenseTokens(
        licensor_ip_id=registered_ip_asset_response['ipId'],
        license_template=PIL_LICENSE_TEMPLATE,
        license_terms_id=register_pil_terms_response['licenseTermsId'],
        amount=1,
        receiver=account.address,
        max_minting_fee=1,
        max_revenue_share=0
    )
    print(f"License Token minted at transaction hash {mint_license_response['txHash']}, License Token IDs: {mint_license_response['licenseTokenIds']}")

    # 6. Mint derivative IP Asset using your license
    derivative_token_id = get_token_id(MockERC721, story_client.web3, story_client.account)
    registered_ip_asset_derivative_response = story_client.IPAsset.register(
        nft_contract=MockERC721,
        token_id=derivative_token_id
    )
    print(f"Derivative IPA created at transaction hash {registered_ip_asset_derivative_response['txHash']}, IPA ID: {registered_ip_asset_derivative_response['ipId']}")

    link_derivative_response = story_client.IPAsset.registerDerivativeWithLicenseTokens(
        child_ip_id=registered_ip_asset_derivative_response['ipId'],
        license_token_ids=mint_license_response['licenseTokenIds'],
        max_rts=5 * 10 ** 6
    )
    print(f"Derivative IPA linked to parent at transaction hash {link_derivative_response['txHash']}")

if __name__ == "__main__":
    main()
