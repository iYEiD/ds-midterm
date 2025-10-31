import { useState } from 'react';
import { apiService } from '../utils/api';
import './JobSubmit.css';

function JobSubmit() {
  const [urls, setUrls] = useState('');
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!urls.trim()) return;

    setLoading(true);
    setError(null);
    setJobId(null);
    setStatus(null);

    try {
      const urlList = urls.split('\n').filter(url => url.trim());
      const response = await apiService.submitScrapingJob(urlList);
      setJobId(response.data.job_id);
      setStatus('Job submitted successfully!');
    } catch (err) {
      setError('Failed to submit job. Please try again.');
      console.error('Job submission error:', err);
    } finally {
      setLoading(false);
    }
  };

  const checkStatus = async () => {
    if (!jobId) return;

    setLoading(true);
    try {
      const response = await apiService.getJobStatus(jobId);
      setStatus(response.data);
    } catch (err) {
      setError('Failed to check job status.');
      console.error('Status check error:', err);
    } finally {
      setLoading(false);
    }
  };

  const exampleUrls = `https://www.basketball-reference.com/players/j/jamesle01.html
https://www.basketball-reference.com/players/c/curryst01.html
https://www.basketball-reference.com/players/d/duranke01.html`;

  return (
    <div className="job-submit">
      <h2>Submit Scraping Job</h2>
      <p className="subtitle">Add URLs to scrape player data from Basketball Reference</p>

      <form onSubmit={handleSubmit} className="job-form">
        <div className="form-group">
          <label>Player URLs (one per line):</label>
          <textarea
            value={urls}
            onChange={(e) => setUrls(e.target.value)}
            placeholder={exampleUrls}
            className="url-input"
            rows="8"
          />
        </div>

        <div className="form-actions">
          <button type="submit" className="submit-button" disabled={loading}>
            {loading ? '⏳ Submitting...' : '📤 Submit Job'}
          </button>
          <button 
            type="button" 
            onClick={() => setUrls(exampleUrls)} 
            className="example-button"
          >
            Load Example URLs
          </button>
        </div>
      </form>

      {error && <div className="error-message">{error}</div>}

      {jobId && (
        <div className="job-result">
          <div className="result-card">
            <h3>✅ Job Submitted</h3>
            <div className="job-id">
              <strong>Job ID:</strong> 
              <code>{jobId}</code>
            </div>
            <button onClick={checkStatus} className="status-button" disabled={loading}>
              {loading ? 'Checking...' : '🔍 Check Status'}
            </button>
          </div>
        </div>
      )}

      {status && typeof status === 'object' && (
        <div className="status-result">
          <div className="status-card">
            <h3>Job Status</h3>
            <div className="status-details">
              <p><strong>Status:</strong> <span className={`status-badge ${status.status}`}>{status.status}</span></p>
              <p><strong>Progress:</strong> {status.processed || 0} / {status.total || 0}</p>
              {status.message && <p><strong>Message:</strong> {status.message}</p>}
              {status.results && (
                <div className="results-preview">
                  <strong>Results:</strong>
                  <pre>{JSON.stringify(status.results, null, 2)}</pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="info-section">
        <h3>ℹ️ How it works</h3>
        <ol>
          <li>Enter Basketball Reference player URLs (one per line)</li>
          <li>Click "Submit Job" to queue the scraping tasks</li>
          <li>The system will use Kafka workers to scrape data in parallel</li>
          <li>Results are processed and stored in MongoDB</li>
          <li>Embeddings are generated and stored in ChromaDB</li>
          <li>Use the "Check Status" button to monitor progress</li>
        </ol>

        <div className="url-format">
          <h4>URL Format:</h4>
          <code>https://www.basketball-reference.com/players/[first-letter]/[player-id].html</code>
        </div>
      </div>
    </div>
  );
}

export default JobSubmit;
