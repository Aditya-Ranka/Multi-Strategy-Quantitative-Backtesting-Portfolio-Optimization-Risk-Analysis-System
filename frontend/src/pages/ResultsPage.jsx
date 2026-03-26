import { useState, useEffect } from 'react';
import { getBacktestRuns, getRunDetails, deleteRun } from '../api.js';

export default function ResultsPage() {
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadRuns = () => {
    setLoading(true);
    getBacktestRuns()
      .then((res) => setRuns(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(loadRuns, []);

  const viewDetails = async (runId) => {
    setSelectedRun(runId);
    try {
      const res = await getRunDetails(runId);
      setDetails(res.data);
    } catch {
      setDetails(null);
    }
  };

  const handleDelete = async (runId) => {
    await deleteRun(runId);
    setSelectedRun(null);
    setDetails(null);
    loadRuns();
  };

  const formatVal = (v) => (v != null ? (typeof v === 'number' ? v.toFixed(4) : v) : '—');

  return (
    <div>
      <div className="section-header">
        <h1 className="section-title">Backtest History</h1>
        <p className="section-subtitle">View and compare past backtest runs</p>
      </div>

      {loading ? (
        <div className="loading"><div className="spinner"></div>Loading runs...</div>
      ) : runs.length === 0 ? (
        <div className="empty-state card">
          <h3>No Runs Yet</h3>
          <p>Run a backtest first to see results here.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Strategy</th>
                  <th>Ticker</th>
                  <th>Period</th>
                  <th>Capital</th>
                  <th>Executed</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.run_id} style={{ cursor: 'pointer' }}>
                    <td>#{r.run_id}</td>
                    <td><span className="badge badge-success">{r.strategy_name}</span></td>
                    <td style={{ fontWeight: 600 }}>{r.ticker_symbol}</td>
                    <td>{r.start_date} → {r.end_date}</td>
                    <td>₹{Number(r.initial_capital).toLocaleString()}</td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.813rem' }}>{r.executed_at}</td>
                    <td>
                      <button className="btn btn-secondary" style={{ marginRight: '0.5rem', padding: '0.375rem 0.75rem', fontSize: '0.75rem' }} onClick={() => viewDetails(r.run_id)}>
                        View
                      </button>
                      <button className="btn btn-danger" style={{ padding: '0.375rem 0.75rem', fontSize: '0.75rem' }} onClick={() => handleDelete(r.run_id)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Run Details Modal */}
      {details && (
        <div className="card fade-in" style={{ marginTop: '1.5rem' }}>
          <div className="card-header">
            <h2 className="card-title">
              Run #{selectedRun} — {details.run?.strategy_name}
            </h2>
            <button className="btn btn-secondary" style={{ padding: '0.375rem 0.75rem', fontSize: '0.75rem' }} onClick={() => { setDetails(null); setSelectedRun(null); }}>
              Close
            </button>
          </div>

          {/* Parameters */}
          {details.parameters?.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <p className="form-label" style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Parameters Used</p>
              <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                {details.parameters.map((p) => (
                  <span key={p.parameter_name} className="badge badge-warning">
                    {p.parameter_name}: {p.parameter_value}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Performance Metrics */}
          {details.metrics && (
            <div className="metrics-grid">
              {Object.entries(details.metrics)
                .filter(([k]) => k !== 'run_id')
                .map(([key, val]) => (
                  <div className="metric-card" key={key}>
                    <div className="metric-label">{key.replace(/_/g, ' ')}</div>
                    <div className="metric-value neutral">{formatVal(val)}</div>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
