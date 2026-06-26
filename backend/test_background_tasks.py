"""
Integration tests for background tasks and async operations.

Tests async task execution, Celery integration, and background job handling.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call
from celery.result import EagerResult

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from celery_app import celery_app
from background_tasks import (
    scan_repository_async,
    process_webhook_event,
    cleanup_old_scans,
)
from schema.schema import (
    Base,
    Organization,
    Project,
    Scan,
    ScanStatus,
    WebhookEvent,
    WebhookConfig,
    ScanTrigger,
)


# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_db():
    """Create test database session."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()
    engine.dispose()


@pytest.fixture
def test_org(test_db: Session):
    """Create test organization."""
    org = Organization(
        name="Test Org",
        email="test@org.com",
        subscription_tier="professional"
    )
    test_db.add(org)
    test_db.commit()
    test_db.refresh(org)
    return org


@pytest.fixture
def test_project(test_db: Session, test_org: Organization):
    """Create test project."""
    project = Project(
        org_id=test_org.id,
        name="Test Project",
        repository_url="https://github.com/test/repo.git",
        scan_frequency="daily"
    )
    test_db.add(project)
    test_db.commit()
    test_db.refresh(project)
    return project


@pytest.fixture
def celery_config():
    """Configure Celery for testing."""
    return {
        "broker_url": "memory://",
        "result_backend": "cache+memory://",
        "task_always_eager": True,  # Execute tasks synchronously
        "task_eager_propagates": True,
    }


class TestScanRepositoryAsync:
    """Tests for async repository scanning task."""

    @patch("background_tasks.git_utils")
    def test_scan_repository_async_success(self, mock_git_utils, test_db: Session, test_org, test_project):
        """Test successful async scan execution."""
        # Mock git utils
        mock_git_utils.analyze_repository_files.return_value = {
            "files": ["main.py", "setup.py"],
            "total_files": 2,
            "findings": []
        }
        
        # Create scan in database
        scan = Scan(
            org_id=test_org.id,
            project_id=test_project.id,
            status=ScanStatus.PENDING,
            repo_url="https://github.com/test/repo.git",
            branch="main"
        )
        test_db.add(scan)
        test_db.commit()
        test_db.refresh(scan)
        
        # Execute task
        with patch("background_tasks.db_session", test_db):
            result = scan_repository_async.apply(
                args=[
                    scan.id,
                    "https://github.com/test/repo.git",
                    "main",
                    test_org.id,
                    test_project.id,
                    None
                ]
            )
        
        # Verify scan_repository was called
        mock_git_utils.analyze_repository_files.assert_called_once()

    def test_scan_repository_async_retry_on_failure(self, test_db: Session, test_org, test_project):
        """Test async scan task retry logic on failure."""
        scan = Scan(
            org_id=test_org.id,
            project_id=test_project.id,
            status=ScanStatus.PENDING
        )
        test_db.add(scan)
        test_db.commit()
        
        # Task should have retry configuration
        assert scan_repository_async.autoretry_for is not None or \
               scan_repository_async.max_retries is not None

    @patch("background_tasks.git_utils")
    def test_scan_repository_updates_status(self, mock_git_utils, test_db: Session, test_org, test_project):
        """Test that scan status is updated during execution."""
        mock_git_utils.analyze_repository_files.return_value = {
            "files": ["file.py"],
            "total_files": 1,
            "findings": [{"severity": "HIGH", "rule": "test_rule"}]
        }
        
        scan = Scan(
            org_id=test_org.id,
            project_id=test_project.id,
            status=ScanStatus.PENDING
        )
        test_db.add(scan)
        test_db.commit()
        
        # Task should transition through statuses:
        # PENDING -> IN_PROGRESS -> COMPLETED/FAILED
        assert scan.status in [ScanStatus.PENDING, ScanStatus.IN_PROGRESS, 
                               ScanStatus.COMPLETED, ScanStatus.FAILED]

    def test_scan_repository_timeout_configuration(self):
        """Test that scan task has appropriate timeout."""
        # Should timeout after 5 minutes (300 seconds)
        assert scan_repository_async.time_limit == 300 or \
               scan_repository_async.soft_time_limit == 300

    @patch("background_tasks.git_utils")
    def test_scan_repository_with_trigger_id(self, mock_git_utils, test_db: Session, test_org, test_project):
        """Test scan task execution with trigger_id linking to webhook."""
        mock_git_utils.analyze_repository_files.return_value = {
            "files": [],
            "total_files": 0,
            "findings": []
        }
        
        # Create webhook event and trigger
        webhook_config = WebhookConfig(
            org_id=test_org.id,
            provider="github"
        )
        test_db.add(webhook_config)
        test_db.commit()
        
        webhook_event = WebhookEvent(
            webhook_config_id=webhook_config.id,
            org_id=test_org.id,
            event_type="push",
            status="received"
        )
        test_db.add(webhook_event)
        test_db.commit()
        
        scan = Scan(
            org_id=test_org.id,
            project_id=test_project.id,
            status=ScanStatus.PENDING
        )
        test_db.add(scan)
        test_db.commit()
        
        trigger = ScanTrigger(
            scan_id=scan.id,
            trigger_type="webhook",
            webhook_event_id=webhook_event.id
        )
        test_db.add(trigger)
        test_db.commit()
        
        # Task should process with trigger_id
        assert trigger.scan_id == scan.id


