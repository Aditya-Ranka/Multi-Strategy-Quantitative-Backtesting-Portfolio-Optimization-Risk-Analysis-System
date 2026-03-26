"""
Risk modeling and statistical validation module.
VaR, CVaR, stationarity tests, walk-forward validation, bootstrap Sharpe.
"""

import numpy as np
import pandas as pd
from scipy import stats
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import query_db


# ==================== VaR / CVaR ====================

def compute_var_cvar(run_id, confidence=0.05):
    """
    Compute Value at Risk and Conditional VaR using three methods.
    """
    daily = query_db(
        "SELECT daily_return FROM Daily_Results WHERE run_id = ? ORDER BY trade_date",
        (run_id,),
    )
    if not daily:
        raise ValueError(f"No daily results for run_id={run_id}")

    returns = np.array([r["daily_return"] for r in daily])

    # 1. Historical VaR
    historical_var = float(np.percentile(returns, confidence * 100))
    historical_cvar = float(returns[returns <= historical_var].mean()) if len(returns[returns <= historical_var]) > 0 else 0.0

    # 2. Parametric VaR (assumes normal distribution)
    mu = returns.mean()
    sigma = returns.std()
    z_score = stats.norm.ppf(confidence)
    parametric_var = float(mu + z_score * sigma)
    parametric_cvar = float(mu - sigma * stats.norm.pdf(z_score) / confidence)

    # 3. Monte Carlo VaR
    np.random.seed(42)
    simulated = np.random.normal(mu, sigma, 10000)
    mc_var = float(np.percentile(simulated, confidence * 100))
    mc_cvar = float(simulated[simulated <= mc_var].mean())

    return {
        "historical": {"var": round(historical_var, 6), "cvar": round(historical_cvar, 6)},
        "parametric": {"var": round(parametric_var, 6), "cvar": round(parametric_cvar, 6)},
        "monte_carlo": {"var": round(mc_var, 6), "cvar": round(mc_cvar, 6)},
    }


# ==================== Drawdown Analysis ====================

def compute_drawdown(run_id):
    """Compute drawdown series and metrics."""
    daily = query_db(
        "SELECT trade_date, daily_return FROM Daily_Results WHERE run_id = ? ORDER BY trade_date",
        (run_id,),
    )
    if not daily:
        raise ValueError(f"No daily results for run_id={run_id}")

    returns = pd.Series([r["daily_return"] for r in daily])
    dates = [r["trade_date"] for r in daily]
    wealth = (1 + returns).cumprod()
    peak = wealth.cummax()
    drawdown = (wealth - peak) / peak

    max_dd = float(drawdown.min())
    avg_dd = float(drawdown[drawdown < 0].mean()) if len(drawdown[drawdown < 0]) > 0 else 0.0

    # Recovery time (days from max drawdown to new peak)
    max_dd_idx = drawdown.idxmin()
    recovery_slice = drawdown.iloc[max_dd_idx:]
    recovery_points = recovery_slice[recovery_slice >= 0]
    recovery_time = int(recovery_points.index[0] - max_dd_idx) if len(recovery_points) > 0 else -1

    return {
        "max_drawdown": round(max_dd, 6),
        "avg_drawdown": round(avg_dd, 6),
        "recovery_time_days": recovery_time,
        "drawdown_series": [{"date": dates[i], "drawdown": round(float(drawdown.iloc[i]), 6)} for i in range(len(dates))],
    }


# ==================== Stationarity Tests ====================

def stationarity_tests(run_id):
    """Run ADF and KPSS tests on strategy returns."""
    try:
        from statsmodels.tsa.stattools import adfuller, kpss
    except ImportError:
        return {"error": "statsmodels not installed"}

    daily = query_db(
        "SELECT daily_return FROM Daily_Results WHERE run_id = ? ORDER BY trade_date",
        (run_id,),
    )
    returns = np.array([r["daily_return"] for r in daily])

    # ADF Test
    adf_result = adfuller(returns, autolag="AIC")
    adf = {
        "test_statistic": round(float(adf_result[0]), 6),
        "p_value": round(float(adf_result[1]), 6),
        "is_stationary": bool(adf_result[1] < 0.05),
    }

    # KPSS Test
    kpss_result = kpss(returns, regression="c", nlags="auto")
    kpss_out = {
        "test_statistic": round(float(kpss_result[0]), 6),
        "p_value": round(float(kpss_result[1]), 6),
        "is_stationary": bool(kpss_result[1] > 0.05),  # KPSS null = stationary
    }

    return {"adf": adf, "kpss": kpss_out}


# ==================== Walk-Forward Validation ====================

def walk_forward_validation(run_id, n_splits=5):
    """
    Walk-forward validation: compare in-sample vs out-of-sample Sharpe ratios.
    """
    daily = query_db(
        "SELECT daily_return FROM Daily_Results WHERE run_id = ? ORDER BY trade_date",
        (run_id,),
    )
    returns = np.array([r["daily_return"] for r in daily])
    n = len(returns)
    split_size = n // n_splits

    results = []
    for i in range(n_splits - 1):
        in_sample = returns[: (i + 1) * split_size]
        out_sample = returns[(i + 1) * split_size: (i + 2) * split_size]

        is_sharpe = float(in_sample.mean() / in_sample.std() * np.sqrt(252)) if in_sample.std() > 0 else 0.0
        os_sharpe = float(out_sample.mean() / out_sample.std() * np.sqrt(252)) if out_sample.std() > 0 else 0.0

        results.append({
            "split": i + 1,
            "in_sample_sharpe": round(is_sharpe, 4),
            "out_of_sample_sharpe": round(os_sharpe, 4),
            "degradation": round(is_sharpe - os_sharpe, 4),
        })

    avg_degradation = np.mean([r["degradation"] for r in results])
    return {
        "splits": results,
        "avg_degradation": round(float(avg_degradation), 4),
        "likely_overfit": bool(float(avg_degradation) > 0.5),
    }


# ==================== Bootstrap Sharpe Confidence Interval ====================

def bootstrap_sharpe(run_id, n_bootstrap=10000, confidence_level=0.95):
    """
    Bootstrap resampling to compute confidence interval for Sharpe ratio.
    """
    daily = query_db(
        "SELECT daily_return FROM Daily_Results WHERE run_id = ? ORDER BY trade_date",
        (run_id,),
    )
    returns = np.array([r["daily_return"] for r in daily])

    original_sharpe = float(returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0.0

    np.random.seed(42)
    bootstrap_sharpes = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(returns, size=len(returns), replace=True)
        s = float(sample.mean() / sample.std() * np.sqrt(252)) if sample.std() > 0 else 0.0
        bootstrap_sharpes.append(s)

    bootstrap_sharpes = np.array(bootstrap_sharpes)
    alpha = (1 - confidence_level) / 2
    lower = float(np.percentile(bootstrap_sharpes, alpha * 100))
    upper = float(np.percentile(bootstrap_sharpes, (1 - alpha) * 100))
    p_value = float((bootstrap_sharpes <= 0).mean())

    return {
        "original_sharpe": round(original_sharpe, 4),
        "bootstrap_mean": round(float(bootstrap_sharpes.mean()), 4),
        "confidence_interval": [round(lower, 4), round(upper, 4)],
        "p_value": round(p_value, 4),
        "is_significant": bool(p_value < 0.05),
    }
