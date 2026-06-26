import React from 'react';
import { useParams } from 'react-router-dom';
import styled from 'styled-components';
import { 
  FiCheckCircle, 
  FiAlertTriangle, 
  FiXCircle,
  FiFile,
  FiGitBranch,
  FiClock,
  FiUser,
  FiCalendar,
  FiDownload,
  FiShare2
} from 'react-icons/fi';
import { useAppContext } from '../context/AppContext';
import { format } from 'date-fns';

const ResultsContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;

  @media (max-width: 768px) {
    padding: 1rem;
  }
`;

const Header = styled.div`
  background: white;
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;

  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-weight: 600;
    margin-bottom: 1rem;
    font-size: 0.875rem;

    &.success {
      background: #dcfce7;
      color: #166534;
    }

    &.error {
      background: #fef2f2;
      color: #dc2626;
    }
  }

  h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 1rem;
    word-break: break-all;

    @media (max-width: 768px) {
      font-size: 1.5rem;
    }
  }

  .repo-info {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-top: 1.5rem;
  }

  .info-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #64748b;
    font-size: 0.875rem;

    .icon {
      color: #94a3b8;
    }
  }
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
`;

const StatCard = styled.div`
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
  text-align: center;

  .stat-icon {
    display: inline-flex;
    padding: 12px;
    border-radius: 12px;
    margin-bottom: 1rem;
    font-size: 1.5rem;
    background: ${props => props.bgColor || '#f1f5f9'};
    color: ${props => props.iconColor || '#64748b'};
  }

  .stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 0.5rem;
  }

  .stat-label {
    color: #64748b;
    font-size: 0.875rem;
    font-weight: 500;
  }
`;

const Section = styled.div`
  background: white;
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;

  h2 {
    font-size: 1.5rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
`;

const IssuesList = styled.div`
  .issue-item {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    margin-bottom: 1rem;

    &:last-child {
      margin-bottom: 0;
    }

    .issue-icon {
      padding: 8px;
      border-radius: 8px;
      margin-top: 2px;

      &.high {
        background: #fef2f2;
        color: #dc2626;
      }

      &.medium {
        background: #fef3c7;
        color: #d97706;
      }

      &.low {
        background: #f0fdf4;
        color: #059669;
      }
    }

    .issue-content {
      flex: 1;

      .issue-title {
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.25rem;
      }

      .issue-file {
        font-size: 0.875rem;
        color: #3b82f6;
        margin-bottom: 0.25rem;
        font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
      }

      .issue-description {
        font-size: 0.875rem;
        color: #64748b;
        line-height: 1.5;
        margin-bottom: 0.5rem;
      }

      .issue-severity {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
      }

      .issue-meta {
        display: flex;
        gap: 1rem;
        font-size: 0.75rem;
        color: #94a3b8;
        
        .meta-item {
          display: flex;
          align-items: center;
          gap: 0.25rem;
        }
      }
    }

    .issue-line {
      font-size: 0.75rem;
      color: #94a3b8;
      background: #f8fafc;
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
      font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
    }
  }

  .no-issues {
    text-align: center;
    padding: 3rem;
    color: #64748b;

    .icon {
      font-size: 3rem;
      margin-bottom: 1rem;
      color: #22c55e;
    }

    h3 {
      font-size: 1.25rem;
      font-weight: 600;
      color: #1e293b;
      margin-bottom: 0.5rem;
    }
  }
`;

const FilesList = styled.div`
  .files-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 0.5rem;
    max-height: 400px;
    overflow-y: auto;
    padding: 1rem;
    background: #f8fafc;
    border-radius: 8px;
  }

  .file-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem;
    background: white;
    border-radius: 6px;
    font-size: 0.875rem;
    color: #64748b;
    border: 1px solid #e5e7eb;

    .icon {
      color: #94a3b8;
      flex-shrink: 0;
    }

    .filename {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
    }
  }
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
  justify-content: center;

  @media (max-width: 768px) {
    flex-direction: column;
  }

  button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;

    &.primary {
      background: #3b82f6;
      color: white;
      border: none;

      &:hover {
        background: #2563eb;
      }
    }

    &.secondary {
      background: white;
      color: #64748b;
      border: 1px solid #e5e7eb;

      &:hover {
        background: #f8fafc;
      }
    }
  }
