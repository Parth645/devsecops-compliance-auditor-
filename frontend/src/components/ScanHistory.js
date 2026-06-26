import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import { 
  FiClock, 
  FiCheckCircle, 
  FiXCircle,
  FiAlertTriangle,
  FiGitBranch,
  FiCalendar,
  FiSearch,
  FiFilter,
  FiRefreshCw
} from 'react-icons/fi';
import { useAppContext } from '../context/AppContext';
import { apiService } from '../services/api';
import { format, formatDistanceToNow } from 'date-fns';

const HistoryContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;

  @media (max-width: 768px) {
    padding: 1rem;
  }
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;

  @media (max-width: 768px) {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  h1 {
    font-size: 2.5rem;
    font-weight: 700;
    color: #1e293b;
    display: flex;
    align-items: center;
    gap: 0.5rem;

    @media (max-width: 768px) {
      font-size: 2rem;
    }
  }

  .actions {
    display: flex;
    gap: 1rem;
    align-items: center;

    @media (max-width: 768px) {
      flex-direction: column;
      width: 100%;
    }
  }
`;

const SearchAndFilter = styled.div`
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;

  .search-row {
    display: flex;
    gap: 1rem;
    align-items: center;

    @media (max-width: 768px) {
      flex-direction: column;
      align-items: stretch;
    }
  }

  .search-input {
    position: relative;
    flex: 1;

    input {
      width: 100%;
      padding: 0.75rem 1rem 0.75rem 2.5rem;
      border: 2px solid #e5e7eb;
      border-radius: 8px;
      font-size: 0.875rem;

      &:focus {
        outline: none;
        border-color: #3b82f6;
      }
    }

    .search-icon {
      position: absolute;
      left: 0.75rem;
      top: 50%;
      transform: translateY(-50%);
      color: #9ca3af;
    }
  }

  .filter-select {
    select {
      padding: 0.75rem;
      border: 2px solid #e5e7eb;
      border-radius: 8px;
      background: white;
      color: #374151;
      font-size: 0.875rem;
      min-width: 120px;

      &:focus {
        outline: none;
        border-color: #3b82f6;
      }
    }
  }
`;

const HistoryList = styled.div`
  .scan-item {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    border: 1px solid #e2e8f0;
    transition: all 0.2s ease;

    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    .scan-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 1rem;

      @media (max-width: 768px) {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
      }
    }

    .scan-title {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex: 1;

      .repo-name {
        font-weight: 600;
        color: #1e293b;
        font-size: 1.1rem;
        word-break: break-all;
      }

      .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;

        &.success {
          background: #dcfce7;
          color: #166534;
        }

        &.error {
          background: #fef2f2;
          color: #dc2626;
        }
      }
    }

    .scan-time {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      color: #64748b;
      font-size: 0.875rem;
    }

    .scan-details {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .detail-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: #64748b;
      font-size: 0.875rem;

      .icon {
        color: #94a3b8;
      }

      .value {
        font-weight: 500;
        color: #374151;
      }
    }

    .scan-summary {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 1rem;
      padding: 1rem;
      background: #f8fafc;
      border-radius: 8px;

      @media (max-width: 768px) {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
      }

      .summary-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.875rem;

        .count {
          font-weight: 600;
          color: #1e293b;
        }
      }
    }

    .scan-actions {
      display: flex;
      gap: 0.5rem;
      justify-content: flex-end;

      @media (max-width: 768px) {
        justify-content: stretch;
      }

      .btn {
        padding: 0.5rem 1rem;
        border-radius: 6px;
        text-decoration: none;
        font-size: 0.875rem;
        font-weight: 500;
        transition: all 0.2s ease;

        &.primary {
          background: #3b82f6;
          color: white;

          &:hover {
            background: #2563eb;
          }
        }

        &.secondary {
          background: #f1f5f9;
          color: #64748b;
          border: 1px solid #e2e8f0;

          &:hover {
            background: #e2e8f0;
          }
        }
      }
    }
  }

  .empty-state {
    text-align: center;
    padding: 3rem;
    color: #64748b;

    .icon {
      font-size: 3rem;
      margin-bottom: 1rem;
      color: #cbd5e1;
    }

    h3 {
      font-size: 1.25rem;
      font-weight: 600;
      color: #1e293b;
      margin-bottom: 0.5rem;
    }

    p {
      margin-bottom: 1.5rem;
    }

    .cta-button {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.75rem 1.5rem;
      background: #3b82f6;
      color: white;
      text-decoration: none;
      border-radius: 8px;
      font-weight: 500;
      transition: all 0.2s ease;

      &:hover {
        background: #2563eb;
        transform: translateY(-1px);
      }
    }
  }
