import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import { 
  FiShield, 
  FiSearch, 
  FiList, 
  FiActivity, 
  FiCheckCircle, 
  FiAlertTriangle,
  FiArrowRight,
  FiGitBranch,
  FiClock
} from 'react-icons/fi';
import { useAppContext } from '../context/AppContext';
import { apiService } from '../services/api';
import { toast } from 'react-toastify';

const DashboardContainer = styled.div`
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

    @media (max-width: 768px) {
      font-size: 2rem;
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
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
`;

const StatCard = styled.div`
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .stat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
  }

  .stat-icon {
    padding: 8px;
    border-radius: 8px;
    background: ${props => props.bgColor || '#f1f5f9'};
    color: ${props => props.iconColor || '#64748b'};
    font-size: 1.2rem;
  }

  .stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 0.25rem;
  }

  .stat-label {
    color: #64748b;
    font-size: 0.875rem;
    font-weight: 500;
  }
`;

const QuickActionsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
`;

const ActionCard = styled(Link)`
  background: white;
  border-radius: 12px;
  padding: 2rem;
  text-decoration: none;
  color: inherit;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
  display: block;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    color: inherit;
  }

  .action-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .action-icon {
    padding: 12px;
    border-radius: 12px;
    background: ${props => props.bgColor || '#f1f5f9'};
    color: ${props => props.iconColor || '#64748b'};
    font-size: 1.5rem;
  }

  .action-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 0.5rem;
  }

  .action-description {
    color: #64748b;
    line-height: 1.5;
    margin-bottom: 1rem;
  }

  .action-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: #3b82f6;
    font-weight: 500;
  }
`;

const RecentActivitySection = styled.div`
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;

  h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .no-activity {
    text-align: center;
    color: #64748b;
    padding: 2rem;
  }
`;

const ActivityItem = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 0;
  border-bottom: 1px solid #f1f5f9;

  &:last-child {
    border-bottom: none;
  }

  .activity-icon {
    padding: 8px;
    border-radius: 8px;
    background: #f1f5f9;
    color: #64748b;
  }

  .activity-content {
    flex: 1;

    .activity-title {
      font-weight: 500;
      color: #1e293b;
      margin-bottom: 0.25rem;
    }

    .activity-time {
      font-size: 0.875rem;
      color: #64748b;
    }
  }

  .activity-status {
    padding: 4px 8px;
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
`;

