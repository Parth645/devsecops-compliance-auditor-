import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import { 
  FiShield, 
  FiAlertTriangle,
  FiLock,
  FiFileText,
  FiGitBranch,
  FiRefreshCw,
  FiInfo,
  FiCheckCircle,
  FiXCircle
} from 'react-icons/fi';
import { useAppContext } from '../context/AppContext';
import { apiService } from '../services/api';
import { toast } from 'react-toastify';

const RulesContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;

  @media (max-width: 768px) {
    padding: 1rem;
  }
`;

const Header = styled.div`
  text-align: center;
  margin-bottom: 3rem;

  h1 {
    font-size: 2.5rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;

    @media (max-width: 768px) {
      font-size: 2rem;
      flex-direction: column;
    }
  }

  p {
    font-size: 1.1rem;
    color: #64748b;
    max-width: 600px;
    margin: 0 auto;
  }
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
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

const RulesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 2rem;
  margin-bottom: 2rem;
`;

const RuleCard = styled.div`
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  }

  .rule-header {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .rule-icon {
    padding: 12px;
    border-radius: 12px;
    font-size: 1.5rem;
    background: ${props => props.bgColor || '#f1f5f9'};
    color: ${props => props.iconColor || '#64748b'};
    flex-shrink: 0;
  }

  .rule-content {
    flex: 1;
  }

  .rule-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 0.5rem;
  }

  .rule-id {
    font-size: 0.875rem;
    color: #64748b;
    font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
    background: #f8fafc;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    display: inline-block;
    margin-bottom: 1rem;
  }

  .rule-description {
    color: #64748b;
    line-height: 1.6;
    margin-bottom: 1.5rem;
  }

  .rule-details {
    .detail-section {
      margin-bottom: 1rem;

      .section-title {
        font-weight: 500;
        color: #374151;
        margin-bottom: 0.5rem;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }

      .section-content {
        font-size: 0.875rem;
        color: #64748b;
        line-height: 1.5;
      }

      .tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;

        .tag {
          padding: 0.25rem 0.5rem;
          background: #eff6ff;
          color: #2563eb;
          border-radius: 4px;
          font-size: 0.75rem;
          font-weight: 500;
        }
      }
    }
  }

  .rule-status {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem;
    background: #f8fafc;
    border-radius: 8px;
    margin-top: 1.5rem;

    .status-badge {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.875rem;
      font-weight: 500;

      &.active {
        color: #166534;
      }

      &.inactive {
        color: #64748b;
      }
    }

    .severity {
      padding: 0.25rem 0.75rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 500;
      text-transform: uppercase;

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
        color: #166534;
      }
    }
  }
