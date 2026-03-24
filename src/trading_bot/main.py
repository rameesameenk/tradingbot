from __future__ import annotations

import time

from trading_bot.config import BotConfig
from trading_bot.exchange import ExchangeClient
from trading_bot.engine import PaperPortfolio, TradingEngine


def run() -> None:
    config = BotConfig()
    config.validate()

    client = ExchangeClient(source=config.data_source, api_key=config.api_key, api_secret=config.api_secret)
    portfolio = PaperPortfolio(initial_usdt=1000.0)
    engine = TradingEngine(config=config, portfolio=portfolio, client=client)

    print(
        f"Starting bot source={config.data_source} symbol={config.symbol} timeframe={config.timeframe}, "
        f"live={config.live_trading}"
    )

    while True:
        try:
            result = engine.step()
            event = result["event"]
            price = result["price"]
            signal = result["signal"]
            pnl = result["pnl"]
            position_state = "open" if result["position"] else "flat"

            if event == "BUY":
                print(f"BUY {config.symbol} at {price:.2f}, balance={result['balance']:.2f}")
            elif event == "SELL":
                print(f"SELL {config.symbol} at {price:.2f}, PnL={pnl:.2f}, balance={result['balance']:.2f}")
            elif event == "RISK_EXIT":
                print(f"Risk exit at {price:.2f}, PnL={pnl:.2f}, balance={result['balance']:.2f}")
            else:
                print(
                    f"price={price:.2f}, signal={signal}, position={position_state}, balance={result['balance']:.2f}"
                )

        except Exception as exc:
            print(f"Loop error: {exc}")

        time.sleep(config.poll_seconds)


if __name__ == "__main__":
    run()
