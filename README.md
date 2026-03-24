# Trading Bot Starter (Python)

This bot supports Indian stocks (NSE via Yahoo Finance) and crypto (Binance).

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run UI (paper mode)
```bash
streamlit run app.py
```

## Run CLI loop
```bash
PYTHONPATH=src python -m trading_bot.main
```

## Export Full Indian Market Lists
This exports complete NSE datasets (equities, indices, futures, options) from the Upstox instrument master.

```bash
source .venv/bin/activate
python scripts/export_indian_market.py
```

Output files:
- `data/indian_market/nse_equities.csv`
- `data/indian_market/nse_indices.csv`
- `data/indian_market/nse_futures.csv`
- `data/indian_market/nse_options.csv`
- `data/indian_market/summary.csv`

## Notes
- UI is paper mode only.
- `yfinance` provides market data, not order execution.
- Current live order placement in this starter is only implemented for Binance.
