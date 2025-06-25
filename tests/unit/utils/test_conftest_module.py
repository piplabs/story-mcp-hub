# Tests that directly exercise the fixture-factory functions defined in tests/conftest.py
# We *don't* rely on Pytest's fixture mechanism here - instead we import the
# module and call the fixture functions like normal Python callables so that we
# can assert on their behaviour in isolation.  This raises coverage for the
# helpers while also detecting subtle mistakes (e.g. mismatched mock shapes).

import os
import types

import pytest

import tests.conftest as cf


# ---------------------------------------------------------------------------
# load_env - ensure it adds and removes the TESTING env-var
# ---------------------------------------------------------------------------

def test_load_env_adds_and_removes_testing_var(monkeypatch, tmp_path):
    # Simulate an `.env.test` file so the fixture's logic takes that branch
    env_file = tmp_path / ".env.test"
    env_file.write_text("DUMMY_KEY=abc\n")

    monkeypatch.chdir(tmp_path)  # make cwd the temp dir where the file exists

    # Obtain the generator returned by the fixture factory and run it manually
    gen = cf.load_env.__wrapped__()  # type: ignore[attr-defined]
    assert isinstance(gen, types.GeneratorType)

    # Ensure starting condition: remove existing TESTING to get predictable behaviour
    if "TESTING" in os.environ:
        prev_val = os.environ.pop("TESTING")
    else:
        prev_val = None

    # Run the setup part of the fixture
    next(gen)
    assert os.environ["TESTING"] == "1"

    # Run the teardown part
    with pytest.raises(StopIteration):
        next(gen)

    if prev_val:
        os.environ["TESTING"] = prev_val
    else:
        assert "TESTING" not in os.environ


# ---------------------------------------------------------------------------
# mock_web3 - basic contract to expected Web3 API surface
# ---------------------------------------------------------------------------

def test_mock_web3_behaviour():
    w3 = cf.mock_web3.__wrapped__()  # type: ignore[attr-defined]

    # Connection state
    assert w3.is_connected() is True  # noqa: B011  # function call in mock

    # Numeric properties
    assert w3.eth.chain_id == 1315
    assert w3.eth.gas_price == 20_000_000_000

    # Helper conversions should mirror Web3.toWei / fromWei
    assert w3.to_wei(1, "ether") == 10**18
    assert w3.from_wei(10**9, "gwei") == 1

    # Account stub has address attribute
    acct = w3.eth.account.from_key("0xdead")
    assert acct.address.startswith("0x")


# ---------------------------------------------------------------------------
# mock_story_client - ensure inner mocks return expected keys
# ---------------------------------------------------------------------------

def test_mock_story_client_shapes():
    client = cf.mock_story_client.__wrapped__()  # type: ignore[attr-defined]

    # License.getLicenseTerms returns a 17-element list (contract ABI spec)
    terms = client.License.getLicenseTerms(1)
    assert isinstance(terms, list) and len(terms) == 17

    # mintLicenseTokens returns dict that includes licenseTokenIds list
    minted = client.License.mintLicenseTokens()
    assert minted["licenseTokenIds"]

    # IPAsset.mintAndRegister... returns dict with ipId and tokenId keys
    reg = client.IPAsset.mintAndRegisterIpAssetWithPilTerms()
    assert set(reg).issuperset({"ipId", "tokenId", "licenseTermsIds"}) 