`;

const RefreshButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: white;
  color: #64748b;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;

  &:hover {
    background: #f8fafc;
    color: #374151;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .icon {
    animation: ${props => props.loading ? 'spin 1s linear infinite' : 'none'};
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
`;

const ScanHistory = () => {
  const { scanResults, setScanHistory, scanHistory } = useAppContext();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadScanHistory();
  }, []);

  const loadScanHistory = async () => {
    setIsLoading(true);
    try {
      const response = await apiService.getScanHistory(50);
      setScanHistory(response.data.history || []);
    } catch (error) {
      console.error('Failed to load scan history:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Combine local scan results with history
  const allScans = [...scanResults, ...scanHistory];

  // Filter scans based on search term and status
  const filteredScans = allScans.filter(scan => {
    const matchesSearch = scan.repo?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         scan.message?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || scan.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Sort by most recent first (assuming we add timestamp in the future)
  const sortedScans = filteredScans.sort((a, b) => {
    // For now, just reverse order (newest first)
    return filteredScans.indexOf(a) - filteredScans.indexOf(b);
  });

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <FiCheckCircle />;
      case 'error':
        return <FiXCircle />;
      default:
        return <FiAlertTriangle />;
    }
  };

  const formatScanTime = (scan) => {
    // Since we don't have timestamps yet, show duration or placeholder
    if (scan.scan_duration) {
      return `Completed in ${scan.scan_duration}s`;
    }
    return 'Recently completed';
  };

  return (
    <HistoryContainer>
      <Header>
        <h1>
          <FiClock />
          Scan History
        </h1>
        <div className="actions">
          <RefreshButton 
            onClick={loadScanHistory} 
            disabled={isLoading}
            loading={isLoading}
          >
            <FiRefreshCw className="icon" />
            Refresh
          </RefreshButton>
        </div>
      </Header>

      <SearchAndFilter>
        <div className="search-row">
          <div className="search-input">
            <FiSearch className="search-icon" />
            <input
              type="text"
              placeholder="Search repositories..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="filter-select">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">All Status</option>
              <option value="success">Success</option>
              <option value="error">Error</option>
            </select>
          </div>
        </div>
      </SearchAndFilter>

      <HistoryList>
        {sortedScans.length === 0 ? (
          <div className="scan-item">
            <div className="empty-state">
              <FiClock className="icon" />
              <h3>No Scan History</h3>
              <p>You haven't performed any repository scans yet.</p>
              <Link to="/scan" className="cta-button">
                <FiSearch />
                Start Your First Scan
              </Link>
            </div>
          </div>
        ) : (
          sortedScans.map((scan, index) => (
            <div key={index} className="scan-item">
              <div className="scan-header">
                <div className="scan-title">
                  <div className="repo-name">{scan.repo || 'Unknown Repository'}</div>
                  <div className={`status-badge ${scan.status}`}>
                    {getStatusIcon(scan.status)}
                    {scan.status}
                  </div>
                </div>
                <div className="scan-time">
                  <FiCalendar />
                  {formatScanTime(scan)}
                </div>
              </div>

              <div className="scan-details">
                {scan.repo_info?.active_branch && (
                  <div className="detail-item">
                    <FiGitBranch className="icon" />
                    Branch: <span className="value">{scan.repo_info.active_branch}</span>
                  </div>
                )}
                {scan.total_files && (
                  <div className="detail-item">
                    <FiClock className="icon" />
                    Files: <span className="value">{scan.total_files}</span>
                  </div>
                )}
                {scan.repo_info?.commit_count && (
                  <div className="detail-item">
                    <FiGitBranch className="icon" />
                    Commits: <span className="value">{scan.repo_info.commit_count}</span>
                  </div>
                )}
              </div>

              {scan.status === 'success' && (
                <div className="scan-summary">
                  <div className="summary-item">
                    <FiCheckCircle style={{ color: '#22c55e' }} />
                    <span className="count">{scan.issues_count || 0}</span>
                    Issues Found
                  </div>
                  <div className="summary-item">
                    <FiAlertTriangle style={{ color: '#f59e0b' }} />
                    <span className="count">{scan.total_files || 0}</span>
                    Files Scanned
                  </div>
                  {scan.compliance_issues && scan.compliance_issues.length > 0 && (
                    <div className="summary-item">
                      <FiAlertTriangle style={{ color: '#dc2626' }} />
                      <span className="count">
                        {scan.compliance_issues.filter(issue => issue.severity === 'high').length}
                      </span>
                      High Severity
                    </div>
                  )}
                </div>
              )}

              {scan.message && (
                <div style={{ 
                  fontSize: '0.875rem', 
                  color: scan.status === 'error' ? '#dc2626' : '#64748b',
                  marginBottom: '1rem',
                  fontStyle: 'italic'
                }}>
                  {scan.message}
                </div>
              )}

              {scan.compliance_issues && scan.compliance_issues.length > 0 && scan.status === 'success' && (
                <div style={{ 
                  background: '#fef2f2', 
                  border: '1px solid #fecaca', 
                  borderRadius: '8px', 
                  padding: '1rem', 
                  marginBottom: '1rem' 
                }}>
                  <div style={{ 
                    fontSize: '0.875rem', 
                    fontWeight: '600', 
                    color: '#dc2626', 
                    marginBottom: '0.5rem' 
                  }}>
                    Critical Issues Found:
                  </div>
                  {scan.compliance_issues
                    .filter(issue => issue.severity === 'high' && !issue.error)
                    .slice(0, 2)
                    .map((issue, issueIndex) => (
                      <div key={issueIndex} style={{ 
                        fontSize: '0.75rem', 
                        color: '#991b1b', 
                        marginBottom: '0.25rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                      }}>
                        <FiAlertTriangle />
                        <span style={{ fontFamily: 'monospace' }}>{issue.file}</span>
                        <span>•</span>
                        <span>{issue.issue}</span>
                        {issue.line && <span>(Line {issue.line})</span>}
                      </div>
                    ))}
                  {scan.compliance_issues.filter(issue => issue.severity === 'high' && !issue.error).length > 2 && (
                    <div style={{ fontSize: '0.75rem', color: '#991b1b', fontStyle: 'italic' }}>
                      +{scan.compliance_issues.filter(issue => issue.severity === 'high' && !issue.error).length - 2} more high severity issues...
                    </div>
                  )}
                </div>
              )}

              <div className="scan-actions">
                <Link 
                  to={`/results/${index}`} 
                  className="btn primary"
                >
                  View Results
                </Link>
                <button 
                  className="btn secondary"
                  onClick={() => {
                    const dataStr = JSON.stringify(scan, null, 2);
                    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
                    
                    const exportFileDefaultName = `scan-${index}-${Date.now()}.json`;
                    
                    const linkElement = document.createElement('a');
                    linkElement.setAttribute('href', dataUri);
                    linkElement.setAttribute('download', exportFileDefaultName);
                    linkElement.click();
                  }}
                >
                  Export
                </button>
              </div>
            </div>
          ))
        )}
      </HistoryList>
    </HistoryContainer>
  );
};

export default ScanHistory;
