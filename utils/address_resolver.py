import requests
from web3 import Web3
from typing import Optional
from ens import ENS


class AddressResolver:
    """
    Utility class for resolving addresses from domain names and vice versa.
    Implements a chain of responsibility pattern for address resolution.
    Supports both ENS (.eth) and Space ID (.ip) domains.
    """

    def __init__(self, web3: Web3, chain_id: int = 1514):
        """
        Initialize the address resolver.

        Args:
            web3: Web3 instance for address validation and formatting
            chain_id: Chain ID for the blockchain (default: 1514 for Story Protocol)
        """
        self.web3 = web3
        self.chain_id = chain_id
        self.space_id_api_url = "https://nameapi.space.id"
        # Initialize ENS instance
        self.ens = ENS(web3.provider)

    def resolve_address(self, address_or_domain: str) -> str:
        """
        Resolve a domain name to an address or return the address if it's already in address format.
        Chain of responsibility: check if it's an address, try ENS, then try Space ID.

        Args:
            address_or_domain: Either an Ethereum address (0x...) or a domain name (name.eth or name.ip)

        Returns:
            str: The resolved Ethereum address

        Raises:
            ValueError: If the address cannot be resolved
        """
        # First handler: Check if it's already an address
        if self._is_ethereum_address(address_or_domain):
            return self.web3.to_checksum_address(address_or_domain)

        # Second handler: Try to resolve as ENS domain
        if address_or_domain.lower().endswith(".eth"):
            ens_address = self._resolve_ens_domain(address_or_domain)
            if ens_address:
                return self.web3.to_checksum_address(ens_address)

        # Third handler: Try to resolve as a Space ID domain
        space_id_address = self._resolve_domain_to_address(address_or_domain)
        if space_id_address:
            return self.web3.to_checksum_address(space_id_address)

        # If we get here, we couldn't resolve the address
        raise ValueError(f"Could not resolve address or domain: {address_or_domain}")

    def get_domain_for_address(self, address: str) -> Optional[str]:
        """
        Get the primary domain name for an address.
        Tries both ENS and Space ID reverse resolution.

        Args:
            address: Ethereum address

        Returns:
            str: The domain name or None if not found
        """
        try:
            # Ensure address is in correct format
            address = self.web3.to_checksum_address(address)

            # Try ENS reverse resolution first
            ens_name = self._get_ens_name(address)
            if ens_name:
                return ens_name

            # If no ENS name, try Space ID
            response = requests.get(
                f"{self.space_id_api_url}/getName?chainid={self.chain_id}&address={address}"
            )

            if response.status_code != 200:
                return None

            data = response.json()

            if data.get("code") != 0:
                return None

            return data.get("name")

        except Exception:
            return None

    def _is_ethereum_address(self, value: str) -> bool:
        """Check if a string is a valid Ethereum address."""
        # Accept either '0x' or '0X' prefix (EIP-55 allows upper-case)
        return (
            isinstance(value, str)
            and value[:2].lower() == "0x"
            and len(value) == 42
            and self.web3.is_address(value)
        )

    def _resolve_ens_domain(self, domain: str) -> Optional[str]:
        """Resolve an ENS domain name to an address."""
        try:
            address = self.ens.address(domain)
            return address if address else None
        except Exception:
            return None

    def _get_ens_name(self, address: str) -> Optional[str]:
        """Get the ENS name for an address using reverse resolution."""
        try:
            name = self.ens.name(address)
            # Verify the forward resolution matches
            if name and self.ens.address(name) == address:
                return name
            return None
        except Exception:
            return None

    def _resolve_domain_to_address(self, domain: str) -> Optional[str]:
        """Resolve a Space ID domain name to an address using Space ID API."""
        try:
            # Make request to Space ID API
            response = requests.get(
                f"{self.space_id_api_url}/getAddress?domain={domain}"
            )

            if response.status_code != 200:
                return None

            data = response.json()

            if data.get("code") != 0:
                return None

            return data.get("address")

        except Exception:
            return None


# Create a convenience function for easy importing
def create_address_resolver(web3: Web3, chain_id: int = 1514) -> AddressResolver:
    """
    Create an AddressResolver instance.

    Args:
        web3: Web3 instance
        chain_id: Chain ID for the blockchain (default: 1514 for Story Protocol)

    Returns:
        AddressResolver: An instance of the AddressResolver
    """
    return AddressResolver(web3, chain_id)
