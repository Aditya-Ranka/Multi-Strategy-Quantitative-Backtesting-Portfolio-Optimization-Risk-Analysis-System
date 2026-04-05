PRAGMA foreign_keys = ON;
-- =============================================
-- Multi-Strategy Quantitative Backtesting System
-- SQLite Schema
-- =============================================

-- Store user information
CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Store strategy definitions
CREATE TABLE IF NOT EXISTS Strategies (
    strategy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Store configurable parameters for each strategy
CREATE TABLE IF NOT EXISTS Strategy_Parameters (
    parameter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL REFERENCES Strategies(strategy_id) ON DELETE CASCADE,
    parameter_name TEXT NOT NULL,
    data_type TEXT NOT NULL,
    default_value TEXT,
    UNIQUE(strategy_id, parameter_name)
);

CREATE INDEX IF NOT EXISTS idx_strategy_params_strategy ON Strategy_Parameters(strategy_id);

-- Store daily OHLCV data
CREATE TABLE IF NOT EXISTS Market_Data (
    data_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_symbol TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    adj_close REAL,
    UNIQUE(ticker_symbol, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_market_data_date ON Market_Data(trade_date);
CREATE INDEX IF NOT EXISTS idx_market_data_ticker ON Market_Data(ticker_symbol);

-- Record each simulation run
CREATE TABLE IF NOT EXISTS Backtest_Runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    strategy_id INTEGER NOT NULL REFERENCES Strategies(strategy_id) ON DELETE CASCADE,
    ticker_symbol TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    initial_capital REAL DEFAULT 100000.00,
    executed_at TEXT DEFAULT (datetime('now')),
    CHECK (end_date > start_date)
);

CREATE INDEX IF NOT EXISTS idx_backtest_runs_user ON Backtest_Runs(user_id);
CREATE INDEX IF NOT EXISTS idx_backtest_runs_strategy ON Backtest_Runs(strategy_id);

-- Store the specific parameter values used for a given run
CREATE TABLE IF NOT EXISTS Run_Parameter_Values (
    run_id INTEGER NOT NULL REFERENCES Backtest_Runs(run_id) ON DELETE CASCADE,
    parameter_id INTEGER NOT NULL REFERENCES Strategy_Parameters(parameter_id) ON DELETE CASCADE,
    parameter_value TEXT NOT NULL,
    PRIMARY KEY (run_id, parameter_id)
);

-- Store daily structured results for historical comparison
CREATE TABLE IF NOT EXISTS Daily_Results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES Backtest_Runs(run_id) ON DELETE CASCADE,
    trade_date TEXT NOT NULL,
    signal TEXT CHECK (signal IN ('BUY', 'SELL', 'HOLD')),
    daily_return REAL,
    cumulative_return REAL,
    position_size REAL,
    UNIQUE(run_id, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_results_run ON Daily_Results(run_id);
CREATE INDEX IF NOT EXISTS idx_daily_results_run_date ON Daily_Results(run_id, trade_date);

-- Store aggregated performance and risk metrics
CREATE TABLE IF NOT EXISTS Performance_Metrics (
    run_id INTEGER PRIMARY KEY REFERENCES Backtest_Runs(run_id) ON DELETE CASCADE,
    total_return REAL,
    cagr REAL,
    volatility REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    max_drawdown REAL,
    calmar_ratio REAL,
    win_rate REAL,
    profit_factor REAL,
    historical_var REAL,
    cvar REAL,
    CHECK (win_rate >= 0 AND win_rate <= 1)
);

-- Store portfolio optimization weights
CREATE TABLE IF NOT EXISTS Portfolio_Weights (
    weight_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES Backtest_Runs(run_id) ON DELETE CASCADE,
    strategy_id INTEGER NOT NULL REFERENCES Strategies(strategy_id) ON DELETE CASCADE,
    allocation_weight REAL NOT NULL,
    optimization_date TEXT NOT NULL,
    UNIQUE(run_id, strategy_id, optimization_date),  -- One weight per strategy per run per date
    CHECK (allocation_weight >= 0 AND allocation_weight <= 1)
);

CREATE INDEX IF NOT EXISTS idx_portfolio_weights_run ON Portfolio_Weights(run_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_weights_strategy ON Portfolio_Weights(strategy_id);

-- Trigger to validate that portfolio weights for a given run and date do not exceed 1.0
CREATE TRIGGER trg_validate_portfolio_weights
AFTER INSERT ON Portfolio_Weights
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Portfolio weights for this run and date exceed 1.0')
    WHERE (
        SELECT SUM(allocation_weight)
        FROM Portfolio_Weights
        WHERE run_id = NEW.run_id
          AND optimization_date = NEW.optimization_date
    ) > 1.0;
END;

-- View: Portfolio allocation history
CREATE VIEW v_portfolio_allocation_history AS
SELECT
    pw.run_id,
    pw.optimization_date,
    s.strategy_name,
    pw.allocation_weight
FROM Portfolio_Weights pw
JOIN Strategies s ON pw.strategy_id = s.strategy_id
JOIN Backtest_Runs br ON pw.run_id = br.run_id
ORDER BY pw.run_id, pw.optimization_date, s.strategy_name;
