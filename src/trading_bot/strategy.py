from __future__ import annotations

import pandas as pd


def compute_signal(df: pd.DataFrame, fast_ma: int, slow_ma: int) -> str:
    """Return BUY, SELL, or HOLD based on moving-average crossover."""
    if len(df) < slow_ma + 2:
        return "HOLD"

    fast = df["close"].rolling(window=fast_ma).mean()
    slow = df["close"].rolling(window=slow_ma).mean()

    prev_fast, curr_fast = fast.iloc[-2], fast.iloc[-1]
    prev_slow, curr_slow = slow.iloc[-2], slow.iloc[-1]

    if pd.isna(prev_fast) or pd.isna(prev_slow) or pd.isna(curr_fast) or pd.isna(curr_slow):
        return "HOLD"

    crossed_up = prev_fast <= prev_slow and curr_fast > curr_slow
    crossed_down = prev_fast >= prev_slow and curr_fast < curr_slow

    if crossed_up:
        return "BUY"
    if crossed_down:
        return "SELL"
    return "HOLD"
