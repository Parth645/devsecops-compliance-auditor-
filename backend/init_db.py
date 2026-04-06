#!/usr/bin/env python3
"""
Database initialization and management script.

This script helps you:
1. Initialize the database with tables
2. Create sample data for testing
3. Run database migrations
"""

import sys
import os
import hashlib
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from sqlalchemy.orm import Session
from schema.database import engine, SessionLocal, create_tables, Base
from schema.schema import Organization, Project, Scan, Violation
import uuid
from datetime import datetime, timedelta


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def init_database():
    """Initialize database tables."""
    print("🏗️  Creating database tables...")
    try:
        create_tables()
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


def create_sample_data():
    """Create sample organizations and projects for testing."""
    print("📝 Creating sample data...")
    
    db = SessionLocal()
    try:
        # Check if sample data already exists
        existing_org = db.query(Organization).filter(Organization.name == "Acme Corp").first()
        if existing_org:
            print("⚠️  Sample data already exists, skipping...")
            return True
        
        # Create sample organization
        sample_org = Organization(
            name="Acme Corp",
            api_key_hash=hash_api_key("acme_test_api_key_123"),
            tier="startup",
            limits={
                "max_projects": 10,
                "max_scans_per_month": 1000,
                "max_violations_per_scan": 5000
            },
            settings={
                "notification_email": "admin@acmecorp.com",
                "slack_webhook": None
            }
        )
        db.add(sample_org)
        db.flush()  # Get the ID
        
        # Create sample project
        sample_project = Project(
            org_id=sample_org.id,
            name="acme-web-app",
            repo_url="https://github.com/acmecorp/web-app.git",
            repo_provider="github",
            default_branch="main",
            settings={
                "scan_triggers": ["push", "pull_request"],
                "notification_settings": {
                    "email_on_critical": True,
                    "slack_on_high": True
                }
            }
        )
        db.add(sample_project)
        db.flush()  # Get the ID
        
        # Create sample scan
        sample_scan = Scan(
            org_id=sample_org.id,
            project_id=sample_project.id,
            commit_sha="abc123def456",
            branch="main",
            pipeline="github_actions",
            trigger_type="push",
            status="completed",
            risk_score=75.5,
            total_violations=12,
            critical_violations=2,
            high_violations=3,
            medium_violations=5,
            low_violations=2,
            security_violations=8,
            privacy_violations=2,
            compliance_violations=1,
            quality_violations=1,
            scan_duration_seconds=45.2,
            files_scanned=156,
            lines_scanned=12843,
            completed_at=datetime.utcnow()
        )
        db.add(sample_scan)
        db.flush()  # Get the ID
        
        # Create sample violations
        sample_violations = [
            Violation(
                org_id=sample_org.id,
                scan_id=sample_scan.id,
                rule_id="SEC-001",
                rule_name="Hardcoded Secrets",
                rule_description="Detect hardcoded API keys, passwords, and tokens",
                severity="critical",
                category="security",
                file_path="src/config.py",
                line_number=15,
                message="Hardcoded API key detected in source code",
                code_snippet="API_KEY = 'sk_live_abc123def456'",
                ai_confidence=0.95,
                ai_explanation="This appears to be a production API key hardcoded in the source code.",
                ai_fix_suggestion="Move this to environment variables or a secure config service.",
                cve_ids=[],
                cwe_ids=["CWE-798"],
                compliance_frameworks=["PCI-DSS", "SOX"],
                exploitability_score=0.8,
                business_impact_score=0.9
            ),
            Violation(
                org_id=sample_org.id,
                scan_id=sample_scan.id,
                rule_id="PRI-002",
                rule_name="Data Collection Without Consent",
                rule_description="Detect data collection without proper user consent",
                severity="high",
                category="privacy",
                file_path="src/analytics.js",
                line_number=42,
                message="User tracking without explicit consent mechanism",
                code_snippet="analytics.track('user_action', userData);",
                ai_confidence=0.87,
                ai_explanation="This code tracks user data without checking for consent.",
                ai_fix_suggestion="Add consent check before tracking: if (hasConsent()) { ... }",
                compliance_frameworks=["GDPR", "CCPA"],
                exploitability_score=0.3,
                business_impact_score=0.7
            )
        ]
        
        for violation in sample_violations:
            db.add(violation)
        
        db.commit()
        print("✅ Sample data created successfully!")
        print(f"   Organization: {sample_org.name} (ID: {sample_org.id})")
        print(f"   Project: {sample_project.name} (ID: {sample_project.id})")
        print(f"   Scan: {sample_scan.id} ({sample_scan.total_violations} violations)")
        print(f"   API Key for testing: acme_test_api_key_123")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating sample data: {e}")
        return False
    finally:
        db.close()


def verify_database():
    """Verify database setup by running basic queries."""
    print("🔍 Verifying database setup...")
    
    db = SessionLocal()
    try:
        # Test basic queries
        org_count = db.query(Organization).count()
        project_count = db.query(Project).count()
        scan_count = db.query(Scan).count()
        violation_count = db.query(Violation).count()
        
        print(f"   Organizations: {org_count}")
        print(f"   Projects: {project_count}")
        print(f"   Scans: {scan_count}")
        print(f"   Violations: {violation_count}")
        
        # Test a join query (multi-tenant filtering)
        sample_org = db.query(Organization).first()
        if sample_org:
            org_violations = db.query(Violation).filter(
                Violation.org_id == sample_org.id
            ).count()
            print(f"   Violations for '{sample_org.name}': {org_violations}")
        
        print("✅ Database verification successful!")
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False
    finally:
        db.close()


def main():
    """Main function to run database setup."""
    print("🚀 DevSecOps Compliance Auditor - Database Setup")
    print("=" * 50)
    
    # Check if PostgreSQL connection works
    try:
        # Try to connect
        with engine.connect() as conn:
            result = conn.execute("SELECT version();")
            version = result.fetchone()[0]
            print(f"📊 Connected to PostgreSQL: {version[:50]}...")
    except Exception as e:
        print(f"❌ Cannot connect to PostgreSQL: {e}")
        print("   Make sure PostgreSQL is running and DATABASE_URL is correct")
        print(f"   Current DATABASE_URL: {os.getenv('DATABASE_URL', 'not set')}")
        return False
    
    # Initialize database
    if not init_database():
        return False
    
    # Create sample data
    if not create_sample_data():
        return False
    
    # Verify setup
    if not verify_database():
        return False
    
    print("\n🎉 Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Update your .env file with the correct DATABASE_URL")
    print("2. Use 'acme_test_api_key_123' for API testing")
    print("3. Check /docs endpoint for API documentation")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)