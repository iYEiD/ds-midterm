import { useState } from 'react';
import { apiService } from '../utils/api';
import './Search.css';

function Search() {
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchTerm.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await apiService.searchPlayers(searchTerm);
      setResults(response.data.results || []);
    } catch (err) {
      setError('Failed to search players. Please try again.');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatStat = (value) => {
    if (typeof value === 'number') {
      return value.toFixed(1);
    }
    return value || 'N/A';
  };

  return (
    <div className="search">
      <h2>Player Search</h2>

      <form onSubmit={handleSearch} className="search-form">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Enter player name..."
          className="search-input"
        />
        <button type="submit" className="search-button" disabled={loading}>
          {loading ? 'Searching...' : '🔍 Search'}
        </button>
      </form>

      {error && <div className="error-message">{error}</div>}

      <div className="results-section">
        {results.length === 0 && !loading && searchTerm && (
          <p className="no-results">No players found matching "{searchTerm}"</p>
        )}

        <div className="results-grid">
          {results.map((player, index) => (
            <div key={index} className="player-card">
              <div className="player-header">
                <h3>{player.player_name}</h3>
                <span className="player-id">
                  {player.metadata?.season_type || 'Regular Season'}
                </span>
              </div>
              
              <div className="player-stats">
                <div className="stat-row">
                  <span className="stat-label">GP:</span>
                  <span className="stat-value">{player.stats?.GP || 'N/A'}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">PTS:</span>
                  <span className="stat-value">{player.stats?.PTS || 'N/A'}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">REB:</span>
                  <span className="stat-value">{player.stats?.REB || 'N/A'}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">AST:</span>
                  <span className="stat-value">{player.stats?.AST || 'N/A'}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">FG%:</span>
                  <span className="stat-value">{player.stats?.['FG%'] || 'N/A'}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">3P%:</span>
                  <span className="stat-value">{player.stats?.['3P%'] || 'N/A'}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">FT%:</span>
                  <span className="stat-value">{player.stats?.['FT%'] || 'N/A'}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">STL:</span>
                  <span className="stat-value">{player.stats?.STL || 'N/A'}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">BLK:</span>
                  <span className="stat-value">{player.stats?.BLK || 'N/A'}</span>
                </div>
              </div>

              {player.metadata?.scraped_at && (
                <div className="player-bio">
                  <p><strong>Category:</strong> {player.stats?.stat_category || 'All Stats'}</p>
                  <p><strong>Scraped:</strong> {new Date(player.metadata.scraped_at).toLocaleDateString()}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Search;
