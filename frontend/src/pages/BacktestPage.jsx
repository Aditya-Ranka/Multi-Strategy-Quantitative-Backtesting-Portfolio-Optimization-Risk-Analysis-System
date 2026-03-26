import { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { getStrategies, fetchMarketData, runBacktest, getRunDetails } from '../api.js';

export default function BacktestPage() {
  const [strategies, setStrategies] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState('');
  const [params, setParams] = useState({});
  const [strategyParams, setStrategyParams] = useState([]);
  const [ticker, setTicker] = useState('RELIANCE.NS');
  const [startDate, setStartDate] = useState('2023-01-01');
  const [endDate, setEndDate] = useState('2024-12-31');
  const [initialCapital, setInitialCapital] = useState(100000);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [dailyData, setDailyData] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    getStrategies()
      .then((res) => setStrategies(res.data))
      .catch(() => setError('Failed to load strategies. Is the backend running?'));
  }, []);

  const handleStrategyChange = (name) => {
    setSelectedStrategy(name);
    const strat = strategies.find((s) => s.strategy_name === name);
    if (strat) {
      setStrategyParams(strat.parameters || []);
      const defaults = {};
      (strat.parameters || []).forEach((p) => {
        defaults[p.parameter_name] = p.default_value || '';
      });
      setParams(defaults);
    }
  };

  const handleRunBacktest = async () => {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      // First fetch market data
      await fetchMarketData(ticker, startDate, endDate);

      // Then run backtest
      const res = await runBacktest({
        user_id: 1,
        strategy_name: selectedStrategy,
        ticker,
        params,
        start_date: startDate,
        end_date: endDate,
        initial_capital: initialCapital,
      });

      setResult(res.data);

      // Fetch daily results for chart
      const details = await getRunDetails(res.data.run_id);
      setDailyData(details.data.daily_results || []);
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Backtest failed');
    } finally {
      setLoading(false);
    }
  };

  const formatPercent = (val) =>
    val != null ? `${(val * 100).toFixed(2)}%` : '—';

  const formatNum = (val) =>
    val != null ? val.toFixed(4) : '—';

  return (
    <div>
      <div className="section-header">
        <h1 className="section-title">Run Backtest</h1>
        <p className="section-subtitle">
          Select a strategy, configure parameters, and simulate trading performance
        </p>
      </div>

      <div className="page-grid">
        {/* Left: Form */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Configuration</h2>
          </div>

          {error && (
            <div style={{ padding: '0.75rem', background: 'rgba(239,68,68,0.1)', borderRadius: 'var(--radius-sm)', color: 'var(--danger)', fontSize: '0.875rem', marginBottom: '1rem' }}>
              {error}
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Strategy</label>
            <select
              id="strategy-select"
              className="form-select"
              value={selectedStrategy}
              onChange={(e) => handleStrategyChange(e.target.value)}
            >
              <option value="">Select a strategy...</option>
              {strategies.map((s) => (
                <option key={s.strategy_id} value={s.strategy_name}>
                  {s.strategy_name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Ticker Symbol</label>
            <input
              id="ticker-input"
              className="form-input"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="e.g. RELIANCE.NS, TCS.NS, INFY.BO"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Start Date</label>
              <input
                id="start-date"
                type="date"
                className="form-input"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label">End Date</label>
              <input
                id="end-date"
                type="date"
                className="form-input"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Initial Capital (₹)</label>
            <input
              id="capital-input"
              type="number"
              className="form-input"
              value={initialCapital}
              onChange={(e) => setInitialCapital(Number(e.target.value))}
            />
          </div>

          {/* Dynamic Strategy Parameters */}
          {strategyParams.length > 0 && (
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem', marginTop: '0.5rem' }}>
              <p className="form-label" style={{ fontWeight: 600, marginBottom: '0.75rem' }}>
                Strategy Parameters
              </p>
              {strategyParams.map((p) => (
                <div className="form-group" key={p.parameter_id}>
                  <label className="form-label">{p.parameter_name}</label>
                  <input
                    className="form-input"
                    type={p.data_type === 'FLOAT' ? 'number' : 'number'}
                    step={p.data_type === 'FLOAT' ? '0.1' : '1'}
                    value={params[p.parameter_name] || ''}
                    onChange={(e) =>
                      setParams({ ...params, [p.parameter_name]: e.target.value })
                    }
                  />
                </div>
              ))}
            </div>
          )}

          <button
            id="run-backtest-btn"
            className="btn btn-primary"
            style={{ width: '100%', justifyContent: 'center', marginTop: '0.5rem' }}
            onClick={handleRunBacktest}
            disabled={!selectedStrategy || loading}
          >
            {loading ? (
              <>
                <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2, marginRight: 0 }}></span>
                Running...
              </>
            ) : (
              '▶ Run Backtest'
            )}
          </button>
        </div>

        {/* Right: Results */}
        <div>
          {result ? (
            <div className="fade-in">
              {/* Metrics Grid */}
              <div className="metrics-grid">
                {[
                  { label: 'Total Return', value: formatPercent(result.metrics.total_return), cls: result.metrics.total_return >= 0 ? 'positive' : 'negative' },
                  { label: 'CAGR', value: formatPercent(result.metrics.cagr), cls: result.metrics.cagr >= 0 ? 'positive' : 'negative' },
                  { label: 'Volatility', value: formatPercent(result.metrics.volatility), cls: 'neutral' },
                  { label: 'Sharpe Ratio', value: formatNum(result.metrics.sharpe_ratio), cls: result.metrics.sharpe_ratio >= 1 ? 'positive' : result.metrics.sharpe_ratio >= 0 ? 'neutral' : 'negative' },
                  { label: 'Sortino Ratio', value: formatNum(result.metrics.sortino_ratio), cls: 'neutral' },
                  { label: 'Max Drawdown', value: formatPercent(result.metrics.max_drawdown), cls: 'negative' },
                  { label: 'Calmar Ratio', value: formatNum(result.metrics.calmar_ratio), cls: 'neutral' },
                  { label: 'Win Rate', value: formatPercent(result.metrics.win_rate), cls: result.metrics.win_rate >= 0.5 ? 'positive' : 'negative' },
                  { label: 'Profit Factor', value: formatNum(result.metrics.profit_factor), cls: result.metrics.profit_factor >= 1 ? 'positive' : 'negative' },
                  { label: 'VaR (5%)', value: formatPercent(result.metrics.historical_var), cls: 'negative' },
                  { label: 'CVaR (5%)', value: formatPercent(result.metrics.cvar), cls: 'negative' },
                ].map((m) => (
                  <div className="metric-card" key={m.label}>
                    <div className="metric-label">{m.label}</div>
                    <div className={`metric-value ${m.cls}`}>{m.value}</div>
                  </div>
                ))}
              </div>

              {/* Equity Curve */}
              {dailyData.length > 0 && (
                <div className="card" style={{ marginTop: '1rem' }}>
                  <div className="card-header">
                    <h2 className="card-title">Equity Curve</h2>
                    <span className="card-subtitle">Cumulative return over time</span>
                  </div>
                  <div className="chart-container">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={dailyData.map((d) => ({
                          ...d,
                          cumulative_pct: (d.cumulative_return * 100).toFixed(2),
                        }))}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#2a3042" />
                        <XAxis
                          dataKey="trade_date"
                          tick={{ fill: '#64748b', fontSize: 11 }}
                          tickFormatter={(v) => v.slice(5)}
                          interval={Math.floor(dailyData.length / 8)}
                        />
                        <YAxis
                          tick={{ fill: '#64748b', fontSize: 11 }}
                          tickFormatter={(v) => `${v}%`}
                        />
                        <Tooltip
                          contentStyle={{
                            background: '#1a1f2e',
                            border: '1px solid #2a3042',
                            borderRadius: 8,
                            color: '#e2e8f0',
                          }}
                          formatter={(val) => [`${val}%`, 'Return']}
                        />
                        <Line
                          type="monotone"
                          dataKey="cumulative_pct"
                          stroke="#6366f1"
                          strokeWidth={2}
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="empty-state card">
              <h3>No Results Yet</h3>
              <p>Configure a strategy and click "Run Backtest" to see results.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
