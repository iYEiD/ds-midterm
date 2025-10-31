import { useState } from 'react';
import { apiService } from '../utils/api';
import './RAGQuery.css';

function RAGQuery() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);

  const exampleQueries = [
    "Who are the top 5 scorers in the NBA?",
    "Compare LeBron James and Stephen Curry shooting percentages",
    "Which players average more than 10 rebounds per game?",
    "Tell me about the best three-point shooters",
    "Who has the highest field goal percentage?"
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await apiService.submitQuery(query);
      const result = {
        query,
        response: response.data.answer || response.data.response, // API returns 'answer'
        sources: response.data.context || response.data.sources || [],
        timestamp: new Date().toISOString(),
      };
      
      setResponse(result);
      setHistory([result, ...history.slice(0, 9)]); // Keep last 10
      setQuery('');
    } catch (err) {
      setError('Failed to process query. Please try again.');
      console.error('Query error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (example) => {
    setQuery(example);
  };

  return (
    <div className="rag-query">
      <h2>Natural Language Query (RAG)</h2>
      <p className="subtitle">Ask questions about NBA players and their statistics</p>

      <form onSubmit={handleSubmit} className="query-form">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question about NBA players..."
          className="query-input"
          rows="4"
        />
        <button type="submit" className="query-button" disabled={loading}>
          {loading ? '🤔 Thinking...' : '🚀 Ask Question'}
        </button>
      </form>

      <div className="example-queries">
        <h3>Example Questions:</h3>
        <div className="example-buttons">
          {exampleQueries.map((example, index) => (
            <button
              key={index}
              onClick={() => handleExampleClick(example)}
              className="example-button"
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {response && (
        <div className="response-section">
          <div className="response-card">
            <div className="response-header">
              <h3>Response</h3>
              <span className="timestamp">
                {new Date(response.timestamp).toLocaleString()}
              </span>
            </div>
            
            <div className="query-text">
              <strong>Your Question:</strong> {response.query}
            </div>
            
            <div className="response-text">
              <strong>Answer:</strong>
              <p>{response.response}</p>
            </div>

            {response.sources && response.sources.length > 0 && (
              <div className="sources-section">
                <h4>Sources:</h4>
                <ul className="sources-list">
                  {response.sources.map((source, index) => (
                    <li key={index} className="source-item">
                      <strong>{source.metadata?.player || source.player || 'Unknown Player'}</strong>
                      <p>{source.stats || source.text}</p>
                      <span className="similarity">
                        Relevance: {((source.similarity || 0) * 100).toFixed(1)}%
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {history.length > 0 && (
        <div className="history-section">
          <h3>Recent Queries</h3>
          <div className="history-list">
            {history.map((item, index) => (
              <div key={index} className="history-item">
                <div className="history-query">{item.query}</div>
                <div className="history-time">
                  {new Date(item.timestamp).toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default RAGQuery;