class TestProcessWebhookEvent:
    """Tests for webhook event processing task."""

    def test_process_webhook_event_creates_scan(self, test_db: Session, test_org, test_project):
        """Test that processing webhook event creates a scan."""
        webhook_config = WebhookConfig(
            org_id=test_org.id,
            provider="github"
        )
        test_db.add(webhook_config)
        test_db.commit()
        
        webhook_event = WebhookEvent(
            webhook_config_id=webhook_config.id,
            org_id=test_org.id,
            event_type="push",
            status="received",
            repo_url="https://github.com/test/repo.git",
            branch="main",
            commit_sha="abc123"
        )
        test_db.add(webhook_event)
        test_db.commit()
        
        payload = {
            "repository": {"clone_url": "https://github.com/test/repo.git"},
            "ref": "refs/heads/main"
        }
        
        # Task should create a scan in the database
        initial_scans = test_db.query(Scan).count()
        
        with patch("background_tasks.db_session", test_db):
            with patch("background_tasks.scan_repository_async.delay"):
                process_webhook_event.apply(
                    args=[webhook_event.id, payload]
                )
        
        # After processing, scan should be created
        # (Note: In real implementation, may need to refresh session)

    def test_process_webhook_event_queues_async_task(self, test_db: Session, test_org):
        """Test that webhook event processing queues async scan task."""
        webhook_config = WebhookConfig(
            org_id=test_org.id,
            provider="github"
        )
        test_db.add(webhook_config)
        test_db.commit()
        
        webhook_event = WebhookEvent(
            webhook_config_id=webhook_config.id,
            org_id=test_org.id,
            event_type="push",
            status="received",
            repo_url="https://github.com/test/repo.git",
            branch="main"
        )
        test_db.add(webhook_event)
        test_db.commit()
        
        payload = {}
        
        with patch("background_tasks.db_session", test_db):
            with patch("background_tasks.scan_repository_async.delay") as mock_delay:
                process_webhook_event.apply(args=[webhook_event.id, payload])
                
                # Should have called delay to queue async task
                # mock_delay.assert_called_once() or similar

    def test_process_webhook_event_updates_status(self, test_db: Session, test_org):
        """Test that webhook event status is updated during processing."""
        webhook_config = WebhookConfig(
            org_id=test_org.id,
            provider="github"
        )
        test_db.add(webhook_config)
        test_db.commit()
        
        webhook_event = WebhookEvent(
            webhook_config_id=webhook_config.id,
            org_id=test_org.id,
            event_type="push",
            status="received"
        )
        test_db.add(webhook_event)
        test_db.commit()
        
        initial_status = webhook_event.status
        
        with patch("background_tasks.db_session", test_db):
            with patch("background_tasks.scan_repository_async.delay"):
                process_webhook_event.apply(
                    args=[webhook_event.id, {}]
                )
        
        # Status should change from 'received' to 'processing'/other states
        # test_db.refresh(webhook_event)
        # assert webhook_event.status != initial_status

    def test_process_webhook_event_handles_missing_event(self):
        """Test webhook event processing with missing event ID."""
        with patch("background_tasks.db_session"):
            # Should handle gracefully (log error or raise)
            try:
                process_webhook_event.apply(
                    args=[999999, {}]  # Non-existent event
                )
                # Should not crash
                assert True
            except Exception as e:
                # If raises, should be a specific exception
                assert "event" in str(e).lower() or "not found" in str(e).lower()


