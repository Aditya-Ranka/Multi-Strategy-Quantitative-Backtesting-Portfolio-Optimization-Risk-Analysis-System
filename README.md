# Multi-Strategy Quantitative Backtesting & Portfolio Optimization System

## Overview
A comprehensive full-stack platform for designing, simulating, and evaluating quantitative trading strategies. The system allows users to backtest multiple strategies against historical market data, compute detailed performance and risk metrics (Sharpe ratio, max drawdown, VaR, CVaR), and optimize portfolio allocations.

## Tech Stack
- **Backend:** Python, Flask
- **Frontend:** React.js, Vite
- **Database:** SQLite (default/development) / PostgreSQL (schema provided)

## Features
- **Multi-Strategy Backtesting:** Simulate various algorithmic trading strategies including *Moving Average Crossover*, *Momentum*, *Mean Reversion*, and *RSI Reversal*.
- **Risk & Performance Analytics:** Calculate key metrics including CAGR, Volatility, Sharpe Ratio, Sortino Ratio, Maximum Drawdown, Value at Risk (VaR), and Conditional Value at Risk (CVaR).
- **Portfolio Optimization:** Optimize weights across different strategies and track allocation history via custom SQL views.
- **Market Data Ingestion:** Process, store, and query end-of-day OHLCV asset data efficiently.
- **Data Integrity:** Robust SQL schemas featuring foreign keys, complex CHECK constraints, and database triggers (e.g., preventing strategy portfolio allocations from exceeding 100%).

## Database Schemas
- `schema_sqlite.sql`: Primary schema used for local execution. Includes comprehensive table definitions and triggers.
- `relationalSchema1.sql`: PostgreSQL schema variant including plpgsql stored procedures and validations.

## Setup Instructions

### 1. Backend Setup
The backend is a Flask API that interfaces with the SQLite database.

```bash
cd backend

# Install required Python dependencies
pip install -r requirements.txt

# Initialize the database (this runs the SQLite schema and seeds initial data)
python3 db.py
# (or optionally python3 seed.py if available)

# Start the Flask development server (typically runs on port 5000)
python3 app.py
```

### 2. Frontend Setup
The frontend is a React application built with Vite.

```bash
cd frontend

# Install Node dependencies
npm install

# Start the Vite development server
npm run dev
```

## Testing & Verifying the Database
A utility script called `run_queries.py` is included in the root directory to manually invoke and verify complex database operations, joins, views, and data-integrity triggers.

```bash
python3 run_queries.py
```
