"""Unit tests for OptionChainEngine."""

from app.marketdata.option_chain import OptionChain, OptionChainEngine, OptionContract


def test_option_chain_engine_strike_step():
    assert OptionChainEngine.get_strike_step("NIFTY") == 50.0
    assert OptionChainEngine.get_strike_step("BANKNIFTY") == 100.0
    assert OptionChainEngine.get_strike_step("FINNIFTY") == 50.0
    assert OptionChainEngine.get_strike_step("SENSEX") == 100.0
    assert OptionChainEngine.get_strike_step("UNKNOWN") == 50.0


def test_option_chain_engine_calculate_atm_strike():
    assert OptionChainEngine.calculate_atm_strike("NIFTY", 24915.20) == 24900.0
    assert OptionChainEngine.calculate_atm_strike("NIFTY", 24935.00) == 24950.0
    assert OptionChainEngine.calculate_atm_strike("BANKNIFTY", 55210.00) == 55200.0


def test_option_chain_engine_generate_chain():
    chain = OptionChainEngine.generate_chain("NIFTY", 24915.20, num_strikes=3)

    assert isinstance(chain, OptionChain)
    assert chain.underlying_symbol == "NIFTY"
    assert chain.spot_price == 24915.20
    assert chain.atm_strike == 24900.0
    assert chain.pcr > 0.0
    assert len(chain.calls) == 7
    assert len(chain.puts) == 7


def test_option_chain_engine_atm_contract_getters():
    chain = OptionChainEngine.generate_chain("NIFTY", 24915.20, num_strikes=2)
    atm_call = chain.get_atm_call()
    atm_put = chain.get_atm_put()

    assert isinstance(atm_call, OptionContract)
    assert isinstance(atm_put, OptionContract)
    assert atm_call.strike == 24900.0
    assert atm_call.option_type == "CE"
    assert atm_put.option_type == "PE"


def test_option_contract_fields():
    contract = OptionContract(
        symbol="NIFTY_24900_CE",
        underlying="NIFTY",
        strike=24900.0,
        option_type="CE",
        ltp=118.0,
        iv=14.5,
        oi=150000,
        oi_change=4.2,
        delta=0.52,
    )
    assert contract.symbol == "NIFTY_24900_CE"
    assert contract.ltp == 118.0
    assert contract.delta == 0.52
