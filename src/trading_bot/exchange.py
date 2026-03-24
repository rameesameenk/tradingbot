from __future__ import annotations

import ccxt
import pandas as pd
import yfinance as yf


class ExchangeClient:
    def __init__(self, source: str = "binance", api_key: str = "", api_secret: str = "") -> None:
        self.source = source
        self.exchange = None
        if self.source == "binance":
            params = {"enableRateLimit": True}
            if api_key and api_secret:
                params.update({"apiKey": api_key, "secret": api_secret})
            self.exchange = ccxt.binance(params)

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 150) -> pd.DataFrame:
        if self.source == "binance":
            raw = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
            return df

        interval = self._to_yf_interval(timeframe)
        period = self._yf_period_for_interval(interval)
        hist = yf.Ticker(symbol).history(period=period, interval=interval)
        if hist.empty:
            raise ValueError(f"No market data found for symbol '{symbol}' with interval '{interval}'")
        hist = hist.reset_index().tail(limit)
        ts_col = "Datetime" if "Datetime" in hist.columns else "Date"
        df = hist.rename(
            columns={
                ts_col: "timestamp",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )[["timestamp", "open", "high", "low", "close", "volume"]]
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        return df

    def place_market_order(self, symbol: str, side: str, amount: float):
        if self.source != "binance":
            raise NotImplementedError("Live order placement is only supported for binance in this starter project.")
        return self.exchange.create_market_order(symbol, side, amount)

    @staticmethod
    def _to_yf_interval(timeframe: str) -> str:
        mapping = {"1h": "60m"}
        return mapping.get(timeframe, timeframe)

    @staticmethod
    def _yf_period_for_interval(interval: str) -> str:
        if interval == "1m":
            return "7d"
        if interval in {"2m", "5m", "15m", "30m", "60m", "90m", "1h"}:
            return "60d"
        return "1y"
