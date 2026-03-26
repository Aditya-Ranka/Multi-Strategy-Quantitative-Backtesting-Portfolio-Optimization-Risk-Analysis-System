"""
Strategy signal generators.
Each function takes a pandas DataFrame of market data and parameters,
and returns a pandas Series of signals: 'BUY', 'SELL', or 'HOLD'.
"""

import pandas as pd
import numpy as np


def moving_average_crossover(df, short_window=20, long_window=50):
    """
    Moving Average Crossover Strategy.
    Buy when short MA > long MA, Sell when short MA < long MA.
    """
    close = df["close_price"]
    short_ma = close.rolling(window=short_window).mean()
    long_ma = close.rolling(window=long_window).mean()

    signals = pd.Series("HOLD", index=df.index)
    signals[short_ma > long_ma] = "BUY"
    signals[short_ma < long_ma] = "SELL"

    # Set warm-up period to HOLD
    signals.iloc[: long_window] = "HOLD"
    return signals


def mean_reversion(df, lookback_window=20, z_threshold=1.5):
    """
    Mean Reversion Strategy.
    Buy when Z-score < -threshold, Sell when Z-score > threshold.
    """
    close = df["close_price"]
    rolling_mean = close.rolling(window=lookback_window).mean()
    rolling_std = close.rolling(window=lookback_window).std()

    z_score = (close - rolling_mean) / rolling_std

    signals = pd.Series("HOLD", index=df.index)
    signals[z_score < -z_threshold] = "BUY"
    signals[z_score > z_threshold] = "SELL"

    # Set warm-up period to HOLD
    signals.iloc[: lookback_window] = "HOLD"
    return signals


def rsi_reversal(df, rsi_period=14, oversold=30, overbought=70):
    """
    RSI Reversal Strategy.
    Buy when RSI < oversold, Sell when RSI > overbought.
    """
    close = df["close_price"]
    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=rsi_period).mean()
    avg_loss = loss.rolling(window=rsi_period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    signals = pd.Series("HOLD", index=df.index)
    signals[rsi < oversold] = "BUY"
    signals[rsi > overbought] = "SELL"

    # Set warm-up period to HOLD
    signals.iloc[: rsi_period] = "HOLD"
    return signals


def momentum(df, lookback_days=20):
    """
    Momentum Strategy.
    Buy if return over the last N days is positive.
    """
    close = df["close_price"]
    returns = close.pct_change(periods=lookback_days)

    signals = pd.Series("HOLD", index=df.index)
    signals[returns > 0] = "BUY"
    signals[returns <= 0] = "SELL"

    # Set warm-up period to HOLD
    signals.iloc[: lookback_days] = "HOLD"
    return signals


# Registry mapping strategy names to their functions and parameter specs
STRATEGY_REGISTRY = {
    "Moving Average Crossover": {
        "func": moving_average_crossover,
        "params": {"short_window": int, "long_window": int},
    },
    "Mean Reversion": {
        "func": mean_reversion,
        "params": {"lookback_window": int, "z_threshold": float},
    },
    "RSI Reversal": {
        "func": rsi_reversal,
        "params": {"rsi_period": int, "oversold": float, "overbought": float},
    },
    "Momentum": {
        "func": momentum,
        "params": {"lookback_days": int},
    },
}


def generate_signals(strategy_name, df, params):
    """
    Generate signals for a given strategy.
    Args:
        strategy_name: Name of the strategy
        df: DataFrame with market data (must have 'close_price' column)
        params: dict of parameter values
    Returns:
        pandas Series of 'BUY'/'SELL'/'HOLD' signals
    """
    if strategy_name not in STRATEGY_REGISTRY:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    entry = STRATEGY_REGISTRY[strategy_name]
    func = entry["func"]
    typed_params = {}
    for key, cast_type in entry["params"].items():
        if key in params:
            typed_params[key] = cast_type(params[key])

    return func(df, **typed_params)