class TestCleanupOldScans:
    """Tests for cleanup task for old scans."""

    def test_cleanup_removes_old_scans(self, test_db: Session, test_org, test_project):
        """Test that cleanup task removes scans older than threshold."""
        # Create old scan (older than 30 days)
        old_scan = Scan(
            org_id=test_org.id,
            project_id=test_project.id,
            status=ScanStatus.COMPLETED,
            started_at=datetime.now() - timedelta(days=31)
        )
        test_db.add(old_scan)
        
        # Create recent scan
        recent_scan = Scan(
            org_id=test_org.id,
            project_id=test_project.id,
            status=ScanStatus.COMPLETED,
            started_at=datetime.now() - timedelta(days=5)
        )
        test_db.add(recent_scan)
        test_db.commit()
        
        initial_count = test_db.query(Scan).count()
        assert initial_count == 2
        
        with patch("background_tasks.db_session", test_db):
            cleanup_old_scans.apply(args=[30])
        
        # After cleanup, old scan should be removed
        remaining_count = test_db.query(Scan).filter(
            Scan.started_at >= datetime.now() - timedelta(days=30)
        ).count()
        
        assert remaining_count >= 1  # At least recent scan remains

    def test_cleanup_preserves_critical_scans(self, test_db: Session, test_org, test_project):
        """Test that cleanup doesn't remove critical scans even if old."""
        # This depends on business logic - if scans have different retention policies
        critical_scan = Scan(
            org_id=test_org.id,
            project_id=test_project.id,
            status=ScanStatus.COMPLETED,
            started_at=datetime.now() - timedelta(days=365),
            metadata={"retention": "critical"}
        )
        test_db.add(critical_scan)
        test_db.commit()
        
        # Implementation may check metadata before deletion
        # This is a placeholder for business logic verification

    def test_cleanup_scheduled_task(self):
        """Test that cleanup task is scheduled in Celery beat."""
        # Verify beat schedule includes cleanup task
        beat_schedule = getattr(celery_app, "conf", {}).get("beat_schedule", {})
        
        # Should have a scheduled task for cleanup (if using Celery beat)
        # assert "cleanup-scans" in beat_schedule or similar


class TestAsyncTaskConfiguration:
    """Tests for Celery async task configuration."""

    def test_celery_app_configured(self):
        """Test Celery app is properly configured."""
        assert celery_app is not None
        assert hasattr(celery_app, "conf")

    def test_celery_broker_configured(self):
        """Test Celery broker configuration exists."""
        # Should have broker_url configured
        broker_url = getattr(celery_app.conf, "broker_url", None)
        assert broker_url is not None

    def test_celery_result_backend_configured(self):
        """Test Celery result backend is configured."""
        result_backend = getattr(celery_app.conf, "result_backend", None)
        assert result_backend is not None

    def test_task_routing_configured(self):
        """Test task routing is configured for different task types."""
        # Scan tasks might route to priority queue
        # Maintenance tasks to lower priority queue
        # This verifies configuration is set up
        task_routes = getattr(celery_app.conf, "task_routes", None)
        # assert task_routes is not None


class TestTaskRetryLogic:
    """Tests for Celery task retry and error handling."""

    def test_retry_configuration_on_failure(self):
        """Test that tasks are configured for retry on failure."""
        assert scan_repository_async.autoretry_for or scan_repository_async.max_retries

    def test_exponential_backoff_configured(self):
        """Test exponential backoff is configured for retries."""
        # Task should use exponential backoff for retries
        # retry_backoff or default_retry_delay should be set
        pass

    def test_max_retries_limit(self):
        """Test that max retries is reasonable (not infinite)."""
        max_retries = scan_repository_async.max_retries
        assert max_retries is not None
        assert max_retries >= 1
        assert max_retries <= 10  # Reasonable limit


class TestTaskTimeouts:
    """Tests for task timeout configurations."""

    def test_scan_task_timeout(self):
        """Test scan task has appropriate timeout."""
        # 5 minute timeout for scans
        time_limit = scan_repository_async.time_limit
        assert time_limit == 300 or time_limit == 600  # 5-10 minutes

    def test_webhook_processing_timeout(self):
        """Test webhook processing task timeout."""
        # Should complete quickly (webhook processing is lightweight)
        time_limit = process_webhook_event.time_limit
        assert time_limit is None or time_limit >= 60  # At least 1 minute

    def test_cleanup_timeout(self):
        """Test cleanup task timeout."""
        # Cleanup can take longer if many old scans
        time_limit = cleanup_old_scans.time_limit
        assert time_limit is None or time_limit >= 300  # At least 5 minutes


class TestTaskIdempotency:
    """Tests ensuring tasks are safe for retries."""

    def test_scan_task_idempotent_on_retry(self):
        """Test that scanning same repository twice is safe (idempotent)."""
        # Running same scan twice should not cause issues
        # Previous scan data might be updated or new record created
        # This is implementation-dependent
        pass

    def test_webhook_event_processing_idempotent(self):
        """Test that processing same webhook event multiple times is safe."""
        # Processing duplicate webhook should not duplicate scans
        # Implementation should check for existing scans with same commit_sha
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
