import sqlite3
import os

def print_header(title):
    print("\n" + "="*80)
    print(title)
    print("="*80)

def print_results(cursor):
    rows = cursor.fetchall()
    if not rows:
        print("No results found.")
        return
    
    col_names = [description[0] for description in cursor.description]
    col_widths = [len(str(name)) for name in col_names]
    
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))
            
    header = " | ".join(str(name).ljust(width) for name, width in zip(col_names, col_widths))
    print(header)
    print("-" * len(header))
    
    for row in rows:
        print(" | ".join(str(val).ljust(width) for val, width in zip(row, col_widths)))

def main():
    # Use the absolute path to backtesting.db found in the backend folder
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', 'backtesting.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}. Please ensure the backend DB is initialized.")
        return

    conn = sqlite3.connect(db_path)
    # Important: Enable SQLite foreign key constraints globally
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # Query 1: All rows from Backtest_Runs
    print_header("1. All rows from Backtest_Runs")
    cur.execute("SELECT * FROM Backtest_Runs;")
    print_results(cur)

    # Query 2: All rows from Performance_Metrics
    print_header("2. All rows from Performance_Metrics")
    cur.execute("SELECT * FROM Performance_Metrics;")
    print_results(cur)

    # Query 3: All Daily_Results for run_id = 1 ordered by trade_date
    print_header("3. All Daily_Results for run_id = 1 ordered by trade_date")
    cur.execute("SELECT * FROM Daily_Results WHERE run_id = 1 ORDER BY trade_date;")
    print_results(cur)

    # Query 4: Sharpe ratio ranking
    print_header("4. Sharpe ratio ranking")
    cur.execute('''
        SELECT 
            b.ticker_symbol, 
            s.strategy_name, 
            p.sharpe_ratio 
        FROM Backtest_Runs b 
        JOIN Strategies s ON b.strategy_id = s.strategy_id 
        JOIN Performance_Metrics p ON b.run_id = p.run_id 
        ORDER BY p.sharpe_ratio DESC;
    ''')
    print_results(cur)

    # Query 5: Average sharpe and drawdown per strategy with run count
    print_header("5. Average sharpe and drawdown per strategy with run count")
    cur.execute('''
        SELECT 
            s.strategy_name, 
            COUNT(b.run_id) as run_count, 
            AVG(p.sharpe_ratio) as avg_sharpe, 
            AVG(p.max_drawdown) as avg_drawdown 
        FROM Strategies s 
        JOIN Backtest_Runs b ON s.strategy_id = b.strategy_id 
        JOIN Performance_Metrics p ON b.run_id = p.run_id 
        GROUP BY s.strategy_name;
    ''')
    print_results(cur)

    # Query 6: All rows from v_portfolio_allocation_history view
    print_header("6. All rows from v_portfolio_allocation_history view")
    try:
        cur.execute("SELECT * FROM v_portfolio_allocation_history;")
        print_results(cur)
    except Exception as e:
        print(f"Error querying view: {e}")

    # Query 7: Trigger test
    print_header("7. Trigger Test: Portfolio_Weights allocation limit")
    try:
        # Dynamically fetch strategies to satisfy foreign key requirement inside test
        cur.execute("SELECT strategy_id FROM Strategies LIMIT 3;")
        strats = cur.fetchall()
        
        # If DB doesn't have 3 strategies, safely fallback
        s1 = strats[0][0] if len(strats) > 0 else 1
        s2 = strats[1][0] if len(strats) > 1 else 2
        s3 = strats[2][0] if len(strats) > 2 else 3
        
        test_date = '2099-12-31'
        
        # Clean state idempotently (in case a prior failure leaked data)
        cur.execute("DELETE FROM Portfolio_Weights WHERE run_id = 1 AND optimization_date = ?", (test_date,))
        conn.commit()

        print("Inserting two Portfolio_Weights rows for run_id=1 summing to 1.0 (weights 0.5 each)...")
        cur.execute("INSERT INTO Portfolio_Weights (run_id, strategy_id, allocation_weight, optimization_date) VALUES (1, ?, 0.5, ?)", (s1, test_date))
        cur.execute("INSERT INTO Portfolio_Weights (run_id, strategy_id, allocation_weight, optimization_date) VALUES (1, ?, 0.5, ?)", (s2, test_date))
        conn.commit()
        print("Success: First two inserts committed.")

        print("Attempting a third insert (weight 0.1) that pushes the sum over 1.0...")
        cur.execute("INSERT INTO Portfolio_Weights (run_id, strategy_id, allocation_weight, optimization_date) VALUES (1, ?, 0.1, ?)", (s3, test_date))
        conn.commit()
        
        # If no error triggers, this line hits
        print("FAIL: The trigger did not abort the transaction and allowed weights to exceed 1.0.")
    except sqlite3.DatabaseError as e:
        print(f"SUCCESS: The trigger correctly aborted the insert.\nRejection Message caught: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        try:
            # Cleanup so as to not pollute real stats with test weights
            cur.execute("DELETE FROM Portfolio_Weights WHERE run_id = 1 AND optimization_date = ?", (test_date,))
            conn.commit()
        except:
             pass

    conn.close()

if __name__ == '__main__':
    main()
