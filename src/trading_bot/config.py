from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass
class BotConfig:
    data_source: str = os.getenv("DATA_SOURCE", "yfinance")
    symbol: str = os.getenv("SYMBOL", "RELIANCE.NS")
    timeframe: str = os.getenv("TIMEFRAME", "1m")
    fast_ma: int = int(os.getenv("FAST_MA", "9"))
    slow_ma: int = int(os.getenv("SLOW_MA", "21"))
    risk_per_trade: float = float(os.getenv("RISK_PER_TRADE", "0.01"))
    max_position_size: float = float(os.getenv("MAX_POSITION_SIZE", os.getenv("MAX_POSITION_SIZE_USDT", "10000")))
    poll_seconds: int = int(os.getenv("POLL_SECONDS", "20"))
    live_trading: bool = _to_bool(os.getenv("LIVE_TRADING"), default=False)
    api_key: str = os.getenv("EXCHANGE_API_KEY", "")
    api_secret: str = os.getenv("EXCHANGE_API_SECRET", "")
    stop_loss_pct: float = 0.01
    take_profit_pct: float = 0.02

    def validate(self) -> None:
        if self.data_source not in {"binance", "yfinance"}:
            raise ValueError("DATA_SOURCE must be 'binance' or 'yfinance'")
        if self.fast_ma >= self.slow_ma:
            raise ValueError("FAST_MA must be lower than SLOW_MA")
        if not (0 < self.risk_per_trade <= 0.05):
            raise ValueError("RISK_PER_TRADE must be between 0 and 0.05")
        if self.max_position_size <= 0:
            raise ValueError("MAX_POSITION_SIZE must be positive")
