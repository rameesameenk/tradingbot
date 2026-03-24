from __future__ import annotations

import pandas as pd
import streamlit as st

from trading_bot.config import BotConfig
from trading_bot.engine import PaperPortfolio, TradingEngine
from trading_bot.exchange import ExchangeClient


@st.cache_data(ttl=90, show_spinner=False)
def fetch_preview_cached(source: str, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    client = ExchangeClient(source=source)
    return client.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)


st.set_page_config(page_title="Trading Bot UI", layout="wide")
st.title("Trading Bot Dashboard")

if "portfolio" not in st.session_state:
    st.session_state.portfolio = PaperPortfolio(initial_usdt=1000.0)
if "trades" not in st.session_state:
    st.session_state.trades = []
if "preview_df" not in st.session_state:
    st.session_state.preview_df = None
if "preview_key" not in st.session_state:
    st.session_state.preview_key = None

config = BotConfig()

with st.sidebar:
    st.header("Settings")
    market_default_idx = 0 if config.data_source == "yfinance" else 1
    market = st.selectbox("Market", options=["NSE (India)", "Crypto"], index=market_default_idx)

    if market == "NSE (India)":
        data_source = "yfinance"
        default_symbol = "RELIANCE.NS"
        timeframe_options = ["1m", "5m", "15m", "30m", "1h", "1d"]
        currency_label = "INR"
    else:
        data_source = "binance"
        default_symbol = "BTC/USDT"
        timeframe_options = ["1m", "5m", "15m", "1h"]
        currency_label = "USDT"

    current_market_source = "yfinance" if market == "NSE (India)" else "binance"
    symbol_default = config.symbol if config.data_source == current_market_source else default_symbol
    symbol = st.text_input("Symbol", value=symbol_default)
    default_idx = timeframe_options.index(config.timeframe) if config.timeframe in timeframe_options else 0
    timeframe = st.selectbox("Timeframe", options=timeframe_options, index=default_idx)
    fast_ma = st.number_input("Fast MA", min_value=2, max_value=100, value=config.fast_ma)
    slow_ma = st.number_input("Slow MA", min_value=3, max_value=200, value=config.slow_ma)
    poll_seconds = st.slider("Refresh seconds", min_value=5, max_value=60, value=config.poll_seconds)
    run_step = st.button("Run One Step")
    refresh_data = st.button("Refresh Data")

runtime_cfg = BotConfig(
    data_source=data_source,
    symbol=symbol or default_symbol,
    timeframe=timeframe,
    fast_ma=int(fast_ma),
    slow_ma=int(slow_ma),
    risk_per_trade=config.risk_per_trade,
    max_position_size=config.max_position_size,
    poll_seconds=int(poll_seconds),
    live_trading=False,
    api_key="",
    api_secret="",
)
try:
    runtime_cfg.validate()
except Exception as exc:
    st.error(f"Invalid configuration: {exc}")
    st.stop()

client = ExchangeClient(source=runtime_cfg.data_source)
engine = TradingEngine(config=runtime_cfg, portfolio=st.session_state.portfolio, client=client)
preview = None
preview_key = (runtime_cfg.data_source, runtime_cfg.symbol, runtime_cfg.timeframe, runtime_cfg.slow_ma)

if run_step:
    try:
        result = engine.step()
        preview = result["df"].copy()
        st.session_state.preview_df = preview
        st.session_state.preview_key = preview_key
        event = result["event"]
        if event in {"BUY", "SELL", "RISK_EXIT"}:
            st.session_state.trades.append(
                {
                    "event": event,
                    "price": round(result["price"], 4),
                    "pnl": round(result["pnl"], 4),
                    "balance": round(result["balance"], 4),
                    "timestamp": pd.Timestamp.utcnow().isoformat(),
                }
            )
    except Exception as exc:
        st.error(f"Step failed: {exc}")
elif refresh_data or st.session_state.preview_df is None or st.session_state.preview_key != preview_key:
    should_fetch = refresh_data
    if st.session_state.preview_df is None and not refresh_data:
        st.info("Click 'Refresh Data' to load market candles.")
        should_fetch = False
    elif st.session_state.preview_key != preview_key and not refresh_data:
        st.info("Settings changed. Click 'Refresh Data' to reload candles.")
        should_fetch = False

    if not should_fetch:
        preview = st.session_state.preview_df
    else:
        try:
            preview = fetch_preview_cached(
                source=runtime_cfg.data_source,
                symbol=runtime_cfg.symbol,
                timeframe=runtime_cfg.timeframe,
                limit=max(100, runtime_cfg.slow_ma + 10),
            ).copy()
            st.session_state.preview_df = preview
            st.session_state.preview_key = preview_key
        except Exception as exc:
            if "Too Many Requests" in str(exc):
                st.warning("Provider rate-limited this request. Wait 1-2 minutes and click 'Refresh Data'.")
            else:
                st.error(f"Data fetch failed: {exc}")
            preview = st.session_state.preview_df
else:
    preview = st.session_state.preview_df

c1, c2, c3 = st.columns(3)
c1.metric(f"Cash Balance ({currency_label})", f"{st.session_state.portfolio.usdt_balance:.2f}")
if st.session_state.portfolio.position:
    c2.metric("Position", "LONG")
    c3.metric("Entry", f"{st.session_state.portfolio.position.entry_price:.2f}")
else:
    c2.metric("Position", "FLAT")
    c3.metric("Entry", "-")

if preview is not None:
    preview = preview.copy()
    st.subheader("Recent Candles + Moving Averages")
    preview["fast_ma"] = preview["close"].rolling(window=runtime_cfg.fast_ma).mean()
    preview["slow_ma"] = preview["close"].rolling(window=runtime_cfg.slow_ma).mean()
    table_df = preview[["timestamp", "close", "fast_ma", "slow_ma"]].tail(120).copy()
    st.dataframe(table_df, use_container_width=True)

st.subheader("Trade Log")
if st.session_state.trades:
    trades_df = pd.DataFrame(st.session_state.trades)
    st.dataframe(trades_df.sort_values("timestamp", ascending=False), use_container_width=True)
else:
    st.info("No trades yet. Click 'Run One Step' to evaluate and execute paper trades.")

st.caption("Paper mode only in UI. For live execution, broker/exchange integration is required.")