`;

const ScanResults = () => {
  const { scanId } = useParams();
  const { currentScan, scanResults } = useAppContext();

  // Get the scan result (either from current scan or find by ID in history)
  const scanResult = currentScan || scanResults.find(scan => scan.id === scanId) || scanResults[0];

  if (!scanResult) {
    return (
      <ResultsContainer>
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <h2>No scan results found</h2>
          <p>Please run a repository scan first.</p>
        </div>
      </ResultsContainer>
    );
  }

  const getIssueIcon = (issue) => {
    const severity = issue.severity?.toLowerCase() || 'medium';
    switch (severity) {
      case 'high':
        return <FiXCircle className="issue-icon high" />;
      case 'medium':
        return <FiAlertTriangle className="issue-icon medium" />;
      case 'low':
        return <FiAlertTriangle className="issue-icon low" />;
      default:
        return <FiAlertTriangle className="issue-icon medium" />;
    }
  };

  const getSeverity = (issue) => {
    return issue.severity?.charAt(0).toUpperCase() + issue.severity?.slice(1) || 'Medium';
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'high':
        return '#dc2626';
      case 'medium':
        return '#d97706';
      case 'low':
        return '#059669';
      default:
        return '#d97706';
    }
  };

  const exportResults = () => {
    const dataStr = JSON.stringify(scanResult, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `compliance-scan-${Date.now()}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const shareResults = () => {
    if (navigator.share) {
      navigator.share({
        title: 'Compliance Scan Results',
        text: `Compliance scan results for ${scanResult.repo}`,
        url: window.location.href
      });
    } else {
      navigator.clipboard.writeText(window.location.href);
      alert('Results URL copied to clipboard!');
    }
  };

  return (
    <ResultsContainer>
      <Header>
        <div className={`status-badge ${scanResult.status}`}>
          {scanResult.status === 'success' ? (
            <FiCheckCircle />
          ) : (
            <FiXCircle />
          )}
          {scanResult.status === 'success' ? 'Scan Completed' : 'Scan Failed'}
        </div>
        
        <h1>{scanResult.repo || 'Repository Scan Results'}</h1>
        
        {scanResult.message && (
          <p style={{ color: '#64748b', marginBottom: '1rem' }}>
            {scanResult.message}
          </p>
        )}

        {scanResult.repo_info && (
          <div className="repo-info">
            <div className="info-item">
              <FiGitBranch className="icon" />
              Branch: {scanResult.repo_info.active_branch}
            </div>
            <div className="info-item">
              <FiUser className="icon" />
              Author: {scanResult.repo_info.latest_commit?.author}
            </div>
            <div className="info-item">
              <FiCalendar className="icon" />
              Last Commit: {scanResult.repo_info.latest_commit?.date && 
                format(new Date(scanResult.repo_info.latest_commit.date), 'MMM dd, yyyy')}
            </div>
            <div className="info-item">
              <FiClock className="icon" />
              Scan Duration: {scanResult.scan_duration}s
            </div>
            {scanResult.ai_enabled !== undefined && (
              <div className="info-item">
                <FiCheckCircle className="icon" style={{ color: scanResult.ai_enabled ? '#22c55e' : '#ef4444' }} />
                AI Analysis: {scanResult.ai_enabled ? 'Enabled' : 'Disabled'}
              </div>
            )}
          </div>
        )}
      </Header>

      <StatsGrid>
        <StatCard bgColor="#f0fdf4" iconColor="#22c55e">
          <div className="stat-icon">
            <FiFile />
          </div>
          <div className="stat-value">{scanResult.total_files || 0}</div>
          <div className="stat-label">Total Files</div>
        </StatCard>

        <StatCard bgColor="#fef3c7" iconColor="#f59e0b">
          <div className="stat-icon">
            <FiAlertTriangle />
          </div>
          <div className="stat-value">{scanResult.issues_count || 0}</div>
          <div className="stat-label">Issues Found</div>
        </StatCard>

        <StatCard bgColor="#eff6ff" iconColor="#3b82f6">
          <div className="stat-icon">
            <FiGitBranch />
          </div>
          <div className="stat-value">{scanResult.repo_info?.commit_count || 0}</div>
          <div className="stat-label">Total Commits</div>
        </StatCard>

        {scanResult.ai_enabled && (
          <StatCard bgColor="#f0f9ff" iconColor="#0ea5e9">
            <div className="stat-icon">
              <FiCheckCircle />
            </div>
            <div className="stat-value">AI</div>
            <div className="stat-label">Analysis Used</div>
          </StatCard>
        )}
      </StatsGrid>

      {scanResult.analysis_summary && (
        <Section>
          <h2>
            <FiCheckCircle />
            AI Analysis Summary
          </h2>
          <div style={{ 
            background: 'white', 
            padding: '1.5rem', 
            borderRadius: '12px', 
            border: '1px solid #e2e8f0',
            marginBottom: '2rem'
          }}>
            <pre style={{ 
              whiteSpace: 'pre-wrap', 
              color: '#1e293b', 
              fontFamily: 'inherit',
              margin: 0
            }}>
              {JSON.stringify(scanResult.analysis_summary, null, 2)}
            </pre>
          </div>
        </Section>
      )}

      <Section>
        <h2>
          <FiAlertTriangle />
          Compliance Issues
        </h2>
        <IssuesList>
          {scanResult.compliance_issues && scanResult.compliance_issues.length > 0 ? (
            scanResult.compliance_issues
              .filter(issue => !issue.error) // Filter out error entries
              .map((issue, index) => (
                <div key={index} className="issue-item">
                  {getIssueIcon(issue)}
                  <div className="issue-content">
                    <div className="issue-title">{issue.issue}</div>
                    <div className="issue-file">📁 {issue.file}</div>
                    {issue.description && (
                      <div className="issue-description">
                        {issue.description}
                      </div>
                    )}
                    <div 
                      className="issue-severity" 
                      style={{ 
                        backgroundColor: getSeverityColor(issue.severity) + '20',
                        color: getSeverityColor(issue.severity),
                        border: `1px solid ${getSeverityColor(issue.severity)}40`
                      }}
                    >
                      {getSeverity(issue)} Severity
                    </div>
                    <div className="issue-meta">
                      {issue.line && (
                        <div className="meta-item">
                          <FiFile />
                          Line {issue.line}
                        </div>
                      )}
                      <div className="meta-item">
                        <FiAlertTriangle />
                        Security Issue
                      </div>
                      {issue.ai_confidence && (
                        <div className="meta-item">
                          <FiCheckCircle />
                          AI Confidence: {Math.round(issue.ai_confidence * 100)}%
                        </div>
                      )}
                    </div>
                  </div>
                  {issue.line && (
                    <div className="issue-line">
                      Line {issue.line}
                    </div>
                  )}
                </div>
              ))
          ) : (
            <div className="no-issues">
              <FiCheckCircle className="icon" />
              <h3>No Compliance Issues Found</h3>
              <p>Great! Your repository appears to follow security best practices.</p>
            </div>
          )}
        </IssuesList>
      </Section>

      {scanResult.files && scanResult.files.length > 0 && (
        <Section>
          <h2>
            <FiFile />
            Repository Files ({scanResult.total_files} total)
          </h2>
          <FilesList>
            <div className="files-grid">
              {scanResult.files.map((file, index) => (
                <div key={index} className="file-item">
                  <FiFile className="icon" />
                  <span className="filename">{file}</span>
                </div>
              ))}
            </div>
          </FilesList>
        </Section>
      )}

      <ActionButtons>
        <button className="primary" onClick={exportResults}>
          <FiDownload />
          Export Results
        </button>
        <button className="secondary" onClick={shareResults}>
          <FiShare2 />
          Share Results
        </button>
      </ActionButtons>
    </ResultsContainer>
  );
};

export default ScanResults;