`;

const LoadingState = styled.div`
  text-align: center;
  padding: 3rem;
  
  .spinner {
    border: 3px solid #f3f3f3;
    border-top: 3px solid #3b82f6;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const RefreshButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
  margin: 0 auto 2rem;

  &:hover {
    background: #2563eb;
    transform: translateY(-1px);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }

  .icon {
    animation: ${props => props.loading ? 'spin 1s linear infinite' : 'none'};
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;

const ComplianceRules = () => {
  const { complianceRules, setComplianceRules } = useAppContext();
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadComplianceRules();
  }, []);

  const loadComplianceRules = async () => {
    setIsLoading(true);
    try {
      const response = await apiService.getComplianceRules();
      setComplianceRules(response.data.rules || []);
    } catch (error) {
      console.error('Failed to load compliance rules:', error);
      toast.error('Failed to load compliance rules');
    } finally {
      setIsLoading(false);
    }
  };

  // Default rules if API doesn't provide them or is not available
  const defaultRules = [
    {
      id: 'hardcoded-secrets',
      name: 'Hardcoded Secrets Detection',
      description: 'Detects potential hardcoded passwords, API keys, and secrets in source code files.',
      severity: 'high',
      category: 'Security',
      fileTypes: ['.py', '.js', '.java', '.cpp', '.c', '.php', '.rb'],
      patterns: ['password', 'api_key', 'secret', 'token'],
      active: true
    },
    {
      id: 'license-compliance',
      name: 'License Compliance',
      description: 'Checks for proper license files and headers in the repository.',
      severity: 'medium',
      category: 'Legal',
      fileTypes: ['LICENSE', 'LICENSE.txt', 'LICENSE.md'],
      patterns: ['MIT', 'Apache', 'GPL', 'BSD'],
      active: true
    },
    {
      id: 'security-vulnerabilities',
      name: 'Security Vulnerabilities',
      description: 'Scans for known security vulnerabilities in dependencies and libraries.',
      severity: 'high',
      category: 'Security',
      fileTypes: ['package.json', 'requirements.txt', 'pom.xml'],
      patterns: ['vulnerable-lib', 'outdated-dependency'],
      active: true
    },
    {
      id: 'code-quality',
      name: 'Code Quality Standards',
      description: 'Validates code follows quality standards and best practices.',
      severity: 'low',
      category: 'Quality',
      fileTypes: ['.py', '.js', '.java', '.cpp'],
      patterns: ['todo', 'fixme', 'hack', 'deprecated'],
      active: true
    },
    {
      id: 'data-privacy',
      name: 'Data Privacy Compliance',
      description: 'Checks for potential privacy violations and sensitive data exposure.',
      severity: 'high',
      category: 'Privacy',
      fileTypes: ['.py', '.js', '.java', '.sql'],
      patterns: ['email', 'phone', 'ssn', 'credit-card'],
      active: true
    },
    {
      id: 'documentation',
      name: 'Documentation Requirements',
      description: 'Ensures proper documentation and README files are present.',
      severity: 'low',
      category: 'Documentation',
      fileTypes: ['README.md', 'CHANGELOG.md', 'CONTRIBUTING.md'],
      patterns: ['installation', 'usage', 'api'],
      active: true
    }
  ];

  const rules = complianceRules.length > 0 ? complianceRules : defaultRules;

  const getRuleIcon = (category) => {
    switch (category?.toLowerCase()) {
      case 'security':
        return FiLock;
      case 'legal':
        return FiFileText;
      case 'quality':
        return FiCheckCircle;
      case 'privacy':
        return FiShield;
      case 'documentation':
        return FiFileText;
      default:
        return FiInfo;
    }
  };

  const getRuleColors = (category) => {
    switch (category?.toLowerCase()) {
      case 'security':
        return { bgColor: '#fef2f2', iconColor: '#dc2626' };
      case 'legal':
        return { bgColor: '#fef3c7', iconColor: '#d97706' };
      case 'quality':
        return { bgColor: '#f0fdf4', iconColor: '#22c55e' };
      case 'privacy':
        return { bgColor: '#eff6ff', iconColor: '#3b82f6' };
      case 'documentation':
        return { bgColor: '#f3e8ff', iconColor: '#9333ea' };
      default:
        return { bgColor: '#f1f5f9', iconColor: '#64748b' };
    }
  };

  // Calculate stats
  const stats = {
    totalRules: rules.length,
    activeRules: rules.filter(rule => rule.active !== false).length,
    highSeverity: rules.filter(rule => rule.severity === 'high').length,
    categories: [...new Set(rules.map(rule => rule.category))].length
  };

  if (isLoading) {
    return (
      <RulesContainer>
        <LoadingState>
          <div className="spinner"></div>
          <p>Loading compliance rules...</p>
        </LoadingState>
      </RulesContainer>
    );
  }

  return (
    <RulesContainer>
      <Header>
        <h1>
          <FiShield />
          Compliance Rules
        </h1>
        <p>
          Review the compliance rules and security checks used to analyze your repositories. 
          These rules help identify potential security vulnerabilities, legal issues, and best practice violations.
        </p>
      </Header>

      <StatsGrid>
        <StatCard bgColor="#eff6ff" iconColor="#3b82f6">
          <div className="stat-icon">
            <FiShield />
          </div>
          <div className="stat-value">{stats.totalRules}</div>
          <div className="stat-label">Total Rules</div>
        </StatCard>

        <StatCard bgColor="#f0fdf4" iconColor="#22c55e">
          <div className="stat-icon">
            <FiCheckCircle />
          </div>
          <div className="stat-value">{stats.activeRules}</div>
          <div className="stat-label">Active Rules</div>
        </StatCard>

        <StatCard bgColor="#fef2f2" iconColor="#dc2626">
          <div className="stat-icon">
            <FiAlertTriangle />
          </div>
          <div className="stat-value">{stats.highSeverity}</div>
          <div className="stat-label">High Severity</div>
        </StatCard>

        <StatCard bgColor="#f8fafc" iconColor="#64748b">
          <div className="stat-icon">
            <FiGitBranch />
          </div>
          <div className="stat-value">{stats.categories}</div>
          <div className="stat-label">Categories</div>
        </StatCard>
      </StatsGrid>

      <RefreshButton 
        onClick={loadComplianceRules} 
        disabled={isLoading}
        loading={isLoading}
      >
        <FiRefreshCw className="icon" />
        Refresh Rules
      </RefreshButton>

      <RulesGrid>
        {rules.map((rule) => {
          const IconComponent = getRuleIcon(rule.category);
          const colors = getRuleColors(rule.category);
          
          return (
            <RuleCard 
              key={rule.id} 
              bgColor={colors.bgColor} 
              iconColor={colors.iconColor}
            >
              <div className="rule-header">
                <div className="rule-icon">
                  <IconComponent />
                </div>
                <div className="rule-content">
                  <div className="rule-title">{rule.name}</div>
                  <div className="rule-id">{rule.id}</div>
                </div>
              </div>

              <div className="rule-description">
                {rule.description}
              </div>

              <div className="rule-details">
                <div className="detail-section">
                  <div className="section-title">Category</div>
                  <div className="section-content">{rule.category || 'General'}</div>
                </div>

                {rule.fileTypes && (
                  <div className="detail-section">
                    <div className="section-title">File Types</div>
                    <div className="tags">
                      {rule.fileTypes.map((type, index) => (
                        <span key={index} className="tag">{type}</span>
                      ))}
                    </div>
                  </div>
                )}

                {rule.patterns && (
                  <div className="detail-section">
                    <div className="section-title">Detection Patterns</div>
                    <div className="tags">
                      {rule.patterns.map((pattern, index) => (
                        <span key={index} className="tag">{pattern}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="rule-status">
                <div className={`status-badge ${rule.active !== false ? 'active' : 'inactive'}`}>
                  {rule.active !== false ? <FiCheckCircle /> : <FiXCircle />}
                  {rule.active !== false ? 'Active' : 'Inactive'}
                </div>
                <div className={`severity ${rule.severity || 'medium'}`}>
                  {rule.severity || 'Medium'}
                </div>
              </div>
            </RuleCard>
          );
        })}
      </RulesGrid>
    </RulesContainer>
  );
};

export default ComplianceRules;
