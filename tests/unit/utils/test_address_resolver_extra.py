# Additional tests for utils.address_resolver to increase coverage and surface edge-case bugs

import pytest
from types import SimpleNamespace

from utils.address_resolver import AddressResolver


class DummyWeb3:
    """Minimal stub of a Web3 instance suitable for AddressResolver unit tests."""

    def __init__(self):
        # We keep an internal set of addresses we consider "valid" so we can
        # tweak behaviour per-test.
        self._valid_addresses = set()

    # ------------------------------------------------------------------
    # API methods that AddressResolver relies on
    # ------------------------------------------------------------------
    @staticmethod
    def is_address(addr: str) -> bool:  # type: ignore[override]
        # Accept any 42-char 0x-prefixed hex string regardless of case.
        return (
            isinstance(addr, str)
            and addr.lower().startswith("0x")
            and len(addr) == 42
            and all(c in "0123456789abcdef" for c in addr[2:].lower())
        )

    @staticmethod
    def to_checksum_address(addr: str) -> str:  # type: ignore[override]
        # For the sake of these tests we pretend checksum == lowercase
        return addr.lower()

    # Web3.provider property needed by ENS() constructor
    @property
    def provider(self):  # pragma: no cover – not really used
        return SimpleNamespace()


class DummyENS:
    """Stub for the ens.ENS class so we don't require a main-net provider."""

    def __init__(self):
        self._forward = {}
        self._reverse = {}

    # Forward resolution (name → address)
    def address(self, name):  # noqa: D401 – mimic ENS API naming
        return self._forward.get(name)

    # Reverse resolution (address → name)
    def name(self, address):
        return self._reverse.get(address)


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------
@pytest.fixture()
def resolver(monkeypatch):
    """Return an AddressResolver wired up with dummy Web3 + ENS stubs."""

    w3 = DummyWeb3()

    # Ensure that when AddressResolver initialises ENS(...) it gets our stub
    # instead of the real class (which requires a genuine Web3 provider).
    monkeypatch.setattr("utils.address_resolver.ENS", lambda _provider: DummyENS())

    ar = AddressResolver(w3)
    return ar


# ----------------------------------------------------------------------
# Happy-path cases (should PASS)
# ----------------------------------------------------------------------

def test_resolve_address_direct(resolver):
    """Passing a freshly checksummed address should be returned unchanged."""
    addr = "0x" + "a" * 40
    assert resolver.resolve_address(addr) == addr


def test_resolve_address_ens(monkeypatch, resolver):
    """Domain ending with .eth should resolve via the ENS stub."""
    domain = "alice.eth"
    addr = "0x" + "b" * 40

    # Teach the stub about the mapping
    resolver.ens._forward[domain] = addr

    assert resolver.resolve_address(domain) == addr


# ----------------------------------------------------------------------
# Edge-case BUG: uppercase "0X" prefix currently rejected by _is_ethereum_address
# ----------------------------------------------------------------------

def test_is_ethereum_address_accepts_uppercase_prefix(resolver):
    """The helper should accept addresses starting with '0X' as valid (EIP-55 allows it).

    At the moment AddressResolver._is_ethereum_address is case-sensitive and
    returns False – that is a *bug* the project should fix.  This test therefore
    **expects** True and will FAIL until the implementation is corrected.
    """

    uppercase_addr = "0X" + "c" * 40
    # The stub's DummyWeb3.is_address *is* case-insensitive, so we only fail if
    # _is_ethereum_address mistakenly insists on lowercase.
    assert resolver._is_ethereum_address(uppercase_addr) is True


# ----------------------------------------------------------------------
# Failure paths (should raise / return None)
# ----------------------------------------------------------------------

def test_resolve_address_unknown_domain_raises(resolver):
    with pytest.raises(ValueError):
        resolver.resolve_address("unknown-domain.xyz")


def test_get_domain_for_address_not_found(resolver):
    """Reverse lookup should return None when ENS & SpaceID have no match."""
    assert resolver.get_domain_for_address("0x" + "d" * 40) is None 