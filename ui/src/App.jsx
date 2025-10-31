import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css';
import Dashboard from './components/Dashboard';
import Search from './components/Search';
import RAGQuery from './components/RAGQuery';
import Leaders from './components/Leaders';
import JobSubmit from './components/JobSubmit';
import SystemHealth from './components/SystemHealth';

function App() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/health');
      const data = await response.json();
      setHealth(data);
    } catch (error) {
      console.error('Health check failed:', error);
      setHealth({ status: 'disconnected' });
    }
  };

  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <div className="nav-container">
            <div className="nav-brand">
              <h1>🏀 NBA Stats Scraper</h1>
              <span className={`health-indicator ${health?.status}`}>
                {health?.status === 'healthy' ? '🟢' : '🔴'} 
                {health?.status || 'checking...'}
              </span>
            </div>
            <ul className="nav-menu">
              <li><Link to="/">Dashboard</Link></li>
              <li><Link to="/search">Search</Link></li>
              <li><Link to="/query">RAG Query</Link></li>
              <li><Link to="/leaders">Leaders</Link></li>
              <li><Link to="/submit">Submit Job</Link></li>
              <li><Link to="/health">System Health</Link></li>
            </ul>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/search" element={<Search />} />
            <Route path="/query" element={<RAGQuery />} />
            <Route path="/leaders" element={<Leaders />} />
            <Route path="/submit" element={<JobSubmit />} />
            <Route path="/health" element={<SystemHealth />} />
          </Routes>
        </main>

        <footer className="footer">
          <p>© 2025 NBA Stats Scraper | Distributed RAG-Based System</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
