import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { 
  FiSearch, 
  FiGithub, 
  FiGitlab, 
  FiBox,
  FiSettings,
  FiPlay,
  FiLoader
} from 'react-icons/fi';
import { useAppContext } from '../context/AppContext';
import { apiService } from '../services/api';
import { toast } from 'react-toastify';

const ScannerContainer = styled.div`
  max-width: 800px;
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
      gap: 1rem;
    }
  }

  p {
    font-size: 1.1rem;
    color: #64748b;
    max-width: 600px;
    margin: 0 auto;
  }
`;

const ScanForm = styled.div`
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
  margin-bottom: 2rem;
`;

const FormGroup = styled.div`
  margin-bottom: 1.5rem;

  label {
    display: block;
    font-weight: 600;
    color: #374151;
    margin-bottom: 0.5rem;
    font-size: 1rem;
  }

  .input-container {
    position: relative;
    display: flex;
    align-items: center;
  }

  input {
    width: 100%;
    padding: 1rem 3rem 1rem 1rem;
    border: 2px solid #e5e7eb;
    border-radius: 12px;
    font-size: 1rem;
    transition: all 0.2s ease;
    background: #fafafa;

    &:focus {
      outline: none;
      border-color: #3b82f6;
      background: white;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }

    &::placeholder {
      color: #9ca3af;
    }
  }

  .input-icon {
    position: absolute;
    right: 1rem;
    color: #9ca3af;
    font-size: 1.2rem;
  }
`;

const GitProviders = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;

  @media (max-width: 768px) {
    flex-direction: column;
  }
`;

const ProviderButton = styled.button`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 1rem;
  border: 2px solid ${props => props.active ? '#3b82f6' : '#e5e7eb'};
  border-radius: 12px;
  background: ${props => props.active ? '#eff6ff' : 'white'};
  color: ${props => props.active ? '#3b82f6' : '#64748b'};
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;

  &:hover {
    border-color: #3b82f6;
    background: #eff6ff;
    color: #3b82f6;
  }

  .icon {
    font-size: 1.2rem;
  }
`;

const AdvancedOptions = styled.div`
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 1.5rem;
`;

const OptionsHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background: #f8fafc;
  border-bottom: 1px solid #e5e7eb;
  cursor: pointer;
  user-select: none;

  .icon {
    color: #64748b;
  }

  .title {
    font-weight: 500;
    color: #374151;
  }

  .toggle {
    margin-left: auto;
    transform: rotate(${props => props.expanded ? '180deg' : '0deg'});
    transition: transform 0.2s ease;
  }
`;

const OptionsContent = styled.div`
  padding: ${props => props.expanded ? '1.5rem' : '0'};
  max-height: ${props => props.expanded ? '300px' : '0'};
  overflow: hidden;
  transition: all 0.3s ease;
  background: white;
`;

const OptionsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
`;

const SelectGroup = styled.div`
  label {
    display: block;
    font-weight: 500;
    color: #374151;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
  }

  select {
    width: 100%;
    padding: 0.75rem;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    background: white;
    color: #374151;
    font-size: 0.875rem;
    cursor: pointer;

    &:focus {
      outline: none;
      border-color: #3b82f6;
    }
  }
`;

const ScanButton = styled.button`
  width: 100%;
  padding: 1rem 2rem;
  background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }

  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
    transform: none;
  }

  .icon {
    font-size: 1.2rem;
  }
