"""
Seed the database with the 4 strategies and their configurable parameters.
"""

from db import init_db, execute_db, query_db


STRATEGIES = [
    {
        "name": "Moving Average Crossover",
        "description": "Generates a buy signal when the short moving average crosses above the long moving average, and a sell signal when it crosses below.",
        "params": [
            ("short_window", "INT", "20"),
            ("long_window", "INT", "50"),
        ],
    },
    {
        "name": "Mean Reversion",
        "description": "Uses Z-score of price relative to a rolling mean. Buy when Z-score is below negative threshold, sell when above positive threshold.",
        "params": [
            ("lookback_window", "INT", "20"),
            ("z_threshold", "FLOAT", "1.5"),
        ],
    },
    {
        "name": "RSI Reversal",
        "description": "Generates a buy signal when RSI drops below the oversold level and a sell signal when RSI rises above the overbought level.",
        "params": [
            ("rsi_period", "INT", "14"),
            ("oversold", "FLOAT", "30"),
            ("overbought", "FLOAT", "70"),
        ],
    },
    {
        "name": "Momentum",
        "description": "Generates a buy signal if the return over the last N days is positive.",
        "params": [
            ("lookback_days", "INT", "20"),
        ],
    },
]


def seed():
    """Seed strategies and their parameters into the database."""
    init_db()

    # Create a default user
    existing = query_db("SELECT user_id FROM Users WHERE username = ?", ("admin",), one=True)
    if not existing:
        execute_db(
            "INSERT INTO Users (username, email) VALUES (?, ?)",
            ("admin", "admin@backtester.com"),
        )
        print("Created default user: admin")

    for strat in STRATEGIES:
        # Check if strategy already exists
        existing = query_db(
            "SELECT strategy_id FROM Strategies WHERE strategy_name = ?",
            (strat["name"],),
            one=True,
        )
        if existing:
            strategy_id = existing["strategy_id"]
            print(f"Strategy '{strat['name']}' already exists (id={strategy_id})")
        else:
            strategy_id = execute_db(
                "INSERT INTO Strategies (strategy_name, description) VALUES (?, ?)",
                (strat["name"], strat["description"]),
            )
            print(f"Inserted strategy: {strat['name']} (id={strategy_id})")

        # Insert parameters
        for param_name, data_type, default_val in strat["params"]:
            existing_param = query_db(
                "SELECT parameter_id FROM Strategy_Parameters WHERE strategy_id = ? AND parameter_name = ?",
                (strategy_id, param_name),
                one=True,
            )
            if not existing_param:
                execute_db(
                    "INSERT INTO Strategy_Parameters (strategy_id, parameter_name, data_type, default_value) VALUES (?, ?, ?, ?)",
                    (strategy_id, param_name, data_type, default_val),
                )
                print(f"  Inserted param: {param_name} ({data_type}, default={default_val})")
            else:
                print(f"  Param '{param_name}' already exists")

    print("\nSeeding complete!")


if __name__ == "__main__":
    seed()
