"""
Flask API for the Multi-Strategy Quantitative Backtesting System.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from db import init_db, query_db, execute_db
from models.market_data import fetch_and_store, get_market_data
from models.strategies import STRATEGY_REGISTRY
from models.backtester import run_backtest
from models.optimizer import optimize_portfolio
from models.risk import (
    compute_var_cvar,
    compute_drawdown,
    stationarity_tests,
    walk_forward_validation,
    bootstrap_sharpe,
)

app = Flask(__name__)
CORS(app)

# Initialize DB on startup
init_db()


# ==================== USER ROUTES ====================

@app.route("/api/users", methods=["GET"])
def get_users():
    users = query_db("SELECT * FROM Users")
    return jsonify(users)


@app.route("/api/users", methods=["POST"])
def create_user():
    data = request.json
    try:
        user_id = execute_db(
            "INSERT INTO Users (username, email) VALUES (?, ?)",
            (data["username"], data["email"]),
        )
        return jsonify({"user_id": user_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ==================== STRATEGY ROUTES ====================

@app.route("/api/strategies", methods=["GET"])
def get_strategies():
    strategies = query_db("SELECT * FROM Strategies")
    for s in strategies:
        s["parameters"] = query_db(
            "SELECT * FROM Strategy_Parameters WHERE strategy_id = ?",
            (s["strategy_id"],),
        )
    return jsonify(strategies)


# ==================== MARKET DATA ROUTES ====================

@app.route("/api/market-data/fetch", methods=["POST"])
def fetch_market_data():
    data = request.json
    try:
        count = fetch_and_store(data["ticker"], data["start_date"], data["end_date"])
        return jsonify({"message": f"Fetched {count} rows", "count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/market-data/<ticker>", methods=["GET"])
def get_ticker_data(ticker):
    start = request.args.get("start")
    end = request.args.get("end")
    data = get_market_data(ticker, start, end)
    return jsonify(data)


# ==================== BACKTEST ROUTES ====================

@app.route("/api/backtest", methods=["POST"])
def run_backtest_api():
    data = request.json
    try:
        result = run_backtest(
            user_id=data.get("user_id", 1),
            strategy_name=data["strategy_name"],
            ticker=data["ticker"],
            params=data.get("params", {}),
            start_date=data["start_date"],
            end_date=data["end_date"],
            initial_capital=data.get("initial_capital", 100000),
            transaction_cost=data.get("transaction_cost", 0.001),
        )
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/backtest/runs", methods=["GET"])
def get_all_runs():
    runs = query_db(
        """SELECT br.*, s.strategy_name
           FROM Backtest_Runs br
           JOIN Strategies s ON br.strategy_id = s.strategy_id
           ORDER BY br.executed_at DESC"""
    )
    return jsonify(runs)


@app.route("/api/backtest/runs/<int:run_id>", methods=["GET"])
def get_run_details(run_id):
    run = query_db(
        """SELECT br.*, s.strategy_name
           FROM Backtest_Runs br
           JOIN Strategies s ON br.strategy_id = s.strategy_id
           WHERE br.run_id = ?""",
        (run_id,),
        one=True,
    )
    if not run:
        return jsonify({"error": "Run not found"}), 404

    # Get parameters used
    params = query_db(
        """SELECT sp.parameter_name, rpv.parameter_value
           FROM Run_Parameter_Values rpv
           JOIN Strategy_Parameters sp ON rpv.parameter_id = sp.parameter_id
           WHERE rpv.run_id = ?""",
        (run_id,),
    )

    # Get metrics
    metrics = query_db(
        "SELECT * FROM Performance_Metrics WHERE run_id = ?",
        (run_id,),
        one=True,
    )

    # Get daily results
    daily = query_db(
        "SELECT trade_date, signal, daily_return, cumulative_return, position_size FROM Daily_Results WHERE run_id = ? ORDER BY trade_date",
        (run_id,),
    )

    return jsonify({
        "run": run,
        "parameters": params,
        "metrics": metrics,
        "daily_results": daily,
    })


@app.route("/api/backtest/runs/<int:run_id>", methods=["DELETE"])
def delete_run(run_id):
    execute_db("DELETE FROM Backtest_Runs WHERE run_id = ?", (run_id,))
    return jsonify({"message": f"Run {run_id} deleted"})


# ==================== PORTFOLIO OPTIMIZATION ROUTES ====================

@app.route("/api/optimize", methods=["POST"])
def optimize_api():
    data = request.json
    try:
        result = optimize_portfolio(data["run_ids"])
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ==================== RISK & VALIDATION ROUTES ====================

@app.route("/api/risk/var/<int:run_id>", methods=["GET"])
def var_cvar_api(run_id):
    try:
        confidence = float(request.args.get("confidence", 0.05))
        result = compute_var_cvar(run_id, confidence)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/risk/drawdown/<int:run_id>", methods=["GET"])
def drawdown_api(run_id):
    try:
        result = compute_drawdown(run_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/risk/stationarity/<int:run_id>", methods=["GET"])
def stationarity_api(run_id):
    try:
        result = stationarity_tests(run_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/risk/walk-forward/<int:run_id>", methods=["GET"])
def walk_forward_api(run_id):
    try:
        n_splits = int(request.args.get("splits", 5))
        result = walk_forward_validation(run_id, n_splits)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/risk/bootstrap/<int:run_id>", methods=["GET"])
def bootstrap_api(run_id):
    try:
        result = bootstrap_sharpe(run_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)
