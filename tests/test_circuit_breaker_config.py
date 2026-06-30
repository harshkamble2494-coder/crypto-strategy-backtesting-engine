from crypto_futures_bot.config.loader import load_config


def test_circuit_breaker_defaults_to_disabled_for_v2_config() -> None:
    config = load_config("config/settings_v2.yaml")

    assert config.circuit_breaker.enabled is False
    assert config.circuit_breaker.resume_mode == "candles"


def test_circuit_breaker_loads_v4_config() -> None:
    config = load_config("config/settings_v4_circuit_breaker.yaml")

    assert config.circuit_breaker.enabled is True
    assert config.circuit_breaker.consecutive_loss_threshold == 2
    assert config.circuit_breaker.cooldown_candles == 24
    assert config.circuit_breaker.resume_mode == "candles"
    assert config.strategy.name == "trend_quality_ema_rsi_v2"
    assert config.risk.exit_mode == "fixed"
