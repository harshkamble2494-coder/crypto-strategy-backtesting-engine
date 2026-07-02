from __future__ import annotations

import argparse
import json
import logging

import pandas as pd

from crypto_futures_bot.backtesting.backtest_engine import BacktestEngine
from crypto_futures_bot.config.loader import load_config
from crypto_futures_bot.data.data_loader import CsvDataLoader
from crypto_futures_bot.reporting.metrics import MetricsCalculator
from crypto_futures_bot.reporting.report_generator import ReportGenerator
from crypto_futures_bot.reporting.trade_logger import TradeLogger
from crypto_futures_bot.utilities.logger import configure_logging
from crypto_futures_bot.utilities.paths import create_backtest_output_dir
from crypto_futures_bot.visualization.charts import ChartGenerator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a crypto futures backtest.")
    parser.add_argument("--config", default="config/settings.yaml", help="Path to YAML config file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    configure_logging(config.logging)
    logger = logging.getLogger(__name__)

    logger.info("Loading historical data from %s", config.data.csv_path)
    candles = CsvDataLoader(config.data).load()

    output_dir = create_backtest_output_dir(config.backtest.results_dir, config.data.symbol, config.data.timeframe)
    logger.info("Running backtest. Outputs: %s", output_dir)
    result = BacktestEngine(config, output_dir).run(candles)

    TradeLogger().write_csv(result.trades, output_dir / "trades.csv")
    result.equity_curve.to_csv(output_dir / "equity_curve.csv", index=False)

    metrics = MetricsCalculator().calculate(result.trades, result.equity_curve, config.backtest.initial_capital)
    metadata = {
        "strategy_name": config.strategy.name,
        "exit_mode": config.risk.exit_mode,
        "take_profit_enabled": config.risk.take_profit_enabled,
        "stop_loss_pct": config.risk.stop_loss_pct,
        "take_profit_pct": config.risk.take_profit_pct,
        "atr_stop_loss_multiplier": config.risk.atr_stop_loss_multiplier,
        "atr_take_profit_multiplier": config.risk.atr_take_profit_multiplier,
        "break_even_enabled": config.risk.break_even_enabled,
        "break_even_trigger_atr_multiplier": config.risk.break_even_trigger_atr_multiplier,
        "trailing_stop_enabled": config.risk.trailing_stop_enabled,
        "trailing_stop_activation_atr_multiplier": config.risk.trailing_stop_activation_atr_multiplier,
        "trailing_stop_atr_multiplier": config.risk.trailing_stop_atr_multiplier,
        "circuit_breaker_enabled": config.circuit_breaker.enabled,
        "circuit_breaker_consecutive_loss_threshold": config.circuit_breaker.consecutive_loss_threshold,
        "circuit_breaker_cooldown_candles": config.circuit_breaker.cooldown_candles,
        "circuit_breaker_resume_mode": config.circuit_breaker.resume_mode,
    }
    ReportGenerator().write_json(metrics, output_dir / "performance_report.json", metadata=metadata)
    ReportGenerator().write_text(metrics, output_dir / "performance_report.txt", metadata=metadata)
    (output_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    circuit_breaker_stats = {
        "blocked_trades": result.circuit_breaker_stats.blocked_trades,
        "cooldown_periods": result.circuit_breaker_stats.cooldown_periods,
        "average_cooldown_duration": result.circuit_breaker_stats.average_cooldown_duration,
        "consecutive_loss_clusters": result.circuit_breaker_stats.consecutive_loss_clusters,
    }
    (output_dir / "circuit_breaker_stats.json").write_text(
        json.dumps(circuit_breaker_stats, indent=2),
        encoding="utf-8",
    )
    pd.DataFrame([period.__dict__ for period in result.circuit_breaker_stats.blocked_periods]).to_csv(
        output_dir / "blocked_periods.csv",
        index=False,
    )
    ChartGenerator().generate_all(result.equity_curve, result.trades, output_dir)

    logger.info("Backtest complete. Total trades: %s", metrics.total_trades)
    logger.info("Net profit: %.2f | Total return: %.2f%%", metrics.net_profit, metrics.total_return_pct)


if __name__ == "__main__":
    main()
