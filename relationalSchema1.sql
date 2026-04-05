/*erDiagram
    Users ||--o{ Backtest_Runs : "executes"
    Strategies ||--o{ Strategy_Parameters : "owns"
    Strategies ||--o{ Backtest_Runs : "simulated_in"
    Strategies ||--o{ Portfolio_Weights : "allocated_in"

    Backtest_Runs ||--o{ Run_Parameter_Values : "configured_with"
    Strategy_Parameters ||--o{ Run_Parameter_Values : "defines_value_for"

    Backtest_Runs ||--o{ Daily_Results : "generates_time_series"
    Backtest_Runs ||--|| Performance_Metrics : "summarized_by"
    Backtest_Runs ||--o{ Portfolio_Weights : "calculates_optimization"
    Market_Data ||--o{ Backtest_Runs : "provides_data_for"

    Users {
        int user_id PK
        string username
        string email
    }
    
    Strategies {
        int strategy_id PK
        string strategy_name
        text description
    }
    
    Strategy_Parameters {
        int parameter_id PK
        int strategy_id FK
        string parameter_name
        string data_type
        string default_value
    }
    
    Market_Data {
        int data_id PK
        string ticker_symbol
        date trade_date
        decimal open_price
        decimal high_price
        decimal low_price
        decimal close_price
        bigint volume
        decimal adj_close
    }
    
    Backtest_Runs {
        int run_id PK
        int user_id FK
        int strategy_id FK
        string ticker_symbol
        date start_date
        date end_date
        decimal initial_capital
    }
    
    Run_Parameter_Values {
        int run_id PK,FK
        int parameter_id PK,FK
        string parameter_value
    }
    
    Daily_Results {
        int result_id PK
        int run_id FK
        date trade_date
        string signal
        decimal daily_return
        decimal cumulative_return
        decimal position_size
    }
    
    Performance_Metrics {
        int run_id PK,FK
        decimal total_return
        decimal cagr
        decimal volatility
        decimal sharpe_ratio
        decimal sortino_ratio
        decimal max_drawdown
        decimal calmar_ratio
        decimal win_rate
        decimal profit_factor
        decimal historical_var
        decimal cvar
    }
    
    Portfolio_Weights {
        int weight_id PK
        int run_id FK
        int strategy_id FK
        decimal allocation_weight
        date optimization_date
    }*/

-- =============================================
-- Multi-Strategy Quantitative Backtesting System
-- Relational Schema v2
-- =============================================

