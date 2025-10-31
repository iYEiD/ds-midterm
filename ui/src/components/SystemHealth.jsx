import { useState, useEffect } from 'react';
import { apiService } from '../utils/api';
import './SystemHealth.css';

function SystemHealth() {
  const [health, setHealth] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [kafkaMetrics, setKafkaMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  const fetchAllData = async () => {
    try {
      const [healthRes, metricsRes] = await Promise.all([
        apiService.getHealth(),
        apiService.getMetrics(),
      ]);
      setHealth(healthRes.data);
      setMetrics(metricsRes.data);
      setKafkaMetrics(metricsRes.data); // Kafka info is in the main metrics response
    } catch (error) {
      console.error('Failed to fetch health data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading system health...</div>;
  }

  const getStatusIcon = (status) => {
    if (status === 'healthy' || status === 'connected') return '✅';
    if (status === 'degraded') return '⚠️';
    return '❌';
  };

  return (
    <div className="system-health">
      <h2>System Health Monitor</h2>

      <div className="health-grid">
        <div className="health-card">
          <h3>Overall Status</h3>
          <div className={`status-indicator ${health?.status}`}>
            {getStatusIcon(health?.status)}
            <span className="status-text">{health?.status?.toUpperCase() || 'UNKNOWN'}</span>
          </div>
          <div className="timestamp">
            Last checked: {new Date().toLocaleTimeString()}
          </div>
        </div>

        <div className="health-card">
          <h3>MongoDB</h3>
          <div className={`status-indicator ${health?.components?.mongodb?.status}`}>
            {getStatusIcon(health?.components?.mongodb?.status)}
            <span className="status-text">{health?.components?.mongodb?.status?.toUpperCase() || 'UNKNOWN'}</span>
          </div>
          <div className="component-details">
            {health?.components?.mongodb?.unique_players && (
              <p>Players: {health.components.mongodb.unique_players}</p>
            )}
          </div>
        </div>

        <div className="health-card">
          <h3>ChromaDB</h3>
          <div className={`status-indicator ${health?.components?.chromadb?.status}`}>
            {getStatusIcon(health?.components?.chromadb?.status)}
            <span className="status-text">{health?.components?.chromadb?.status?.toUpperCase() || 'UNKNOWN'}</span>
          </div>
          <div className="component-details">
            {health?.components?.chromadb?.embeddings && (
              <p>Embeddings: {health.components.chromadb.embeddings}</p>
            )}
          </div>
        </div>

        <div className="health-card">
          <h3>Kafka</h3>
          <div className={`status-indicator ${health?.components?.kafka?.status}`}>
            {getStatusIcon(health?.components?.kafka?.status)}
            <span className="status-text">{health?.components?.kafka?.status?.toUpperCase() || 'UNKNOWN'}</span>
          </div>
        </div>
      </div>

      <div className="metrics-section">
        <h3>System Metrics</h3>
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-label">CPU Usage</div>
            <div className="metric-value">
              {metrics?.system?.cpu?.percent?.toFixed(1)}%
            </div>
            <div className={`metric-bar ${metrics?.system?.cpu?.percent > 80 ? 'high' : ''}`}>
              <div 
                className="metric-fill"
                style={{ width: `${metrics?.system?.cpu?.percent || 0}%` }}
              />
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-label">Memory Usage</div>
            <div className="metric-value">
              {metrics?.system?.memory?.used_gb?.toFixed(2)} GB
            </div>
            <div className="metric-bar">
              <div 
                className="metric-fill"
                style={{ 
                  width: `${metrics?.system?.memory?.percent || 0}%` 
                }}
              />
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-label">Disk Usage</div>
            <div className="metric-value">
              {metrics?.system?.disk?.percent?.toFixed(1)}%
            </div>
            <div className={`metric-bar ${metrics?.system?.disk?.percent > 80 ? 'high' : ''}`}>
              <div 
                className="metric-fill"
                style={{ width: `${metrics?.system?.disk?.percent || 0}%` }}
              />
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-label">Active Threads</div>
            <div className="metric-value">
              {metrics?.system?.process?.num_threads || 0}
            </div>
          </div>
        </div>
      </div>

      <div className="kafka-section">
        <h3>Scraping Statistics</h3>
        <div className="kafka-topics">
          <div className="topic-card">
            <div className="topic-header">
              <h4>Total Scraped</h4>
              <span className="topic-status healthy">✅</span>
            </div>
            <div className="topic-details">
              <div className="topic-stat">
                <span>Documents:</span>
                <strong>{metrics?.scraping?.total_scraped || 0}</strong>
              </div>
              <div className="topic-stat">
                <span>Rate:</span>
                <strong>{metrics?.scraping?.scraping_rate?.toFixed(2) || 0} / hour</strong>
              </div>
            </div>
          </div>

          <div className="topic-card">
            <div className="topic-header">
              <h4>Processed Stats</h4>
              <span className="topic-status healthy">✅</span>
            </div>
            <div className="topic-details">
              <div className="topic-stat">
                <span>Total:</span>
                <strong>{metrics?.scraping?.total_processed || 0}</strong>
              </div>
              <div className="topic-stat">
                <span>Rate:</span>
                <strong>{metrics?.scraping?.processing_rate?.toFixed(2) || 0} / hour</strong>
              </div>
            </div>
          </div>

          <div className="topic-card">
            <div className="topic-header">
              <h4>Vector Store</h4>
              <span className="topic-status healthy">✅</span>
            </div>
            <div className="topic-details">
              <div className="topic-stat">
                <span>Embeddings:</span>
                <strong>{metrics?.scraping?.embeddings_count || 0}</strong>
              </div>
              <div className="topic-stat">
                <span>Unique Players:</span>
                <strong>{metrics?.scraping?.unique_players || 0}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="system-info">
        <h3>System Information</h3>
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">Python Version:</span>
            <span className="info-value">3.12.3</span>
          </div>
          <div className="info-item">
            <span className="info-label">FastAPI Version:</span>
            <span className="info-value">0.120.2</span>
          </div>
          <div className="info-item">
            <span className="info-label">Kafka Version:</span>
            <span className="info-value">7.5.0</span>
          </div>
          <div className="info-item">
            <span className="info-label">Uptime:</span>
            <span className="info-value">{health?.uptime || 'N/A'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SystemHealth;
