"""
Backtesting engine: simulates trades, computes daily returns with transaction costs,
and calculates performance metrics.
"""

import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import get_db, execute_db, query_db
from models.strategies import generate_signals


def run_backtest(user_id, strategy_name, ticker, params, start_date, end_date,
                 initial_capital=100000.0, transaction_cost=0.001):
    """
    Run a full backtest simulation.

    Args:
        user_id: ID of the user running the backtest
        strategy_name: Name of the strategy to use
        ticker: Ticker symbol to backtest on
        params: dict of strategy parameters
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        initial_capital: Starting capital
        transaction_cost: Cost per trade as fraction (default 0.1%)

    Returns:
        dict with run_id and computed metrics
    """
    # 1. Fetch market data from DB
    market_data = query_db(
        """SELECT trade_date, open_price, high_price, low_price, close_price, volume, adj_close
           FROM Market_Data WHERE ticker_symbol = ? AND trade_date >= ? AND trade_date <= ?
           ORDER BY trade_date""",
        (ticker, start_date, end_date),
    )

    if not market_data:
        raise ValueError(f"No market data found for {ticker} between {start_date} and {end_date}")

    df = pd.DataFrame(market_data)
    df["close_price"] = df["close_price"].astype(float)

    # 2. Generate signals
    signals = generate_signals(strategy_name, df, params)

    # 3. Convert signals to positions (1=long, 0=flat, -1=short)
    position_map = {"BUY": 1, "SELL": -1, "HOLD": 0}
    positions = signals.map(position_map).fillna(0)

    # 4. Compute daily market returns
    df["market_return"] = df["close_price"].pct_change().fillna(0)

    # 5. Compute strategy returns with transaction costs
    position_changes = positions.diff().abs().fillna(0)
    costs = position_changes * transaction_cost
    df["strategy_return"] = (positions.shift(1).fillna(0) * df["market_return"]) - costs

    # 6. Compute cumulative returns
    df["cumulative_return"] = (1 + df["strategy_return"]).cumprod() - 1

    # 7. Store backtest run in DB
    strategy = query_db(
        "SELECT strategy_id FROM Strategies WHERE strategy_name = ?",
        (strategy_name,),
        one=True,
    )
    if not strategy:
        raise ValueError(f"Strategy '{strategy_name}' not found in database")

    strategy_id = strategy["strategy_id"]

    run_id = execute_db(
        """INSERT INTO Backtest_Runs (user_id, strategy_id, ticker_symbol, start_date, end_date, initial_capital)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, strategy_id, ticker, start_date, end_date, initial_capital),
    )

    # 8. Store parameter values
    for param_name, param_value in params.items():
        param_row = query_db(
            "SELECT parameter_id FROM Strategy_Parameters WHERE strategy_id = ? AND parameter_name = ?",
            (strategy_id, param_name),
            one=True,
        )
        if param_row:
            execute_db(
                "INSERT INTO Run_Parameter_Values (run_id, parameter_id, parameter_value) VALUES (?, ?, ?)",
                (run_id, param_row["parameter_id"], str(param_value)),
            )

    # 9. Store daily results
    conn = get_db()
    for i, row in df.iterrows():
        conn.execute(
            """INSERT INTO Daily_Results (run_id, trade_date, signal, daily_return, cumulative_return, position_size)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                row["trade_date"],
                signals.iloc[i],
                float(row["strategy_return"]),
                float(row["cumulative_return"]),
                float(positions.iloc[i]),
            ),
        )
    conn.commit()
    conn.close()

    # 10. Compute and store performance metrics
    metrics = compute_metrics(df, initial_capital)
    execute_db(
        """INSERT INTO Performance_Metrics
           (run_id, total_return, cagr, volatility, sharpe_ratio, sortino_ratio,
            max_drawdown, calmar_ratio, win_rate, profit_factor, historical_var, cvar)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            run_id,
            metrics["total_return"],
            metrics["cagr"],
            metrics["volatility"],
            metrics["sharpe_ratio"],
            metrics["sortino_ratio"],
            metrics["max_drawdown"],
            metrics["calmar_ratio"],
            metrics["win_rate"],
            metrics["profit_factor"],
            metrics["historical_var"],
            metrics["cvar"],
        ),
    )

    return {"run_id": run_id, "metrics": metrics}


def compute_metrics(df, initial_capital=100000.0, risk_free_rate=0.02):
    """
    Compute all performance and risk metrics.
    """
    returns = df["strategy_return"]
    cum_returns = df["cumulative_return"]

    # Total return
    total_return = float(cum_returns.iloc[-1]) if len(cum_returns) > 0 else 0.0

    # CAGR
    n_days = len(returns)
    n_years = n_days / 252
    cagr = ((1 + total_return) ** (1 / n_years) - 1) if n_years > 0 and total_return > -1 else 0.0

    # Volatility (annualized)
    volatility = float(returns.std() * np.sqrt(252)) if len(returns) > 1 else 0.0

    # Sharpe Ratio
    excess_returns = returns - risk_free_rate / 252
    sharpe_ratio = float(excess_returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0.0

    # Sortino Ratio
    downside_returns = returns[returns < 0]
    downside_std = float(downside_returns.std()) if len(downside_returns) > 0 else 0.0
    sortino_ratio = float(excess_returns.mean() / downside_std * np.sqrt(252)) if downside_std > 0 else 0.0

    # Maximum Drawdown
    wealth = (1 + returns).cumprod()
    peak = wealth.cummax()
    drawdown = (wealth - peak) / peak
    max_drawdown = float(drawdown.min())

    # Calmar Ratio
    calmar_ratio = float(cagr / abs(max_drawdown)) if max_drawdown != 0 else 0.0

    # Win Rate
    winning_trades = (returns > 0).sum()
    total_trades = (returns != 0).sum()
    win_rate = float(winning_trades / total_trades) if total_trades > 0 else 0.0

    # Profit Factor
    gross_profit = float(returns[returns > 0].sum())
    gross_loss = float(abs(returns[returns < 0].sum()))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

    # Historical VaR (5%)
    historical_var = float(np.percentile(returns, 5)) if len(returns) > 0 else 0.0

    # CVaR (5%)
    cvar = float(returns[returns <= historical_var].mean()) if len(returns[returns <= historical_var]) > 0 else 0.0

    return {
        "total_return": round(total_return, 6),
        "cagr": round(cagr, 6),
        "volatility": round(volatility, 6),
        "sharpe_ratio": round(sharpe_ratio, 6),
        "sortino_ratio": round(sortino_ratio, 6),
        "max_drawdown": round(max_drawdown, 6),
        "calmar_ratio": round(calmar_ratio, 6),
        "win_rate": round(win_rate, 6),
        "profit_factor": round(profit_factor, 6),
        "historical_var": round(historical_var, 6),
        "cvar": round(cvar, 6),
    }
