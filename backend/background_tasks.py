"""
Background tasks for compliance auditor.
Handles async scanning, webhook processing, and other long-running operations.
"""

import logging
from typing import Optional, Dict, Any
from celery import current_task
from celery_app import celery_app
from schema.database import SessionLocal
from schema.schema import Scan, WebhookEvent, ScanTrigger, Organization, Project
import traceback
from datetime import datetime
from utils.git_utils import git_clone, analyze_repository_files

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def scan_repository_async(
    self,
    scan_id: str,
    repo_url: str,
    branch: str = "main",
    org_id: str = None,
    project_id: str = None,
    trigger_id: str = None
) -> Dict[str, Any]:
    """
    Asynchronous repository scanning task.
    
    This task:
    1. Clones the repository
    2. Analyzes files for compliance issues
    3. Stores results in database
    4. Updates scan status
    
    Args:
        scan_id: UUID of the scan record
        repo_url: Repository URL to scan
        branch: Branch to scan (default: main)
        org_id: Organization ID for multi-tenancy
        project_id: Project ID if part of a project
        trigger_id: Scan trigger ID (webhook, scheduled, etc.)
        
    Returns:
        Dict with scan results and status
    """
    db = SessionLocal()
    
    try:
        self.update_state(state="PROGRESS", meta={"status": "Starting scan"})
        logger.info(f"Starting async scan {scan_id} for repo {repo_url}")
        
        # Update scan status to in_progress
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            logger.error(f"Scan {scan_id} not found")
            return {"status": "error", "message": "Scan not found"}
        
        scan.status = "in_progress"
        scan.started_at = datetime.utcnow()
        db.commit()
        
        # Clone repository
        self.update_state(state="PROGRESS", meta={"status": "Cloning repository"})
        logger.info(f"Cloning repository: {repo_url}")
        
        repo_path = git_clone(repo_url, branch)
        if not repo_path:
            raise Exception(f"Failed to clone repository: {repo_url}")
        
        logger.info(f"Repository cloned to {repo_path}")
        
        # Analyze repository
        self.update_state(state="PROGRESS", meta={"status": "Analyzing repository"})
        logger.info(f"Analyzing repository for compliance issues")
        
        violations, analysis_metadata = analyze_repository_files(repo_path)
        
        logger.info(f"Found {len(violations)} violations")
        
        # Store violations in database
        scan.violations_count = len(violations)
        scan.status = "completed"
        scan.completed_at = datetime.utcnow()
        scan.scan_context = {
            "violations": violations,
            "analysis_metadata": analysis_metadata,
        }
        
        db.commit()
        
        logger.info(f"Scan {scan_id} completed successfully")
        
        return {
            "status": "success",
            "scan_id": scan_id,
            "violations_count": len(violations),
            "message": f"Scan completed with {len(violations)} violations found"
        }
    
    except Exception as e:
        logger.error(f"Error in scan_repository_async: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Update scan status to failed
        try:
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if scan:
                scan.status = "failed"
                scan.completed_at = datetime.utcnow()
                scan.scan_context = {"error": str(e)}
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update scan status: {db_error}")
        
        # Retry the task
        raise self.retry(exc=e, countdown=60)  # Retry after 60 seconds
    
    finally:
        db.close()


@celery_app.task(bind=True)
def process_webhook_event(
    self,
    webhook_event_id: str,
    webhook_payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process webhook event and trigger scan.
    
    Args:
        webhook_event_id: ID of the webhook event record
        webhook_payload: Normalized webhook payload
        
    Returns:
        Dict with processing status
    """
    db = SessionLocal()
    
    try:
        logger.info(f"Processing webhook event {webhook_event_id}")
        
        # Update webhook event status
        webhook_event = db.query(WebhookEvent).filter(
            WebhookEvent.id == webhook_event_id
        ).first()
        
        if not webhook_event:
            logger.error(f"Webhook event {webhook_event_id} not found")
            return {"status": "error", "message": "Webhook event not found"}
        
        webhook_event.status = "processing"
        db.commit()
        
        # Extract webhook payload data
        repo_url = webhook_payload.get("repo_url")
        branch = webhook_payload.get("branch", "main")
        commit_sha = webhook_payload.get("commit_sha")
        org_id = webhook_payload.get("org_id")
        
        # Create new scan record
        scan = Scan(
            org_id=org_id,
            repo_url=repo_url,
            branch=branch,
            status="queued",
        )
        db.add(scan)
        db.commit()
        
        # Create scan trigger record
        trigger = ScanTrigger(
            scan_id=scan.id,
            trigger_type="webhook",
            trigger_source=webhook_event.webhook_config.provider,
            webhook_event_id=webhook_event.id,
            metadata=webhook_payload
        )
        db.add(trigger)
        
        # Update scan with trigger
        scan.trigger_id = trigger.id
        
        webhook_event.status = "processed"
        webhook_event.scan_id = scan.id
        db.commit()
        
        # Queue async scan task
        scan_task = scan_repository_async.delay(
            scan_id=str(scan.id),
            repo_url=repo_url,
            branch=branch,
            org_id=str(org_id) if org_id else None,
            trigger_id=str(trigger.id)
        )
        
        logger.info(f"Queued scan task {scan_task.id} for webhook event {webhook_event_id}")
        
        return {
            "status": "success",
            "scan_id": str(scan.id),
            "task_id": scan_task.id,
            "message": "Webhook event processed and scan queued"
        }
    
    except Exception as e:
        logger.error(f"Error processing webhook event: {str(e)}")
        logger.error(traceback.format_exc())
        
        try:
            webhook_event = db.query(WebhookEvent).filter(
                WebhookEvent.id == webhook_event_id
            ).first()
            if webhook_event:
                webhook_event.status = "failed"
                webhook_event.webhook_context = {"error": str(e)}
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update webhook event status: {db_error}")
        
        return {"status": "error", "message": str(e)}
    
    finally:
        db.close()


@celery_app.task
def cleanup_old_scans(days: int = 30) -> Dict[str, Any]:
    """
    Cleanup old scan records (optional maintenance task).
    
    Args:
        days: Delete scans older than this many days
        
    Returns:
        Dict with cleanup statistics
    """
    db = SessionLocal()
    
    try:
        from sqlalchemy import and_
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Delete old completed scans
        deleted_count = db.query(Scan).filter(
            and_(
                Scan.status == "completed",
                Scan.completed_at < cutoff_date
            )
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old scans")
        
        return {
            "status": "success",
            "deleted_scans": deleted_count,
            "cutoff_date": str(cutoff_date)
        }
    
    except Exception as e:
        logger.error(f"Error cleaning up old scans: {str(e)}")
        return {"status": "error", "message": str(e)}
    
    finally:
        db.close()
