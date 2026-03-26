import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Users
export const getUsers = () => api.get('/users');
export const createUser = (data) => api.post('/users', data);

// Strategies
export const getStrategies = () => api.get('/strategies');

// Market Data
export const fetchMarketData = (ticker, startDate, endDate) =>
  api.post('/market-data/fetch', { ticker, start_date: startDate, end_date: endDate });
export const getMarketData = (ticker, start, end) =>
  api.get(`/market-data/${ticker}`, { params: { start, end } });

// Backtest
export const runBacktest = (data) => api.post('/backtest', data);
export const getBacktestRuns = () => api.get('/backtest/runs');
export const getRunDetails = (runId) => api.get(`/backtest/runs/${runId}`);
export const deleteRun = (runId) => api.delete(`/backtest/runs/${runId}`);

// Portfolio Optimization
export const optimizePortfolio = (runIds) => api.post('/optimize', { run_ids: runIds });

// Risk & Validation
export const getVarCvar = (runId, confidence) =>
  api.get(`/risk/var/${runId}`, { params: { confidence } });
export const getDrawdown = (runId) => api.get(`/risk/drawdown/${runId}`);
export const getStationarity = (runId) => api.get(`/risk/stationarity/${runId}`);
export const getWalkForward = (runId, splits) =>
  api.get(`/risk/walk-forward/${runId}`, { params: { splits } });
export const getBootstrapSharpe = (runId) => api.get(`/risk/bootstrap/${runId}`);

export default api;
