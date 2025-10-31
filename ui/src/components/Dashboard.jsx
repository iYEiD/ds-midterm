import { useState, useEffect } from 'react';
import { apiService } from '../utils/api';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './Dashboard.css';

function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [systemStats, setSystemStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [metricsRes, statsRes] = await Promise.all([
        apiService.getMetrics(),
        apiService.getSystemStats(),
      ]);
      setMetrics(metricsRes.data);
      setSystemStats(statsRes.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  const cpuData = metrics?.system_metrics ? [
    { name: 'CPU Usage', value: metrics.system_metrics.cpu_percent }
  ] : [];

  const memoryData = metrics?.system_metrics ? [
    { name: 'Used', value: metrics.system_metrics.memory_used_mb },
    { name: 'Available', value: metrics.system_metrics.memory_available_mb }
  ] : [];

  return (
    <div className="dashboard">
      <h2>System Dashboard</h2>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>📊 Unique Players</h3>
          <p className="stat-value">{systemStats?.database?.unique_players || 0}</p>
        </div>
        
        <div className="stat-card">
          <h3>📝 Processed Stats</h3>
          <p className="stat-value">{systemStats?.database?.processed_stats_count || 0}</p>
        </div>
        
        <div className="stat-card">
          <h3>🔢 Total Embeddings</h3>
          <p className="stat-value">{systemStats?.vector_store?.total_embeddings || 0}</p>
        </div>
        
        <div className="stat-card">
          <h3>💾 Raw Documents</h3>
          <p className="stat-value">{systemStats?.database?.raw_data_count || 0}</p>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-card">
          <h3>System Resources</h3>
          <div className="system-info">
            <p><strong>CPU Usage:</strong> {metrics?.system_metrics?.cpu_percent?.toFixed(1)}%</p>
            <p><strong>Memory Used:</strong> {metrics?.system_metrics?.memory_used_mb?.toFixed(0)} MB</p>
            <p><strong>Memory Available:</strong> {metrics?.system_metrics?.memory_available_mb?.toFixed(0)} MB</p>
            <p><strong>Disk Usage:</strong> {metrics?.system_metrics?.disk_usage_percent?.toFixed(1)}%</p>
          </div>
        </div>

        <div className="chart-card">
          <h3>Kafka Metrics</h3>
          <div className="kafka-info">
            {metrics?.kafka_metrics?.consumer_offsets && 
              Object.entries(metrics.kafka_metrics.consumer_offsets).map(([topic, data]) => (
                <div key={topic} className="topic-info">
                  <p><strong>{topic}:</strong></p>
                  <p className="indent">Offset: {data.offset}</p>
                  <p className="indent">Lag: {data.lag}</p>
                </div>
              ))
            }
          </div>
        </div>
      </div>

      <div className="recent-activity">
        <h3>System Status</h3>
        <div className="activity-list">
          <div className="activity-item">
            <span className="activity-time">{new Date().toLocaleTimeString()}</span>
            <span className="activity-text">System is operational</span>
            <span className="activity-status success">✓</span>
          </div>
          <div className="activity-item">
            <span className="activity-time">{new Date().toLocaleTimeString()}</span>
            <span className="activity-text">MongoDB connected</span>
            <span className="activity-status success">✓</span>
          </div>
          <div className="activity-item">
            <span className="activity-time">{new Date().toLocaleTimeString()}</span>
            <span className="activity-text">ChromaDB connected</span>
            <span className="activity-status success">✓</span>
          </div>
          <div className="activity-item">
            <span className="activity-time">{new Date().toLocaleTimeString()}</span>
            <span className="activity-text">Kafka consumers active</span>
            <span className="activity-status success">✓</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
