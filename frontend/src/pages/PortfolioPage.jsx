import { useState, useEffect } from 'react';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { getBacktestRuns, optimizePortfolio } from '../api.js';

export default function PortfolioPage() {
  const [runs, setRuns] = useState([]);
  const [selectedRuns, setSelectedRuns] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    getBacktestRuns().then((res) => setRuns(res.data)).catch(() => {});
  }, []);

  const toggleRun = (runId) => {
    setSelectedRuns((prev) =>
      prev.includes(runId) ? prev.filter((id) => id !== runId) : [...prev, runId]
    );
  };

  const handleOptimize = async () => {
    if (selectedRuns.length < 2) {
      setError('Select at least 2 backtest runs to optimize');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await optimizePortfolio(selectedRuns);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Optimization failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="section-header">
        <h1 className="section-title">Portfolio Optimization</h1>
        <p className="section-subtitle">
          Combine multiple strategies using mean-variance optimization
        </p>
      </div>

      <div className="page-grid">
        {/* Left: Run Selection */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Select Runs to Combine</h2>
            <span className="badge badge-success">{selectedRuns.length} selected</span>
          </div>

          {error && (
            <div style={{ padding: '0.75rem', background: 'rgba(239,68,68,0.1)', borderRadius: 'var(--radius-sm)', color: 'var(--danger)', fontSize: '0.875rem', marginBottom: '1rem' }}>
              {error}
            </div>
          )}

          {runs.length === 0 ? (
            <div className="empty-state">
              <p>No backtest runs available. Run some backtests first.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {runs.map((r) => (
                <label
                  key={r.run_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.75rem',
                    borderRadius: 'var(--radius-sm)',
                    border: `1px solid ${selectedRuns.includes(r.run_id) ? 'var(--accent)' : 'var(--border)'}`,
                    background: selectedRuns.includes(r.run_id) ? 'rgba(99,102,241,0.08)' : 'transparent',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedRuns.includes(r.run_id)}
                    onChange={() => toggleRun(r.run_id)}
                    style={{ accentColor: 'var(--accent)' }}
                  />
                  <div>
                    <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>
                      #{r.run_id} — {r.strategy_name}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {r.ticker_symbol} | {r.start_date} → {r.end_date}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          )}

          <button
            id="optimize-btn"
            className="btn btn-primary"
            style={{ width: '100%', justifyContent: 'center', marginTop: '1rem' }}
            onClick={handleOptimize}
            disabled={selectedRuns.length < 2 || loading}
          >
            {loading ? 'Optimizing...' : '⚡ Optimize Portfolio'}
          </button>
        </div>

        {/* Right: Results */}
        <div>
          {result ? (
            <div className="fade-in">
              {/* Max Sharpe Portfolio */}
              <div className="card" style={{ marginBottom: '1rem' }}>
                <div className="card-header">
                  <h2 className="card-title">📈 Max Sharpe Portfolio</h2>
                  <span className="badge badge-success">
                    Sharpe: {result.max_sharpe_portfolio.sharpe_ratio.toFixed(4)}
                  </span>
                </div>
                <div className="metrics-grid">
                  <div className="metric-card">
                    <div className="metric-label">Expected Return</div>
                    <div className="metric-value positive">
                      {(result.max_sharpe_portfolio.return * 100).toFixed(2)}%
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-label">Volatility</div>
                    <div className="metric-value neutral">
                      {(result.max_sharpe_portfolio.volatility * 100).toFixed(2)}%
                    </div>
                  </div>
                </div>
                <p className="form-label" style={{ fontWeight: 600, margin: '1rem 0 0.5rem' }}>
                  Optimal Weights
                </p>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  {Object.entries(result.max_sharpe_portfolio.weights).map(([runId, w]) => {
                    const run = runs.find((r) => r.run_id === Number(runId));
                    return (
                      <span key={runId} className="badge badge-warning">
                        {run ? run.strategy_name : `Run #${runId}`}: {(w * 100).toFixed(1)}%
                      </span>
                    );
                  })}
                </div>
              </div>

              {/* Min Variance Portfolio */}
              <div className="card" style={{ marginBottom: '1rem' }}>
                <div className="card-header">
                  <h2 className="card-title">🛡️ Min Variance Portfolio</h2>
                </div>
                <div className="metrics-grid">
                  <div className="metric-card">
                    <div className="metric-label">Expected Return</div>
                    <div className="metric-value positive">
                      {(result.min_variance_portfolio.return * 100).toFixed(2)}%
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-label">Volatility</div>
                    <div className="metric-value neutral">
                      {(result.min_variance_portfolio.volatility * 100).toFixed(2)}%
                    </div>
                  </div>
                </div>
              </div>

              {/* Efficient Frontier */}
              <div className="card">
                <div className="card-header">
                  <h2 className="card-title">Efficient Frontier</h2>
                  <span className="card-subtitle">{result.efficient_frontier.returns.length.toLocaleString()} simulated portfolios</span>
                </div>
                <div className="chart-container">
                  <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart>
                      <CartesianGrid strokeDasharray="3 3" stroke="#2a3042" />
                      <XAxis
                        dataKey="volatility"
                        name="Volatility"
                        tick={{ fill: '#64748b', fontSize: 11 }}
                        tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                        label={{ value: 'Volatility', position: 'bottom', fill: '#64748b' }}
                      />
                      <YAxis
                        dataKey="ret"
                        name="Return"
                        tick={{ fill: '#64748b', fontSize: 11 }}
                        tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                        label={{ value: 'Return', angle: -90, position: 'left', fill: '#64748b' }}
                      />
                      <Tooltip
                        contentStyle={{ background: '#1a1f2e', border: '1px solid #2a3042', borderRadius: 8, color: '#e2e8f0' }}
                        formatter={(val, name) => [`${(val * 100).toFixed(2)}%`, name]}
                      />
                      <Scatter
                        data={result.efficient_frontier.returns.map((r, i) => ({
                          ret: r,
                          volatility: result.efficient_frontier.volatilities[i],
                          sharpe: result.efficient_frontier.sharpe_ratios[i],
                        }))}
                        fill="#6366f1"
                        fillOpacity={0.4}
                        r={2}
                      />
                      {/* Max Sharpe point */}
                      <Scatter
                        data={[{
                          ret: result.max_sharpe_portfolio.return,
                          volatility: result.max_sharpe_portfolio.volatility,
                        }]}
                        fill="#10b981"
                        r={8}
                        name="Max Sharpe"
                      />
                      {/* Min Var point */}
                      <Scatter
                        data={[{
                          ret: result.min_variance_portfolio.return,
                          volatility: result.min_variance_portfolio.volatility,
                        }]}
                        fill="#f59e0b"
                        r={8}
                        name="Min Variance"
                      />
                    </ScatterChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          ) : (
            <div className="empty-state card">
              <h3>Select Runs & Optimize</h3>
              <p>Choose at least 2 backtest runs to find the optimal portfolio allocation.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
