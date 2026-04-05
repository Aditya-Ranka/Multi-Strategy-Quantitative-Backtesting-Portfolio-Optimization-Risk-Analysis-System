import sqlite3
import pandas as pd
import sys
import os

from db import init_db
from models.market_data import fetch_and_store

def check_ticker_data(ticker):
    conn = sqlite3.connect('backtesting.db')
    conn.execute("PRAGMA foreign_keys = ON")
    query = f"SELECT * FROM Market_Data WHERE ticker_symbol = '{ticker}' ORDER BY trade_date"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print(f"No data found for {ticker}")
        return
        
    print(f"\n--- Data Summary for {ticker} ---")
    print(f"Total trading days: {len(df)}")
    print(f"Date range: {df['trade_date'].min()} to {df['trade_date'].max()}")
    print("\nFirst 3 days:")
    print(df.head(3)[['trade_date', 'open_price', 'high_price', 'low_price', 'close_price', 'adj_close', 'volume']])
    print("\nLast 3 days:")
    print(df.tail(3)[['trade_date', 'open_price', 'high_price', 'low_price', 'close_price', 'adj_close', 'volume']])

if __name__ == '__main__':
    print("Fetching RELIANCE.NS data (2023-01-01 to 2024-12-31)...")
    init_db()
    fetch_and_store("RELIANCE.NS", "2023-01-01", "2024-12-31")
    check_ticker_data("RELIANCE.NS")
