"""
Webhook endpoints for CI/CD platform integration.

Supports GitHub, GitLab, and Bitbucket webhooks.
Handles signature verification and routes to async tasks.
"""

import os
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from webhook_handler import (
    WebhookDispatcher,
    WebhookProvider,
    WebhookPayload,
    GitHub,
    GitLab,
    Bitbucket
)
from schema.database import SessionLocal
from schema.schema import WebhookConfig, WebhookEvent, Organization
from background_tasks import process_webhook_event
from auth import get_current_org, OrgContext

logger = logging.getLogger(__name__)

# Create webhook router
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/github")
async def handle_github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    GitHub webhook endpoint.
    
    Verifies webhook signature, parses payload, and queues scan task.
    
    Args:
        request: FastAPI request object
        background_tasks: Background task queue
        db: Database session
        
    Returns:
        JSON response with webhook processing status
    """
    try:
        # Get headers
        signature = request.headers.get("X-Hub-Signature-256")
        event_type = request.headers.get("X-GitHub-Event")
        
        if not signature or not event_type:
            logger.warning("Missing GitHub webhook headers")
            raise HTTPException(status_code=400, detail="Missing webhook headers")
        
        # Read request body
        body = await request.body()
        
        # Get webhook secret from query parameter or config
        # In production, this should be retrieved from database based on repo
        webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
        
        if not webhook_secret:
            logger.error("GITHUB_WEBHOOK_SECRET not configured")
            raise HTTPException(status_code=500, detail="Webhook secret not configured")
        
        # Verify signature
        if not GitHub.verify_signature(body, signature, webhook_secret):
            logger.warning("GitHub webhook signature verification failed")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Parse request body as JSON
        import json
        payload = json.loads(body)
        
        # Parse webhook payload
        webhook_payload = GitHub.parse_push_event(payload)
        
        if not webhook_payload and event_type == "pull_request":
            webhook_payload = GitHub.parse_pull_request_event(payload)
        
        if not webhook_payload:
            logger.warning(f"Could not parse GitHub webhook event type: {event_type}")
            return JSONResponse(
                status_code=202,
                content={"status": "ignored", "message": f"Skipped event type: {event_type}"}
            )
        
        # Get org_id from webhook payload or default
        org_id = payload.get("organization", {}).get("id")
        if not org_id:
            # Try to get from repository owner
            org_id = payload.get("repository", {}).get("owner", {}).get("id")
        
        # Store webhook event
        webhook_event = WebhookEvent(
            webhook_config_id=None,  # Will be populated by webhook setup
            org_id=None,  # Will be populated from auth
            event_type=event_type,
            repo_url=str(webhook_payload.repo_url),
            branch=webhook_payload.branch,
            commit_sha=webhook_payload.commit_sha,
            status="received",
            payload=payload,
            metadata={"provider": "github"}
        )
        db.add(webhook_event)
        db.commit()
        
        # Queue webhook processing task
        process_webhook_event.delay(
            webhook_event_id=str(webhook_event.id),
            webhook_payload=webhook_payload.dict()
        )
        
        logger.info(f"Processed GitHub webhook event: {event_type} for {webhook_payload.repo_url}")
        
        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted",
                "message": "Webhook received and queued for processing",
                "webhook_event_id": str(webhook_event.id)
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing GitHub webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/gitlab")
async def handle_gitlab_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    GitLab webhook endpoint.
    
    GitLab uses token-based verification (X-Gitlab-Token header).
    
    Args:
        request: FastAPI request object
        background_tasks: Background task queue
        db: Database session
        
    Returns:
        JSON response with webhook processing status
    """
    try:
        # Get headers
        token = request.headers.get("X-Gitlab-Token")
        event_type = request.headers.get("X-Gitlab-Event")
        
        if not token or not event_type:
            logger.warning("Missing GitLab webhook headers")
            raise HTTPException(status_code=400, detail="Missing webhook headers")
        
        # Read request body
        body = await request.body()
        
        # Get webhook secret
        webhook_secret = os.getenv("GITLAB_WEBHOOK_SECRET", "")
        
        if not webhook_secret:
            logger.error("GITLAB_WEBHOOK_SECRET not configured")
            raise HTTPException(status_code=500, detail="Webhook secret not configured")
        
        # Verify token
        if not GitLab.verify_signature(body, token, webhook_secret):
            logger.warning("GitLab webhook token verification failed")
            raise HTTPException(status_code=401, detail="Invalid webhook token")
        
        # Parse request body as JSON
        import json
        payload = json.loads(body)
        
        # Parse webhook payload
        webhook_payload = None
        if event_type == "push_events":
            webhook_payload = GitLab.parse_push_event(payload)
        elif event_type == "merge_requests_events":
            webhook_payload = GitLab.parse_merge_request_event(payload)
        
        if not webhook_payload:
            logger.warning(f"Could not parse GitLab webhook event type: {event_type}")
            return JSONResponse(
                status_code=202,
                content={"status": "ignored", "message": f"Skipped event type: {event_type}"}
            )
        
        # Store webhook event
        webhook_event = WebhookEvent(
            webhook_config_id=None,
            org_id=None,
            event_type=event_type,
            repo_url=str(webhook_payload.repo_url),
            branch=webhook_payload.branch,
            commit_sha=webhook_payload.commit_sha,
            status="received",
            payload=payload,
            metadata={"provider": "gitlab"}
        )
        db.add(webhook_event)
        db.commit()
        
        # Queue webhook processing task
        process_webhook_event.delay(
            webhook_event_id=str(webhook_event.id),
            webhook_payload=webhook_payload.dict()
        )
        
        logger.info(f"Processed GitLab webhook event: {event_type} for {webhook_payload.repo_url}")
        
        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted",
                "message": "Webhook received and queued for processing",
                "webhook_event_id": str(webhook_event.id)
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing GitLab webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/bitbucket")
async def handle_bitbucket_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Bitbucket webhook endpoint.
    
    Verifies webhook signature using HMAC and processes payload.
    
    Args:
        request: FastAPI request object
        background_tasks: Background task queue
        db: Database session
        
    Returns:
        JSON response with webhook processing status
    """
    try:
        # Get headers
        signature = request.headers.get("X-Hub-Signature")
        
        if not signature:
            logger.warning("Missing Bitbucket webhook signature")
            raise HTTPException(status_code=400, detail="Missing webhook signature")
        
        # Read request body
        body = await request.body()
        
        # Get webhook secret
        webhook_secret = os.getenv("BITBUCKET_WEBHOOK_SECRET", "")
        
        if not webhook_secret:
            logger.error("BITBUCKET_WEBHOOK_SECRET not configured")
            raise HTTPException(status_code=500, detail="Webhook secret not configured")
        
        # Verify signature
        if not Bitbucket.verify_signature(body, signature, webhook_secret):
            logger.warning("Bitbucket webhook signature verification failed")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Parse request body as JSON
        import json
        payload = json.loads(body)
        
        # Parse webhook payload (only supporting push events for now)
        webhook_payload = Bitbucket.parse_push_event(payload)
        
        if not webhook_payload:
            logger.warning("Could not parse Bitbucket webhook payload")
            return JSONResponse(
                status_code=202,
                content={"status": "ignored", "message": "Skipped event type"}
            )
        
        # Store webhook event
        webhook_event = WebhookEvent(
            webhook_config_id=None,
            org_id=None,
            event_type="push",
            repo_url=str(webhook_payload.repo_url),
            branch=webhook_payload.branch,
            commit_sha=webhook_payload.commit_sha,
            status="received",
            payload=payload,
            metadata={"provider": "bitbucket"}
        )
        db.add(webhook_event)
        db.commit()
        
        # Queue webhook processing task
        process_webhook_event.delay(
            webhook_event_id=str(webhook_event.id),
            webhook_payload=webhook_payload.dict()
        )
        
        logger.info(f"Processed Bitbucket webhook for {webhook_payload.repo_url}")
        
        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted",
                "message": "Webhook received and queued for processing",
                "webhook_event_id": str(webhook_event.id)
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Bitbucket webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/events/{org_id}")
def list_webhook_events(
    org_id: str,
    current_org: OrgContext = Depends(get_current_org),
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List webhook events for an organization.
    
    Multi-tenant: Only returns events for the current organization.
    
    Args:
        org_id: Organization ID
        current_org: Current organization context
        status: Optional status filter (received/processing/processed/failed)
        limit: Number of events to return
        offset: Pagination offset
        db: Database session
        
    Returns:
        List of webhook events
    """
    try:
        # Tenant isolation: Verify user has access to this org
        if str(current_org.id) != org_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        query = db.query(WebhookEvent).filter(WebhookEvent.org_id == org_id)
        
        if status:
            query = query.filter(WebhookEvent.status == status)
        
        events = query.order_by(WebhookEvent.created_at.desc()).offset(offset).limit(limit).all()
        
        return {
            "status": "success",
            "org_id": org_id,
            "events": [
                {
                    "id": str(event.id),
                    "event_type": event.event_type,
                    "repo_url": event.repo_url,
                    "branch": event.branch,
                    "commit_sha": event.commit_sha,
                    "status": event.status,
                    "scan_id": str(event.scan_id) if event.scan_id else None,
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                    "error_message": event.error_message
                }
                for event in events
            ],
            "count": len(events)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing webhook events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/events/{org_id}/{event_id}")
def get_webhook_event(
    org_id: str,
    event_id: str,
    current_org: OrgContext = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific webhook event.
    
    Args:
        org_id: Organization ID
        event_id: Webhook event ID
        current_org: Current organization context
        db: Database session
        
    Returns:
        Webhook event details including full payload
    """
    try:
        # Tenant isolation
        if str(current_org.id) != org_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        event = db.query(WebhookEvent).filter(
            WebhookEvent.id == event_id,
            WebhookEvent.org_id == org_id
        ).first()
        
        if not event:
            raise HTTPException(status_code=404, detail="Webhook event not found")
        
        return {
            "status": "success",
            "event": {
                "id": str(event.id),
                "event_type": event.event_type,
                "repo_url": event.repo_url,
                "branch": event.branch,
                "commit_sha": event.commit_sha,
                "status": event.status,
                "scan_id": str(event.scan_id) if event.scan_id else None,
                "payload": event.payload,
                "error_message": event.error_message,
                "retry_count": event.retry_count,
                "created_at": event.created_at.isoformat() if event.created_at else None,
                "processed_at": event.processed_at.isoformat() if event.processed_at else None
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving webhook event: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
