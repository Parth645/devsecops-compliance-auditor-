"""
Database models for the multi-tenant compliance auditor system.

Schema Design:
1. Organizations (root of multi-tenancy)
2. Projects (scoped to organizations)  
3. Scans (belongs to projects and organizations)
4. Violations (belongs to scans and organizations)
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, Text, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

# Function to generate UUID objects
def generate_uuid():
    return uuid.uuid4()


class Organization(Base):
    """
    Organizations table - root of multi-tenancy.
    Every business that signs up gets an organization row.
    """
    __tablename__ = "organizations"
    
    # Core fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, index=True)  # "Acme Corp"
    
    # Authentication  
    api_key_hash = Column(String(255), nullable=False, unique=True, index=True)  # Hashed API key
    
    # Plan and limits
    tier = Column(String(50), nullable=False, default="free")  # free/startup/team/enterprise
    limits = Column(JSON, nullable=False, default=lambda: {
        "max_projects": 3,
        "max_scans_per_month": 100,
        "max_violations_per_scan": 1000
    })
    
    # Status and settings
    is_active = Column(Boolean, default=True, nullable=False)
    settings = Column(JSON, default=lambda: {})  # Additional org-specific settings
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    projects = relationship("Project", back_populates="organization", cascade="all, delete-orphan")
    scans = relationship("Scan", back_populates="organization")
    violations = relationship("Violation", back_populates="organization")

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}', tier='{self.tier}')>"


class Project(Base):
    """
    Projects table - repositories/projects scoped to organizations.
    Each project belongs to exactly one organization.
    """
    __tablename__ = "projects"
    
    # Core fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Project details
    name = Column(String(255), nullable=False, index=True)  # Short name for project
    repo_url = Column(Text, nullable=False)
    repo_provider = Column(String(50), nullable=False)  # github/gitlab/bitbucket/azure/custom
    default_branch = Column(String(255), default="main")
    
    # Status and metadata
    is_active = Column(Boolean, default=True, nullable=False)
    last_scan_at = Column(DateTime(timezone=True))
    scan_count = Column(Integer, default=0, nullable=False)
    
    # Configuration
    settings = Column(JSON, default=lambda: {
        "scan_triggers": ["push", "pull_request"],
        "notification_settings": {}
    })
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="projects")
    scans = relationship("Scan", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', org_id={self.org_id})>"


class Scan(Base):
    """
    Scans table - represents one scan run for a project.
    Belongs to a project and organization (duplicated org_id for performance).
    """
    __tablename__ = "scans"
    
    # Core fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    trigger_id = Column(UUID(as_uuid=True), ForeignKey("scan_triggers.id", ondelete="SET NULL"), nullable=True)
    
    # Git details
    commit_sha = Column(String(255))
    branch = Column(String(255))
    repo_url = Column(Text)  # Stored for scans without a project
    
    # Pipeline context
    pipeline = Column(String(100))  # github_actions/gitlab_ci/jenkins/manual/api
    trigger_type = Column(String(50))  # push/pull_request/scheduled/manual
    
    # Scan status and results
    status = Column(String(50), nullable=False, default="pending")  # pending/in_progress/completed/failed
    risk_score = Column(Float)  # 0-100 overall risk score
    
    # Violation counts for quick access
    violations_count = Column(Integer, default=0, nullable=False)  # Total violations shorthand
    total_violations = Column(Integer, default=0, nullable=False)
    critical_violations = Column(Integer, default=0, nullable=False)
    high_violations = Column(Integer, default=0, nullable=False)
    medium_violations = Column(Integer, default=0, nullable=False)
    low_violations = Column(Integer, default=0, nullable=False)
    
    # Categories
    security_violations = Column(Integer, default=0, nullable=False)
    privacy_violations = Column(Integer, default=0, nullable=False)
    compliance_violations = Column(Integer, default=0, nullable=False)
    quality_violations = Column(Integer, default=0, nullable=False)
    
    # Execution details
    scan_duration_seconds = Column(Float)
    files_scanned = Column(Integer)
    lines_scanned = Column(Integer)
    started_at = Column(DateTime(timezone=True))
    
    # Error information (if scan failed)
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # Metadata
    scan_context = Column(JSON, default=lambda: {})  # Additional scan-specific data
    scan_metadata = Column(JSON, default=lambda: {})  # Additional scan-specific data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    organization = relationship("Organization", back_populates="scans")
    project = relationship("Project", back_populates="scans")
    violations = relationship("Violation", back_populates="scan", cascade="all, delete-orphan")
    trigger = relationship("ScanTrigger", back_populates="scan", foreign_keys=[trigger_id])
    
    def __repr__(self):
        return f"<Scan(id={self.id}, status='{self.status}', risk_score={self.risk_score})>"


class Violation(Base):
    """
    Violations/Findings table - individual compliance violations found in scans.
    Each violation belongs to a scan and organization (duplicated org_id for performance).
    """
    __tablename__ = "violations"
    
    # Core fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Rule identification
    rule_id = Column(String(100), nullable=False, index=True)  # SEC-001, PRI-002, etc.
    rule_name = Column(String(255))
    rule_description = Column(Text)
    
    # Classification
    severity = Column(String(20), nullable=False, index=True)  # critical/high/medium/low
    category = Column(String(50), nullable=False, index=True)  # security/privacy/compliance/quality
    
    # Location details
    file_path = Column(Text, nullable=False)
    line_number = Column(Integer)
    line_end = Column(Integer)  # For multi-line violations
    column_start = Column(Integer)
    column_end = Column(Integer)
    
    # Violation details
    message = Column(Text, nullable=False)
    code_snippet = Column(Text)  # The problematic code
    context = Column(Text)  # Additional context around the violation
    
    # AI-generated insights
    ai_confidence = Column(Float)  # 0-1 confidence score from AI detection
    ai_explanation = Column(Text)  # AI explanation of why this is a violation
    ai_fix_suggestion = Column(Text)  # AI-suggested fix
    
    # Status and resolution
    status = Column(String(50), default="open")  # open/acknowledged/fixed/false_positive/suppressed
    assignee = Column(String(255))  # Who is responsible for fixing
    resolution_notes = Column(Text)
    
    # External references
    cve_ids = Column(JSON)  # Related CVE numbers
    cwe_ids = Column(JSON)  # Related CWE numbers
    compliance_frameworks = Column(JSON)  # GDPR, SOX, PCI-DSS, etc.
    
    # Risk assessment
    exploitability_score = Column(Float)  # How easily exploitable
    business_impact_score = Column(Float)  # Business impact if exploited
    
    # Metadata
    violation_metadata = Column(JSON, default=lambda: {})  # Additional violation-specific data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True))
    
    # Relationships
    organization = relationship("Organization", back_populates="violations")
    scan = relationship("Scan", back_populates="violations")
    
    def __repr__(self):
        return f"<Violation(id={self.id}, rule_id='{self.rule_id}', severity='{self.severity}')>"


class WebhookConfig(Base):
    """
    WebhookConfig table - stores webhook configuration for CI/CD platforms.
    Each webhook config belongs to an organization and connects to a specific repo.
    """
    __tablename__ = "webhook_configs"
    
    # Core fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Webhook details
    provider = Column(String(50), nullable=False, index=True)  # github/gitlab/bitbucket
    webhook_url = Column(Text, nullable=False)  # URL where webhook is registered
    webhook_secret = Column(String(255), nullable=False)  # Secret for HMAC verification
    
    # Configuration
    events = Column(JSON, default=lambda: ["push", "pull_request"])  # Events to listen for
    branches = Column(JSON, default=lambda: ["main", "master", "develop"])  # Branches to scan
    active = Column(Boolean, default=True, nullable=False)
    
    # Status
    last_triggered_at = Column(DateTime(timezone=True))
    last_trigger_status = Column(String(50))  # success/failed
    
    # Metadata
    webhook_config_data = Column(JSON, default=lambda: {})  # Additional webhook configuration
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", foreign_keys=[org_id])
    webhook_events = relationship("WebhookEvent", back_populates="webhook_config", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<WebhookConfig(id={self.id}, provider='{self.provider}', org_id={self.org_id})>"


class WebhookEvent(Base):
    """
    WebhookEvent table - stores individual webhook events received from CI/CD platforms.
    Used for debugging, audit trails, and reprocessing failed events.
    """
    __tablename__ = "webhook_events"
    
    # Core fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    webhook_config_id = Column(UUID(as_uuid=True), ForeignKey("webhook_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # push, pull_request, merge_request, etc.
    repo_url = Column(Text, nullable=False)
    branch = Column(String(255), nullable=False)
    commit_sha = Column(String(255), nullable=False, index=True)
    
    # Processing status
    status = Column(String(50), default="received")  # received/processing/processed/failed
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id", ondelete="SET NULL"), nullable=True)
    
    # Event payload
    payload = Column(JSON, nullable=False)  # Full webhook payload
    
    # Error tracking
    error_message = Column(Text)
    error_details = Column(JSON)
    retry_count = Column(Integer, default=0)
    
    # Metadata
    webhook_context = Column(JSON, default=lambda: {})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # Relationships
    webhook_config = relationship("WebhookConfig", back_populates="webhook_events")
    organization = relationship("Organization", foreign_keys=[org_id])
    
    def __repr__(self):
        return f"<WebhookEvent(id={self.id}, event_type='{self.event_type}', status='{self.status}')>"


class ScanTrigger(Base):
    """
    ScanTrigger table - tracks what triggered a scan (webhook, scheduled, manual, etc.).
    Links scans to their origin events for audit and troubleshooting.
    """
    __tablename__ = "scan_triggers"
    
    # Core fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Trigger type
    trigger_type = Column(String(50), nullable=False)  # webhook/scheduled/manual/api/ci_pipeline
    trigger_source = Column(String(50))  # github/gitlab/bitbucket/jenkins/github_actions
    
    # Source reference
    webhook_event_id = Column(UUID(as_uuid=True), ForeignKey("webhook_events.id", ondelete="SET NULL"), nullable=True)
    ci_pipeline_id = Column(String(255))  # Job ID or pipeline ID for CI systems
    
    # Additional metadata
    trigger_metadata = Column(JSON, default=lambda: {})  # Trigger-specific data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    scan = relationship("Scan", back_populates="trigger", foreign_keys=[scan_id])
    webhook_event = relationship("WebhookEvent", foreign_keys=[webhook_event_id])
    
    def __repr__(self):
        return f"<ScanTrigger(id={self.id}, trigger_type='{self.trigger_type}', scan_id={self.scan_id})>"


class ScanProfile(Base):
    """
    ScanProfile table - defines scan configurations for different environments/projects.
    Allows organizations to have different scanning rules per environment (dev/staging/prod).
    """
    __tablename__ = "scan_profiles"
    
    # Core fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Profile details
    name = Column(String(255), nullable=False)  # e.g., "Production", "Development"
    environment = Column(String(50), nullable=False)  # dev/staging/production
    description = Column(Text)
    
    # Scanning behavior
    scan_on_push = Column(Boolean, default=True)  # Auto-scan on push events
    scan_on_pr = Column(Boolean, default=True)  # Auto-scan on pull requests
    
    # Enforcement
    auto_approve = Column(Boolean, default=False)  # Auto-approve low-severity violations
    enforcement_level = Column(String(50), default="warning")  # warning/block
    
    # Configuration
    policies = Column(JSON, default=lambda: {})  # Which compliance frameworks to check
    notifications = Column(JSON, default=lambda: {})  # Notification settings
    max_violations = Column(Integer)  # Max violations allowed before blocking
    min_risk_score = Column(Float)  # Minimum acceptable risk score
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    profile_metadata = Column(JSON, default=lambda: {})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", foreign_keys=[org_id])
    
    def __repr__(self):
        return f"<ScanProfile(id={self.id}, name='{self.name}', environment='{self.environment}')>"

"""
Key Indexes for Performance:

1. Organizations:
   - api_key_hash (unique index for authentication)
   - name (for searching organizations)

2. Projects:
   - (org_id) (for tenant isolation)
   - (org_id, name) (for finding projects within org)

3. Scans:
   - (org_id) (for tenant isolation)
   - (project_id) (for project scan history)
   - (org_id, created_at) (for org scan timeline)
   - (status) (for finding active scans)

4. Violations:
   - (org_id) (for tenant isolation)
   - (scan_id) (for scan violations)
   - (org_id, severity) (for org risk reporting)
   - (org_id, category) (for category filtering)
   - (rule_id) (for rule-based queries)
   - (file_path) (for file-based queries)
"""