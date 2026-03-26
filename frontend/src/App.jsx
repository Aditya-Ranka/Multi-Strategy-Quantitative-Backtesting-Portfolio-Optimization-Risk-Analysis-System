import { useState } from 'react';
import BacktestPage from './pages/BacktestPage.jsx';
import ResultsPage from './pages/ResultsPage.jsx';
import PortfolioPage from './pages/PortfolioPage.jsx';
import RiskPage from './pages/RiskPage.jsx';

const PAGES = ['Backtest', 'Results', 'Portfolio', 'Risk Analysis'];

export default function App() {
  const [activePage, setActivePage] = useState('Backtest');

  const renderPage = () => {
    switch (activePage) {
      case 'Backtest': return <BacktestPage />;
      case 'Results': return <ResultsPage />;
      case 'Portfolio': return <PortfolioPage />;
      case 'Risk Analysis': return <RiskPage />;
      default: return <BacktestPage />;
    }
  };

  return (
    <div className="app">
      <nav className="navbar">
        <div className="navbar-inner">
          <div className="logo">QuantBacktest</div>
          <div className="nav-links">
            {PAGES.map((page) => (
              <button
                key={page}
                className={`nav-link ${activePage === page ? 'active' : ''}`}
                onClick={() => setActivePage(page)}
              >
                {page}
              </button>
            ))}
          </div>
        </div>
      </nav>
      <main className="main-content fade-in" key={activePage}>
        {renderPage()}
      </main>
    </div>
  );
}
