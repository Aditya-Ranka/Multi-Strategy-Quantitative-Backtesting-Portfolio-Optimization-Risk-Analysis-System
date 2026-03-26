import { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import {
  getBacktestRuns, getVarCvar, getDrawdown, getStationarity, getWalkForward, getBootstrapSharpe,
} from '../api.js';

export default function RiskPage() {
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState('');
  const [loading, setLoading] = useState(false);
  const [varData, setVarData] = useState(null);
  const [drawdownData, setDrawdownData] = useState(null);
  const [stationarityData, setStationarityData] = useState(null);
  const [walkForwardData, setWalkForwardData] = useState(null);
  const [bootstrapData, setBootstrapData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getBacktestRuns().then((res) => setRuns(res.data)).catch(() => {});
  }, []);

  const runAllAnalytics = async () => {
    if (!selectedRun) return;
    setLoading(true);
    setError('');
    try {
      const [var_, dd, stat, wf, bs] = await Promise.all([
        getVarCvar(selectedRun),
        getDrawdown(selectedRun),
        getStationarity(selectedRun),
        getWalkForward(selectedRun),
        getBootstrapSharpe(selectedRun),
      ]);
      setVarData(var_.data);
      setDrawdownData(dd.data);
      setStationarityData(stat.data);
      setWalkForwardData(wf.data);
      setBootstrapData(bs.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const fmt = (v) => (v != null ? (typeof v === 'number' ? v.toFixed(6) : v) : '—');
  const fmtPct = (v) => (v != null ? `${(v * 100).toFixed(3)}%` : '—');

  return (
    <div>
      <div className="section-header">
        <h1 className="section-title">Risk Analysis & Validation</h1>
        <p className="section-subtitle">
          VaR/CVaR, drawdown, stationarity tests, walk-forward validation, and bootstrap Sharpe
        </p>
      </div>

      {/* Run selector */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'end' }}>
          <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
            <label className="form-label">Select Backtest Run</label>
            <select
              id="risk-run-select"
              className="form-select"
              value={selectedRun}
              onChange={(e) => setSelectedRun(e.target.value)}
            >
              <option value="">Choose a run...</option>
              {runs.map((r) => (
                <option key={r.run_id} value={r.run_id}>
                  #{r.run_id} — {r.strategy_name} ({r.ticker_symbol})
                </option>
              ))}
            </select>
          </div>
          <button
            id="run-risk-btn"
            className="btn btn-primary"
            onClick={runAllAnalytics}
            disabled={!selectedRun || loading}
            style={{ marginBottom: 0 }}
          >
            {loading ? 'Analyzing...' : '🔍 Run Full Analysis'}
          </button>
        </div>
        {error && (
          <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: 'rgba(239,68,68,0.1)', borderRadius: 'var(--radius-sm)', color: 'var(--danger)', fontSize: '0.875rem' }}>
            {error}
          </div>
        )}
      </div>

      {/* Results */}
      {varData && (
        <div className="fade-in">
          {/* VaR / CVaR */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div className="card-header">
              <h2 className="card-title">Value at Risk & Conditional VaR (5%)</h2>
            </div>
            <div className="risk-method-grid">
              {['historical', 'parametric', 'monte_carlo'].map((method) => (
                <div className="metric-card" key={method}>
                  <div className="metric-label" style={{ textTransform: 'capitalize' }}>
                    {method.replace('_', ' ')}
                  </div>
                  <div style={{ marginTop: '0.75rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>VaR</span>
                      <span className="metric-value negative" style={{ fontSize: '1rem' }}>
                        {fmtPct(varData[method]?.var)}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>CVaR</span>
                      <span className="metric-value negative" style={{ fontSize: '1rem' }}>
                        {fmtPct(varData[method]?.cvar)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Drawdown Chart */}
          {drawdownData && (
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <div className="card-header">
                <h2 className="card-title">Drawdown Analysis</h2>
                <div style={{ display: 'flex', gap: '1rem' }}>
                  <span className="badge badge-danger">Max: {fmtPct(drawdownData.max_drawdown)}</span>
                  <span className="badge badge-warning">Avg: {fmtPct(drawdownData.avg_drawdown)}</span>
                  <span className="badge badge-success">
                    Recovery: {drawdownData.recovery_time_days >= 0 ? `${drawdownData.recovery_time_days} days` : 'Not recovered'}
                  </span>
                </div>
              </div>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={drawdownData.drawdown_series}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a3042" />
                    <XAxis
                      dataKey="date"
                      tick={{ fill: '#64748b', fontSize: 11 }}
                      tickFormatter={(v) => v.slice(5)}
                      interval={Math.floor(drawdownData.drawdown_series.length / 8)}
                    />
                    <YAxis
                      tick={{ fill: '#64748b', fontSize: 11 }}
                      tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                    />
                    <Tooltip
                      contentStyle={{ background: '#1a1f2e', border: '1px solid #2a3042', borderRadius: 8, color: '#e2e8f0' }}
                      formatter={(val) => [`${(val * 100).toFixed(3)}%`, 'Drawdown']}
                    />
                    <ReferenceLine y={0} stroke="#64748b" strokeDasharray="3 3" />
                    <Line type="monotone" dataKey="drawdown" stroke="#ef4444" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Stationarity Tests */}
          {stationarityData && (
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <div className="card-header">
                <h2 className="card-title">Stationarity Tests</h2>
              </div>
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Test</th>
                      <th>Statistic</th>
                      <th>P-Value</th>
                      <th>Result</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td style={{ fontWeight: 600 }}>Augmented Dickey-Fuller</td>
                      <td>{fmt(stationarityData.adf?.test_statistic)}</td>
                      <td>{fmt(stationarityData.adf?.p_value)}</td>
                      <td>
                        <span className={`badge ${stationarityData.adf?.is_stationary ? 'badge-success' : 'badge-danger'}`}>
                          {stationarityData.adf?.is_stationary ? 'Stationary' : 'Non-Stationary'}
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td style={{ fontWeight: 600 }}>KPSS</td>
                      <td>{fmt(stationarityData.kpss?.test_statistic)}</td>
                      <td>{fmt(stationarityData.kpss?.p_value)}</td>
                      <td>
                        <span className={`badge ${stationarityData.kpss?.is_stationary ? 'badge-success' : 'badge-danger'}`}>
                          {stationarityData.kpss?.is_stationary ? 'Stationary' : 'Non-Stationary'}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Walk-Forward Validation */}
          {walkForwardData && (
            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <div className="card-header">
                <h2 className="card-title">Walk-Forward Validation</h2>
                <span className={`badge ${walkForwardData.likely_overfit ? 'badge-danger' : 'badge-success'}`}>
                  {walkForwardData.likely_overfit ? '⚠ Likely Overfit' : '✓ Robust'}
                </span>
              </div>
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Split</th>
                      <th>In-Sample Sharpe</th>
                      <th>Out-of-Sample Sharpe</th>
                      <th>Degradation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {walkForwardData.splits.map((s) => (
                      <tr key={s.split}>
                        <td>#{s.split}</td>
                        <td>{s.in_sample_sharpe}</td>
                        <td>{s.out_of_sample_sharpe}</td>
                        <td>
                          <span className={s.degradation > 0.5 ? 'metric-value negative' : ''} style={{ fontSize: '0.875rem' }}>
                            {s.degradation}
                          </span>
                        </td>
                      </tr>
                    ))}
                    <tr style={{ fontWeight: 700 }}>
                      <td>Average</td>
                      <td></td>
                      <td></td>
                      <td>{walkForwardData.avg_degradation}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Bootstrap Sharpe */}
          {bootstrapData && (
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Bootstrap Sharpe Ratio Significance</h2>
                <span className={`badge ${bootstrapData.is_significant ? 'badge-success' : 'badge-danger'}`}>
                  {bootstrapData.is_significant ? '✓ Significant (p < 0.05)' : '✗ Not Significant'}
                </span>
              </div>
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-label">Original Sharpe</div>
                  <div className="metric-value neutral">{bootstrapData.original_sharpe}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Bootstrap Mean</div>
                  <div className="metric-value neutral">{bootstrapData.bootstrap_mean}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">95% CI Lower</div>
                  <div className="metric-value neutral">{bootstrapData.confidence_interval[0]}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">95% CI Upper</div>
                  <div className="metric-value neutral">{bootstrapData.confidence_interval[1]}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">P-Value</div>
                  <div className={`metric-value ${bootstrapData.p_value < 0.05 ? 'positive' : 'negative'}`}>
                    {bootstrapData.p_value}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