const Dashboard = () => {
  const { scanResults, apiStatus, setApiStatus } = useAppContext();
  const [stats, setStats] = useState({
    totalScans: 0,
    successfulScans: 0,
    issuesFound: 0,
    recentScans: []
  });

  useEffect(() => {
    checkApiStatus();
    loadDashboardData();
  }, []);

  const checkApiStatus = async () => {
    try {
      const response = await apiService.healthCheck();
      setApiStatus({ 
        status: 'online', 
        data: response.data,
        ai_enabled: response.data.ai_enabled || false
      });
    } catch (error) {
      setApiStatus({ 
        status: 'offline', 
        error: error.message,
        ai_enabled: false
      });
      toast.error('Backend API is not available');
    }
  };

  const loadDashboardData = () => {
    // Calculate stats from scan results
    const successfulScans = scanResults.filter(scan => scan.status === 'success').length;
    const totalIssues = scanResults.reduce((total, scan) => 
      total + (scan.issues_count || 0), 0
    );

    setStats({
      totalScans: scanResults.length,
      successfulScans,
      issuesFound: totalIssues,
      recentScans: scanResults.slice(0, 5)
    });
  };

  useEffect(() => {
    loadDashboardData();
  }, [scanResults]);

  const quickActions = [
    {
      title: 'Scan Repository',
      description: 'Analyze a Git repository for compliance issues and security vulnerabilities.',
      path: '/scan',
      icon: FiSearch,
      bgColor: '#eff6ff',
      iconColor: '#3b82f6'
    },
    {
      title: 'View Scan History',
      description: 'Review previous repository scans and their compliance results.',
      path: '/history',
      icon: FiList,
      bgColor: '#f0fdf4',
      iconColor: '#22c55e'
    },
    {
      title: 'Compliance Rules',
      description: 'View and manage the compliance rules and security checks.',
      path: '/rules',
      icon: FiShield,
      bgColor: '#fef3c7',
      iconColor: '#f59e0b'
    }
  ];

  return (
    <DashboardContainer>
      <Header>
        <h1>Compliance Auditor Dashboard</h1>
        <p>
          Monitor your Git repositories and CI/CD pipelines for compliance issues, security vulnerabilities, 
          and best practice violations with AI automated scanning and detailed reporting.
        </p>
      </Header>

      <StatsGrid>
        <StatCard bgColor="#eff6ff" iconColor="#3b82f6">
          <div className="stat-header">
            <div className="stat-icon">
              <FiGitBranch />
            </div>
          </div>
          <div className="stat-value">{stats.totalScans}</div>
          <div className="stat-label">Total Scans</div>
        </StatCard>

        <StatCard bgColor="#f0fdf4" iconColor="#22c55e">
          <div className="stat-header">
            <div className="stat-icon">
              <FiCheckCircle />
            </div>
          </div>
          <div className="stat-value">{stats.successfulScans}</div>
          <div className="stat-label">Successful Scans</div>
        </StatCard>

        <StatCard bgColor="#fef3c7" iconColor="#f59e0b">
          <div className="stat-header">
            <div className="stat-icon">
              <FiAlertTriangle />
            </div>
          </div>
          <div className="stat-value">{stats.issuesFound}</div>
          <div className="stat-label">Issues Found</div>
        </StatCard>

        <StatCard bgColor="#f1f5f9" iconColor="#64748b">
          <div className="stat-header">
            <div className="stat-icon">
              <FiActivity />
            </div>
          </div>
          <div className="stat-value">
            {apiStatus?.status === 'online' ? 'Online' : 'Offline'}
          </div>
          <div className="stat-label">API Status</div>
        </StatCard>

        <StatCard bgColor={apiStatus?.ai_enabled ? "#f0f9ff" : "#fef2f2"} iconColor={apiStatus?.ai_enabled ? "#0ea5e9" : "#ef4444"}>
          <div className="stat-header">
            <div className="stat-icon">
              <FiShield />
            </div>
          </div>
          <div className="stat-value">
            {apiStatus?.ai_enabled ? 'Active' : 'Inactive'}
          </div>
          <div className="stat-label">AI Engine</div>
        </StatCard>
      </StatsGrid>

      <QuickActionsGrid>
        {quickActions.map((action, index) => (
          <ActionCard
            key={index}
            to={action.path}
            bgColor={action.bgColor}
            iconColor={action.iconColor}
          >
            <div className="action-header">
              <div className="action-icon">
                <action.icon />
              </div>
            </div>
            <div className="action-title">{action.title}</div>
            <div className="action-description">{action.description}</div>
            <div className="action-footer">
              <span>Get Started</span>
              <FiArrowRight />
            </div>
          </ActionCard>
        ))}
      </QuickActionsGrid>

      <RecentActivitySection>
        <h3>
          <FiClock />
          Recent Activity
        </h3>
        {stats.recentScans.length === 0 ? (
          <div className="no-activity">
            <p>No recent scan activity. Start by scanning your first repository!</p>
          </div>
        ) : (
          <div>
            {stats.recentScans.map((scan, index) => (
              <ActivityItem key={index}>
                <div className="activity-icon">
                  <FiGitBranch />
                </div>
                <div className="activity-content">
                  <div className="activity-title">
                    Scanned {scan.repo || 'Unknown repository'}
                  </div>
                  <div className="activity-time">
                    {scan.scan_duration ? `Completed in ${scan.scan_duration}s` : 'Recently completed'}
                  </div>
                </div>
                <div className={`activity-status ${scan.status}`}>
                  {scan.status}
                </div>
              </ActivityItem>
            ))}
          </div>
        )}
      </RecentActivitySection>
    </DashboardContainer>
  );
};

export default Dashboard;
