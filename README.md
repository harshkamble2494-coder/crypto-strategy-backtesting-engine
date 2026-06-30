# Crypto Futures Trading Bot

Phase 1 implements a modular backtesting engine for a BTCUSDT 1-hour crypto futures strategy. Paper trading, live trading, and CoinDCX integration are intentionally left for later phases.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

## Data

Place historical candles at:

```text
data/raw/BTCUSDT_1h.csv
```

Required columns:

```text
timestamp,open,high,low,close,volume
```

`timestamp` should be parseable by pandas, preferably UTC. Backtest date ranges are configured in `config/settings.yaml`.

## Run A Backtest

```powershell
python -m crypto_futures_bot.main --config config/settings.yaml
```

Outputs are written to a timestamped folder under `results/backtests/`.

## Phase Boundaries

Implemented now:

- CSV-based historical data loading
- Indicator calculation
- EMA/RSI strategy signal generation
- Futures-style long and short backtesting
- Risk-based position sizing
- Stop loss, take profit, opposite signal exits
- Daily loss lockout
- Fees and slippage
- Trade log, metrics report, and charts
- Unit tests

Placeholders only:

- `exchange/`
- `optimization/`