`;

const ExampleUrls = styled.div`
  background: #f8fafc;
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid #e2e8f0;

  h4 {
    font-size: 1rem;
    font-weight: 600;
    color: #374151;
    margin-bottom: 1rem;
  }

  .examples {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .example {
    font-size: 0.875rem;
    color: #64748b;
    font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
    padding: 0.5rem;
    background: white;
    border-radius: 6px;
    border: 1px solid #e5e7eb;
    cursor: pointer;
    transition: all 0.2s ease;

    &:hover {
      background: #eff6ff;
      border-color: #3b82f6;
      color: #3b82f6;
    }
  }
`;

const RepositoryScanner = () => {
  const navigate = useNavigate();
  const { setLoading, addScanResult, isLoading } = useAppContext();
  
  const [repoUrl, setRepoUrl] = useState('');
  const [selectedProvider, setSelectedProvider] = useState('github');
  const [expandedOptions, setExpandedOptions] = useState(false);
  const [scanOptions, setScanOptions] = useState({
    branch: 'main',
    analysis_depth: 'basic',
    use_ai: true  // Enable AI analysis by default
  });
  const [apiInfo, setApiInfo] = useState(null);

  // Check API capabilities on component mount
  useEffect(() => {
    const checkApiCapabilities = async () => {
      try {
        const response = await apiService.getApiInfo();
        setApiInfo(response.data);
      } catch (error) {
        console.error('Failed to get API info:', error);
      }
    };
    checkApiCapabilities();
  }, []);

  const gitProviders = [
    { id: 'github', name: 'GitHub', icon: FiGithub },
    { id: 'gitlab', name: 'GitLab', icon: FiGitlab },
    { id: 'bitbucket', name: 'Bitbucket', icon: FiBox },
  ];

  const exampleUrls = [
    'https://github.com/username/repository.git',
    'https://gitlab.com/username/repository.git',
    'https://bitbucket.org/username/repository.git',
    'git@github.com:username/repository.git'
  ];

  const handleScan = async (e) => {
    e.preventDefault();
    
    if (!repoUrl.trim()) {
      toast.error('Please enter a repository URL');
      return;
    }

    setLoading(true);

    try {
      // Prepare scan data
      const scanData = {
        git_repo_url: repoUrl.trim(),
        branch: scanOptions.branch,
        analysis_depth: scanOptions.analysis_depth,
        use_ai: scanOptions.use_ai
      };

      let response;
      
      // Use AI scan if enabled and available
      if (scanOptions.use_ai && apiInfo?.ai_enabled) {
        toast.info('Starting AI-powered analysis...');
        response = await apiService.aiScanRepository(scanData);
      } else {
        // Fallback to detailed scan
        response = await apiService.scanRepositoryDetailed(scanData);
      }
      
      if (response.data.status === 'success') {
        addScanResult(response.data);
        const aiUsed = response.data.ai_enabled && scanOptions.use_ai;
        toast.success(`Repository scan completed successfully! ${aiUsed ? '(AI-powered)' : ''}`);
        navigate('/results');
      } else {
        toast.error(response.data.message || 'Scan failed');
      }
    } catch (error) {
      console.error('Scan error:', error);
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message || 
                          error.message || 
                          'Failed to scan repository';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const fillExampleUrl = (url) => {
    setRepoUrl(url);
  };

  return (
    <ScannerContainer>
      <Header>
        <h1>
          <FiSearch />
          Repository Scanner
        </h1>
        <p>
          Enter a Git repository URL to scan for compliance issues, security vulnerabilities, 
          and best practice violations. Supports GitHub, GitLab, and Bitbucket repositories.
        </p>
      </Header>

      <ScanForm>
        <form onSubmit={handleScan}>
          <FormGroup>
            <label>Git Repository URL</label>
            <div className="input-container">
              <input
                type="url"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/username/repository.git"
                required
                disabled={isLoading}
              />
              <FiGithub className="input-icon" />
            </div>
          </FormGroup>

          <GitProviders>
            {gitProviders.map((provider) => (
              <ProviderButton
                key={provider.id}
                type="button"
                active={selectedProvider === provider.id}
                onClick={() => setSelectedProvider(provider.id)}
                disabled={isLoading}
              >
                <provider.icon className="icon" />
                {provider.name}
              </ProviderButton>
            ))}
          </GitProviders>

          <AdvancedOptions>
            <OptionsHeader 
              expanded={expandedOptions}
              onClick={() => setExpandedOptions(!expandedOptions)}
            >
              <FiSettings className="icon" />
              <span className="title">Advanced Options</span>
              <span className="toggle">▼</span>
            </OptionsHeader>
            <OptionsContent expanded={expandedOptions}>
              <OptionsGrid>
                <SelectGroup>
                  <label>Branch</label>
                  <select
                    value={scanOptions.branch}
                    onChange={(e) => setScanOptions({
                      ...scanOptions,
                      branch: e.target.value
                    })}
                  >
                    <option value="main">main</option>
                    <option value="master">master</option>
                    <option value="develop">develop</option>
                    <option value="dev">dev</option>
                  </select>
                </SelectGroup>
                <SelectGroup>
                  <label>Analysis Depth</label>
                  <select
                    value={scanOptions.analysis_depth}
                    onChange={(e) => setScanOptions({
                      ...scanOptions,
                      analysis_depth: e.target.value
                    })}
                  >
                    <option value="basic">Basic</option>
                    <option value="detailed">Detailed</option>
                    <option value="full">Full</option>
                  </select>
                </SelectGroup>
                <SelectGroup>
                  <label>
                    AI Analysis {apiInfo?.ai_enabled ? '✓' : '✗'}
                  </label>
                  <select
                    value={scanOptions.use_ai.toString()}
                    onChange={(e) => setScanOptions({
                      ...scanOptions,
                      use_ai: e.target.value === 'true'
                    })}
                    disabled={!apiInfo?.ai_enabled}
                  >
                    <option value="true">Enabled</option>
                    <option value="false">Disabled</option>
                  </select>
                  {!apiInfo?.ai_enabled && (
                    <small style={{ color: '#ef4444', fontSize: '0.75rem', marginTop: '0.25rem', display: 'block' }}>
                      AI engine not available
                    </small>
                  )}
                </SelectGroup>
              </OptionsGrid>
            </OptionsContent>
          </AdvancedOptions>

          <ScanButton type="submit" disabled={isLoading}>
            {isLoading ? (
              <>
                <FiLoader className="icon" style={{ animation: 'spin 1s linear infinite' }} />
                Scanning Repository...
              </>
            ) : (
              <>
                <FiPlay className="icon" />
                Start Compliance Scan
              </>
            )}
          </ScanButton>
        </form>
      </ScanForm>

      <ExampleUrls>
        <h4>Example Repository URLs</h4>
        <div className="examples">
          {exampleUrls.map((url, index) => (
            <div
              key={index}
              className="example"
              onClick={() => fillExampleUrl(url)}
              title="Click to use this example"
            >
              {url}
            </div>
          ))}
        </div>
      </ExampleUrls>
    </ScannerContainer>
  );
};

export default RepositoryScanner;
