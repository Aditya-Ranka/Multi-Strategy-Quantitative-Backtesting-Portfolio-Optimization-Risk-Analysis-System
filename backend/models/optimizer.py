"""
Portfolio optimization module.
Mean-variance optimization to find optimal strategy allocations.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import query_db, execute_db, get_db


def get_strategy_returns_matrix(run_ids):
    """
    Build a returns matrix from multiple backtest runs.
    Rows = dates, Columns = strategies (run_ids).
    """
    all_returns = {}
    for run_id in run_ids:
        daily = query_db(
            "SELECT trade_date, daily_return FROM Daily_Results WHERE run_id = ? ORDER BY trade_date",
            (run_id,),
        )
        if daily:
            returns_series = {row["trade_date"]: row["daily_return"] for row in daily}
            all_returns[run_id] = returns_series

    if not all_returns:
        raise ValueError("No daily results found for the given run IDs")

    df = pd.DataFrame(all_returns).dropna()
    return df


def optimize_portfolio(run_ids, risk_free_rate=0.02, num_portfolios=5000):
    """
    Perform mean-variance portfolio optimization.

    Returns:
        dict with optimal_weights, efficient_frontier, min_variance_portfolio, max_sharpe_portfolio
    """
    returns_matrix = get_strategy_returns_matrix(run_ids)
    n_strategies = len(run_ids)
    mean_returns = returns_matrix.mean() * 252  # Annualized
    cov_matrix = returns_matrix.cov() * 252      # Annualized

    # --- Generate random portfolios for efficient frontier visualization ---
    frontier_returns = []
    frontier_volatilities = []
    frontier_sharpe = []
    frontier_weights = []

    for _ in range(num_portfolios):
        weights = np.random.dirichlet(np.ones(n_strategies))
        port_return = np.dot(weights, mean_returns)
        port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe = (port_return - risk_free_rate) / port_vol if port_vol > 0 else 0

        frontier_returns.append(float(port_return))
        frontier_volatilities.append(float(port_vol))
        frontier_sharpe.append(float(sharpe))
        frontier_weights.append(weights.tolist())

    # --- Maximum Sharpe Ratio portfolio ---
    def neg_sharpe(weights):
        port_return = np.dot(weights, mean_returns)
        port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        return -(port_return - risk_free_rate) / port_vol if port_vol > 0 else 0

    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
    bounds = tuple((0, 1) for _ in range(n_strategies))
    init_weights = np.array([1 / n_strategies] * n_strategies)

    max_sharpe_result = minimize(
        neg_sharpe, init_weights, method="SLSQP", bounds=bounds, constraints=constraints
    )
    max_sharpe_weights = max_sharpe_result.x.tolist()
    max_sharpe_return = float(np.dot(max_sharpe_weights, mean_returns))
    max_sharpe_vol = float(np.sqrt(np.dot(max_sharpe_weights, np.dot(cov_matrix, max_sharpe_weights))))
    max_sharpe_ratio = (max_sharpe_return - risk_free_rate) / max_sharpe_vol if max_sharpe_vol > 0 else 0

    # --- Minimum Variance portfolio ---
    def portfolio_vol(weights):
        return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

    min_var_result = minimize(
        portfolio_vol, init_weights, method="SLSQP", bounds=bounds, constraints=constraints
    )
    min_var_weights = min_var_result.x.tolist()
    min_var_return = float(np.dot(min_var_weights, mean_returns))
    min_var_vol = float(np.sqrt(np.dot(min_var_weights, np.dot(cov_matrix, min_var_weights))))

    # --- Store weights in DB ---
    for i, run_id in enumerate(run_ids):
        run_info = query_db("SELECT strategy_id FROM Backtest_Runs WHERE run_id = ?", (run_id,), one=True)
        if run_info:
            try:
                execute_db(
                    """INSERT OR REPLACE INTO Portfolio_Weights
                       (run_id, strategy_id, allocation_weight, optimization_date)
                       VALUES (?, ?, ?, date('now'))""",
                    (run_id, run_info["strategy_id"], max_sharpe_weights[i]),
                )
            except Exception:
                pass

    return {
        "run_ids": run_ids,
        "max_sharpe_portfolio": {
            "weights": {str(run_ids[i]): round(w, 6) for i, w in enumerate(max_sharpe_weights)},
            "return": round(max_sharpe_return, 6),
            "volatility": round(max_sharpe_vol, 6),
            "sharpe_ratio": round(float(max_sharpe_ratio), 6),
        },
        "min_variance_portfolio": {
            "weights": {str(run_ids[i]): round(w, 6) for i, w in enumerate(min_var_weights)},
            "return": round(min_var_return, 6),
            "volatility": round(min_var_vol, 6),
        },
        "efficient_frontier": {
            "returns": frontier_returns,
            "volatilities": frontier_volatilities,
            "sharpe_ratios": frontier_sharpe,
        },
    }
