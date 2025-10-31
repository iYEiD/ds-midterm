import { useState, useEffect } from 'react';
import { apiService } from '../utils/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './Leaders.css';

function Leaders() {
  const [category, setCategory] = useState('PTS');
  const [limit, setLimit] = useState(10);
  const [leaders, setLeaders] = useState([]);
  const [loading, setLoading] = useState(false);

  const categories = [
    { value: 'PTS', label: 'Total Points' },
    { value: 'REB', label: 'Total Rebounds' },
    { value: 'AST', label: 'Total Assists' },
    { value: 'STL', label: 'Total Steals' },
    { value: 'BLK', label: 'Total Blocks' },
    { value: 'FG%', label: 'Field Goal %' },
    { value: '3P%', label: 'Three Point %' },
    { value: 'FT%', label: 'Free Throw %' },
  ];

  useEffect(() => {
    fetchLeaders();
  }, [category, limit]);

  const fetchLeaders = async () => {
    setLoading(true);
    try {
      const response = await apiService.getLeaders(category, limit);
      setLeaders(response.data.leaders || []);
    } catch (error) {
      console.error('Failed to fetch leaders:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatValue = (player) => {
    const value = player.stats?.[category];
    if (!value) return 0;
    // Remove commas from numbers like "1,562"
    return parseFloat(value.toString().replace(/,/g, '')) || 0;
  };

  const chartData = leaders.map(player => ({
    name: player.player_name?.split(' ').pop() || 'Unknown', // Last name only for chart
    value: getStatValue(player),
    fullName: player.player_name,
  }));

  return (
    <div className="leaders">
      <h2>Statistical Leaders</h2>

      <div className="controls">
        <div className="control-group">
          <label>Category:</label>
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            {categories.map(cat => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Top:</label>
          <select value={limit} onChange={(e) => setLimit(Number(e.target.value))}>
            <option value={5}>5</option>
            <option value={10}>10</option>
            <option value={15}>15</option>
            <option value={20}>20</option>
          </select>
        </div>

        <button onClick={fetchLeaders} className="refresh-button" disabled={loading}>
          {loading ? '⏳ Loading...' : '🔄 Refresh'}
        </button>
      </div>

      {leaders.length > 0 && (
        <>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip 
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="custom-tooltip">
                          <p><strong>{payload[0].payload.fullName}</strong></p>
                          <p>{payload[0].value.toFixed(1)}</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend />
                <Bar dataKey="value" fill="#1d428a" name={categories.find(c => c.value === category)?.label} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="leaders-table">
            <table>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Player</th>
                  <th>{categories.find(c => c.value === category)?.label}</th>
                </tr>
              </thead>
              <tbody>
                {leaders.map((player, index) => (
                  <tr key={index} className={index < 3 ? 'top-three' : ''}>
                    <td className="rank">
                      {index === 0 && '🥇'}
                      {index === 1 && '🥈'}
                      {index === 2 && '🥉'}
                      {index > 2 && (index + 1)}
                    </td>
                    <td className="player-name">{player.player_name}</td>
                    <td className="stat-value">
                      {category.includes('%') 
                        ? getStatValue(player).toFixed(1) + '%'
                        : getStatValue(player).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {!loading && leaders.length === 0 && (
        <div className="no-data">
          No data available for this category
        </div>
      )}
    </div>
  );
}

export default Leaders;
