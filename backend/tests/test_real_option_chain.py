"""Unit tests for OptionChainEngine and Black-Scholes Greeks."""

import pytest

from app.marketdata.option_chain import OptionChain, OptionChainEngine, calculate_option_greeks


def test_black_scholes_greeks_ce():
    delta, gamma, theta, vega = calculate_option_greeks(24900.0, 24900.0, 0.02, 0.07, 15.0, "CE")
    assert 0.45 <= delta <= 0.60
    assert gamma > 0.0
    assert theta < 0.0
    assert vega > 0.0


def test_black_scholes_greeks_pe():
    delta, gamma, theta, vega = calculate_option_greeks(24900.0, 24900.0, 0.02, 0.07, 15.0, "PE")
    assert -0.60 <= delta <= -0.40
    assert gamma > 0.0
    assert theta < 0.0
    assert vega > 0.0


def test_option_chain_generation_nifty():
    chain = OptionChainEngine.generate_chain("NIFTY", 24915.20)
    assert isinstance(chain, OptionChain)
    assert chain.symbol == "NIFTY"
    assert chain.atm_strike == 24900.0
    assert chain.pcr > 0.0
    assert len(chain.calls) == 11
    assert len(chain.puts) == 11
    assert 24900.0 in chain.calls
    assert chain.calls[24900.0].is_atm


def test_option_chain_max_pain_and_support_resistance():
    chain = OptionChainEngine.generate_chain("BANKNIFTY", 55201.00)
    assert chain.support_level > 0.0
    assert chain.resistance_level > 0.0
    assert chain.highest_call_oi_strike > 0.0
    assert chain.highest_put_oi_strike > 0.0
