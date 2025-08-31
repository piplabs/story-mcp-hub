# New tests for gas_utils and contract_addresses to improve coverage
import math
import pytest

from types import SimpleNamespace

from utils.gas_utils import (
    wei_to_gwei,
    gwei_to_wei,
    gwei_to_eth,
    wei_to_eth,
    eth_to_wei,
    format_gas_prices,
    calculate_fee,
    convert_units,
    get_gas_price_strategy,
)

from utils.contract_addresses import (
    CHAIN_IDS,
    get_contracts_by_chain_id,
    get_contracts_by_network_name,
    AENEID_CONTRACTS,
    MAINNET_CONTRACTS,
)


class DummyStoryscanService:
    """Very small stub that mimics StoryScanService.get_stats()."""

    def __init__(self, prices):
        self._stats = {"gas_prices": prices}

    def get_stats(self):
        return self._stats


# -------------------------------------------------------------
# gas_utils – conversion helpers
# -------------------------------------------------------------
@pytest.mark.parametrize(
    "value,from_unit,to_unit,expected",
    [
        (10**18, "wei", "eth", 1.0),
        (1, "gwei", "wei", 1_000_000_000),
        (1_500_000_000, "wei", "gwei", 1.5),
        (1, "eth", "wei", 10**18),
        (1, "gwei", "eth", 1e-9),
    ],
)
def test_convert_units_numeric(value, from_unit, to_unit, expected):
    result = convert_units(value, from_unit, to_unit)
    assert math.isclose(result["converted_value"], expected, rel_tol=1e-12)


def test_calculate_fee_happy_path():
    fee_info = calculate_fee(gas_price=20, gas_limit=21_000)
    # 20 gwei → 20 * 1e9 wei per gas → 4.2e14 wei total
    assert fee_info["fee_wei"] == 20 * 1_000_000_000 * 21_000
    # Cross-check some helper conversions used inside
    assert math.isclose(fee_info["fee_eth"], wei_to_eth(fee_info["fee_wei"]))


@pytest.mark.parametrize(
    "prices,to_unit,expected_first",
    [
        ({"slow": 1_000_000_000}, "gwei", 1.0),
        ({"slow": 1_000_000_000}, "eth", 1e-9),
        ({"slow": 1_000_000_000}, "wei", 1_000_000_000),
    ],
)
def test_format_gas_prices_conversion(prices, to_unit, expected_first):
    formatted = format_gas_prices(prices, to_unit=to_unit)
    assert math.isclose(formatted["slow"], expected_first, rel_tol=1e-12)


def test_get_gas_price_strategy_average():
    svc = DummyStoryscanService({"slow": 10, "average": 20, "fast": 30})
    assert get_gas_price_strategy("average", storyscan_service=svc) == 20


# -------------------------------------------------------------
# contract_addresses – selection helpers
# -------------------------------------------------------------

def test_get_contracts_by_chain_id_known():
    assert get_contracts_by_chain_id(CHAIN_IDS["aeneid"]) is AENEID_CONTRACTS
    assert get_contracts_by_chain_id(CHAIN_IDS["mainnet"]) is MAINNET_CONTRACTS


def test_get_contracts_by_chain_id_invalid():
    with pytest.raises(ValueError):
        get_contracts_by_chain_id(999_999)


def test_get_contracts_by_network_name():
    assert get_contracts_by_network_name("Aeneid") is AENEID_CONTRACTS
    assert get_contracts_by_network_name("mainnet") is MAINNET_CONTRACTS
    with pytest.raises(ValueError):
        get_contracts_by_network_name("unknownNet") 