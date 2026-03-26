"""
Market data ingestion module using yfinance.
"""

import yfinance as yf
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db import get_db, query_db


def fetch_and_store(ticker, start_date, end_date):
    """
    Fetch OHLCV data from Yahoo Finance and store in the Market_Data table.
    Uses INSERT OR IGNORE to skip duplicates.
    """
    print(f"Fetching {ticker} data from {start_date} to {end_date}...")
    df = yf.download(ticker, start=start_date, end=end_date, auto_adjust=False)

    if df.empty:
        print(f"No data found for {ticker}")
        return 0

    # Handle multi-level columns from yfinance
    if hasattr(df.columns, 'levels') and len(df.columns.levels) > 1:
        df.columns = df.columns.get_level_values(0)

    conn = get_db()
    count = 0
    for date, row in df.iterrows():
        trade_date = date.strftime("%Y-%m-%d")
        try:
            conn.execute(
                """INSERT OR IGNORE INTO Market_Data
                   (ticker_symbol, trade_date, open_price, high_price, low_price, close_price, volume, adj_close)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    ticker,
                    trade_date,
                    float(row["Open"]),
                    float(row["High"]),
                    float(row["Low"]),
                    float(row["Close"]),
                    int(row["Volume"]),
                    float(row.get("Adj Close", row["Close"])),
                ),
            )
            count += 1
        except Exception as e:
            print(f"Error inserting {trade_date}: {e}")

    conn.commit()
    conn.close()
    print(f"Inserted {count} rows for {ticker}")
    return count


def get_market_data(ticker, start_date=None, end_date=None):
    """Retrieve market data from DB as list of dicts."""
    query = "SELECT * FROM Market_Data WHERE ticker_symbol = ?"
    args = [ticker]
    if start_date:
        query += " AND trade_date >= ?"
        args.append(start_date)
    if end_date:
        query += " AND trade_date <= ?"
        args.append(end_date)
    query += " ORDER BY trade_date"
    return query_db(query, args)


if __name__ == "__main__":
    from db import init_db
    init_db()
    fetch_and_store("RELIANCE.NS", "2023-01-01", "2024-12-31")
