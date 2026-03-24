#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import pandas as pd

URL = "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz"
OUT_DIR = Path("data/indian_market")


def _clean_columns(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    available = [c for c in cols if c in df.columns]
    return df[available].copy()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_json(URL, compression="gzip")
    df = df[df["exchange"].eq("NSE")].copy()

    common_cols = [
        "segment",
        "instrument_type",
        "trading_symbol",
        "name",
        "underlying_symbol",
        "expiry",
        "strike_price",
        "lot_size",
        "tick_size",
        "instrument_key",
        "exchange_token",
    ]

    equities = df[df["segment"].eq("NSE_EQ")].copy()
    indices = df[df["segment"].eq("NSE_INDEX")].copy()
    nse_fo = df[df["segment"].eq("NSE_FO")].copy()

    futures = nse_fo[nse_fo["instrument_type"].eq("FUT")].copy()
    options = nse_fo[nse_fo["instrument_type"].isin(["CE", "PE"])].copy()

    _clean_columns(equities, common_cols + ["isin"]).to_csv(OUT_DIR / "nse_equities.csv", index=False)
    _clean_columns(indices, common_cols).to_csv(OUT_DIR / "nse_indices.csv", index=False)
    _clean_columns(futures, common_cols).to_csv(OUT_DIR / "nse_futures.csv", index=False)
    _clean_columns(options, common_cols).to_csv(OUT_DIR / "nse_options.csv", index=False)

    summary = {
        "nse_equities": len(equities),
        "nse_indices": len(indices),
        "nse_futures": len(futures),
        "nse_options": len(options),
        "total_nse_rows": len(df),
    }
    pd.DataFrame([summary]).to_csv(OUT_DIR / "summary.csv", index=False)

    print("Export complete:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print(f"Files saved in: {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