-- Store user information
CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Store strategy definitions (e.g., 'Moving Average Crossover', 'Mean Reversion')
CREATE TABLE Strategies (
    strategy_id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Store configurable parameters for each strategy
CREATE TABLE Strategy_Parameters (
    parameter_id SERIAL PRIMARY KEY,
    strategy_id INT NOT NULL REFERENCES Strategies(strategy_id) ON DELETE CASCADE,
    parameter_name VARCHAR(50) NOT NULL, -- e.g., 'Short Window', 'Z-Score Threshold'
    data_type VARCHAR(20) NOT NULL,      -- e.g., 'INT', 'FLOAT'
    default_value VARCHAR(50),
    UNIQUE(strategy_id, parameter_name)
);

-- Index on FK for faster JOINs
CREATE INDEX idx_strategy_params_strategy ON Strategy_Parameters(strategy_id);

-- Store daily OHLCV data
CREATE TABLE Market_Data (
    data_id SERIAL PRIMARY KEY,
    ticker_symbol VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    open_price DECIMAL(18, 6),
    high_price DECIMAL(18, 6),
    low_price DECIMAL(18, 6),
    close_price DECIMAL(18, 6),
    volume BIGINT,
    adj_close DECIMAL(18, 6),
    UNIQUE(ticker_symbol, trade_date)
);

-- Indexes for efficient time-series querying
CREATE INDEX idx_market_data_date ON Market_Data(trade_date);
CREATE INDEX idx_market_data_ticker ON Market_Data(ticker_symbol);

-- Record each simulation run
CREATE TABLE Backtest_Runs (
    run_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    strategy_id INT NOT NULL REFERENCES Strategies(strategy_id) ON DELETE CASCADE,
    ticker_symbol VARCHAR(20) NOT NULL,  -- Asset used for backtesting
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(18, 2) DEFAULT 100000.00,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (end_date > start_date)
);

-- Indexes on FKs for faster JOINs
CREATE INDEX idx_backtest_runs_user ON Backtest_Runs(user_id);
CREATE INDEX idx_backtest_runs_strategy ON Backtest_Runs(strategy_id);

-- Store the specific parameter values used for a given run
CREATE TABLE Run_Parameter_Values (
    run_id INT NOT NULL REFERENCES Backtest_Runs(run_id) ON DELETE CASCADE,
    parameter_id INT NOT NULL REFERENCES Strategy_Parameters(parameter_id) ON DELETE CASCADE,
    parameter_value VARCHAR(50) NOT NULL,
    PRIMARY KEY (run_id, parameter_id)
);

-- Store daily structured results for historical comparison
CREATE TABLE Daily_Results (
    result_id SERIAL PRIMARY KEY,
    run_id INT NOT NULL REFERENCES Backtest_Runs(run_id) ON DELETE CASCADE,
    trade_date DATE NOT NULL,
    signal VARCHAR(10),              -- 'BUY', 'SELL', 'HOLD'
    daily_return DECIMAL(18, 6),     -- Net return after transaction costs
    cumulative_return DECIMAL(18, 6),
    position_size DECIMAL(18, 6),
    UNIQUE(run_id, trade_date)       -- Prevent duplicate daily entries per run
);

-- Indexes for fast retrieval of time-series results
CREATE INDEX idx_daily_results_run ON Daily_Results(run_id);
CREATE INDEX idx_daily_results_run_date ON Daily_Results(run_id, trade_date);

-- Store aggregated performance and risk metrics
CREATE TABLE Performance_Metrics (
    run_id INT PRIMARY KEY REFERENCES Backtest_Runs(run_id) ON DELETE CASCADE,
    total_return DECIMAL(18, 6),
    cagr DECIMAL(10, 6),
    volatility DECIMAL(10, 6),
    sharpe_ratio DECIMAL(10, 6),
    sortino_ratio DECIMAL(10, 6),
    max_drawdown DECIMAL(10, 6),
    calmar_ratio DECIMAL(10, 6),     -- CAGR / Max Drawdown
    win_rate DECIMAL(10, 6),
    profit_factor DECIMAL(10, 6),    -- Gross Profit / Gross Loss
    historical_var DECIMAL(10, 6),   -- Historical Value at Risk
    cvar DECIMAL(10, 6),             -- Conditional VaR
    CHECK (win_rate >= 0 AND win_rate <= 1)
);

-- Store portfolio optimization weights
CREATE TABLE Portfolio_Weights (
    weight_id SERIAL PRIMARY KEY,
    run_id INT NOT NULL REFERENCES Backtest_Runs(run_id) ON DELETE CASCADE,
    strategy_id INT NOT NULL REFERENCES Strategies(strategy_id) ON DELETE CASCADE,
    allocation_weight DECIMAL(10, 6) NOT NULL,
    optimization_date DATE NOT NULL,
    UNIQUE(run_id, strategy_id, optimization_date),  -- One weight per strategy per run per date
    CHECK (allocation_weight >= 0 AND allocation_weight <= 1)
);

-- Indexes on FKs for faster JOINs
CREATE INDEX idx_portfolio_weights_run ON Portfolio_Weights(run_id);
CREATE INDEX idx_portfolio_weights_strategy ON Portfolio_Weights(strategy_id);

-- Trigger to validate that portfolio weights for a given run and date do not exceed 1.0
CREATE OR REPLACE FUNCTION fn_validate_portfolio_weights()
RETURNS TRIGGER AS $$
DECLARE
    total_weight DECIMAL;
BEGIN
    SELECT SUM(allocation_weight) INTO total_weight
    FROM Portfolio_Weights
    WHERE run_id = NEW.run_id
      AND optimization_date = NEW.optimization_date;

    IF total_weight > 1.0 THEN
        RAISE EXCEPTION 'Portfolio weights for this run and date exceed 1.0';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_portfolio_weights
AFTER INSERT OR UPDATE ON Portfolio_Weights
FOR EACH ROW
EXECUTE FUNCTION fn_validate_portfolio_weights();

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