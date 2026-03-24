from __future__ import annotations

from dataclasses import dataclass

from trading_bot.config import BotConfig
from trading_bot.exchange import ExchangeClient
from trading_bot.strategy import compute_signal


@dataclass
class Position:
    side: str
    entry_price: float
    amount: float


class PaperPortfolio:
    def __init__(self, initial_usdt: float = 1000.0) -> None:
        self.usdt_balance = initial_usdt
        self.position: Position | None = None

    def open_long(self, price: float, usdt_size: float) -> None:
        amount = usdt_size / price
        self.usdt_balance -= usdt_size
        self.position = Position(side="LONG", entry_price=price, amount=amount)

    def close_long(self, price: float) -> float:
        if not self.position:
            return 0.0
        proceeds = self.position.amount * price
        cost = self.position.amount * self.position.entry_price
        pnl = proceeds - cost
        self.usdt_balance += proceeds
        self.position = None
        return pnl


def position_size(config: BotConfig, balance: float, price: float) -> float:
    risk_budget = balance * config.risk_per_trade
    stop_loss_distance = price * config.stop_loss_pct
    size_from_risk = risk_budget / stop_loss_distance * price
    return min(size_from_risk, config.max_position_size, balance)


class TradingEngine:
    def __init__(self, config: BotConfig, portfolio: PaperPortfolio, client: ExchangeClient) -> None:
        self.config = config
        self.portfolio = portfolio
        self.client = client

    def step(self) -> dict:
        df = self.client.fetch_ohlcv(
            self.config.symbol, self.config.timeframe, limit=max(150, self.config.slow_ma + 10)
        )
        price = float(df["close"].iloc[-1])
        signal = compute_signal(df, self.config.fast_ma, self.config.slow_ma)
        event = "NONE"
        pnl = 0.0

        if self.portfolio.position:
            change = (price - self.portfolio.position.entry_price) / self.portfolio.position.entry_price
            if change <= -self.config.stop_loss_pct or change >= self.config.take_profit_pct:
                pnl = self.portfolio.close_long(price)
                event = "RISK_EXIT"
                signal = "HOLD"

        if signal == "BUY" and self.portfolio.position is None:
            size = position_size(self.config, self.portfolio.usdt_balance, price)
            if size > 10:
                if self.config.live_trading:
                    amount = size / price
                    self.client.place_market_order(self.config.symbol, "buy", amount)
                self.portfolio.open_long(price, size)
                event = "BUY"

        elif signal == "SELL" and self.portfolio.position is not None:
            if self.config.live_trading:
                self.client.place_market_order(self.config.symbol, "sell", self.portfolio.position.amount)
            pnl = self.portfolio.close_long(price)
            event = "SELL"

        return {
            "event": event,
            "price": price,
            "signal": signal,
            "balance": self.portfolio.usdt_balance,
            "pnl": pnl,
            "position": self.portfolio.position,
            "df": df,
        }
